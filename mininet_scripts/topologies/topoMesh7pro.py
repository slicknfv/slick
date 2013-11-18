"""Custom Bipartite

author: Maciej Korczynski (maciej.korczynski@rutgers.edu)

example of usage:
sudo mn --custom ~/mininet/custom/topoMesh7pro.py --topo mesh7pro
"""

from mininet.topo import Topo
import random

class Mesh7pro( Topo ):
    "Mesh topology, by default 20 switches and 2 hosts per switch"

    def __init__( self, X = 20, Y = 2):

        # Initialize topology
        Topo.__init__( self )

	# number of hosts attached to each switch (index in table indicates the switch) IT STARTS from 0
        self.nr_of_hosts = []


        # Set Node IDs for both group of switches (X and Y group)
	switches = []
	for s in range(1, X + 1):
		switches.append('s%s' % s)

        # Add nodes (group of X switches)
	# h = X + 1
        h = 1
	for switch in switches:
          nr_hosts = Y # random.randint(1, Y)
	  self.nr_of_hosts.append(nr_hosts)

          switch = self.addSwitch(switch)
          for i in range(1, nr_hosts+1):
            host = self.addHost('h%s' % h)
	    self.addLink(switch,host)
            h += 1

	# Add edges between switches
        for s1 in range(1, X+1):
          for s2 in range(s1+1, X+1):
            if(random.random() <= 1): #0.2 0.3
              self.addLink( 's%s' % s1, 's%s' % s2 )


    def get_nr_of_hosts( self, index ):
      return self.nr_of_hosts[index]


topos = { 'mesh7pro': ( lambda: Mesh7pro() ) }
