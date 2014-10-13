#!/usr/bin/python
 
"""
Example to create a Mininet topology and connect it to the internet via NAT
through eth0 on the host.
 
Glen Gibb, February 2011
 
- slight modifications by BL, 5/13
- fixes by Nick Feamster, July 2013
- more fixes by Dave Levin, August 2013

"""
 
from mininet.cli import CLI
from mininet.log import lg, info

from mininet.node import Node
from mininet.net import Mininet
# For resource isolation.
from mininet.node import CPULimitedHost
from mininet.link import TCLink

from mininet.topo import Topo
from topologies.topolib import TreeNet, TreeTopo
from mininet.util import quietRun, dumpNetConnections
from mininet.node import OVSController, Controller, RemoteController
from mininet.node import Node, OVSKernelSwitch,UserSwitch

from optparse import OptionParser

from topologies.DCTopo import FatTreeTopo
from topologies.jellyfish import JellyfishTopo
from topologies.DCell import DCellTopo

import json
import time
import middleboxes
import build_topology
import sflow
#import demand_matrix
import sys

def read_json(filename,debug=None):
    if(debug):
        print "Loading data from file: " +filename
    f = open(filename,'r')
    data = json.load(f)
    if(debug):
        print "Loaded global dictionary size" + str(len(data))
    return data

#################################
def startNAT( root, subnet='10.0/8', inetIntf='eth1' ):
    """Start NAT/forwarding between Mininet and external network
    root: node to access iptables from
    inetIntf: interface for internet access
    subnet: Mininet subnet (default 10.0/8)="""
 
    # Identify the interface connecting to the mininet network
    localIntf =  root.defaultIntf()

    print "Root's external-facing interface: ", inetIntf
    print "Root's local interface: ", localIntf
 
    # Flush any currently active rules
    root.cmd( 'iptables -F' )
    root.cmd( 'iptables -t nat -F' )
 
    # Create default entries for unmatched traffic
    root.cmd( 'iptables -P INPUT ACCEPT' )
    root.cmd( 'iptables -P OUTPUT ACCEPT' )
    root.cmd( 'iptables -P FORWARD DROP' )

    # Allow queries e.g, dpctl dump-flows tcp:127.0.0.1:6634
    root.cmd( 'iptables -A INPUT -p tcp -i ' + str(localIntf) + ' -d 127.0.0.1 -j ACCEPT' )
    # Configure NAT
    root.cmd( 'iptables -I FORWARD -i', localIntf, '-d', subnet, '-j DROP' )
    root.cmd( 'iptables -A FORWARD -i', localIntf, '-s', subnet, '-j ACCEPT' )
    root.cmd( 'iptables -A FORWARD -i', inetIntf, '-d', subnet, '-j ACCEPT' )
    root.cmd( 'iptables -t nat -A POSTROUTING -o ', inetIntf, '-j MASQUERADE' )
 
    # Instruct the kernel to perform forwarding
    root.cmd( 'sysctl net.ipv4.ip_forward=1' )
 
def stopNAT( root ):
    """Stop NAT/forwarding between Mininet and external network"""
    # Flush any currently active rules
    root.cmd( 'iptables -F' )
    root.cmd( 'iptables -t nat -F' )
 
    # Instruct the kernel to stop forwarding
    root.cmd( 'sysctl net.ipv4.ip_forward=0' )
 
def fixNetworkManager( root, intf ):
    """Prevent network-manager from messing with our interface,
       by specifying manual configuration in /etc/network/interfaces
       root: a node in the root namespace (for running commands)
       intf: interface name"""
    cfile = '/etc/network/interfaces'
    line = '\niface %s inet manual\n' % intf
    config = open( cfile ).read()
    if ( line ) not in config:
        print '*** Adding', line.strip(), 'to', cfile
        with open( cfile, 'a' ) as f:
            f.write( line )
    # Probably need to restart network-manager to be safe -
    # hopefully this won't disconnect you
    root.cmd( 'service network-manager restart' )
 
