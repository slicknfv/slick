# Copyright 2011 James McCauley
#
# This file is part of POX.
#
# POX is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# POX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with POX.  If not, see <http://www.gnu.org/licenses/>.

import time
import logging
import sys  # for loading the application from commandline

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.util import dpid_to_str
from pox.lib.util import str_to_bool
from pox.lib.recoco import Timer # For timer calls.
from pox.lib.addresses import *


from route_compiler import RouteCompiler
from msmessageproc import MSMessageProcessor
from conf import *
from download import Download
#from pox_interface import POXInterface
from utils.packet_utils import *

from apps import *

log = core.getLogger()


class slick_controller (object):
    """
    Waits for OpenFlow switches to connect 
    """
    def __init__ (self, transparent, application):
        print "INITIALIZING SLICK with application '" + application + "'"

        self.transparent = transparent

        # add the standard OpenFlow event handlers
        core.openflow.addListeners(self)
        #self.connection.addListeners(self)

        # Function Descriptors
        self.function_descriptor = int(1)
        self.prev_time = 0
        #routing
        self.route_compiler =  RouteCompiler()
        # JSON Messenger Handlers
        self.json_msg_events = {}

        # Application descriptor
        self._latest_app_descriptor = 100

        # Message Processor.  Where App Handles are Initialized.
        self.ms_msg_proc = MSMessageProcessor(self)

        # TODO Initialize the application
        
        app_class = sys.modules['slick.apps.'+application].__dict__[application]
        self.app_instance = app_class( self, self._get_unique_app_descriptor() )
        self.ms_msg_proc.add_application( self.app_instance )

        print "Successfully loaded",application,"application"

        #
        self.app_initialized = False
        self.switches = {} # A dictionary of switch ids and if the mac is a middlebox or not. 
        self.switch_connections = {}
        self.download = Download()
        self.controller_interface = POXInterface(self)

        # Application Initialization and Configuration.
        Timer(APPCONF_REFRESH_RATE, self.timer_callback, recurring = True)

    def _get_unique_app_descriptor(self):
        self._latest_app_descriptor += 1
        return self._latest_app_descriptor

    def _handle_ConnectionUp (self, event):
        log.debug("Connection %s" % (event.connection,))
        self.switches[event.dpid] = self._is_middlebox() # Keep track of switches.
        self.switch_connections[event.dpid] = event.connection

    # This box is for the middlebox.
    # Can one MAC be a middlebox and an IP address.
    def _is_middlebox(self):
        # If this mac is for the middlebox.
        return False

    def get_connection(self,dpid):
        if(self.switch_connections.has_key(dpid)):
            return self.switch_connections[dpid]
    
    def timer_callback(self):
        # Periodically initialize the applications.
        # Calling repeatedly allows for dynamic app loading (in theory)
        for app in self.ms_msg_proc.app_handles:
            log.debug("timer_callback %s", str(app))
            if not (app.installed):
                app.init()

        # Configure/Read the configurations again and again
        # Call configuration on the application repeatedly so
        # we can change configuration on the fly

        for fd in self.route_compiler.application_handles:
            app_handle = self.route_compiler.get_application_handle(fd)
            app_handle.configure_user_params()
        return True

    # Slick API Functions
    """
    Controller to Application Functions
    """
    # return function descriptor.
    # ERROR Codes:
    #   -1 : Error in installing the function
    #   -2 : Error in downloading the files to middlebox.
    #   -3 : Error in adding a middlebox client.
    def apply_elem(self, app_desc,flow, function_name,parameters,application_object):

        is_last_call = True # Should be argument of the apply_elem functions
        self.function_descriptor += 1

        ##
        # STEP 1: Find the middlebox where this function should be installed.

        #self.application_descriptor = app_desc#+= 1 # App is providing the right application descriptor to the controller.
        if(self.route_compiler.is_installed(app_desc)):# We have the application installed
            log.debug("Creating another function for application: %d",app_desc)

        # Note: Optimization should be happening here, but right now we're just pulling
        # the first middlebox that implements the function
        mac_addr = self.route_compiler.fmap.get_machine_for_element(function_name)

        if(mac_addr != None):
            log.debug("MAC Address of middlebox machine %s" % mac_addr)
        ip_addr = self.route_compiler.fmap.get_ip_addr(mac_addr)

        if(mac_addr == None): # There is no machine registered for function installation.
            print "Warning: Could not find a middlebox for function " + function_name + " for application with descriptor (" + str(app_desc) + ")"
            return -1
        msg_dst = ip_addr

        ##
        # STEP 2: Install the function.

        #mac_addr = self.route_compiler.fmap.fd_machine_map[ip_addr]
        self.route_compiler.fmap.update_element_machine(ip_addr,mac_addr,self.function_descriptor)
        self.route_compiler.policy.add_flow(None,flow,{self.function_descriptor:function_name}) #Function descriptor 
        self.route_compiler.update_application_handles(self.function_descriptor,application_object,app_desc)
        #msg = {"type":"install", "fd":self.function_descriptor, "flow":flow,"function_name":function_name,"params":{"k1":"dummy"}}

        if(self.download.add_mb_client(mac_addr,ip_addr,None,None)):
            # Given the function name send the files to the middlebox.
            if(self.download.put_file(mac_addr,function_name)):
                if(self.ms_msg_proc.send_install_msg(self.function_descriptor,flow,function_name,parameters,mac_addr)):
                    #if(is_last_call):
                    #    self.controller_interface.mb_placement_steering(mac_addr,flow,self.function_descriptor)
                    return self.function_descriptor
                else:
                    return -1
            else:
                return -2
        else:
            return -3

    def configure_elem(self,app_desc,fd,application_conf_params):
        if(self.route_compiler.application_handles.has_key(fd)):
            if(self.route_compiler.is_allowed(app_desc,fd)):
                msg_dst = self.route_compiler.fmap.get_mac_addr_from_element_desc(fd)
                app_handle = self.route_compiler.get_application_handle(fd) # not requied by additional check 
                if((msg_dst != None) and (app_handle != None)):
                    self.ms_msg_proc.send_configure_msg(fd,application_conf_params,msg_dst)

    #TODO:
    def remove_elem(self,app_desc,fd):
        # roll back
        if(self.ms_msg_proc.send_remove_msg(fd,parameters,mac_addr)):
          desc_removed = self.route_compiler.fmap.del_element_desc(fd)
        #update mb_placement_steering for changed elements

