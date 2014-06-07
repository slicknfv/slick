# This module has code that should decide if we need to place 
# and route or perform one of them.
# Following Type of Decisions are made: 
# Add Instance
# Move Instance
# Steer/Redirect traffic.
import time
from collections import defaultdict

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

class ElementLoads():
    def __init__(self):
        pass

class PlacenSteer(object):
    def __init__(self, controller):
        self.controller = controller
        # Element Descriptors in this dict should be delete once we recieve their 
        # FlowRemoved Event. Keeps track of migrating elements
        self.migrating_elems = { } # FlowTuple -> (old_ed, app_desc)
        self.migrating_flows = { } # Dict of flows tuples being migrated. FlowTuple -> old_ed
        self.active_elems = { } # switch_dpid -> active elements.
        core.openflow.addListenerByName("FlowRemoved", self._handle_FlowRemoved)

    def update_active_elements(self, eds):
        """Use this function when get_steering is dispatching
        the traffic to elements. This is to keep track of active
        elements that are processing the traffic.
        Args:
            eds: element descriptors.
        Returns:
            None
        """
        mac_addr =  [ ]
        for elem_desc in eds:
            elem_machine_mac = self.controller.elem_to_mac.get(elem_desc)
            elem_switch_mac = self.controller.network_model.overlay_net.get_connected_switch(elem_machine_mac)
            if elem_switch_mac in self.active_elems:
                self.active_elems[elem_switch_mac].append(elem_desc)
            else:
                self.active_elems[elem_switch_mac] = [elem_desc]

    def remove_active_elements(self, flow_removed_event):
        # Get all the element descriptors associated with the flow
        # But only remove those element descriptor from active flows
        # from the switch we have received the removeflow.
        flow_removed = flow_removed_event.ofp
        dpid = flow_removed_event.dpid
        replica_sets = self.controller.flow_to_elems.get(None, flow_removed.match)
        for replica_set in replica_sets:
            for ed in replica_set:
                if dpid in self.active_elems:
                    # Its possible that one switch has more than one rule for same ed.
                    # once any of the rules is removed we consider the element instnace
                    # to be inactive.
                    #if (ed in self.active_elems[dpid]) and (not self.controller.network_model.is_pivot_element_instance(ed)):
                    if (ed in self.active_elems[dpid]):
                        self.active_elems[dpid].remove(ed)

    def get_active_element_descs(self, eds):
        """Given the element descriptors return active elements only."""
        active_elems = [ ]
        for ed in eds:
            for dpid, elem_descs in self.active_elems.iteritems():
                if ed in elem_descs:
                    if ed not in active_elems:
                        active_elems.append(ed)
        return active_elems

    def _handle_FlowRemoved (self, event):
        """
        process a flow removed event and remove the element descriptor
        that is being migrated.
        """
        flow_removed = event.ofp
        removed_flow_tuple = self.controller.flow_to_elems.get_matching_flow(flow_removed.match)
        self.remove_active_elements(event)
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

    def _create_element_instance(self, ed):
        """Given the elment descriptor, create a new element instance copy in the network.
        Args:
            ed: element descriptor integer.
        Returns:
            Element descriptor after successful creation of element instance.
            If failure then returns None.
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
        controller_param = [self.controller.elem_to_app.get_controller_params(ed)]
        # Call apply_elem but first build all the arguments
        # for the function call.
        # For now duplicate all element instances on the machine.
        created_elem_descs = self.controller.apply_elem(app_desc, flow, element_names, parameters, controller_param, application_object)
        if len(created_elem_descs):
            return created_elem_descs[0]
        else:
            return None

    def handle_loaded_elements(self, loaded_element_descs):
        print "Handling Loaded Elements."
        element_names = [ ]
        for ed in loaded_element_descs:
            element_name = self.controller.network_model.get_elem_name(ed)
            element_names.append(element_name)
        for element_name in element_names:
            eds = self.controller.network_model.get_elem_descs(element_name)
            if not len(eds):
                raise RuntimeError
            # For each new call to this function this can potentially return a different ed
            # Thus resulting in load from many elements to be redirected to not_loaded_element_instance.
            ed = eds[0]
            avail_eds = self.controller.network_model.get_not_loaded_element_descs(element_name)
            print "Available Element Descriptors: ",avail_eds
            # TODO: Add the check to see if we don't have avail_eds in the same network partition.
            # Then create new element instnace; even if there are available in other partitions.
            if len(avail_eds) == 0:
                new_ed = self._create_element_instance(ed)
                if new_ed:
                    #self.forced_steer_traffic(ed, new_ed)
                    pass
            else:
                # There are some instances available that are not loaded.
                # steer traffic towards them.
                new_ed = avail_eds.pop()
                # Any new flows should be redirected to new element.
                self.steer_traffic(ed, new_ed)
        # TODO: After modifying apply_elem() and get_placement() make this call from get_placement()

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

    def collect_garbage(self):
        """If the resources are filled then collect the garbage."""
        print "Collecting Garbage."
        elem_names = self.controller.network_model.get_elem_names()
        # Sweep through all the element types and remove any extra 
        # element descriptors.
        for elem_name in elem_names:
            avail_eds = self.controller.network_model.get_not_loaded_element_descs(elem_name)
            # print "avail_eds:", avail_eds
            if len(avail_eds):
                # There are no more loaded element descs.
                active_eds = self.get_active_element_descs(avail_eds)
                passive_eds = list(set(avail_eds) - set(active_eds))
                # print "active_eds:", active_eds
                # print "passive_eds:", passive_eds
                min_elem_instances = self.controller.network_model.get_min_elem_descs(elem_name)
                # Check to make sure we don't delete all the element instnaces.
                if len(passive_eds) > min_elem_instances:
                    # Remove element instances that are not being used anymore.
                    for ed in passive_eds:
                        app_desc = self.controller.elem_to_app.get_app_desc(ed)
                        log.debug("Removing element %d for application: %d", ed, app_desc)
                        self.controller.remove_elem(app_desc, ed)


    def place_n_steer(self):
        """Decide should we add/move elements or steer traffic."""
        # Return the list of congested middlebox machines.
        loaded_middleboxes = self.controller.network_model.get_loaded_middleboxes()
        loaded_elements = self.controller.network_model.get_loaded_elements()
        # Return the list of congested links
        congested_links = self.controller.network_model.get_congested_links()
        print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        print "Loaded Middleboxes:", loaded_middleboxes
        print "Loaded Element Instances:", loaded_elements
        print "Congested Links:", congested_links
        print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        # update the map so that we know if there are any less loaded element 
        # descriptors are available for a given load.
        self.controller.network_model.update_function_loads(loaded_elements)
        if len(loaded_elements) and (not len(congested_links)):
            self.handle_loaded_elements(loaded_elements)
        if len(congested_links) and (not len(loaded_elements)):
            pass
        if len(congested_links) and len(loaded_elements):
            pass
        # self.collect_garbage()

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

    ##########################################################################################
    # Use this module to help routing, placement and steering implement the heuristics.
    # Perform loop detection for routing.
    # Check partition boundary crossing over here.
    # Check the placement of elements based on the LEG heuristic.
    #########################################################################################

    def update_elem_descriptors(self, eds):
        pass

    def resolve_partitions(self, src, dst, eds):
        """
        src: src switch mac address
        dst: dst switch mac address
        eds: *Ordered* list of element descriptors
        """
        print "RESOLVING PARTITION."
        policy_direction = "NS"
        src_partition_number = self.controller.network_model.physical_net.get_partition_number(src)
        dst_partition_number = self.controller.network_model.physical_net.get_partition_number(dst)
        element_partition_number_vector = [ ]
        eds_to_create =  [ ] # list of element descriptors that are required to be created again.
        new_eds = [ ] # List of new element descriptors.
        for i in range(0, len(eds)):
            element_partition_number_vector.append(-1)
        assert len(element_partition_number_vector) == len(eds), "Local function assertion failed."
        pivot_partition = None
        #if (src_partition_number == dst_partition_number) and (policy_direction == "NS"):
        if (policy_direction == "NS"):
            log.debug("Source and Destination have same partition.")
            # Source and destination are in the same partition so no need
            # to cross the boundaries.
            pivot_partition = src_partition_number
            for index, ed in enumerate(eds):
                machine_mac = self.controller.network_model.get_machine_mac(ed)
                switch_mac = self.controller.network_model.overlay_net.get_connected_switch(machine_mac)
                switch_partition_number = self.controller.network_model.physical_net.get_partition_number(switch_mac)
                element_partition_number_vector[index] = switch_partition_number
            print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",eds, src_partition_number, dst_partition_number, element_partition_number_vector
            for index, elem_part_number in enumerate(element_partition_number_vector):
                if elem_part_number != src_partition_number: #Note src and dst partition numbers are the same.
                    eds_to_create.append(eds[index])
            print "Missing elements:", eds_to_create
            for ed in eds_to_create:
                # Create new element instance as there are no crresponding elements in the network.
                # in the required partition
                new_ed = self._create_element_instance(ed)
                if new_ed:
                    print "Steering created new element instnace." 
                else:
                    print "Steering was unable to create the element instnace."
        # This code section is for North-South/South-North traffic. 
        # It will not work for the East-West/West-East traffic.
        # NOTE: The EW code will be similar to this code, but with some tweaks.
        """
        if (src_partition_number != dst_partition_number) and (policy_direction == "NS"):
            log.debug("Source and Destination have different partitions.")
            # Get partition numbers for all the elements in the list.
            for ed in eds:
                machine_mac = self.controller.network_model.get_machine_mac(ed)
                switch_mac = self.controller.network_model.overlay_net.get_connected_switch(machine_mac)
                switch_partition_number = self.controller.network_model.physical_net.get_partition_number(switch_mac)
                element_partition_number_vector.append(switch_partition_number)
            # Check if we are only crossing boundaries in the same direction
            # not doing zig zag.
            # Assuming that the network has two partitions.
            # Assuming only two partitions:
            # Steering through partitions s->1,2,2->d is fine.
            # But partitions s->1,2,1->d is not; assuming d is in partition 2.
            # --
            # but if d is in partition 1 then we'll not reach here as s and d 
            # are in the same parition therefore it will be handled by src_partition_number == dst_partition_number
            # --

            # Please note here we assume instead of colors we have the parition numbers.
            # Checks if we are crossing boundaries or not.
            ascend = all(element_partition_number_vector[i] <= element_partition_number_vector[i+1] for i in xrange(len(element_partition_number_vector)-1))
            descend = all(element_partition_number_vector[i] >= element_partition_number_vector[i+1] for i in xrange(len(element_partition_number_vector)-1))

            print ascend, descend
            if ascend or descend:
                # We are fine as we are not crossing here.
                pass
            else:
                log.debug("We are crossing boundary here.")
                # We are crossing partition boundary, lets create the element instances where required.
                visited_partitions = [ ]
                prev_elem_part_number = src_partition_number
                for index, elem_part_number in enumerate(element_partition_number_vector):
                    if prev_elem_part_number == elem_part_number:
                        continue
                    else:
                        if elem_part_number not in visited_partitions:
                            visited_partitions.append(elem_part_number)
                        elif elem_part_number in visited_partitions:
                            if elem_part_number != visited_partitions[-1]:
                                # We have a crossing between two parition. 
                                # Lets create an element instance in the same prtition
                                # Where it should be.
                                eds_to_create.append(eds[index])
                        prev_elem_part_number = elem_part_number
                    if elem_part_number != pivot_position:
                        eds_to_create.append(eds[index])
            print "Missing elements:", eds_to_create
            for ed in eds_to_create:
                # Create new element instance as there are no crresponding elements in the network.
                # in the required partition
                new_ed = self._create_element_instance(ed)
                if new_ed:
                    print "Steering created new element instnace." 
                else:
                    print "Steering was unable to create the element instnace."
        """
        if (src_partition_number != dst_partition_number) and (policy_direction == "EW"):
            # TODO: handle the case such that the boundarties are not crossed in case of "EW" traffic.
            pass
            #
            #if switch_partition_number == pivot_partition:
            #    continue
            #else:
            #    #element_name = self.get_element_name(ed)
            #    #element_leg_type = self.get_element_leg_type(ed)
            #    #element_placement_pref = self.get_element_placement_pref(ed)
            #if dst in gateway_switches:

