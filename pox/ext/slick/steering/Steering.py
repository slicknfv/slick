"""
    Steering base class
"""

class Steering():
    def __init__ (self, network_model):
        self.network_model = network_model

    def get_steering (self, app_desc, element_sequence, src, dst):
        """
            Inputs:
                - app_desc: the application description for whom we're steering (this is necessary because we need to look up where that application in particular has installed elements)
                - element_sequence: an *ordered* list element *names* the flow should be applied to
                - src/dst: each is a (mac,port) pair
            Outputs:
                - an *ordered* list of machines (actually, (mac,port) pairs)
                    - The order matches that of the input, element_sequence
                    - It does *NOT* include src/dst
                - return None if no such steering exists.  This could happen because:
                    - A necessary element hasn't been placed
                    - It would exceed the maximum load on a given machine
            Side effects:
                - None

            This method makes use of the following from the network model:
                - The set of machines where a given element has been placed
                - The congestion on any given link
                - The current load on any given machine

            This method benefits from (and possibly ought to construct) an overlay graph

            After calling this method, the following state in the network model should be updated:
                - The per-machine load
        """
        return None
