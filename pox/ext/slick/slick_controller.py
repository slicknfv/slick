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
import sys  # for loading the application from commandline

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.util import dpid_to_str
from pox.lib.util import str_to_bool
from pox.lib.recoco import Timer # For timer calls.
from pox.lib.addresses import *


#from route_compiler import ElementToApplication
from networkmaps import ElementToMac,FlowToElementsMapping,MacToIP,ElementToApplication,FlowAffinity, ElementMigration
from msmessageproc import MSMessageProcessor
from conf import *
from download import Download
#from pox_interface import POXInterface
from utils.packet_utils import *

from apps import *

from slick.routing.ShortestPathRouting import ShortestPathRouting
from slick.steering.RandomSteering import RandomSteering
from slick.steering.ShortestHopCountSteering import ShortestHopCountSteering
from slick.steering.ShortestPathSteering import ShortestPathSteering
from slick.steering.LoadAwareShortestPathSteering import LoadAwareShortestPathSteering
from slick.placement.RandomPlacement import RandomPlacement
from slick.placement.RoundRobinPlacement import RoundRobinPlacement
from slick.placement.IncrementalKPlacement import IncrementalKPlacement
from slick.placement.KPlacement import KPlacement
from slick.NetworkModel import NetworkModel
from slick.NetworkModel import ElementInstance
from place_n_steer import PlacenSteer
import slick_exceptions
import queryengine

log = core.getLogger()


