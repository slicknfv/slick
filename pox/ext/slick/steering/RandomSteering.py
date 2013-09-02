"""
    RandomSteering randomizes selection
"""

from slick.steering.Steering import Steering
from random import choice

from pox.core import core
log = core.getLogger()

class RandomSteering(Steering):
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
        rv = []

        i = 1
        for replicas in replica_sets:
            log.debug("Choosing from " + str(len(replicas)) + " replicas for element " + str(i) + " of flow " + str(flow))
            i = i + 1

            if(len(replicas) == 0): return None
            rv.append(choice(replicas))

        return rv
