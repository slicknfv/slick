###########################################################
# Given a topology file with certain format
# build a network topology from it that can be used
# by mininet.
###########################################################
import sys
import networkx as nx
from mininet.topo import Topo
import matplotlib.pyplot as plt

HOSTS_PER_SWITCH = 4

class NetworkXTopo(Topo):
    def __init__(self):
        super(NetworkXTopo, self).__init__( )

    def build_network(self, topo_graph, hosts_per_switch):
        node_count = 0
        dpid = 0
        for switch in topo_graph.nodes():
            dpid += 1
            self.addSwitch('%s' % str(switch), dpid=str(dpid))
            for count in range(hosts_per_switch):
                node_count += 1
                # Add host to the switch.
                self.addHost('h%d' % node_count)
                self.addLink('%s' % str(switch), 'h%d' % node_count)
        for n1, n2 in topo_graph.edges():
            self.addLink('%s' % str(n1), '%s' % str(n2))

def validate_graph(graph):
    """Return the largest component of the graph > 100 nodes.
    """
    if not nx.is_connected(graph):
        print "WARNING: This network is not connected."
        num_connected_comps = nx.number_connected_components(graph)
        print "Total number of components: ", num_connected_comps
        subgraphs = nx.connected_component_subgraphs(graph)
        biggest_subg = None
        max_nodes = 0
        subg_nodes = 0
        for subg in subgraphs:
            print len(subg.nodes())
            print subg.nodes()
            subg_nodes = len(subg.nodes())
            if subg_nodes > max_nodes:
                max_nodes = subg_nodes
                biggest_subg = subg
        return biggest_subg
    else:
        print "Graph is connected."
        return graph

def is_gt_topo(topo_file):
    f = None
    with open(topo_file, 'r') as f:
        for index, line in enumerate(f.readlines()):
            if line[0] == '#':
                continue
            elif line.rstrip('\n') == 'gt':
                f.close()
                return True
        f.close()


# This function simply checks if the topology is 
# from Theo's IMC paper or not. As the file has
# different format.
def is_imc_topo(topo_file):
    f = None
    with open(topo_file, 'r') as f:
        for index, line in enumerate(f.readlines()):
            if line[0] == '#':
                continue
            elif line.rstrip('\n') == 'imc':
                f.close()
                return True
        f.close()

def is_snd_lib_topo(topo_file):
    f = None
    with open(topo_file, 'r') as f:
        for index, line in enumerate(f.readlines()):
            if line[0] == '#':
                continue
            elif line.rstrip('\n') == 'sndlib':
                f.close()
                return True
        f.close()
    pass

def read_topo(topo_file):
    """Args:
        topo_file: String of the topology file path.
       Returns:
        File content to build the mininet.
    """
    topo_graph = None
    if is_gt_topo(topo_file):
        topo_graph = get_gt_topo(topo_file)
    if is_imc_topo(topo_file):
        topo_graph = get_imc_topo(topo_file)
    if is_snd_lib_topo(topo_file):
        topo_graph = get_sndlib_topo(topo_file)
    if not topo_graph:
        raise IOError("Unable to read the topoogy file %s" % topo_file)
    return topo_graph

def get_imc_capacity(source_str, dest_str):
    """This function is called once per link."""
    source_capacity = sys.maxint
    dest_capacity = sys.maxint
    link_cap = 0
    # figure out source interface.
    # 1G
    if "Gig" in source_str:
        source_capacity = 1000
    if "Gig" in dest_str:
        dest_capacity = 1000
    # 100M
    if "FastEthernet" in source_str:
        source_capacity = 100
    if "FastEthernet" in source_str:
        dest_capacity = 100
    # 10G
    if "Ten" in source_str:
        source_capacity = 10000
    if "Ten" in dest_str:
        dest_capacity = 10000
    if source_capacity < dest_capacity:
        link_cap = source_capacity
    if dest_capacity < source_capacity:
        link_cap = dest_capacity
    # If the capacities are equal
    link_cap = source_capacity
    return link_cap


