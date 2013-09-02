"""
    ShortestPathRouting makes use of l2_multi_routing's mechanisms
"""

from slick.routing.Routing import Routing

from pox.core import core
log = core.getLogger()

class ShortestPathRouting(Routing):
    def __init__ (self, network_model):
        Routing.__init__ (self, network_model)

    def get_path (self, src, machine_sequence, dst):
        from pox.forwarding.l2_multi_slick import _get_path  # FIXME pull this method out and add it here
        """
            Inputs:
                - src/dst: each is a (mac,port) pair
                - machine_sequence: an ordered list of (mac,port) pairs, as delivered from Steering
            Outputs:
                - an ordered list of "pathlets", such that
                    - each pathlet is an ordered list of (mac,port) pairs
                    - the first pathlet starts with the source
                    - the last pathlet ends with the destination
                    - collectively it constitutes an end-to-end path
                    - the overall length of the return value is equal to len(ms)+1
        """

        # the full machine sequence (machine_sequence does not include src/dst)
        ms = [src] + machine_sequence + [dst]
        log.debug("Constructing a path for machine sequence: " + str(ms))

        rv = []
        for index in range(0,len(ms)-1): #For n nodes we need n-1 paths installed.
            # Place we saw this ethaddr   -> loc = (self, event.port) 
            switch1_mac  = ms[index][0]
            switch1_port = ms[index][1]
            switch2_mac  = ms[index+1][0]
            switch2_port = ms[index+1][1]
            
            # FIXME currently using l2_multi_slick_refactored's _get_path; strip that out or clean up the interface
            p = _get_path(switch1_mac, switch2_mac, switch1_port, switch2_port)
            #if p is None: return None # append None; let l2_multi_slick deal with it
            log.debug("   Pathlet " + str(index) + ": " + str(p))
            rv.append(p)
        return rv
