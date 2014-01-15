"""ShortestPathSteering returns the shortet hop count 
    from source to destination.
"""
import sys
import itertools # For pair-wise cross product.

from slick.steering.Steering import Steering
from random import choice

import networkx as nx

from pox.core import core
log = core.getLogger()

class ShortestPathSteering(Steering):
    def __init__ (self, network_model):
        Steering.__init__(self, network_model)
        # Its a NetworkX graph.
        self.subgraph = None

    def get_steering (self, replica_sets, src, dst, flow):
        """
            Inputs:
                - replica_sets: a list of sets; each set corresponds to an
                     element; each member of the set is an element descriptor
                     corresponding to a replica of that element.
                - src: the source of the flow (from l2_multi) (switch, port) tuple.
                - dst: the destination of the flow (from l2_multi) (switch, port) tuple.
                - flow: the flow match (from l2_multi)
            Outputs:
                - a list of the same size as replica_sets, but with only a single
                     element chosen from each of the sets; must maintain the same order
                - returns None on failure
        """

        # Every time get_steering is called subgraph is updated.
        self.network_model.add_elem_to_switch_mapping(replica_sets)
        self.subgraph = self.network_model.get_overlay_subgraph(src[0], dst[0], replica_sets)
        rv = self._get_element_instances(src[0], dst[0], replica_sets)
        return rv

    def _is_valid_path(self, path, replica_sets):
        element_chain_length = len(replica_sets)
        valid_path_length = element_chain_length
        if len(path) != valid_path_length:
            return False
        else:
            return True

    def _convert_ed_to_switches(self, src_switch, dst_switch, paths):
        """Convert the element descriptors to corresponding switch identifiers."""
        switch_paths = [ ]
        for j, p in enumerate(paths):
            switch_paths.append( [ ] )
            switch_paths[j].append(src_switch)
            for index, ed in enumerate(p):
                machine_mac = self.network_model.get_machine_mac(ed)
                switch = self.network_model.get_connected_switch(machine_mac)
                switch_paths[j].append(switch)
            switch_paths[j].append(dst_switch)
        return switch_paths

    def _get_shortest_path(self, src_switch, dst_switch, paths):
        """Return the shortest path among the paths passed as argument."""
        min_dist = sys.maxint
        shortest_path = None
        switch_paths = self._convert_ed_to_switches(src_switch, dst_switch, paths)
        for p in switch_paths:
            # Add the source and destination switch to the path.
            path_distance = 0
            for index, switch in enumerate(p):
                if index < (len(p)-1):
                    edge_data = self.subgraph.get_edge_data(p[index], p[index+1])
                    distance = edge_data['hop_count']
                    path_distance += distance
            if path_distance < min_dist:
                min_dist = path_distance
                shortest_path = p
        return shortest_path

    def _get_element_instances(self, src, dst, replica_sets):
        """Get the element instances required for packet forwarding."""
        rv = [ ]
        path_switches = [ ]
        start = src
        #print "Subgraph Nodes:", self.subgraph.nodes()
        #print "Subgraph Edges:", self.subgraph.edges()
        shortest_path = [ ]
        pruned_paths = [ ]
        for replicas in replica_sets:
            if(len(replicas) == 0):
                return None
        if len(replica_sets):
            # This is the maximum number of overlay network 
            # nodes the flow should traverse.
            service_chain_length = len(replica_sets) + 2
            # Get all the paths between the src and dst
            all_paths = self._get_all_paths(src, dst, replica_sets) 
            #print all_paths
            for p in all_paths:
                if (self._is_valid_path(p, replica_sets)):
                    print p, " is a valid path."
                    pruned_paths.append(p)
            #print pruned_paths
        if len(pruned_paths):
            path_switches = self._get_shortest_path(src, dst, pruned_paths)
        #print "Shortest Path:", path_switches
        # Remove source and destination switch.
        # As we need to return the shortest_path
        # ordered element descriptors.
        if len(path_switches) >= 2:
            del path_switches[0]
            del path_switches[-1]
        for switch_mac in path_switches:
            ed = self.network_model.get_elem_descriptor(switch_mac)
            if ed:
                rv.append(ed)
            else:
                raise Exception("No element descriptor to switch mapping found")
        return rv

    def _get_all_paths(self, src, dst, replica_sets):
        """Build all possible valid paths from src -> replica_sets -> dst
        Args:
            src: src switch mac address
            dst: dst switch mac address
            replica_sets: list of lists of the element desc of the element instances.
        Returns:
            list of lists, where each list is a valid path from source to destination.
        """
        list_of_paths = [ ]
        replica_products = itertools.product(*replica_sets)
        for index, chain in enumerate(replica_products):
            list_of_paths.append([ ])
            for elem_inst in chain:
                list_of_paths[index].append(elem_inst)
        return list_of_paths
