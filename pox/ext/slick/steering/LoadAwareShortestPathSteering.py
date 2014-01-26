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

LINK_USAGE_THRESHOLD = 90 # This is percentage.

class LoadAwareShortestPathSteering(Steering):
    def __init__ (self, network_model):
        Steering.__init__(self, network_model)
        # Its a NetworkX graph.
        self.subgraph = None

    def _get_congested_overlay_links(self):
        congested_overlay_links = [ ]
        for v1, v2, data in self.subgraph.edges(data=True):
            utilization = self.subgraph[v1][v2]['utilization']
            #print v1, v2, utilization
            if (utilization > LINK_USAGE_THRESHOLD):
                congested_overlay_links.append((v1, v2))
        return congested_overlay_links

    def _remove_congested_links(self):
        # Return a list of tuples, where each item is a tuple representing a link.
        congested_links = self._get_congested_overlay_links()
        #congested_links = [(3,1),(4,1)]
        for v1,v2 in congested_links:
            if self.subgraph.has_edge(v1, v2):
                self.subgraph.remove_edge(v1, v2)
        #print self.subgraph.edges()

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
        # This also updates the overlay link weights. Which means "hop_count" and "utilization"
        self.subgraph = self.network_model.get_overlay_subgraph(src[0], dst[0], replica_sets)
        self._remove_congested_links( )
        rv = self._get_element_instances(src[0], dst[0], replica_sets)
        return rv

    def _is_valid_path(self, path, replica_sets):
        """ helper function to check if the path has 
        selected at most one element instance for each 
        type of replica.
        """
        element_chain_length = len(replica_sets)
        valid_path_length = element_chain_length
        if len(path) != valid_path_length:
            return False
        else:
            return True

    def _convert_ed_to_switches(self, src_switch, dst_switch, paths):
        """Convert the element descriptors to corresponding switch identifiers.

        Args:
            src_switch: MAC address of the source switch.
            dst_switch: MAC address of the destination switch.
            paths: List of lists

        Returns:
            List of lists where each entry is a switch MAC address
            corresponding to element descriptors.
        """
        switch_paths = [ ]
        for j, p in enumerate(paths):
            switch_paths.append( [ ] )
            switch_paths[j].append(src_switch)
            for index, ed in enumerate(p):
                machine_mac = self.network_model.get_machine_mac(ed)
                switch = self.network_model.overlay_net.get_connected_switch(machine_mac)
                switch_paths[j].append(switch)
            switch_paths[j].append(dst_switch)
        return switch_paths

    def _get_shortest_path(self, src_switch, dst_switch, paths):
        """Return the shortest path among the paths passed as argument.

        Args:
            src_switch: MAC address of the source switch.
            dst_switch: MAC address of the destination switch.
            paths: List of lists with element descriptors in each list.

        Returns:
            List of the switches with shortest path.
        """
        min_dist = sys.maxint
        shortest_path = [ ]
        switch_paths = self._convert_ed_to_switches(src_switch, dst_switch, paths)
        for p in switch_paths:
            # Add the source and destination switch to the path.
            path_distance = 0
            for index, switch in enumerate(p):
                if index < (len(p)-1):
                    #print p[index], p[index+1]
                    if not self.subgraph.has_edge(p[index], p[index+1]):
                        # Since there is no edge we need to assign infinity weight 
                        # for the link. And look for another path.
                        path_distance = sys.maxint
                        break
                    edge_data = self.subgraph.get_edge_data(p[index], p[index+1])
                    distance = edge_data['hop_count']
                    path_distance += distance
            if path_distance < min_dist:
                min_dist = path_distance
                shortest_path = p
        if not shortest_path:
            shortest_path.append(src_switch)
            shortest_path.append(dst_switch)
        return shortest_path

    def _get_element_instances(self, src, dst, replica_sets):
        """Get the element instances required for packet forwarding.
        Args:
            src: MAC address of the source switch.
            dst: MAC address of the destination switch.
            replica_sets: list of lists where each list has element descriptors in it.
        Returns:
            List of element descriptors that should be traversed by the flow.
        """
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
        """Build all possible valid paths from src -> replica_sets -> dst.
        i.e. paths from src -> dst going through replica_sets
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
