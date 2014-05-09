"""
    RandomPlacement chooses a random compatible machine, and ignores load
"""
from collections import defaultdict

from slick.placement.Placement import Placement
from random import choice

from pox.core import core
log = core.getLogger()

class RoundRobinPlacement(Placement):
    def __init__ (self, network_model):
        log.debug("Round Robin Placement Algorithm")
        Placement.__init__ (self, network_model)
        # element_name -> element_machine_mac set
        self.elem_name_to_machine_macs = defaultdict(list)
        self.used_macs = [ ]

    def get_placement (self, flowspace_desc, elements_to_install):
        """
            Inputs:
                - elements_to_install: list of elements to be placed (can have repeats)
            Outputs:
                - a list of mac addresses, of the same size as elements_to_install, providing a one-to-one mapping of where to install each element
                - return None if no placement is possible
        """
        rv = [ ]
        for elem_name in elements_to_install:
            machine = self._get_next_machine(elem_name)
            rv.append(machine)
        return rv

    def _get_next_machine(self, elem_name):
        """Given the element name return the element machine
        in the round robin fashion.

        Args:
            elem_name: String of element name.
        Returns:
            Mac address of the element machine where the elem_name should be hosted.
        """
        machines = self.network_model.get_compatible_machines( elem_name )
        log.debug("Placement choosing from " + str(len(machines)) + " machines for element '" + elem_name + "': " + str(machines))
        if (len(machines) == 0): return None
        # Update the placement algorithm record
        # for any machine added.
        if elem_name not in self.elem_name_to_machine_macs:
            self.elem_name_to_machine_macs[elem_name] = [ ]
        for machine_mac in machines:
            if (machine_mac not in self.elem_name_to_machine_macs[elem_name]) and (machine_mac not in self.used_macs):
                self.used_macs.append(machine_mac)
                self.elem_name_to_machine_macs[elem_name].append(machine_mac)
                return machine_mac
        # If we have reached here it means that all the element machines have been used.
        self.elem_name_to_machine_macs[elem_name][:] = [ ]
        # Start over with the first elem_machine_mac
        elem_machine_mac = machines[0]
        self.elem_name_to_machine_macs[elem_name].append(elem_machine_mac)
        return elem_machine_mac
