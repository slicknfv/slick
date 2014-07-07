"""
    KPlacement picks up the machines according to centrality:
        If the placement preference is None or center. Then simple centrality.
        If the palcement preference is "near", Then picks K virtual places near the server of the network and based on demand places elements.
        If the placement preference is "far", then picks the element instances on all the gateways and scales up/down near the gateway.
        hint vector for placement:
            1- Consolidate: such that the KPlacement can consolidate to optimize the placement. If consolidate is False then  no consolidation is preferred over consolidation.
            2- Avoid Paths: In case a certain path is to be avoided such that its overloaded we should provide the hint tsuch that certain machines are avoided.
            3- Initial_Placement: So that we can create a partitioning of the graph and then place the elements using LEG.
        total_number_of_hosts
        # What is the right number of partitions?
        # Too small a number of partitions will mean that we'll have more latency. 
        # Too large a number of partition will mean we'll have a larger footprint and under utilized resources.
        Number of partitions = K = Total # of hosts/ max # of hosts(min capacity element in the chain)

        Things impacting placement:
            1- shim layers. (limitation in hosts where we have shim installed can limit the element installation.)
            2- demand matrix. ( traffic demand matrix can impact this also.)
"""
from collections import defaultdict
import operator
from consolidation import Consolidate
from tm import TrafficMatrix

from slick.placement.Placement import Placement

from pox.core import core
import networkx as nx
import metis # required for graph partitioning
log = core.getLogger()


USER_DEFINED_NETWORK_PARTITIONS = 2

PREFER_CONSOLIDATION = True