def connectToInternet( network, switch='s1', rootInterface='eth1', rootip='10.254', subnet='10.0.0.0/8'):
    """Connect the network to the internet
       switch: switch to connect to root namespace
       rootip: address for interface in root namespace
       subnet: Mininet subnet"""
    switch = network.get( switch )
    prefixLen = subnet.split( '/' )[ 1 ]
    routes = [ subnet ]  # host networks to route to
 
    # Create a node in root namespace
    root = Node( 'root', inNamespace=False )
 
    # Prevent network-manager from interfering with our interface
    fixNetworkManager( root, 'root-eth0' )
 
    # Create link between root NS and switch
    link = network.addLink( root, switch )
    # This statement also adds a route entry in the root context.
    # 192.168.100.0   0.0.0.0         255.255.255.0   U     0      0        0 root-eth0
    link.intf1.setIP( rootip, prefixLen )
 
    # Start network that now includes link to root namespace
    network.start()
 
    # Start NAT and establish forwarding
    # HACK: eth0 is the interface in the root context that connects
    # to the Internet.  Should be a parameter.
    # dml: This used to be eth1.
    startNAT( root, subnet, rootInterface )
 
    # Establish routes from end hosts
    i = 1
    k = 100
    for host in network.hosts:
        j = i + 10

        # HACK: We should set the IP according to 'subnet'
        # dml: note that using ifconfig will not update mininet's bindings of h1, etc.; setIP is necessary
        host.setIP( '192.168.' + str(k) +'.'+ str(j) )
        if (j >= 252):
            # move to the next subnet
            k += 1
            # Reset the i counter.
            i = 0
        host.cmd( 'ip route flush root 0/0' )
        host.cmd( 'route add -net', subnet, 'dev', host.defaultIntf() )
        host.cmd( 'route add default gw', rootip )
        i = i + 1

    start_sshd(network)

    return root

def start_sshd( network, cmd='/usr/sbin/sshd', opts='-D' ):
    "Run sshd on all hosts."
    for host in network.hosts:
        host.cmd( cmd + ' ' + opts + '&' )
    print
    print "*** Hosts are running sshd ***"
    print

# HACK: This is busted until we fix host.setIP above
#    for host in network.hosts:
#        print host.name, host.IP()
#    print

def read_config(network, filename):
    """Read the configuration file for the hosts that have the
    middlebox machine and hosts that can be used for sources and destinations.
    Args:
        filename: file name to read the config file.
    Returns:
        Two arrays of middlebox names and hosts."""
    middleboxes = [ ]
    hosts = [ ]
    for host in network.hosts:
        # Experimenting with all hosts as middleboxes.
        middleboxes.append(host.name)
        hosts.append(host.name)
    #config_dict = read_json(filename)
    #middleboxes = config_dict["middlebox_machines"]
    #hosts = config_dict["hosts"]
    return middleboxes, hosts

def perform_experiment(network, slick_controller, filename, middlebox_machines, src_dst_pairs, traffic_pattern, kill_wait_sec):
    """Perform the operation specified with provided parameters."""
    if filename:
        middlebox_names , hosts = read_config(network, filename)
        print "Middlebox Machines: ", middlebox_names
        print "Network Servers: ", hosts
    else:
        print "No filename provided to laod the network configuration."
    if middlebox_machines: # In case user has provided with the middlebox machine names. Use those instead of config file.
        middlebox_names = middlebox_machines
    if src_dst_pairs:
        hosts = src_dst_pairs
    middleboxes.load_shims(network, slick_controller, middlebox_names)
    time.sleep(10)
    middleboxes.generate_traffic(network, hosts, middlebox_names, traffic_pattern, kill_wait_sec)

def setup_sflow(network, switch_names):
    print "Setting up sflow agents on all the switches."
    sflow.setup_switch_sflow_agents(switch_names)
    time.sleep(3)
    # Need to start the collector first.
    print "Starting sflow collector."
    sflow.start_sflow_collector()
    # Wait for collector to start.
    time.sleep(3)
    # collector and switch agents must be started before setting 
    # up host metrices.
    #print "Setting up host monitoring metrics."
    #sflow.setup_host_sflow_metrics(net)

