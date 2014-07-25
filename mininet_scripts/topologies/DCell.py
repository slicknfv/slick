#!/usr/bin/python
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import lg, output
from mininet.node import CPULimitedHost, RemoteController, Controller
from mininet.link import TCLink
from mininet.cli import CLI

import sys
import os

#Copied this code.

# Topology to be instantiated in Mininet
class DCellTopo(Topo):
    "DCell Topology k = 2, n = 4"

    def __init__(self, n=1, cpu=.1, bw=1000, delay=None,
                 max_queue_size=None, **params):

        # Initialize topo
        Topo.__init__(self, **params)

        # Host and link configuration
        hconfig = {'cpu': cpu}
        lconfig = {'bw': bw, 'delay': delay,
                   'max_queue_size': max_queue_size }

        # Create the actual topology
        # Creats each sub-module Dcell0
        for i in range(1, 6):
            s = self.addSwitch(name = 's'+str(i))
            for j in range(1, 5):
                h = self.addHost('h'+str(i)+str(j), **hconfig)
                s_h = self.addSwitch(name = 's'+str(i)+str(j))
                self.addLink(h, s_h, port1=0, port2=0, **lconfig)
                self.addLink(s_h, s, port1=1, port2=j, **lconfig)
                
        # Creats the connection between sub-modules        
        for i in range(1, 5):
            for j in range(i, 5):
                self.addLink('s'+str(i)+str(j), 's'+str(j+1)+str(i), port1=2, port2=2, **lconfig)


