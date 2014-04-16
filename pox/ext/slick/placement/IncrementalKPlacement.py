"""
    IncrementalKPlacement chooses a random compatible machine, and ignores load
"""
from collections import defaultdict
import operator

from slick.placement.Placement import Placement

from pox.core import core
import networkx as nx
log = core.getLogger()


class IncrementalKPlacement(Placement):
    def __init__ (self, network_model):
        log.debug("Incremental K Placement Algorithm")
        Placement.__init__ (self, network_model)
        self._used_macs = [ ]

    def get_placement (self, elements_to_install):
        """
            Inputs:
                - elements_to_install: list of elements to be placed (can have repeats)
            Outputs:
                - a list of mac addresses, of the same size as elements_to_install, providing a one-to-one mapping of where to install each element
                - return None if no placement is possible
        """
        rv = [ ]
        for elem_name in elements_to_install:
            machine = self._get_machine(elem_name)
            rv.append(machine)
        return rv

    def _get_machine(self, elem_name):
        """Given the element name return the element machine
        in the round robin fashion.

        Args:
            elem_name: String of element name.
        Returns:
            Mac address of the element machine where the elem_name should be hosted.
        """
        # In the simplest case we have all the machines.
        all_machines = self.network_model.get_compatible_machines( elem_name )
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
            return machines[0]
        # second/third/fourth/... calls need to get the next optimal placement.
        machine_mac = self._get_inc_k_placement(elem_name, machines)
        return machine_mac

    def _get_inc_k_placement(self, elem_name, machines):
        """
            Args: 
                elem_name: element name string.
                machines: list of machine mac addresses which are compatible with element name.
            Returns:
                machine mac address.
        """
        selected_machine_mac = None
        # Get the recommended placement for the element.
        placement_pref = None
        spec_placement  = self.network_model.get_elem_spec_placement(elem_name)
        admin_placement = self.network_model.get_elem_admin_placement(elem_name)
        if admin_placement:
            placement_pref = admin_placement
        elif spec_placement:
            placement_pref = spec_placement

        if (placement_pref == None or placement_pref == "middle"):
            # If we calculate betweenness on all switches its possible to find
            # a central node where we cannot place the element instance.
            selected_machine_mac = self._get_betweenness_centrality(machines)
        # Figure out "near" and "far" for the flows.
        """Need a module that can detect the "near" and "far" for a policy
        and place the elements near the source or destination.
        """
        if (placement_pref == "near"):
            pass
        if (placement_pref == "far"):
            pass
        return selected_machine_mac

    def _get_betweenness_centrality(self, machines):
        """Given the list of machines return the switch with highest betweenness
        in placement graph and that has a middlebox machine connected to it.

        Args:
            List of machine mac addresses.
        Returns:
            machine mac address.
        """
        central_machine_mac = None
        switch_list = [ ]
        for machine in machines:
            switch_mac = self.network_model.overlay_net.get_connected_switch(machine)
            switch_list.append(switch_mac)
        # Get the graph for all the switches in the network.
        placement_graph = self.network_model.physical_net.get_placement_graph()
        # A dict of centralities node-> centrality
        node_cents = nx.betweenness_centrality(placement_graph, normalized = True)
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
