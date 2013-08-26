"""
    RandomPlacement chooses a random compatible machine, and ignores load
"""

from slick.placement.Placement import Placement
from random import choose

class RandomPlacement(Placement):
    def __init__( self, network_model ):
        Placement.__init__( self, network_model )

    def get_placement( self, elements_to_install ):
        """
            Inputs:
                - elements_to_install: dictionary mapping element *name* to how many instances should be placed
            Outputs:
                - a dictionary mapping element name to an array of machines (where to install the instances)
                - return None if no placement is possible
        """
        rv = {}
        for elem_name in elements_to_install.keys():
            rv[elem_name] = []
            for i in range( elements_to_install[elem_name] ):
                machines = get_compatible_machines( elem_name )
                if (len(machines) == 0): return None
                rv[elem_name].append(choose(machines))
        return rv
