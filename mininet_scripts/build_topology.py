###########################################################
# Given a topology file with certain format
# build a network topology from it that can be used
# by mininet.
###########################################################
import sys
import networkx as nx
from mininet.topo import Topo
import matplotlib.pyplot as plt

class NetworkXTopo(Topo):
    def __init__(self):
        super(NetworkXTopo, self).__init__( )

    def build_network(self, topo_graph, hosts_per_switch):
        node_count = 0
        for switch in topo_graph.nodes():
            self.addSwitch('s%d' % switch)
            for count in range(hosts_per_switch):
                node_count += 1
                # Add host to the switch.
                self.addHost('h%d' % node_count)
                self.addLink('s%d' % switch, 'h%d' % node_count)
        for n1, n2 in topo_graph.edges():
            self.addLink('s%d' % n1, 's%d' % n2)


def read_topo(topo_file):
    """Args:
        topo_file: String of the topology file path.
       Returns:
        File content to build the mininet.
    """
    topo_graph = nx.Graph()

    line_num = 0
    with open(topo_file, 'r') as f:
        for line in f.readlines():
            if line_num != 0:
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

                topo_graph.add_edge(object_id, r_object_id, capacity = capacity)
            line_num = line_num +1
    f.close()
    return topo_graph


def build_topo(topo_file):
    """Reads the topology in csv and returns a mininet Topo object."""
    topo_graph = read_topo( topo_file )
    net = NetworkXTopo( )
    net.build_network( topo_graph, 1 )
    hosts = net.hosts( )
    # Debug 
    #for host in hosts:
    #    print host
    #for link in net.links():
    #    print link
    draw_graph(topo_graph)

def draw_graph(netx_graph):
    pos = nx.graphviz_layout(netx_graph, prog='dot')
    nx.draw(netx_graph, pos)
    plt.show()


#### Test Code. ####
def main(argv):
    #build_topo("/home/mininet/middlesox/mininet_scripts/topo_data/sample_topo.csv")
    build_topo("/home/mininet/middlesox/mininet_scripts/topo_data/l2traceJuly29.2013.csv")

if __name__ == "__main__":
    main(sys.argv[1:])