if __name__ == '__main__':

    desc = ( 'Initiate a Mininet Network that is connected to the Internet via NAT' )
    usage = ( '%prog -i <interface> [options]\n'
              '(type %prog -h for details)' )

    op = OptionParser( description=desc, usage=usage )
    # Options -c, -m, -p and -k are for expriments.
    op.add_option( '--config', '-c', action="store", 
                     dest="config", help = 'Configuration file for middlebox machines and network hosts.'  )
    op.add_option( '--middleboxes', '-m', action="store", 
                     dest="mblist", help = 'List of middlebox machines to install the shim layers.'  )
    op.add_option( '--traffic-pattern', '-p', action="store", 
                     dest="tpattern", help = 'Traffic pattern to generate. Please see documentation for identifiers.'  )
    op.add_option( '--kill-wait', '-k', action="store", 
                     dest="kill_wait", help = 'Number of seconds to wait before killing the experiment.'  )
    # topologies related option
    # These 2 options are for the depth and fanout of the tree.
    op.add_option( '--depth', '-d', action="store", 
                     dest="treedepth", help = 'Depth of Tree Topology'  )
    op.add_option( '--fanout', '-f', action="store", 
                     dest="fanout", help = 'Tree Fanout for tree topology'  )
    # -t use this option if the topology is to be created from a custom file.
    op.add_option( '--topo-file', '-t', action="store", 
                     dest="topology_file", help = 'Path of topology file.'  )
    # If -z is used then a Fat Tree topology will be created with the degree
    # specified to -z
    op.add_option( '--fattree-degree', '-z', action="store", 
                     dest="ft_degree", help = 'Switch degree for FatTree.'  )
    # Use this option to create a Jellyfish topology.
    op.add_option( '--jellyfish', '-j', action="store", 
                     dest="jellyfish_seed", help = 'JellyFish topology\'s seed.'  )
    # Use this option to create a DCell Topo.
    op.add_option( '-y', action="store_true", 
                     dest="create_dcell_network", help = 'Flag to create DCell Network'  )
    # This to identify the gateway box.
    # Currently we have only one gateway per network support.
    op.add_option( '--gateway', '-g', action="store", 
                     dest="gateway_switch", help = 'Please specify the switch name (e.g, "s1") that should be connected to internet.'  )
    op.add_option( '--root-interface', '-i', action="store", 
                     dest="rootInterface", help = 'The Ethernet interface that connects to the Internet'  )
    op.add_option( '--slick_controller', '-s', action="store", 
                     dest="slick_controller", help = 'IP Address of the slick contrller.'  )

    options, args = op.parse_args()
    if options.rootInterface is None:   # if filename is not given
        op.error('Must specify the Ethernet interface that connects to the Internet')
    config_filename = options.config
    middlebox_machines = options.mblist
    traffic_pattern = int(options.tpattern) if options.tpattern else None
    kill_wait_sec = int(options.kill_wait) if options.kill_wait else None
    topo_file_name = str(options.topology_file) if options.topology_file else None
    ft_degree = int(options.ft_degree) if options.ft_degree else None
    jellyfish_seed = int(options.jellyfish_seed) if options.jellyfish_seed else None
    gateway_switch = str(options.gateway_switch) if options.gateway_switch else None
    slick_controller = options.slick_controller
    print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXX", options.create_dcell_network, slick_controller

    lg.setLogLevel( 'info')

    topo = None
    rootnode = None
    host = CPULimitedHost
    link = TCLink
    # If the topology is to be read.
    if topo_file_name:
        print "Building network topology from file: ", topo_file_name
        topo = build_topology.build_topo(topo_file_name, False)
    elif ft_degree:
        print "Building a FatTree with K=", ft_degree
        topo = FatTreeTopo(ft_degree)
    elif jellyfish_seed:
        print "Building Jellyfish Topology."
        topo = JellyfishTopo(seed = jellyfish_seed, switches=16, nodes=16,bw=1)
        topo.draw()
    elif options.create_dcell_network:
        print "Building DCell Topology."
        topo = DCellTopo(bw=1, delay='1ms')
        #host = custom(CPULimitedHost, cpu=.15)  # 15% of system bandwidth
        #link = custom(TCLink, bw=1, delay='1ms', max_queue_size=20000)
        #net = Mininet(topo=topo, host=host, link=link, controller=RemoteController, autoStaticArp=True)
    elif options.treedepth and options.fanout:
        print "Building Tree Topology."
        topo = TreeTopo( depth = int(options.treedepth), fanout = int(options.fanout) , bw =1, delay='1ms')
    else:
        topo = TreeTopo( depth = 1, fanout = 3)
    # 6633 is controller port, 6634 is for dpctl queries, dump-flows etc.
    # This sets the controller port to 6634 by default, which can conflict
    # if we also start up another controller.  We should have this listen
    # somewher else since it is just for the NAT.
    print "Using the topo:", topo
    #net = Mininet(controller = lambda name: RemoteController( name, ip='127.0.0.1', port=6633 ) , switch=OVSKernelSwitch, topo=topo, listenPort=6634, host=host, link=link)
    net = Mininet(controller = lambda name: RemoteController( name, ip=slick_controller, port=6633 ) , switch=OVSKernelSwitch, topo=topo, listenPort=6634, host=host, link=link)
    #for link in topo.links():
    #    print link.intfName1
    #    print link.intfName2
    link_interfaces = [ ]
    switch_names = [ ]
    f = open("interfaces.txt",'w')
    for switch in net.switches:
	switch_names.append(switch.name)
    for link in topo.links():
        if link[0] in switch_names and link[1] in switch_names:
	    print link
	    s1 = net.getNodeByName(link[0])
	    s2 = net.getNodeByName(link[1])
 	    links = s1.connectionsTo(s2)
            for l in links:
		print l[0], l[1]
		print type(l[0]), type(l[1])
                link_interfaces.append((l[0].name,l[1].name))
                f.write(l[0].name + ','+ l[1].name + '\n')
                pass
            pass
    f.close()
    #net = Mininet(switch=OVSKernelSwitch, topo=topo, host=CPULimitedHost, link=TCLink)
    #net.start( )
    #time.sleep(5)
    #CLI( net )
    #net.stop( )
    #sys.exit(1)
    if gateway_switch:
        for switch in net.switches:
            switch_names.append(switch.name)
        if gateway_switch not in switch_names:
            print "ERROR: The specified gateway switch %s does not exist." % gateway_switch
            print "**** Cleaning up ssh background jobs..."
            # HACK: This assumes ssh is the only thing in the background on these hosts
            for host in net.hosts:
                host.cmd('kill %1')
            net.stop()
            sys.exit(1)
        print "Using %s as gateway switch." % gateway_switch
        rootnode = connectToInternet( net,
                                      gateway_switch,
                                      options.rootInterface,
                                      '192.168.100.1',
                                      '192.168.100.0/24') # Need this change so that 192.168.56.X traffic can be sent to controller.

    else:
        # Pick a network that is different from your 
        # NAT'd network if you are behind a NAT
        rootnode = connectToInternet( net,
                                      's1', # This assumes that the root switch of a topology is s1
                                      options.rootInterface,
                                      '192.168.100.1',
                                      '192.168.100.0/24')

    setup_sflow(net, switch_names)
    #demand_matrix.generate_binary_demand_matrix(net.hosts)
    src_dst_pairs = [ ]
    # Wait for n seconds before starting the middlebox instacnes.
    time.sleep(5)
    print "Generating Traffic Pattern: ", traffic_pattern
    if traffic_pattern and kill_wait_sec:
        # Once the network is built read the configuration file and start the software.
        perform_experiment( net, slick_controller, config_filename, middlebox_machines, src_dst_pairs, traffic_pattern, kill_wait_sec)

        #time.sleep(5)
        ## Shut down NAT
        #stopNAT( rootnode )
        ## Stop sflow
        #sflow.stop_sflow( )

        #print "**** Cleaning up ssh background jobs..."
        ## HACK: This assumes ssh is the only thing in the background on these hosts
        #for host in net.hosts:
        #    host.cmd('kill %1')

        #net.stop()
    else:
        print "WARNING: Not performing the experiment as required parameters are missing."

    print "*** Hosts are running and should have internet connectivity"
    print "*** Type 'exit' or control-D to shut down network"
    # Command Line
    CLI( net )

    # Shut down NAT
    stopNAT( rootnode )
    # Stop sflow
    sflow.stop_sflow( )

    print "**** Cleaning up ssh background jobs..."
    # HACK: This assumes ssh is the only thing in the background on these hosts
    for host in net.hosts:
        host.cmd('kill %1')

    net.stop()
