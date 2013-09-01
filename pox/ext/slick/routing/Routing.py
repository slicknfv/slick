"""
    Routing base class
"""

class Routing():
    def __init__ (self, network_model):
        self.network_model = network_model

    def get_path (self, src, machine_sequence, dst):
        """
            Inputs:
                - src/dst: each is a (mac,port) pair
                - machine_sequence: an ordered list of (mac,port) pairs, as delivered from Steering
            Outputs:
                - an ordered list of (mac,port) pairs, such that:
                    - it begins with src and ends with dst
                    - machine_sequence is a subsequence
                    - it constitutes a full underlay path between src and dst
            Side effects:
                - None

            This method makes use of the following from the network model:
                - The topology
                - The traffic matrix

            After calling this method, the following state in the network model should be updated:
                - The per-link congestion
        """
        return None
