"""
    RandomSteering randomizes selection
"""
import sys

from slick.steering.Steering import Steering
from random import choice

from pox.core import core
log = core.getLogger()

class ShortestHopCountSteering(Steering):
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
        print src, dst, replica_sets
        self.subgraph = self.network_model.get_overlay_subgraph(src[0], dst[0], replica_sets)
        rv = self.get_element_instances(src[0], dst[0], replica_sets)
        return rv

    def get_element_instances(self, src, dst, replica_sets):
        rv = [ ]
        start = src
        for replicas in replica_sets:
            if(len(replicas) == 0):
                return None
        for replicas in replica_sets:
            # For each element type find the nearest replica.
            nearest_replica = self._get_nearest_replica(start, replicas)
            start = nearest_replica
            rv.append(nearest_replica)
        return rv

    def _get_nearest_replica(self, start_node, element_replicas):
        """Greedy approach is inefficient.
           Given the starting node and set of possible
           element machines return the one with least weight.
        """
        min_distance = sys.maxint
        nearest_replica = None
        for element_desc in element_replicas:
            # Get the MAC address for the element descriptor.
            machine_mac = self.network_model.get_machine_mac(element_desc)
            machine_switch_mac = self.network_model.get_connected_switch(machine_mac)
            # Get the distance from the start_node
            edge_data = self.subgraph.get_edge_data(start_node, machine_switch_mac)
            # Please look at the LinkWeight Class in overlay_net module for 
            # fields of edge_data.
            distance = edge_data['hop_count']
            print "Distance:", distance
            if distance < min_distance:
                min_distance = distance
                nearest_replica = element_desc
        return nearest_replica