class NetworkAwarePlacement(Placement):
    def __init__ (self, network_model):
        log.debug("NetworkAware Placement Algorithm")
        Placement.__init__ (self, network_model)
        self._used_macs = [ ]
        # This is the first installation of the elements by the policy.
        #self.first_install = False
        self.partitioned_graph = None
        self.consolidate = Consolidate(network_model)
        traffic_matrix_dir = "/home/mininet/Abilene/2004/Measured/"
        traffic_matrix_file = "/home/mininet/Abilene/2004/Measured/tm.2004-04-11.23-40-00.dat"
        self.tm = TrafficMatrix(None, traffic_matrix_file)

    def get_placement (self, flowspace_desc, elements_to_install): # 0
        """
            Inputs:
                - elements_to_install: list of elements to be placed (can have repeats)
            Outputs:
                - a list of mac addresses, of the same size as elements_to_install, providing a one-to-one mapping of where to install each element
                - return None if no placement is possible
        """
        rv = [ ]
        # Create appropriate number of partitions of the graph.
        self.network_model.physical_net.create_partitions()
        #if self.is_first_flowspace_placement():
        consolidated_chain, virtual_locs_to_place = self._consolidate_using_leg(elements_to_install)
        print "SIGN"*100, consolidated_chain, virtual_locs_to_place
        #else:
        #    consolidated_chain, virtual_locs_to_place = self._consolidate_using_leg_n_existing_chains(elements_to_install)
        rv = self._place_consolidated_chain(flowspace_desc, elements_to_install, consolidated_chain, virtual_locs_to_place)
        return rv

    def _consolidate_using_leg(self, element_names): # 1
        """Given the list of element_names list. 
           Find the best possible partitioning of the elements
           that corresponds to minimum link cost for deployment.
           Args:
               element_names: List of element name chain.
           Returns:
               List of lists with best partitioning for the elements.
               Tuple for virtual assignment location.
        """
        # Get the ordered list of leg_factors corresponding to each element in the element_names.
        leg_factors = self.consolidate.get_leg_factors(element_names)
        consolidation_combinations = self.consolidate.generate_consolidation_combinations(element_names)
        least_cost_partition, least_cost_locs = self.consolidate.get_least_cost_assignment(consolidation_combinations, element_names, leg_factors)
        print "The least cost assignment for the element_names: ", element_names, " is: ", least_cost_partition, least_cost_locs
        return least_cost_partition, least_cost_locs

    def _consolidate_using_leg_n_existing_chains(self, element_names): # 1
        """Given the list of element_names list. Return list of lists.
        TODO"""
        pass

    def _place_consolidated_chain(self, flowspace_desc, elements_to_install, consolidated_chain, virtual_locs_to_place): # 2
        """
        Args: 
            flowspace_desc: An integer describing the flowspace for the element instance.
            consolidated_chain: Its a list of list where each sublist is a consolidated element.
            virtual_locs_to_place: Estimated locations to place the elements.
            elements_to_install: List of element names to install.

            Given the flowspace_desc, consolidated_chian and virtual locations to place.
           Place the elements in the network.
        Returns the list of MAC addresses where the elements should be placed
        This list can have repeated MAC addresses(for consolidated elements)."""
        # Read the matrix from the data set of Internet. 
        rv = [ ]
        machines = None
        traffic_matrix = self.tm.get_traffic_matrix(flowspace_desc)
        sources, destinations = self.tm.get_sources_and_destinations(traffic_matrix)
        print consolidated_chain, virtual_locs_to_place
        log.debug("Source Switches: "+ str(sources))
        log.debug("Destination Switches: "+ str(destinations))
        for index, consolidated_element in enumerate(consolidated_chain):
        #    consolidated_element_type = consolidated_element[0]
            position_to_place_consolidated_element = virtual_locs_to_place[index]
            print virtual_locs_to_place
            print "Position to place conslidated element: ", consolidated_element, " is :", position_to_place_consolidated_element
            if position_to_place_consolidated_element == 'SRCS':#0:
                machines = self._place_element_near_nodes(flowspace_desc, sources, consolidated_element)
            if position_to_place_consolidated_element == 'DESTS':#len(consolidated_chain)-1:
                machines = self._place_element_near_nodes(flowspace_desc, destinations, consolidated_element)
            if position_to_place_consolidated_element == 'ANY':#((position_to_place_consolidated_element != len(consolidated_chain)-1) and (position_to_place_consolidated_element != 0)):
                machines = self._place_element_anywhere(flowspace_desc, consolidated_element)
            print consolidated_element
            print "APPENDING machines to the list:", machines
            if machines:
                rv = rv + machines
        return rv


    def _place_element_near_nodes(self,flowspace_desc,  nodes, consolidated_element): # 3
        """Place the consoldiated_element near the nodes in all the partitions.i
        Return the MAC address for the element machine name."""
        machine_macs =  [ ]
        machine = None
        for element_name in consolidated_element:
            #partition_number_to_install_element = self.get_partition_number_to_install_element(element_name)
            # Check which partitions have the element and which do not and place the
            # elements based on that.
            partition_number = self._get_partition_number_to_place(flowspace_desc, element_name)
            machine = self._get_machine(nodes, element_name, partition_number)
            # This is not mistake(since its a consolidated element) we need to run it once.
            break;
        print "PLACING element near nodes:",  consolidated_element, " in partition: ", partition_number
        for elem_name in consolidated_element:
            machine_macs.append(machine)
        return machine_macs

    def _place_element_anywhere(self, flowspace_desc, consolidated_element): # 3
        """Given the consolidated element return the MAC address where this
           element should be placed.
            Return the MAC address for the machine as it where to place the element."""
        machine_macs = [ ]
        for element_name in consolidated_element:
            # Check which partitions have the element and which do not and place the
            # elements based on that.
            partition_number = self._get_partition_number_to_place(flowspace_desc, element_name)
            machine = self._get_machine(None, element_name, partition_number)
            machine_macs.append(machine)
        print "PLACING element near nodes:",  consolidated_element, " in partition: ", partition_number
        return machine_macs


    def _get_machine(self, nodes, elem_name, partition_number): # 4
        """Given the element name return the element machine for
            the given partition that is closer to the switches
            in the nodes list.

        Args:
            elem_name: String of element name.
            nodes: List of switches near which we need to place the element. 
            partition_number: Network partition where we should palce the element.
        Returns:
            Mac address of the element machine where the elem_name should be hosted.
        """
        # In the simplest case we have all the machines.
        all_machines = self.network_model.get_compatible_machines( elem_name )
        print all_machines
        machines = [ ]
        # Make sure that we only used machines that have < MAX number of
        # element instances running on them.
        for mac in all_machines:
            if self.network_model.element_placement_allowed(mac):
                machines.append(mac)
        log.debug("Placement choosing from " + str(len(machines)) + " machines for element '" + elem_name + "': " + str(machines))
        print machines
        if ((len(machines) == 0) and (len(all_machines) > 0)):
            log.warn("All compatibale middlebox machines are fully loaded. Element cannot be placed.")
            print "ERROR"*100
            return None

        if (len(machines) == 1): # No need if we have only one available machine.
            # Check if the machine is in the same partition.
            return machines[0]

        partition_machines = self._get_partition_machines(partition_number, machines)
        # Place the element_name in the provided partition_number.
        machine_mac = self._get_partition_placement(elem_name, nodes, partition_machines, partition_number)
        return machine_mac

    def _get_partition_machines(self, partition_number, machines): # 5
        """Given the list list of all midldlebox machines and partition number,
            return the list of machines that belong to the partition."""
        partition_machines =  [ ]
        partition_nodes = self.network_model.physical_net.get_partition_nodes(partition_number)
        for machine in machines:
            switch_mac = self.network_model.overlay_net.get_connected_switch(machine)
            print switch_mac, partition_nodes
            if switch_mac in partition_nodes:
                partition_machines.append(machine)
        print "PARTITION MACHINES:",partition_machines
        return partition_machines

    def _get_partition_number_to_place(self, flowspace_desc, elem_name): #4
        """Given the element_name return the partition number to place
        the element in the network.
        In other words look at the partitions that already have the pivot element
        instance and return the partition where flow is instantiated.
        Args: 
            flowspace_desc: flowspace against which this elem_name corresponds.
            elem_name: Name of the elemen as string(element type)
        Returns:
            partition number as int.
        """
        # Dict to keep track of partition and presence of pivot element instance in it.
        partition_to_pivot_map = { }
        number_of_partitions = self.network_model.physical_net.get_num_partitions()
        for part_num in range(0, number_of_partitions):
            partition_to_pivot_map[part_num] = False
        # Check which partition does not has an element in it.
        for part_num in partition_to_pivot_map:
            print part_num
            if self._is_element_instance_present(flowspace_desc, part_num, elem_name):
                partition_to_pivot_map[part_num] = True
            else:
                partition_to_pivot_map[part_num] = False

        # List of partition numbers that require a pivot element instance.
        partitions_requiring_pivot = [ ]
        # Select the partitions that require a pivot instance.
        for part_num, elem_inst_present in partition_to_pivot_map.iteritems():
            if not elem_inst_present:
                partitions_requiring_pivot.append(part_num)
        # TODO: This code will work for max. number of two partitions in the netowrk.
        # To add support for more we need to integrate placement with steering to see
        # which partitions to place the elements. So that we know the source and destination.
        if len(partitions_requiring_pivot):
            return partitions_requiring_pivot[0]
        else:
            # TODO: immediately
            # If partition_number is -ve => we have pivots in all the paritions
            # Now we are just creating the elements for load balancing.
            # Then the question is which partition needs the new element 
            # instance for load balancing?
            return -1

    def _is_element_instance_present(self, flowspace_desc, part_num, elem_name):
        """If the partition has a single copy of element instance with the 
        given element_name and for the given flowspace_desc. return True else return False."""
        elem_descs = self.network_model.get_flowspace_elem_descs(flowspace_desc, elem_name)
        for ed in elem_descs:
            machine_mac = self.network_model.get_machine_mac(ed)
            switch_mac = self.network_model.overlay_net.get_connected_switch(machine_mac)
            switch_partition_number = self.network_model.physical_net.get_partition_number(switch_mac)
            if switch_partition_number == part_num:
                return True
            else:
                continue
        return False

    def _get_partition_placement(self, elem_name, nodes, machines, partition_number): # 5
        """
            Place elem_name near the nodes. If nodes are not provided place it anywhere.
            machine is selected from list of machines in machines.
            Args: 
                elem_name: element name string.
                machines: list of machine mac addresses which are compatible with element name and are not at full capacity from Virtual machine perspective..
                nodes: Place elements near the nodes.
                partition_number: Network partition number where to place the elements.
            Returns:
                machine mac address.
        """
        selected_machine_mac = None
        # Get the recommended placement for the element.
        placement_pref = self.network_model.get_elem_placement_pref(elem_name)
        if not nodes: # => we are placing in the partition for element of leg_type E
            if (placement_pref == None or placement_pref == "middle"):
                # If we calculate betweenness on all switches its possible to find
                # a central node where we cannot place the element instance.
                # This betweenness should be found within a single partition
                selected_machine_mac = self._get_betweenness_centrality(partition_number, machines)
            if (placement_pref == "near"): # For example in case of proxy we need it near the machines.
                selected_machine_mac = self._get_closeness_centrality(partition_number, machines)
            if (placement_pref == "far"):
                selected_machine_mac = self._get_closeness_centrality(partition_number, machines)
        if nodes:
            selected_machine_mac = self._get_closeness_centrality(partition_number, machines)
        return selected_machine_mac

    def _get_closeness_centrality(self, partition_number, machines): # 6
        # 1- Get machine to switch mapping.
        central_machine_mac = None
        switch_list = [ ]
        for machine in machines:
            switch_mac = self.network_model.overlay_net.get_connected_switch(machine)
            switch_list.append(switch_mac)
        # 2- Get the partition graph from the physical graph of the switches.
        # Get the graph for all the switches in the network.
        placement_graph = self.network_model.physical_net.get_placement_graph()
        partition_nodes = self.network_model.physical_net.get_partition_nodes(partition_number)
        print "Partition Nodes:", partition_nodes
        partition_subgraph = nx.Graph(placement_graph.subgraph(partition_nodes))
        print "Subgraph Edges:", partition_subgraph.edges()

        # 3- Find the highest centrality node.
        # A dict of centralities node-> centrality
        node_cents = nx.closeness_centrality(partition_subgraph, normalized = True)
        print node_cents
        sorted_centralities = sorted(node_cents.iteritems(), key=operator.itemgetter(1), reverse=True)
        print sorted_centralities
        log.debug("Sorted Centralities: " + str(sorted_centralities))
        central_machine_mac = self._select_not_used_machine(sorted_centralities, machines)
        if not central_machine_mac:
            all_reg_machines = self.network_model.get_all_registered_machines()
            if len(self._used_macs) >= len(all_reg_machines):
                self._used_macs[:] = [ ]
                central_machine_mac = self._select_not_used_machine(sorted_centralities, machines)
        return central_machine_mac

    def _get_betweenness_centrality(self, partition_number, machines): # 6
        """Given the list of machines return the switch with highest betweenness
        in placement graph and that has a middlebox machine connected to it.

        Args:
            partition_number: Graph partition number in which to find the central node.
            List of machine mac addresses.
        Returns:
            machine mac address.
        """
        # 1- Get machine to switch mapping.
        central_machine_mac = None
        switch_list = [ ]
        for machine in machines:
            switch_mac = self.network_model.overlay_net.get_connected_switch(machine)
            switch_list.append(switch_mac)
        # 2- Get the partition graph from the physical graph of the switches.
        # Get the graph for all the switches in the network.
        placement_graph = self.network_model.physical_net.get_placement_graph()
        partition_nodes = self.network_model.physical_net.get_partition_nodes(partition_number)
        print "Partition Nodes:", partition_nodes
        partition_subgraph = nx.Graph(placement_graph.subgraph(partition_nodes))
        print "Subgraph Edges:", partition_subgraph.edges()

        # 3- Find the highest centrality node.
        # A dict of centralities node-> centrality
        node_cents = nx.betweenness_centrality(partition_subgraph, normalized = True)
        sorted_centralities = sorted(node_cents.iteritems(), key=operator.itemgetter(1), reverse=True)
        print sorted_centralities
        log.debug("Sorted Centralities: " + str(sorted_centralities))
        central_machine_mac = self._select_not_used_machine(sorted_centralities, machines)
        if not central_machine_mac:
            all_reg_machines = self.network_model.get_all_registered_machines()
            if len(self._used_macs) >= len(all_reg_machines):
                self._used_macs[:] = [ ]
                central_machine_mac = self._select_not_used_machine(sorted_centralities, machines)
        return central_machine_mac

    def _select_not_used_machine(self, sorted_centralities, machines):
        """Given sorted centralities and machine mac addresses return the machine
        with highest centrality."""
        machine_mac = None
        for tup in sorted_centralities:
            switch_mac = tup[0]
            # find the machine mac that is connected with switch_mac.
            machine_mac = self._get_switch_machine(switch_mac, machines)
            # This machine mac is already used get the next optimal placement.
            if machine_mac:
                if machine_mac not in self._used_macs:
                    self._used_macs.append(machine_mac)
                    return machine_mac
                else:
                    continue

    def _get_switch_machine(self, switch_mac, machines):
        """
        Args:
            switch_mac: DPID in int.
            machines: list of machine mac addresses that are compatible.
        Returns:
            machine_mac attached with switch_mac if no compatible machine is attached with
            switch then return None.
        """
        for machine in machines:
            s_mac = self.network_model.overlay_net.get_connected_switch(machine)
            if s_mac == switch_mac:
                # print "Machine", machine, "switch mac", s_mac
                return machine
        return None

    def is_first_flowspace_placement(self):
        active_fds = self.network_model.get_active_flowspace_descs()
        if len(active_fds):
            return False
        else:
            return True


