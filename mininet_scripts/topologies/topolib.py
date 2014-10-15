"Library of potentially useful topologies for Mininet"

from mininet.topo import Topo
from mininet.net import Mininet

class TreeTopoOld( Topo ):
    "Topology for a tree network with a given depth and fanout."

    def __init__( self, depth=1, fanout=2, bw=1000, delay='0ms'):
        super( TreeTopo, self ).__init__()
        # Numbering:  h1..N, s1..M
        self.hostNum = 1
        self.switchNum = 1
        self.bw = bw
        self.delay = delay
        self.switches_with_host= [ ]
        # Build topology
        self.addTree( depth, fanout )
        self.addHosts()

    def addTree( self, depth, fanout ):
        """Add a subtree starting with node n.
           returns: last node added"""
        isSwitch = depth > 0
        if isSwitch:
            node = self.addSwitch( 's%s' % self.switchNum )
            self.switchNum += 1
            for _ in range( fanout ):
                child = self.addTree( depth - 1, fanout )
                self.addLink( node, child, bw=self.bw, delay=self.delay)
        else:
            node = self.addHost( 'h%s' % self.hostNum )
            self.hostNum += 1
        return node

    def addHosts(self):
    	for switch in self.switches():
            host = self.addHost( 'h%s' % self.hostNum )
            self.addLink( switch, host, bw=self.bw, delay=self.delay)
            self.hostNum += 1

    def addTreeSlick( self, depth, fanout ):
        """Add a subtree starting with node n.
           returns: last node added"""
        isSwitch = depth > 0
        if isSwitch:
            node = self.addSwitch( 's%s' % self.switchNum )
            self.switchNum += 1
            for _ in range( fanout ):
                child = self.addTreeSlick( depth - 1, fanout )
            	host = self.addHost( 'h%s' % self.hostNum )
                self.hostNum += 1
                self.addLink( node, child, bw=self.bw, delay=self.delay)
                self.addLink( node, host, bw=self.bw, delay=self.delay) # host attached with the switch.
        else:
            node = self.addHost( 'h%s' % self.hostNum )
            self.hostNum += 1
        return node


class TreeTopo( Topo ):
    """Topology for a tree network with a given depth and fanout.
     And each switch has atleast one host connected with it. Leaves
     have three hosts connected with them."""

    def __init__( self, depth=1, fanout=2, bw=1000, delay='0ms'):
        super( TreeTopo, self ).__init__()
        # Numbering:  h1..N, s1..M
        self.hostNum = 1
        self.switchNum = 1
        self.bw = bw
        self.delay = delay
        self.switches_with_host= [ ]
        # Build topology
        self.addTree( depth, fanout )
        # Add hosts to all the switches
        self.addHosts()

    def addTree( self, depth, fanout ):
        """Add a subtree starting with node n.
           returns: last node added"""
        isSwitch = depth > 0
        if isSwitch:
            node = self.addSwitch( 's%s' % self.switchNum )
            self.switchNum += 1
            for _ in range( fanout ):
                child = self.addTree( depth - 1, fanout )
                self.addLink( node, child, bw=self.bw, delay=self.delay)
        else:
            node = self.addHost( 'h%s' % self.hostNum )
            self.hostNum += 1
        return node

    def addHosts(self):
    	for switch in self.switches():
            host = self.addHost( 'h%s' % self.hostNum )
            self.addLink( switch, host, bw=self.bw, delay=self.delay)
            self.hostNum += 1


def TreeNet( depth=1, fanout=2, **kwargs ):
    "Convenience function for creating tree networks."
    topo = TreeTopo( depth, fanout )
    return Mininet( topo, **kwargs )
