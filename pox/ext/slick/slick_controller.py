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

"""
An L2 learning switch.

It is derived from one written live for an SDN crash course.
It is somwhat similar to NOX's pyswitch in that it installs
exact-match rules for each flow.
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.util import dpid_to_str
from pox.lib.util import str_to_bool
import time
from pox.lib.recoco import Timer # For timer calls.


from route_compiler import RouteCompiler
from msmessageproc import MSMessageProcessor
from conf import *

log = core.getLogger()


## This class has information about the Slick Controller initialization.
#class SlickInit (object):
#    def __init__ (self, connection, transparent):
#        # Switch we'll be adding L2 learning switch capabilities to
#        self.connection = connection
#        # We want to hear PacketIn messages, so we listen
#        # to the connectio
#        # But we also need datapath_join event and the datapath_leave event.i.e. connectionUP and connectionDown
#        self.connection.addListeners(self)


class slick_controller (object):
    """
    Waits for OpenFlow switches to connect 
    """
    def __init__ (self, transparent):
        self.transparent = transparent
        core.openflow.addListeners(self)
        #self.connection.addListeners(self)

        # Function Descriptors
        self.function_descriptor = int(1)
        self.prev_time = 0
        #routing
        self.route_compiler =  RouteCompiler(self)
        # JSON Messenger Handlers
        self.json_msg_events = {}
        self.ms_msg_proc = MSMessageProcessor(self)
        self.app_initialized = False
        self.switches = {} # A dictionary of switch ids and if the mac is a middlebox or not. 
        self.switch_connections = {}

        # Application Initialization and Configuration.
        Timer(APPCONF_REFRESH_RATE, self.timer_callback, recurring = True)

    def _handle_ConnectionUp (self, event):
        log.debug("Connection %s" % (event.connection,))
        print "Connection %s" % (event.connection,)
        self.switches[event.dpid] = self._is_middlebox() # Keep track of switches.
        self.switch_connections[event.dpid] = event.connection

    def _handle_PacketIn (self, event):
        """
        Handle packet in messages from the switch to implement above algorithm.
        """
        packet = event.parsed
        """
        print packet.src
        print packet.dst
        """
        # Handle the functions
        #self.handle_functions(event)

    # This box is for the middlebox.
    # Can one MAC be a middlebox and an IP address.
    def _is_middlebox(self):
        # If this mac is for the middlebox.
        return False

    def get_connection(self,dpid):
        if(self.switch_connections.has_key(dpid)):
            return self.switch_connections[dpid]
    
    def app_installations(self):
        # For the  MSManager for JSONMsgs
        JSONMsg_event.register_event_converter(self.ctxt)
        self.register_handler(JSONMsg_event.static_get_name(), self.json_message_handler)

    def timer_callback(self):
        # initialize the applications.
        for app in self.ms_msg_proc.app_handles:
            if not (app.installed):
                app.init()
                print app

        #Configure/ Read the configurations again and again
        for fd in self.route_compiler.application_handles:
            app_handle = self.route_compiler.get_application_handle(fd)
            app_handle.configure_user_params()
        return True

    # Slick API Functions
    """
    Controller to Application Functions
    """
    # return function descriptor.
    def apply_func(self, app_desc,flow, function_name,parameters,application_object):
        self.function_descriptor += 1
        #self.application_descriptor = app_desc#+= 1 # App is providing the right application descriptor to the controller.
        if(self.route_compiler.is_installed(app_desc)):# We have the application installed
            print "Creating another function for application: ",app_desc
        mac_addr = self.route_compiler.fmap.get_machine_for_function()
        ip_addr = self.route_compiler.fmap.get_ip_addr(mac_addr)
        if(mac_addr == None): # There is no machine registerd for function installation.
            print "Could not find the Middlebox"
            return -1
        msg_dst = ip_addr
        #mac_addr = self.route_compiler.fmap.fd_machine_map[ip_addr]
        self.route_compiler.fmap.update_function_machine(ip_addr,mac_addr,self.function_descriptor)
        self.route_compiler.policy.add_flow(None,flow,{self.function_descriptor:function_name}) #Function descriptor 
        self.route_compiler.update_application_handles(self.function_descriptor,application_object,app_desc)
        #msg = {"type":"install", "fd":self.function_descriptor, "flow":flow,"function_name":function_name,"params":{"k1":"dummy"}}
        if(self.ms_msg_proc.send_install_msg(self.function_descriptor,flow,function_name,parameters,mac_addr)):
            return self.function_descriptor
        else:
            return -1

                
    #This function takes the src dpid, dst dpid and list of machines .. the
    #
    def pickMBMachine(self, src, dst, machinelist):
        shortestPath = 0
        shortestPath_MB = machinelist[0]
        for mb in machinelist:
            mb_dpid = XXXXXXXXXXXXXXXXXXXXXX
            route1 = pyrouting.Route()
            route1.id.src = src
            route1.id.dst = mb_dpid
            route2 = pyrouting.Route()
            route2.id.src = mb_dpid
            route2.id.dst = dst
            if( len(route1.path) + len(route2.path) < shortestPath):
                shortestPath = len(route1.path) + len(route2.path)
                shortestPath_MB = mb
        return mb

    def configure_func(self,app_desc,fd,application_conf_params):
        if(self.route_compiler.application_handles.has_key(fd)):
            if(self.route_compiler.is_allowed(app_desc,fd)):
                msg_dst = self.route_compiler.fmap.get_mac_addr_from_func_desc(fd)
                app_handle = self.route_compiler.get_application_handle(fd) # not requied by additional check 
                #print "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV",str(msg_dst)
                if((msg_dst != None) and (app_handle != None)):
                    self.ms_msg_proc.send_configure_msg(fd,application_conf_params,msg_dst)

    #TODO:
    def remove_func(self,app_desc,fd):
        # roll back
        desc_removed = self.route_compiler.fmap.del_function_desc(fd)

##############################
# POX Launch the application.
##############################
def launch (transparent=False):
    # The second component is argument for slick_controller.
    core.registerNew(slick_controller, str_to_bool(transparent))