#    """
#    # This function should be used to resolve the LEG heuristic in the network.
#    # This network allows us to save the bandwidth utiliztion.
#    """
#    def place_element(self, policy_direction, flowspace_desc, element_names):
#        """
#        policy_direction: is an enumerator that tells us if the direction
#            of the policy is: outgoing => South to North
#                              incoming => North to South
#                              inside => East to West or West to East
#        """
#        # Get the element name vector.
#        chain_elements = self.network_model.get_chain_elements(flowspace_desc)
#        if len(element_names) == 1:
#            element_name = element_names[0]
#            if policy_direction == "incoming":
#                if type(elment_name) == 'G':
#                    place_element_near_north(element_name)
#                if type(elment_name) == 'L':
#                    place_element_near_south(element_name)
#                if type(elment_name) == 'E':
#                    place_element_anywhere(element_name)
#            elif policy_direction == "outgoing":
#                if type(elment_name) == 'G':
#                    place_element_near_north(element_name)
#                if type(elment_name) == 'L':
#                    place_element_near_south(element_name)
#                if type(elment_name) == 'E':
#                    place_element_anywhere(element_name)
#            elif policy_direction == "inside":
#                if type(elment_name) == 'G':
#                    place_element_near_sources(element_name)
#                if type(elment_name) == 'L':
#                    place_element_near_destinations(element_name)
#                if type(elment_name) == 'E':
#                    place_element_anywhere(element_name)
#        if len(element_names) == 2:
#            decision = should_consolidate(element_names)
#            if decision == CONSOLIDATE:
#                macs = placement.get_placement(decision, element_names)
#                if len(macs) != 1:
#                    raise Exception("This should not happen.")
#            if decision  == DONT_CONSOLIDATE:
#                macs = placement.get_placement(decision, element_names)
#                if len(macs) != 2:
#                    raise Exception("This should not happen.")
#            if decision == DONT_CARE:
#                macs = placement.get_placement(decision, element_names)
#                if len(macs) != 1 or len(macs) != 2:
#                    raise Exception("This should not happen.")
#    def should_consolidate(self, element_names):
#        if len(element_names) == 2:
#            fet_
    
        #if len(element_names) == 2:
        #    first_element_name = element_chain[0]
        #    second_element_name = elemnt_chian[1]
        #    t1 = self.network_model.get_elem_leg_type(first_element_name)
        #    t2 = self.network_model.get_elem_leg_type(second_element_name)
        #    if not PREFER_CONSOLIDATION:
        #        if t1 == 'L' and t2 == 'L':
        #            # consolidating the elements.
        #            return [('L', element_names)]
        #        if t1 == "L" and t2 == "G":
        #            # Dont care but we are not consolidating the elements together
        #            # Decision to place depends on the configuration of element t1 and t2.
        #            return [('L', [first_element_name]), ('G', [second_element_name])]
        #        if t1 ==  'L' and t2 ==  'E':
        #            # Consolidate
        #            return [('L', element_names)]
        #        if t1 == 'G' and t2 == 'G':
        #            # Consolidate
        #            return ['G', element_names]
        #        if t1 == 'G' and t2 == 'L':
        #            # STRICTLY Don't consolidate.
        #            return [('G', [first_element_name]), ('L', [second_element_name])]
        #        if t1 == 'G' and t2 == 'E':
        #            # Dont care but we are not consolidating the elements together.
        #            return [('G', [first_element_name]), ('E', [second_element_name])]
        #        if t1 == 'E' and t2 == 'E':
        #            # Dont care but we are not consolidating the elements together.
        #            return [('E', [first_element_name]), ('E', [second_element_name])]
        #        if t1 == 'E' and t2 == 'G':
        #            # Consolidate
        #            return [('G', element_names)]
        #        if t1 == 'E' and t2 == 'L':
        #            # Dont care but we are not consolidating the elements together.
        #            return [('E', [first_element_name]), ('L', [second_element_name])]
        #    else:
        #        if t1 == 'L' and t2 == 'L':
        #            # consolidating the elements.
        #            return [('L', element_names)]
        #        if t1 == 'L' and t2 == 'G':
        #            #Dont care but we are not consolidating the elements together.
        #            return [('L', [first_element_name]), ('G', [second_element_name])]
        #        if t1 ==  'L' and t2 ==  'E':
        #            # Consolidate
        #            return [('L', element_names)]
        #        if t1 == 'G' and t2 == 'G':
        #            # Consolidate
        #            return ['G', element_names]
        #        if t1 == 'G' and t2 == 'L':
        #            # STRICTLY Don't consolidate.
        #            return [('G', [first_element_name]), ('L', [second_element_name])]
        #        if t1 == 'G' and t2 == 'E':
        #            # Dont care but we are consolidating the elements together.
        #            # Due to CONSOLIDATION_PREF flag.
        #            return [('G', element_names)]
        #        if t1 == 'E' and t2 == 'E':
        #            # Dont care but we are consolidating the elements together.
        #            return [('E', element_names)]
        #        if t1 == 'E' and t2 == 'G':
        #            # Consolidate
        #            return [('G', element_names)]
        #        if t1 == 'E' and t2 == 'L':
        #            # Dont care but we are consolidating the elements together.
        #            # Due to CONSOLIDATE_PREF flag
        #            return [('L', element_names)]





"""
        #if (leg_type == "L"):
        #    # Given the demand matrix and element name find the max need for element instances.
        #    max_num_elem_instances = self.network_model.get_max_element_instances(element_name)
        #    # Get current element instances.
        #    elem_descs = self.network_model.get_elem_descs(element_name)
        #    current_num_elem_descs = len(elem_descs)
        #    if current_num_elem_descs < max_num_elem_instances:
        #        selected_machine_mac = self._get_element_instance_near_destination(machines)
        #    else:
        #        # This means there is room for optimization and element instances
        #        # can be moved to free up resources.
        #        log.warn (" We are going above the quota.")
        #if (leg_type == "G"):
        #    selected_machine_mac = self._get_element_instance_near_source(machines)
"""
