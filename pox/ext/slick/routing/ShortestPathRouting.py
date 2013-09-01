"""
    ShortestPathRouting makes use of l2_multi_routing's mechanisms
"""

from slick.routing.Routing import Routing
from l2_multi_slick import _get_path  # FIXME pull this method out and add it here

class ShortestPathRouting(Routing):
    def __init__ (self, network_model):
        Routing.__init__ (self, network_model)

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
        """

        # the full machine sequence (machine_sequence does not include src/dst)
        ms = [src] + machine_sequence + [dst]

        rv = []
        for index in range(0,len(ms)-1): #For n nodes we need n-1 paths installed.
            # Place we saw this ethaddr   -> loc = (self, event.port) 
            switch1_mac  = ms[index][0]
            switch1_port = ms[index][1]
            switch2_mac  = ms[index+1][0]
            switch2_port = ms[index+1][1]
            
            # FIXME currently using l2_multi_slick_refactored's _get_path; strip that out or clean up the interface
            p = _get_path(switch1_mac, switch2_mac, switch1_port, switch2_port)
            if p is None: return None
            rv.append(p)
        return rv
