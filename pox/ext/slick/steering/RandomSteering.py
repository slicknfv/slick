"""
    RandomSteering randomizes selection
"""

from slick.steering.Steering import Steering
from random import choice

class RandomSteering(Steering):
    def __init__( self, network_model )
        Steering.__init__( self, network_model )

    def get_steering( self, element_sequence, src, dst )
        """
            Inputs:
                - element_sequence: an *ordered* list element *names* the flow should be applied to
                - src/dst: each is a (mac,port) pair
            Outputs:
                - an *ordered* list of machines (actually, (mac,port) pairs)
        """
        rv = []

        for element_name in element_sequence.iteritems():
            machines = self.network_model.get_element_placements( element_name )
            if(len(machines) == 0): return None
            rv.append(choose(machines))

        return rv
