# This module has code that should decide if we need to place 
# and route or perform one of them.
# Following Type of Decisions are made: 
# Add Instance
# Move Instance
# Steer/Redirect traffic.
import time

from pox.core import core
from pox.lib.util import dpid_to_str
from pox.lib.recoco import Timer # For timer calls.
import pox.openflow.libopenflow_01 as of

import slick_exceptions
from slick.NetworkModel import ElementInstance
log = core.getLogger()

def convert_fd_to_fm(flow):
    """Convert Flow Dict to FlowMatch data structure."""
    match = of.ofp_match()
    match.dl_src = flow['dl_src']
    match.dl_dst = flow['dl_dst']
    match.dl_vlan = flow['dl_vlan']
    match.dl_vlan_pcp = flow['dl_vlan_pcp']
    match.dl_type = flow['dl_type']
    match.nw_tos = None #flow['nw_tos']
    match.nw_proto = flow['nw_proto']
    match.nw_src = flow['nw_src']
    match.nw_dst = flow['nw_dst']
    match.tp_dst = flow['tp_dst']
    match.tp_src = flow['tp_src']
    return match


class PlacenSteer(object):
    def __init__(self, controller):
        self.controller = controller
        # Element Descriptors in this dict should be delete once we recieve their 
        # FlowRemoved Event. Keeps track of migrating elements
        self.migrating_elems = { } # FlowTuple -> (old_ed, app_desc)
        self.migrating_flows = { } # Dict of flows tuples being migrated. FlowTuple -> old_ed
        core.openflow.addListenerByName("FlowRemoved", self._handle_FlowRemoved)

    def _handle_FlowRemoved (self, event):
        """
        process a flow removed event and remove the element descriptor
        that is being migrated.
        """
        flow_removed = event.ofp
        removed_flow_tuple = self.controller.flow_to_elems.get_matching_flow(flow_removed.match)
        # If the element is migrated and there
        # is not more active traffic we need to migrate the flow.
        if removed_flow_tuple in self.migrating_elems:
            print "Removed Flow Tuple from Migrating Elements:",removed_flow_tuple
            for flow, ed in self.migrating_elems.iteritems():
                print flow, ed
            (old_ed, app_desc) = self.migrating_elems[removed_flow_tuple]
            log.debug("Removing element %d for application: %d", old_ed, app_desc)
            self.controller.remove_elem(app_desc, old_ed)
            del self.migrating_elems[removed_flow_tuple]
            self.controller.elem_migration.end_migration(old_ed)
        if removed_flow_tuple in self.migrating_flows:
            print "Removed Flow Tuple from Migrating Flows",removed_flow_tuple
            old_ed = self.migrating_flows[removed_flow_tuple]
            self.controller.elem_migration.end_migration(old_ed)
            del self.migrating_flows[removed_flow_tuple]

    def _create_element_copy(self, ed, dst_mac):
        """Given the elment descriptor create a copy of the element on the destination mac address.
        Args:
            ed: Element Descriptor (int)
            dst_mac: Middlebox machine mac address
        """
        element_name = self.controller.network_model.get_elem_name(ed)
        app_desc = self.controller.elem_to_app.get_app_desc(ed)
        application_object = self.controller.elem_to_app.get_app_handle(ed)
        # Flow that should be processed by element.
        flow = self.controller.flow_to_elems.get_element_flow(ed)
        # Element parameters
        parameter = self.controller.elem_to_app.get_elem_parameters(ed)
        # Use the same parameters as the original element instance.
        controller_param = self.controller.elem_to_app.get_controller_params(ed)

        # STEP 0: check that this application actually owns this element
        if(self.controller.elem_to_app.contains_app(app_desc)):# We have the application installed
            src_mac = self.controller.elem_to_mac.get(ed)
            log.debug("Moving element %d with name %s for application: %d", ed, element_name, app_desc)
            log.debug("Moving element %d from element machine %s -> element machine %s:", ed, dpid_to_str(src_mac), dpid_to_str(dst_mac))

        # STEP 1: Install the elements.
        try:
            self.controller.download_files([element_name], [dst_mac])
        except slick_exceptions.ElementDownloadFailed as e:
            log.warn(e.__str__())
            return -2

        elem_desc = self.controller.get_unique_element_descriptor()
        mac_addr = dst_mac
        # Inform the shim that it should be running these elements on this flow space
        if(self.controller.ms_msg_proc.send_install_msg(elem_desc, flow, element_name, parameter, mac_addr)):
            # STEP 3: Now that we've uploaded and installed, we update our state
            ip_addr = self.controller.mac_to_ip.get(mac_addr)
            # Update our internal state of where the element is installed
            self.controller.elem_to_mac.add(mac_addr, elem_desc)
            self.controller.mac_to_ip.add(mac_addr, ip_addr)

            # Update our internal state of flow to elements mapping
            element_instance = ElementInstance(element_name, app_desc, elem_desc, mac_addr)

            self.controller.flow_to_elems.add_element(None, flow, element_instance)
            self.controller.flow_to_elems.add_element_instance(None, flow, element_instance)

            # Update our internal state, noting that app_desc owns elem_desc
            self.controller.elem_to_app.update(elem_desc, application_object, app_desc, parameter, controller_param)

            self.controller.network_model.add_placement(element_name, app_desc, elem_desc, mac_addr)
        else:
            return -1
        return elem_desc



    def _add_element_instance(self, ed):
        """Given the elment descriptor, create a new element instance copy in the network.
        Args:
            ed: element descriptor integer.
        Returns:
            None
        Side Effect:
            Create a new element instance.
        """
        element_names = [ ]
        app_desc = None
        application_object = None
        parameters = [ ]
        flow = None

        e_name = self.controller.network_model.get_elem_name(ed)
        element_names.append(e_name)
        app_desc = self.controller.elem_to_app.get_app_desc(ed)
        application_object = self.controller.elem_to_app.get_app_handle(ed)
        flow = self.controller.flow_to_elems.get_element_flow(ed)
        param_dict = self.controller.elem_to_app.get_elem_parameters(ed)
        parameters.append(param_dict)
        # Call apply_elem but first build all the arguments
        # for the function call.
        # For now duplicate all element instances on the machine.
        self.controller.apply_elem(app_desc, flow, element_names, parameters, application_object)

    def add_element_instance(self, overloaded_machine_mac):
        # Get all the elements that are on the machine.
        element_descs = list(self.controller.elem_to_mac.get_elem_descs(overloaded_machine_mac))
        # TODO: After modifying apply_elem() and get_placement() make this call from get_placement()
        elem_descs = self.controller.network_model.get_loaded_elements(element_descs)
        # Move one element instance at a time.
        for ed in elem_descs:
            self._add_element_instance(ed)


    def _perform_stateless_migration(self, ed, dst_mac):
        """Even though the element is stateless it needs to maintain the affinities of the element.
        Therefore update element admin parameters."""
        element_name = self.controller.network_model.get_elem_name(ed)
        compatible_machine_macs = self.controller.network_model.get_compatible_machines(element_name)
        old_ed = ed
        new_ed = ed
        if dst_mac in compatible_machine_macs:
            # Step 0 Get the flow that is being processed by old_ed
            flow_dict = self.controller.flow_to_elems.get_element_flow(old_ed)
            flow_match = convert_fd_to_fm(flow_dict)
            matched_flow_tuple = self.controller.flow_to_elems.get_matching_flow(flow_match)
            app_desc = self.controller.elem_to_app.get_app_desc(old_ed)
            self.migrating_elems[matched_flow_tuple] = (old_ed, app_desc)
            # Step1: Create new element instance 
            new_ed = self._create_element_copy(old_ed, dst_mac)
            assert old_ed != new_ed, "Old and New element descriptor cannot be equal."
            # Step 2
            # Tell controller about the migration.
            self.controller.elem_migration.init_migration(old_ed, new_ed)
            self.controller.network_model.remove_elem_to_switch_mapping(old_ed)
            # Step 3 
            # Update element instance specific parameters to the new elment instance.
            old_elem_name = self.controller.network_model.get_elem_name(old_ed)
            if self.controller.network_model.is_affinity_required(old_ed, old_elem_name):
                # that flows should be affined to the new element instances
                # Now if there is a cache miss for the packets they'll be told
                # by controller to be sent to new paths.
                self.controller.flow_affinity.update_flow_affinity(old_ed, new_ed)
            # Step4: Retire the old element instance if path is not used any more.
            # This step is taken when the path is not used any more.
            # Please see the FlowRemoved function.
            pass

    def _perform_stateful_migration(self, ed, dst_mac):
        raise NotImplementedError("This method is not supported yet.")

    def move_element(self, ed, dst_mac):
        """Given the elment descriptor, move it to the destination mac."""
        #if self._controller.isstateful_element(ed):
        #    self._perform_stateful_migration(ed, dst_mac)
        #else:
        self._perform_stateless_migration(ed, dst_mac)

    def steer_traffic(self, old_ed, new_ed):
        """Given the element descriptor, steer the traffic away from the element desc
        such that it passes through the new_ed."""
        assert old_ed != new_ed, "Old and New element descriptor cannot be equal."
        flow_dict = self.controller.flow_to_elems.get_element_flow(old_ed)
        flow_match = convert_fd_to_fm(flow_dict)
        matched_flow_tuple = self.controller.flow_to_elems.get_matching_flow(flow_match)
        # Step 1
        # Tell controller about the migration.
        self.controller.elem_migration.init_migration(old_ed, new_ed)
        self.controller.network_model.remove_elem_to_switch_mapping(old_ed)
        # Step 2
        # Add flow to migrating flow.
        self.migrating_flows[matched_flow_tuple] = old_ed
        # Step 3
        # End path migration once FlowRemoved message is received.
        pass

    def garbage_collect(self):
        """If the resources are filled then collect the garbage."""
        pass

    # Testing function.
    def random_move(self):
        """Function for testing to perform random moving of element instances."""
        free_machines = [ ]
        all_elem_descs = [ ]
        registered_machines = self.controller.get_all_registered_machines()
        for mac in registered_machines:
            elem_descs = self.controller.elem_to_mac.get_elem_descs(mac)
            all_elem_descs += elem_descs
            if len(elem_descs) == 0:
                print "Middlebox machine with zero element instances:", mac
                free_machines.append(mac)
        print all_elem_descs
        print free_machines
        if (len(free_machines) >= 2) and (len(all_elem_descs) == 1):
            print "MOVEMENT"*100
            self.move_element(all_elem_descs[0], free_machines[0])

    # Testing function.
    def test_steer_traffic(self):
        """Function for testing to perform random moving of element instances."""
        free_machines = [ ]
        all_elem_descs = [ ]
        new_ed = None
        old_ed = None
        registered_machines = self.controller.get_all_registered_machines()
        for mac in registered_machines:
            elem_descs = self.controller.elem_to_mac.get_elem_descs(mac)
            all_elem_descs += elem_descs
            if len(elem_descs) == 0:
                print "Middlebox machine with zero element instances:", mac
                free_machines.append(mac)
        print all_elem_descs
        print free_machines
        if (len(free_machines) >= 1) and (len(all_elem_descs) == 1):
            new_ed = self._create_element_copy(all_elem_descs[0], free_machines[0])
            self.steer_traffic(all_elem_descs[0], new_ed)

    def place_n_steer(self):
        """Decide should we add/move elements or steer traffic."""
        # Return the list of congested middlebox machines.
        loaded_middleboxes = self.controller.network_model.get_loaded_middleboxes()
        # Return the list of congested links
        congested_links = self.controller.network_model.get_congested_links()
        print loaded_middleboxes
        print congested_links
    
        # If network is optimized i.e. we are minimizing the
        # resource usage for middlebox machines and network bandwidth
        # than we don't need to do much else we need to take further action.
        # steer traffic or move element instance.
        #
        # Return the list of loaded element instances.
        #loaded_elements = self._controller.network_model.get_loaded_elements()
        #if self._middlebox_overloaded(trigger_msg):
        #    element_descs = list(self.controller.elem_to_mac.get_elem_descs(overloaded_machine_mac))
        #    available_element_instances = lookup_available_element_instances(element_descs)
        #    if len(available_element_instances) == 0:
        #        self.add_element_instance()
        #    else:
        #        # Either move element instance or steer traffic.
        #        # Decide to move or steer traffic to existing element instances.
        #        # Decision to steer traffic over placing an element instance should 
        #        # be made how much traffic do we need to steer. If we need to steer 
        #        # traffic more than certain volume then we place element instance in the
        #        # path else we steer traffic.
        #        # To calculate the traffic to steer, estimate the volume of 
        #        # traffic.
        #        calc_distance
        ## Possible options.
        #self.add_element_instance(overloaded_machine_mac)
        #self.move_element_instance(overloaded_machine_mac)
        #self.remove_element_instance(overloaded_machine_mac)

