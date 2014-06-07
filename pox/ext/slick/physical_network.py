from pox.core import core

import networkx as nx
import metis # required for graph partitioning

# List of network types.
# Tree, FatTree, JellyFish, Enterprise, WAN

class NetworkType(object):
    # This parameter has to be changed by the admin.
    def __init__(self):
        # DC
        self.TREE = True
        self.FATTREE = False
        self.JELLYFISH = False
        # Starbucks/real estate offices.
        self.WAN = False
        # Enterprise 
        self.enterprise = False
        # special cases
        self.GT = False
        self.UNI1 = False

class PhysicalNetwork(object):
    def __init__(self, controller):
        self.controller = controller
        # Register listeners
        core.listen_to_dependencies(self)
        # Simple switch topology graph.
        self.topo_graph = nx.Graph()
        # Key value pairs where the keys are the switch MAC addresses
        # and values are the list of partition nodes.
        self.partitioned_graph = None # Its an nx.Graph() copy
        self.nt = NetworkType( )

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

    def get_num_partitions(self, policy_id=0):
        if self.nt.TREE:
            return 2
            #self.controller.get_number_of_gateways()
        else:
            raise Exception("Please specifiy the desired number of vertical partitions for the network type.")

    def get_partition(self, part_id):
        """return the subgraph for the partition."""
        pass

    def create_partitions(self):
        #print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"*10
        self.partitioned_graph = self.topo_graph.copy()
        #http://metis.readthedocs.org/en/latest/
        # We are using off the shelf software to partition the network.
        num_partitions = self.get_num_partitions( )
        # For now using the default partitioning algorithm.
        # Should experiment with different types and different partitioning algorithms.
        # Or ir does not matter whatever partition algorithm we use.
        (objective_function, partitions) = metis.part_graph(self.partitioned_graph, nparts = num_partitions)
        # For debugging
        print "Objective Function:", objective_function
        print "Partitions:", partitions
        # Add more colors to this array if get_num_partitions is > 4
        colors = ['red','blue','green','orange']
        print len(self.partitioned_graph.nodes())
        for i, p in enumerate(partitions):
            # Please not p starts from zero, one, two etc.
            self.partitioned_graph.node[i+1] = {'color': colors[p], 'part_number': p}
        nx.write_dot(self.partitioned_graph, 'slick_parts.dot')

    def get_partition_number(self, src_switch_mac):
        # Given the switch mac address return the partition number.
        """
            Args:
                Switch mac address
            Returns:
                graph part number an integer and part numbers start from zero
        """
        if self.partitioned_graph:
            if src_switch_mac in self.partitioned_graph.nodes():
                if 'part_number' in self.partitioned_graph.node[src_switch_mac]:
                    return self.partitioned_graph.node[src_switch_mac]['part_number']
                else:
                    print "ERROR: This should not happen."

    def get_partition_nodes(self, partition_number):
        """Given the partition_number, return the partition_nodes list."""
        partition_nodes = [ ]
        for node in self.partitioned_graph.nodes():
            if 'part_number' in self.partitioned_graph.node[node]:
                node_partition_number = self.partitioned_graph.node[node]['part_number']
                if partition_number == node_partition_number:
                    partition_nodes.append(node)
        return partition_nodes