class slick_controller (object):
    """
    Waits for OpenFlow switches to connect 
    """
    def __init__ (self, transparent, application, query):
        print "INITIALIZING SLICK with application '" + application + "'"

        self.transparent = transparent
        # Message Processor.  Where App Handles are Initialized.
        self.ms_msg_proc = MSMessageProcessor(self)


        # Modules
        self.network_model = NetworkModel(self)
        #self.placement_module = RandomPlacement( self.network_model )
        #self.placement_module = RoundRobinPlacement( self.network_model )
        #self.placement_module = IncrementalKPlacement( self.network_model )
        self.placement_module = KPlacement( self.network_model )
        #self.placement_module = OptimalKPlacement( self.network_model )
        #self.steering_module = RandomSteering( self.network_model )
        #self.steering_module = ShortestHopCountSteering( self.network_model )
        #self.steering_module = ShortestPathSteering( self.network_model )
        self.steering_module = LoadAwareShortestPathSteering( self.network_model )
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
        self.flow_affinity = FlowAffinity()
        self.elem_migration = ElementMigration()

        # JSON Messenger Handlers
        self.json_msg_events = {}

        # Application descriptor
        self._latest_app_descriptor = 100

        # Load the application
        app_class = sys.modules['slick.apps.'+application].__dict__[application]
        self.app_instance = app_class( self, self._get_unique_app_descriptor() )
        self.ms_msg_proc.add_application( self.app_instance )

        log.debug("Successfully loaded " + application + "application. I will now periodically try to initialize it.")

        self.app_initialized = False

        # For uploading element code to machines
        self.download = Download()

        # Exposes some wrappers, particularly for l2_multi_slick
        self.controller_interface = POXInterface(self)

        # Application Initialization and Configuration.
        Timer(5, self.timer_callback, recurring = True)
        # Network state callback
        #Timer(1000, self.network_state_callback, recurring = True)
        Timer(5, self.network_state_callback, recurring = True)
        # Anything can be queried from the controller.
        self._query_engine = queryengine.QueryEngine(self, query)
        # Module repsonsible for continuosly performing placement or steering.
        self.place_n_steer = PlacenSteer(self)

    def _get_unique_app_descriptor(self):
        self._latest_app_descriptor += 1
        return self._latest_app_descriptor

    def get_unique_element_descriptor(self):
        self._latest_element_descriptor += 1
        return self._latest_element_descriptor

    def _handle_ConnectionUp (self, event):
        log.debug("Connection %s" % (event.connection,))
        #self.switch_connections[event.dpid] = event.connection

    def _handle_ConnectionDown (self, event):
        log.debug("Disconnecting %s" % (event.connection,))

    def get_connection(self,dpid):
        if(self.switch_connections.has_key(dpid)):
            return self.switch_connections[dpid]

    def network_state_callback(self):
        # Run update network state continuously.
        # For sflow: This should be same as the polling interval of sflow agent.
        self.controller_interface.update_network_state()

    """
    This method is periodically called for each running application (currently only one app)
    The rationale behind having it is that the app might be registered before shims have come online,
    so it tries init()'ing the application until it is able to install its elements
    """
    def timer_callback(self):
        # Calling this function to continuously display the status of 
        # middlebox machines, element types, element descriptors etc.
        self._query_engine.process_query()
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
        self.elem_to_mac.add(machine_mac, None)  # as per old msmessageproc

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
       SUCCESS: List of Element Descriptors in case of success
        [-1]    : Error installing one or more than one elements requested
                by the application.
        [-2]    : Error in downloading the files to middlebox.
        [-3]    : Error in adding a middlebox client.
        [-4]    : Error no middlebox is registered.

    Args:
        app_desc: Application descriptor from the application.
        flow: flow space
        element_names: List of element names to be applied.
        parameters: List of parameter dicts to be used for each element name
        application_object: application handle to be used by the controller
                            e.g. to send back the events etc.
        controller_params: List of parameter dicts that are provided by application
                      writer to overrride slick controller preferences. Only provided preferences
                      will be applied rest will be taken from element specification file.These parameters are taken from 
                      <element_name>.spec file. e.g,
                      {"placement" : "middle", affinity: "yes", "inline": "no"}
    Returns:
        A list of error codes or element descs.
    """
    def apply_elem (self, app_desc, flow, element_names, parameters, controller_params, application_object):

        print "CALINNG APPLY_ELEM. <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>"
        # Update element preferences according to app.
        if len(controller_params) and len(controller_params[0]):
            self.network_model.update_admin_elem_specs(element_names, controller_params)

        # Return list of all machines.
        all_machines = self.network_model.overlay_net.get_all_machines()
        registered_machines = self.get_all_registered_machines()
        if  not len(registered_machines):
            log.warn("No middlebox is registered.")
            # Need to update the graph for placement.
            self.network_model.physical_net.update_topo_graph()
            # This is a hack
            # Wait until all shims are up.
            if len(registered_machines) < len(all_machines):
                return [-4]

        ##
        # STEP 0: check that this application actually owns this element

        # TODO We need to see if this application is installed some other way;
        #      the problem with this is that elem_to_app won't know anything
        #      about app_desc until it has applied an element (i.e., this will fail
        #      the first time an app tries to apply an element)
        if(self.elem_to_app.contains_app(app_desc)):# We have the application installed
            log.debug("Creating another element for application: %d", app_desc)

        # Get unique flowspace id
        flowspace_desc = self.flow_to_elems.get_unique_flowspace_desc(flow)

        ##
        # STEP 1: Find the middlebox where this function should be installed.

        # TODO get_placement expects an array; this method should eventually
        #      take an array, but right now we're building it by hand
        # One of the benefits of passing arrays over iterative element passing
        # is Placement module has better view of how to place elements.
        mac_addrs = self.placement_module.get_placement(flowspace_desc, element_names)

        if len(mac_addrs) != len(element_names):
#           # => we are creating copies of element instances because of placement algorithm.
            pass

        # Return an error if there is no machine registered for function installation.
        placeless_element_names = self.__get_placeless_element_names(element_names, mac_addrs)
        if len(placeless_element_names):
            for elem_name in placeless_element_names:
                log.warn("Could not find a middlebox for element %s for application with descriptor (%d)" % (elem_name, app_desc))
            return [-1]
        else:
            for index, elem_name in enumerate(element_names):
                log.debug("Placement module returned MAC Address %s for element_name %s" % (mac_addrs[index], elem_name))

        # TODO when we support element composition (an array of element_name's
        #      as input), the placement module will return an array of mac
        #      addresses.  At that point, we should iterate through mac_addrs,
        #      but since composition isn't yet supported, we'll just pull out
        #      the one mac addr
        ##
        # STEP 2: Install the elements.
        try:
            #print "All machines: ", all_machines
            #print "Registered machines:", registered_machines
            self.download_files(element_names, mac_addrs)
        except slick_exceptions.ElementDownloadFailed as e:
            log.warn(e.__str__())
            return [-2]

        elem_descs = [ ]
        for e in element_names:
            elem_descs.append(self.get_unique_element_descriptor())

        # Keeping these assertions to avoid any issues.
        assert len(mac_addrs) == len(element_names) , 'Number of Element Names != Number of Middlebox MACs'
        assert len(element_names) == len(elem_descs) , 'Number of Element Names != Number of Element Descriptors'
        assert len(element_names) == len(parameters) , 'Number of Element Names != Number of Parameters'
        assert len(element_names) == len(controller_params) , 'Number of Element Names != Number of Controller parameters to be specified.'
        # Given above assertions intentionally iterating over element_names
        # to keep a reminder about the element_names order matters and this 
        # should be the order that we intert in flow_to_elems mapping.
        for index, element_name in enumerate(element_names):
            elem_desc = elem_descs[index]
            element_name = element_names[index]
            parameter = parameters[index]
            controller_param = controller_params[index]
            mac_addr = mac_addrs[index]
            # Inform the shim that it should be running these elements on this flow space
            if(self.ms_msg_proc.send_install_msg(elem_desc, flow, element_name, parameter, mac_addr)):

                ##
                # STEP 3: Now that we've uploaded and installed, we update our state
                ip_addr = self.mac_to_ip.get(mac_addr)
                # Update our internal state of where the element is installed
                self.elem_to_mac.add(mac_addr, elem_desc)
                self.mac_to_ip.add(mac_addr, ip_addr)

                # Update our internal state of flow to elements mapping
                element_instance = ElementInstance(element_name, app_desc, elem_desc, mac_addr, flowspace_desc)

                self.flow_to_elems.add_element(None, flow, element_instance)
                self.flow_to_elems.add_element_instance(None, flow, element_instance)

                # Update our internal state, noting that app_desc owns elem_desc
                self.elem_to_app.update(elem_desc, application_object, app_desc, parameter, controller_param)

                self.network_model.add_placement(element_name, app_desc, elem_desc, mac_addr, flowspace_desc)

                # Adding pivot element so it does not gets deleted.
                #self.network_model.add_pivot_elem_desc(elem_desc)
            else:
                # TODO rollback the updated states in case of failure.
                return [-1]
        # We should return the list of all sucessful elem_descs
        return elem_descs


    def download_files(self, element_names, mac_addrs):
        """Download files to middlebox machines.

        Args:
            element_names: Array of element names.
            mac_addrs: Array of mac_addrs
        Returns:
            None
        Raises:
            ElementDownloadFailed
        """
        assert len(mac_addrs) == len(element_names) , 'Number of Element Names != Number of Places'
        elements_downloaded = [ ] 
        for index, mac_addr in enumerate(mac_addrs):
            # We need the IP address for pushing the code; this is the only time we need a machine's IP address
            ip_addr = self.mac_to_ip.get(mac_addr)
            if(self.download.add_mb_client(mac_addr, ip_addr, None, None)):
                # Given the function name send the files to the middlebox.
                element_name = element_names[index]
                if(self.download.put_file(mac_addr, element_name)):
                    elements_downloaded.append(mac_addr)
                else:
                    raise slick_exceptions.ElementDownloadFailed('Download to machine ' + mac_to_str(mac_addr) + ' failed.')
            else:
                raise slick_exceptions.ElementDownloadFailed('Download to machine ' + mac_to_str(mac_addr) + ' failed.')

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
        parameters = self.elem_to_app.get_elem_parameters(elem_desc)
        msg_dst = self.elem_to_mac.get(elem_desc)
        # Step 1 Tell the shim to remove the element.
        if(self.ms_msg_proc.send_remove_msg(elem_desc, parameters, msg_dst)):
            log.debug("Removing the elements by sending commands to shim layer.")
            desc_removed = self.elem_to_mac.remove(msg_dst, elem_desc)
        # Step 2 Remove all the mappings.
        self.flow_to_elems.remove_element_instance(elem_desc)
        self.elem_to_app.remove(elem_desc)
        # Step 3 Remove the element information from the controller.
        self.network_model.remove_placement(elem_desc)
        log.debug("Removed element instance with element descriptor: " + str(elem_desc) + "application id:" + str(app_desc))

    def __get_placeless_element_names(self, element_names, mac_addrs):
        """Return elements that cannot be placed.

        Given mac_addrs and element_names return list of 
        element names that cannot be placed.
        Args:
            mac_addrs: List of mac_addrs returned by get_placement.
            element_names: List of element_names that are requested
                           by application.
        Returns:
            element_names: List of element names that cannot be placed.
        """
        assert len(mac_addrs) == len(element_names) , 'Number of Element Names != Number of Places'
        homeless_element_names =  [ ]
        if mac_addrs:
            for index, mac_addr in enumerate(mac_addrs):
                if not mac_addr:
                    homeless_element_names.append(element_names[index])
        return homeless_element_names

from pox.core import core
import pox.openflow.discovery

"""
Wrapper class for slick controller interface; used by l2_multi_slick
"""
class POXInterface():
    def __init__(self,controller):
        self.controller = controller

    """Flowspaces cannot overlapp with each other,
    if there is an overlap then it will not work."""
    def update_flow_affinity(self, flow, element_descriptors):
        """Given the flow and a list of lists of element_descriptors, 
        check if flow's affinity is set. 
        Should be called before get_steering.
        If set:
        update element descriptors with affined element_desc
        and return the list of lists for element descriptors.

        Should be called after get_steering.
        If not set:
        check if any of flow's elements require affinity. If yes
        update flow affinity. flow_ed_mapping according to get_steering's returned
        value.
        """
        #ed = self.controller.flow_affinity.get_element_desc(flow)
        pass

    def get_updated_replicas(self, eds, replica_sets):
        """Given the replica_sets remove the replicas and leave the affined eds."""
        print "Element descriptor affinity found."
        for ed in eds: # This is required for path affinity.
            for index, replicas in enumerate(replica_sets):
                if ed in replicas:
                    for elem_desc in replicas:
                        if elem_desc != ed:
                            # remove all the replica_sets that we cannot use for the given elem_desc
                            replica_sets[index].remove(elem_desc)
        return replica_sets

    def update_flow_affinities(self, flow, element_descriptors):
        """This function is called once element descs are selected by get_steering."""
        # Get the list of element instances corresponding to the flow.
        element_instances = self.controller.flow_to_elems.lookup_element_instances(flow.in_port, flow)
        print element_instances
        # At this point there is only one instance of each element type in the 
        # chain.
        for elem_inst in element_instances:
            ed = elem_inst.elem_desc
            elem_name = elem_inst.name
            if ed in element_descriptors:
                # uniquely identify the element preference specified by the application.
                if(self.controller.network_model.is_affinity_required(elem_inst.elem_desc, elem_inst.name)):
                    # check the load on elem_inst and its machine. If elem_inst is
                    # overloaded or machine is overloaded then
                    # create new element instance else following code
                    # to add affinity to existing element instance.
                    print "This element %s requires flow affinity." % elem_name
                    self.controller.flow_affinity.add_flow_affinity(flow, ed)
                    #self.controller.flow_affinity.dump()
        return element_descriptors

    def is_flow_affined(self, flow):
        """Return True if the flow already belongs to an elem desc else False."""
        ed = self.controller.flow_affinity.get_element_desc(flow)
        return ed

    """
    Args:
        src: Source switch and port tuple. e.g, (00-00-00-00-00-03, 1)
        dst: Destination switch and port tuple.
        flow: flow fields.
    Returns:
        returns the dictionary of function descriptors to MAC addresses
    Note: This assumes that the placement of elements is already fixed.
    The updates to element placement could happen on a slower timescale.
    Replaces get_element_descriptors
    """
    def get_steering (self, src, dst, flow):
        element_descriptors = None
        element_macs = [ ]
        if ((src[0] is None) or (dst[0] is None)):
            return element_macs
        # replica_sets is a list of lists of element descriptors
        # [[e_11, e_12, ...], [e_21, e_22, ...], ...]
        replica_sets_temp = self.controller.flow_to_elems.get(flow.in_port, flow)
        print "0",replica_sets_temp
        #replica_sets = self.controller.elem_migration.replace_migrating_elements(replica_sets_temp)
        replica_sets = replica_sets_temp
        print "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC"
        print "1",replica_sets
        # Check if flow is already 'affined' to an element instance.
        eds = self.controller.flow_affinity.get_element_descs(flow) 
        print "EEEEEEEEEEEEEEEEEEEEEEEEEEEE",eds
        if eds:# If flow is affined then remove other element instnaces
            replica_sets = self.get_updated_replicas(eds, replica_sets_temp)
        print "R",replica_sets
        # element_descriptors is a list of individual element descriptors: one chosen from
        # each element in the replica list, e.g.: [e_11, e_25, e_32, ...]
        self.controller.network_model.add_elem_to_switch_mapping(replica_sets)
        element_descs = self.controller.steering_module.get_steering(replica_sets, src, dst, flow)
        element_descriptors = element_descs
        print "E1",element_descriptors
        # If there is no affinity for the flow then check if element specs
        # from admin/default require affinity. If that is the case then assign affinity.
        if not eds:
            element_descriptors = self.update_flow_affinities(flow, element_descs)
        # TODO if this fails, try to scale out the appropriate element(s)
        print "E2",element_descriptors

        self.controller.place_n_steer.update_active_elements(element_descriptors)
        for elem_desc in element_descriptors:
            mac_addr = self.controller.elem_to_mac.get(elem_desc)
            print self.controller.elem_to_mac
            print mac_addr
            #print "MAC ADDRESS GOT FOR THE ELEMENT DESC:", elem_desc, mac_addr
            #element_macs[elem_desc] = EthAddr(mac_to_str(mac_addr)) # Convert MAC in Long to EthAddr
            eth_addr = EthAddr(mac_to_str(mac_addr)) # Convert MAC in Long to EthAddr
            element_macs.append((elem_desc, eth_addr))
            # For first flow we'll get the the original ed
            # for next new flow it should give the moved element instance.
            #self.controller.place_n_steer.random_move()
            #self.controller.place_n_steer.test_steer_traffic()
        return element_macs


    #def chain_required(self, element_macs):
    #    """Returns True/False if the flow processing
    #    requires it to go through a chain of elements 
    #    on different machines.
    #    Args:
    #        list of replica sets.
    #    Returns:
    #            True/False."""
    #    #if (len(element_macs) > 1):
    #    if (len(element_macs) >= 1): # For dev purpose using VLAN tags change to > 1 later on.
    #        return True
    #    else:
    #        return False

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

    def is_unidirection_required(self, ed):
        bidirection = self.controller.network_model.is_bidirection_required(ed)
        print bidirection, type(bidirection)
        return not bidirection

    def update_network_state(self, trigger_msg = None):
        """This is the placement recalculation function."""
        if trigger_msg:
            if "max_flows" in trigger_msg:
                if trigger_msg["max_flows"]:
                    print "TRIGGER RECEIVED"
                    assert "mac" in trigger_msg, "Shim Resources Trigger is missing the MAC address."
                    overloaded_machine_mac = trigger_msg["mac"]
                    # Get all the elements that are on the machine.
                    #element_descs = list(self.controller.elem_to_mac.get_elem_descs(overloaded_machine_mac))
                    ## TODO: After modifying apply_elem() and get_placement() make this call from get_placement()
                    #elem_descs = self.controller.network_model.get_loaded_elements(element_descs)
                    ## Move one element instance at a time.
                    #for ed in elem_descs:
                    #    #print elem_descs
                    #    element_names = [ ]
                    #    app_desc = None
                    #    application_object = None
                    #    parameters = [ ]
                    #    flow = None

                    #    e_name = self.controller.network_model.get_elem_name(ed)
                    #    element_names.append(e_name)
                    #    app_desc = self.controller.elem_to_app.get_app_desc(ed)
                    #    application_object = self.controller.elem_to_app.get_app_handle(ed)
                    #    flow = self.controller.flow_to_elems.get_element_flow(ed)
                    #    param_dict = self.controller.elem_to_app.get_elem_parameters(ed)
                    #    parameters.append(param_dict)
                    #    # Call apply_elem but first build all the arguments
                    #    # for the function call.
                    #    # For now duplicate all element instances on the machine.
                    #    # TODO: Add the code to get controller_param from the application
                    #    # from elem_to_app object, such that we provide the same parameters 
                    #    # for this element.
                    #    #self.controller.apply_elem(app_desc, flow, element_names, parameters, [{}],application_object)
        else:
            # Call the function continuously if
            # no trigger message from shim or from user.
            self.controller.place_n_steer.place_n_steer()
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
def launch (transparent=False, application="TwoLoggers", query="summary"):
#def launch (transparent=False, application="LoggerTriggerChain"):
    # The second component is argument for slick_controller.
    core.registerNew(slick_controller, str_to_bool(transparent), application, query)