from pox.core import core
import pox.openflow.discovery

class POXInterface():
    def __init__(self,cntxt):
        self.cntxt = cntxt
        
    """ 
      This interface is for Placement and Steering Algorithm.
    """

    """
      @args:
         List of swiches that represents the path. This includes source and destination switch.
      @returns:
         Return the capacituy on the given path.
    """
    def GetPathCapacity(self,path):
      pass

    """
      @args:
         List of swiches that represents the path. This includes source and destination switch.
      @returns:
         Return the bandwidth on the given path.
    """
    def GetPathAvailableBandwidth(self,path):
      pass

    """
      @args:
         Given a link return the capacity.
         Each location is switch,port
      @returns:
         Return the capacity of link.
    """
    def GetLinkCapacity(self,loc1,loc2):
        pass

    """
      @args:
         Given a link return the available bandwidth.
         Each location is switch,port
      @returns:
         Return the bandwidth on the given path.
    """
    def GetLinkBandwidth(self,loc1,loc2):
      pass

    
    """
      @args:
         MAC Address of machine that we want to get the resources about.
      @returns:
         Return key:value pair of machine resources.
    """
    def GetMachineResource(self,mac_addr):
      pass

    """
      @args:
         MAC Address of machine that we want to get the memory usage.
      @returns:
         Return bytes available on the machine.
    """
    def GetMemoryUsage(self,mac_addr):
      pass

    """
      @args:
         MAC Address of machine that we want to get the Processor Usage.
      @returns:
         Return bytes available on the machine.
    """
    def GetProcessorUsage(self,mac_addr):
      pass

    """
      @args:
         Return Network Usage.
      @returns:
         Return bytes available on the machine.
    """
    def GetNetworkUsage(self,mac_addr):
      pass

    """
        Description:
            Return all available flows that need servicing. These flows are taken from applications.
            As each flow is registered before being applied.
    """
    def GetFlows(self):
      pass

    """
        Description:
            Return flow to Element matching.
    """
    def GetElement(self,flow):
      pass

    """
        Description:
            Return the element implementations for the given element name.
            This information is required by the PSA (Placement and Steering Algorithm) 
            to instantiate best implmentation of an Element.
    """
    def GetElements(self,element_name):
        pass

    """
        List of element instance ids that are currently serving flows. For each
        new flow a new element instance is instantiated but for element instances that
        can be shared by multiple applications th
    """
    def GetActiveElements(self):
        pass


    """Get Elements running on the given mac """ 
    def GetElements(self,machine_mac):
        pass

    """
        return the  mac addresses that we can use for middlebox machines.
    """
    def GetMiddleboxes(self):
        pass

    """ Given the path return all the middleboxes on the  path """
    def GetMiddleboxes(self,path):
        pass

    """ Given the element_id return number of flows that can be redirected to the middlebox """
    def GetMiddleboxCapacity(self,element_id):
      pass
    # @args:
    #       List of function descriptors
    # 
    # -
    def mb_placement_steering(self,mb_mac,flow,function_descriptors):
        print mb_mac
        print flow
        print function_descriptor
        if(mb_mac!= None): # we have already placed the function
            for item in function_descriptors:
                pass
            pass
        pass

    # Wrapper for slick controller interface.
    # returns the dictionary of function descriptors to MAC addresses
    # Note: This assumes that the placement of elements is already fixed.
    # The updates to element placement could happen on a slower timescale.

    # This should ultimately:
    # 1. Determine the right set of middleboxes
    # 2. Determine the right ordering for the middleboxes
    # (doesn't do this right now)

    def get_element_descriptors(self,flow):
        element_macs = {}

        # Find the function descriptors.
        # TODO: can you remove a level of indirection here?
        function_descriptors = self.cntxt.route_compiler.policy.get_flow_functions(flow.in_port,flow) 

        for func_desc,function_name in function_descriptors.iteritems():
            #print func_desc,function_name
            mac_addr_temp = self.cntxt.route_compiler.fmap.get_mac_addr_from_element_desc(func_desc) 

            # Convert MAC in Long to EthAddr
            mac_str = mac_to_str(mac_addr_temp)
            mac_addr = EthAddr(mac_str)
            element_macs[func_desc] = mac_addr
        return element_macs


    # This is a utils function.
    # This function returns a matching flow 
    # flow is of type ofp_match
    def get_generic_flow(self,flow):
        matching_flow = flow
        matched_flow_tuple = self.cntxt.route_compiler.policy.get_matching_flow(flow) # Find the function descriptors.
        return matched_flow_tuple

        if(matched_flow_tuple != None):
            #Can't assign in port as its assigned by the routing algorithm.
            matching_flow.dl_src = matched_flow_tuple.dl_src
            matching_flow.dl_dst = matched_flow_tuple.dl_dst
            matching_flow.dl_vlan = matched_flow_tuple.dl_vlan
            matching_flow.dl_vlan_pcp = matched_flow_tuple.dl_vlan_pcp
            matching_flow.dl_type = matched_flow_tuple.dl_type
            matching_flow.nw_tos = None  #matched_flow_tuple.nw_tos
            matching_flow.nw_proto = matched_flow_tuple.nw_proto
            matching_flow.nw_src = matched_flow_tuple.nw_src
            matching_flow.nw_dst = matched_flow_tuple.nw_dst
            matching_flow.tp_dst = matched_flow_tuple.tp_dst
            matching_flow.tp_src = matched_flow_tuple.tp_src
        else:
            return None # so we know there is no match.
        return matching_flow

##############################
# POX Launch the application.
##############################
def launch (transparent=False, application="TwoLoggers"):
    # The second component is argument for slick_controller.
    core.registerNew(slick_controller, str_to_bool(transparent), application)
