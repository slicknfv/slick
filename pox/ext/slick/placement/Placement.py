"""
    Placement base class
"""

class Placement():
    def __init__( self, network_model ):
        self.network_model = network_model

    def get_placement( self, elements_to_install ):
        """
            Inputs:
                - elements_to_install: dictionary mapping element *name* to how many instances should be placed
            Outputs:
                - a dictionary mapping element name to an array of machines (where to install the instances)
                - return None if no placement is possible
            Side effects:
                - None

            This method makes use of the following from the network model:
                - The set of machines
                - A method that tells us if a machine and an element have compatible manifests
                - How proximal any two machines are
                - The load at each machine
                - Each element's expected load (possibly from its manifest; possibly from profiling)
                - On which machines a given element is installed

            After calling this method, the following state in the network model should be updated:
                - On which machines a given element instance is installed
        """
        return None
