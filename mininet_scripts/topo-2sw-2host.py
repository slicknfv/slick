"""Custom topology example

Two directly connected switches plus a host for each switch:

   host --- switch --- switch --- host

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""

from mininet.cli import CLI
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.node import OVSKernelSwitch,UserSwitch,OVSSwitch

class MyTopo( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches
        leftHost = self.addHost( 'h1' )
        rightHost = self.addHost( 'h2' )
        leftSwitch = self.addSwitch( 's1' )
        rightSwitch = self.addSwitch( 's2' )

        # Add links
        self.addLink( leftHost, leftSwitch )
        self.addLink( leftSwitch, rightSwitch )
        self.addLink( rightSwitch, rightHost )


topos = { 'mytopo': ( lambda: MyTopo() ) }
topo = MyTopo()
net = Mininet(controller = lambda name: RemoteController( name, ip='127.0.0.1', port=6633 ) , switch=OVSSwitch, topo=topo, listenPort=6634)
#net = Mininet(controller = lambda name: RemoteController( name, ip='127.0.0.1', port=6633 ) , switch=OVSKernelSwitch, topo=topo, listenPort=6634)
net.start()
CLI( net )
print "**** Cleaning up ssh background jobs..."
for host in net.hosts:
    host.cmd('kill %1')

net.stop()
