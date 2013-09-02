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


#from route_compiler import ElementToApplication
from networkmaps import ElementToMac,FlowToElementsMapping,MacToIP,ElementToApplication
from msmessageproc import MSMessageProcessor
from conf import *
from download import Download
#from pox_interface import POXInterface
from utils.packet_utils import *

from apps import *

from slick.routing.ShortestPathRouting import ShortestPathRouting
from slick.steering.RandomSteering import RandomSteering
from slick.placement.RandomPlacement import RandomPlacement
from slick.NetworkModel import NetworkModel

log = core.getLogger()


class slick_controller (object):
    """
    Waits for OpenFlow switches to connect 
    """
    def __init__ (self, transparent, application):
        print "INITIALIZING SLICK with application '" + application + "'"

        self.transparent = transparent

        # Modules
        self.network_model = NetworkModel(self)
        self.placement_module = RandomPlacement( self.network_model )
        self.steering_module = RandomSteering( self.network_model )
        self.routing_module = ShortestPathRouting( self.network_model )

        # add the standard OpenFlow event handlers
        core.openflow.addListeners(self)
        #self.connection.addListeners(self)

        # Element Descriptors
        self._latest_element_descriptor = int(1)
        self.prev_time = 0

        # Various mappings between elements, applications, and machines -- TODO Rename
        self.elem_to_app =  ElementToApplication()
        self.elem_to_mac = ElementToMac()
        self.flow_to_elems = FlowToElementsMapping()
        self.mac_to_ip = MacToIP()

        # JSON Messenger Handlers
        self.json_msg_events = {}

        # Application descriptor
        self._latest_app_descriptor = 100

        # Message Processor.  Where App Handles are Initialized.
        self.ms_msg_proc = MSMessageProcessor(self)

        # Load the application
        app_class = sys.modules['slick.apps.'+application].__dict__[application]
        self.app_instance = app_class( self, self._get_unique_app_descriptor() )
        self.ms_msg_proc.add_application( self.app_instance )

        log.debug("Successfully loaded " + application + "application. I will now periodically try to initialize it.")

        self.app_initialized = False
        self.switches = {} # A dictionary of switch ids and if the mac is a middlebox or not. 
        self.switch_connections = {}

        # For uploading element code to machines
        self.download = Download()

        # Exposes some wrappers, particularly for l2_multi_slick
        self.controller_interface = POXInterface(self)

        # Application Initialization and Configuration.
        Timer(APPCONF_REFRESH_RATE, self.timer_callback, recurring = True)

    def _get_unique_app_descriptor(self):
        self._latest_app_descriptor += 1
        return self._latest_app_descriptor

    def _get_unique_element_descriptor(self):
        self._latest_element_descriptor += 1
        return self._latest_element_descriptor

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
    
    """
    This method is periodically called for each running application (currently only one app)
    The rationale behind having it is that the app might be registered before shims have come online,
    so it tries init()'ing the application until it is able to install its elements
    """
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

        for elem_desc in self.elem_to_app.application_handles:
            app_handle = self.elem_to_app.get_app_handle(elem_desc)
            app_handle.configure_user_params()
        return True

    """
    msmessageproc calls this method when it receives a "register" message from a shim
    The goal is to simply maintain a list of all registered machines
    """
    def register_machine(self, machine_ip, machine_mac):
        self.mac_to_ip.add(machine_mac, machine_ip)
        self.elem_to_mac.add(machine_ip, machine_mac, None)  # as per old msmessageproc

    """
    Returns all shims who have registered (TODO: remove those who have gone offline)
    This is used by the NetworkModel to inform the Placement module about viable placements
    """
    def get_all_registered_machines(self):
        return self.mac_to_ip.get_all_macs()
        

    # Slick API Functions

    """
    Applications call this method to install new elements.  When they do so, they must
    specify a flowspace ('flow') on which to apply the element.  They can also supply
    initialization parameters.
    The method does the following:
        - Perform placement (i.e., decide on which machine to install the element)
        - Upload the element to the machine
        - Inform the shim of what flows to apply the element to
        - Update our internal state

    Return values:
       >=0 : success (returns the element descriptor)
        -1 : Error installing the function
        -2 : Error in downloading the files to middlebox.
        -3 : Error in adding a middlebox client.

    TODO : support *chains* of elements, that is, instead of taking a single
           element_name, take an array of element names, so an application can
           compose elements for a given flowspace
    """
    def apply_elem (self, app_desc, flow, element_name, parameters, application_object):

        elem_desc = self._get_unique_element_descriptor()

        ##
        # STEP 0: check that this application actually owns this element

        # TODO We need to see if this application is installed some other way;
        #      the problem with this is that elem_to_app won't know anything
        #      about app_desc until it has applied an element (i.e., this will fail
        #      the first time an app tries to apply an element)
        if(self.elem_to_app.contains_app(app_desc)):# We have the application installed
            log.debug("Creating another function for application: %d",app_desc)

        ##
        # STEP 1: Find the middlebox where this function should be installed.

        # TODO get_placement expects an array; this method should eventually
        #      take an array, but right now we're building it by hand
        mac_addrs = self.placement_module.get_placement([element_name])

        # Return an error if there is no machine registered for function installation.
        if(mac_addrs == None):
            print "Warning: Could not find a middlebox for function " + element_name + " for application with descriptor (" + str(app_desc) + ")"
            return -1

        # TODO when we support element composition (an array of element_name's
        #      as input), the placement module will return an array of mac
        #      addresses.  At that point, we should iterate through mac_addrs,
        #      but since composition isn't yet supported, we'll just pull out
        #      the one mac addr
        [mac_addr] = mac_addrs
        
        log.debug("Placement module returned MAC Address of middlebox machine %s" % mac_addr)

        ##
        # STEP 2: Install the function.

        # We need the IP address for pushing the code; this is the only time we need a machine's IP address
        ip_addr = self.mac_to_ip.get(mac_addr)

        if(self.download.add_mb_client(mac_addr,ip_addr,None,None)):

            # Given the function name send the files to the middlebox.
            if(self.download.put_file(mac_addr,element_name)):

                # Inform the shim that it should be running these elements on this flow space
                if(self.ms_msg_proc.send_install_msg(elem_desc, flow, element_name, parameters,mac_addr)):

                    ##
                    # STEP 3: Now that we've uploaded and installed, we update our state

                    # Update our internal state of where the element is installed
                    self.elem_to_mac.add(ip_addr, mac_addr, elem_desc)
                    self.mac_to_ip.add(mac_addr, ip_addr)

                    # Update our internal state of flow to elements mapping
                    self.flow_to_elems.add(None, flow, {elem_desc:element_name}) #Function descriptor 

                    # Update our internal state, noting that app_desc owns elem_desc
                    self.elem_to_app.update(elem_desc, application_object, app_desc)

                    return elem_desc
                else:
                    return -1
            else:
                return -2
        else:
            return -3

    """
    Applications call this to send configuration parameters to their elements.
    This method ensures that the application actually owns the specified element before sending the message
    """
    def configure_elem(self, app_desc, elem_desc, application_conf_params):
        if(self.elem_to_app.get_app_desc(elem_desc) == app_desc):
            msg_dst = self.elem_to_mac.get(elem_desc)
            app_handle = self.elem_to_app.get_app_handle(elem_desc) # not requied by additional check 
            if((msg_dst != None) and (app_handle != None)):
                self.ms_msg_proc.send_configure_msg(elem_desc, application_conf_params ,msg_dst)

    #TODO:
    def remove_elem(self, app_desc, elem_desc):
        # roll back
        if(self.ms_msg_proc.send_remove_msg(elem_desc, parameters,mac_addr)):
            desc_removed = self.elem_to_mac.remove(elem_desc)
        #update mb_placement_steering for changed elements


