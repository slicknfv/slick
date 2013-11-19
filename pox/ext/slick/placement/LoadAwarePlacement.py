"""
    LoadAwawrePlacement chooses a compatible machine
    based on the machine load or the flow load.
    1- Before placing the machine.
        a- get compatible machines.
        b- get machines that are not fully loaded.
        c- randomly place the machine.( initial placement.)
        d- after epoch check flow load.
        e- if flow_load < MAX:
            NOTHING
           else:
            create_new_element_instance()
    def create_new_element_instance():
        pass
"""
from collections import defaultdict

from slick.placement.Placement import Placement

from pox.core import core
log = core.getLogger()

class LoadAwarePlacement(Placement):
    def __init__ (self, network_model):
        log.debug("Load Aware Placement Algorithm")
        Placement.__init__ (self, network_model)
        # element_name -> element_machine_mac set
        self.elem_name_to_machine_macs = defaultdict(list)

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
            machine = self._get_next_machine(elem_name)
            rv.append(machine)
        return rv

    def _get_next_machine(self, elem_name):
        """Given the element name return the element machine.

        Args:
            elem_name: String of element name.
        Returns:
            Mac address of the element machine where the elem_name should be hosted.
        """
        machines = self.network_model.get_compatible_machines( elem_name )
        log.debug("Placement choosing from " + str(len(machines)) + " machines for element '" + elem_name + "': " + str(machines))
        if (len(machines) == 0): return None
        for machine_mac in machines:
            # Return machine load in terms of number of flows.
            machine_laod = self.network_model.get_machine_load(machine_mac)

    def update_placement(self):
        """Recalculate the placement."""
        pass

