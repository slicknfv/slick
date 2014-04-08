from pox.core import core

import networkx as nx

class PhysicalNetwork(object):
    def __init__(self, controller):
        self.controller = controller
        # Register listeners
        core.listen_to_dependencies(self)
        # Simple switch topology graph.
        self.topo_graph = nx.Graph()

    def _handle_LinkEvent (self, event):
        self.update_topo_graph()

    def get_placement_graph(self):
        return self.topo_graph

    def update_topo_graph(self):
        """Update topology graph if new element instance is added, 
        i.e. apply_elem is called. or a new link is discovered."""
        from slick.l2_multi_slick import switches
        from slick.l2_multi_slick import adjacency
        sws = switches.values()
        for i in sws:
            for j in sws:
                # Debug information
                # print i.dpid, j.dpid
                # print type(i.dpid), type(j.dpid)
                if i.dpid != j.dpid:
                    if adjacency[i][j] is not None:
                        self.topo_graph.add_edge(i.dpid, j.dpid)