from pox.core import core
import pox.openflow.discovery

"""
Wrapper class for slick controller interface; used by l2_multi_slick
"""
class POXInterface():
    def __init__(self,controller):
        self.controller = controller

    """
    returns the dictionary of function descriptors to MAC addresses
    Note: This assumes that the placement of elements is already fixed.
    The updates to element placement could happen on a slower timescale.
    Replaces get_element_descriptors
    """
    def get_steering (self, src, dst, flow):
        # replica_sets is a list of lists of element descriptors
        # [[e_11, e_12, ...], [e_21, e_22, ...], ...]
        # TODO this is what flow_to_elems should return, but it does not yet support replicas
        #replica_sets = self.controller.flow_to_elems.get(flow.in_port, flow)

        # XXX as a result, we'll construct it by hand for now
        # elems is a {elem_desc:elem_name} mapping
        # TODO replace these 2 lines with the commented-out one above
        replica_sets = []
        elems = self.controller.flow_to_elems.get(flow.in_port, flow)
        if(len(elems.keys()) > 0):
            replica_sets = [elems.keys()]

        # element_descriptors is a list of individual element descriptors: one chosen from
        # each element in the replica list, e.g.: [e_11, e_25, e_32, ...]
        element_descriptors = self.controller.steering_module.get_steering(replica_sets, src, dst, flow)

        # TODO if this fails, try to scale out the appropriate element(s)

        element_macs = {}
        for elem_desc in element_descriptors:
            mac_addr = self.controller.elem_to_mac.get(elem_desc) 
            element_macs[elem_desc] = EthAddr(mac_to_str(mac_addr)) # Convert MAC in Long to EthAddr

        return element_macs

    """
    Constructs a list of "pathlets" between src -> machines in the machine
    sequence -> dst

    Returns it as this list of pathlets because that appears to be what
    l2_multi_slick expects when installing forwarding rules.
    """
    def get_path (self, src, machine_sequence, dst):
        return self.controller.routing_module.get_path(src, machine_sequence, dst)

    """
    Not currently used or tested: should be called after a path has been
    successfully installed to update the NetworkModel.

    We explicitly do not include it in get_path or get_steering, because it
    should only be called after all of the forwarding rules have been
    successfully installed
    """
    def path_was_installed (self, match, element_sequence, machine_sequence, path):
        return self.controller.network_model.path_was_installed(match, element_sequence, machine_sequence, path)


    """
    This is a utils function.
    This function returns a matching flow 
    flow is of type ofp_match
    """
    def get_generic_flow(self,flow):
        matching_flow = flow
        matched_flow_tuple = self.controller.flow_to_elems.get_matching_flow(flow) # Find the function descriptors.
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