def get_imc_topo(topo_file):
    """Path to the topology file."""
    topo_graph = nx.Graph()
    with open(topo_file, 'r') as f:
        for line in f.readlines():
            if (len(line) > 10) and (line[0] != '#'):
                split_data = line.split()
                source = split_data[0]
                dest = split_data[2]
                #capacity = 1000 # We are fixing this to one.
                capacity = get_imc_capacity(split_data[1], split_data[3])
                if not topo_graph.has_edge(source, dest):
                    topo_graph.add_edge(source, dest, capacity = capacity)
    # Checks graph for any componnets and returns the largest one.
    topo_graph = validate_graph(topo_graph)
    f.close()
    return topo_graph

def get_gt_topo(topo_file):
    topo_graph = nx.Graph()
    line_num = 0
    with open(topo_file, 'r') as f:
        for line in f.readlines():
            if (len(line) > 10) and (line[0] != '#'):
                split_data = line.split(',')

                object_id = int(split_data[1])
                ipaddr = split_data[2]
                port_index = split_data[3]

                r_object_id = int (split_data[8])
                r_ipaddr = split_data[9]
                r_port_index = int(split_data[10])

                # This data is in mbps.
                capacity = float(split_data[5])
                vlan = int(split_data[6])

                if not topo_graph.has_edge(object_id, r_object_id):
                    topo_graph.add_edge(object_id, r_object_id, capacity = capacity)
            line_num = line_num +1
    topo_graph = validate_graph(topo_graph)
    if not nx.is_connected(topo_graph):
        print "WARNING: This network is not connected."
    f.close()
    return topo_graph

def get_sndlib_topo(topo_file):
    topo_graph = nx.Graph()
    line_num = 0
    with open(topo_file, 'r') as f:
        for line in f.readlines():
            if (len(line) > 10) and (line[0] != '#'):
                split_data = line.split(' ')

                src_node_id = str(split_data[2])
                dst_node_id = str(split_data[3])

                capacity = float(split_data[5])
                print capacity
                if not topo_graph.has_edge(src_node_id, dst_node_id):
                    topo_graph.add_edge(src_node_id, dst_node_id, capacity = capacity)
    topo_graph = validate_graph(topo_graph)
    if not nx.is_connected(topo_graph):
        print "WARNING: This network is not connected."
    f.close()
    return topo_graph


def build_topo(topo_file, display_graph = False):
    """Reads the topology in csv and returns a mininet Topo object."""
    topo_graph = read_topo( topo_file )
    # mininet topo
    topo = NetworkXTopo( )
    topo.build_network( topo_graph, HOSTS_PER_SWITCH )
    hosts = topo.hosts( )
    # Debug 
    print "Total number of Vertices:", len(topo.switches())
    print "Total number of Edges(including edges to hosts):", len(topo.links())
    #for host in hosts:
    #    print host
    #for link in net.links():
    #    print link
    if display_graph:
        draw_graph(topo_graph)
    return topo

def draw_graph(netx_graph):
    pos = nx.graphviz_layout(netx_graph, prog='dot')
    nx.draw(netx_graph, pos)
    # generate graph
    plt.savefig("graph.png", dpi = 2000)
    plt.savefig("graph.pdf")
    plt.show()


#### Test Code. ####
def main(argv):
    #build_topo("/home/mininet/middlesox/mininet_scripts/topo_data/sample_topo.csv")
    #build_topo("/home/mininet/middlesox/mininet_scripts/topo_data/l2traceJuly29.2013.csv", True)
    #build_topo("/home/mininet/middlesox/mininet_scripts/topo_data/unv2.cdp.txt", True)
    #build_topo("/home/mininet/middlesox/mininet_scripts/topo_data/unv1.cdp.txt", True)
    #build_topo("/home/mininet/middlesox/mininet_scripts/topo_data/prv1.cdp.txt", True)
    build_topo("/home/mininet/middlesox/mininet_scripts/topo_data/atlanta.txt", True)

if __name__ == "__main__":
    main(sys.argv[1:])
