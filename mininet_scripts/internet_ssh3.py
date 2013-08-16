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

from mininet.topo import Topo
from mininet.topolib import TreeNet, TreeTopo
from mininet.util import quietRun
from mininet.node import OVSController, Controller, RemoteController
 
#################################
def startNAT( root, inetIntf='eth0', subnet='10.0/8' ):
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
 
def connectToInternet( network, switch='s1', rootip='10.254', subnet='10.0.0.0/8'):
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
    link.intf1.setIP( rootip, prefixLen )
 
    # Start network that now includes link to root namespace
    network.start()
 
    # Start NAT and establish forwarding
    # HACK: eth1 is the interface in the root context that connects
    # to the Internet.  Should be a parameter.
    startNAT( root, 'eth0', subnet )
 
    # Establish routes from end hosts
    i = 1
    for host in network.hosts:
        j = i + 10

        # HACK: We should set the IP according to 'subnet', and probably using setIP
        host.cmd( 'ifconfig h' + str(i) + '-eth0 192.168.100.' + str(j) )
        host.cmd( 'ip route flush root 0/0' )
        host.cmd( 'route add -net', subnet, 'dev', host.defaultIntf() )
        host.cmd( 'route add default gw', rootip )
        i = i + 1

    start_sshd(network)

    return root

def start_sshd( network, cmd='/usr/sbin/sshd', opts='-D' ):
    "Start a network, connect it to root ns, and run sshd on all hosts."
    for host in network.hosts:
        host.cmd( cmd + ' ' + opts + '&' )
    print
    print "*** Hosts are running sshd ***"
    print

# HACK: This is busted until we fix host.setIP above
#    for host in network.hosts:
#        print host.name, host.IP()
#    print


############################################################
# MAIN
 
if __name__ == '__main__':
    lg.setLogLevel( 'info')

# This sets the controller port to 6634 by default, which can conflict
# if we also start up another controller.  We should have this listen
# somewher else since it is just for the NAT.
#    net = TreeNet( depth=1, fanout=4)

    #net = Mininet()
    #net.addController('c0', port=6639)
    #net = Mininet(controller = lambda name: RemoteController( name, ip='10.0.2.15', port=6633 ), listenPort=6639 )
    #net = Mininet(controller = lambda name: RemoteController( name, ip='127.0.0.1', port=6633 ), listenPort=6639 )
    net = Mininet(controller = lambda name: RemoteController( name, ip='127.0.0.1', port=6633 ) )
    net.addController('c0')

    s1 = net.addSwitch('s1')

    for hostNum in range(1,4):
        node = net.addHost( 'h%s' % hostNum )
        net.addLink(node,s1)

    # Configure and start NATted connectivity
    #rootnode = connectToInternet( net )

    # Pick a network that is different from your 
    # NAT'd network if you are behind a NAT
    rootnode = connectToInternet( net, 's1', '192.168.100.1', '192.168.100.0/24')

    print "*** Hosts are running and should have internet connectivity"
    print "*** Type 'exit' or control-D to shut down network"
    # Command Line
    CLI( net )

    # Shut down NAT
    stopNAT( rootnode )

    print "**** Cleaning up ssh background jobs..."
    # HACK: This assumes ssh is the only thing in the background on these hosts
    for host in net.hosts:
        host.cmd('kill %1')

    net.stop()
