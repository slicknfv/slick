"""
    RandomPlacement chooses a random compatible machine, and ignores load
"""

from slick.placement.Placement import Placement
from random import choice

from pox.core import core
log = core.getLogger()

class RandomPlacement(Placement):
    def __init__ (self, network_model):
        Placement.__init__ (self, network_model)

    def get_placement (self, elements_to_install):
        """
            Inputs:
                - elements_to_install: list of elements to be placed (can have repeats)
            Outputs:
                - a list of mac addresses, of the same size as elements_to_install, providing a one-to-one mapping of where to install each element
                - return None if no placement is possible
        """
        rv = []
        for elem_name in elements_to_install:
            machines = self.network_model.get_compatible_machines( elem_name )
            log.debug("Placement choosing from " + str(len(machines)) + " machines for element '" + elem_name + "': " + str(machines))
            if (len(machines) == 0): return None
            rv.append(choice(machines))
        return rv
