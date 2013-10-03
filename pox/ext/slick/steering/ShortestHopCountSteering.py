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

    def get_steering (self, replica_sets, src, dst, flow):
        """
            Inputs:
                - replica_sets: a list of sets; each set corresponds to an
                     element; each member of the set is an element descriptor
                     corresponding to a replica of that element.
                - src: the source of the flow (from l2_multi)
                - dst: the destination of the flow (from l2_multi)
                - flow: the flow match (from l2_multi)
            Outputs:
                - a list of the same size as replica_sets, but with only a single
                     element chosen from each of the sets; must maintain the same order
                - returns None on failure
        """
        rv = [ ]

        start = src
        for replicas in replica_sets:
            if(len(replicas) == 0):
                return None

        for replicas in replica_sets:
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
            # Get the distance between the start_node
            distance = self.network_model.get_weight(start_node, machine_mac)
            if distance < min_distance:
                min_distance = distance
                nearest_replica = element_desc
        return nearest_replica
