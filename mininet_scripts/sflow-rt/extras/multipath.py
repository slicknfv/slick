#!/usr/bin/env python
# based on article:
# http://blog.sflow.com/2013/06/flow-collisions.html

from mininet.net  import Mininet
from mininet.node import RemoteController
from mininet.link import TCLink
from mininet.cli  import CLI
from mininet.util import quietRun

c = RemoteController('c',ip='127.0.0.1')
net = Mininet(link=TCLink);

# Add hosts and switches
leftHost1  = net.addHost('h1',ip='10.0.0.1',mac='00:04:00:00:00:01')
leftHost2  = net.addHost('h2',ip='10.0.0.2',mac='00:04:00:00:00:02')
rightHost1 = net.addHost('h3',ip='10.0.0.3',mac='00:04:00:00:00:03')
rightHost2 = net.addHost('h4',ip='10.0.0.4',mac='00:04:00:00:00:04')

leftSwitch     = net.addSwitch('s1')
rightSwitch    = net.addSwitch('s2')
leftTopSwitch  = net.addSwitch('s3')
rightTopSwitch = net.addSwitch('s4')

# Add links
# set link speeds to 10Mbit/s
linkopts = dict(bw=10)
net.addLink(leftHost1,  leftSwitch,    **linkopts )
net.addLink(leftHost2,  leftSwitch,    **linkopts )
net.addLink(rightHost1, rightSwitch,   **linkopts )
net.addLink(rightHost2, rightSwitch,   **linkopts )
net.addLink(leftSwitch, leftTopSwitch, **linkopts )
net.addLink(leftSwitch, rightTopSwitch,**linkopts )
net.addLink(rightSwitch,leftTopSwitch, **linkopts )
net.addLink(rightSwitch,rightTopSwitch,**linkopts )

# Start
net.controllers = [ c ]
net.build()
net.start()

# Enable sFlow
# 1-in-10 sampling rate for 10Mbit/s links is proportional to 1-in-1000 for 1G
# see http://blog.sflow.com/2013/02/sdn-and-large-flows.html
quietRun('ovs-vsctl -- --id=@sflow create sflow agent=eth0 target=127.0.0.1 sampling=10 polling=20 -- -- set bridge s1 sflow=@sflow -- set bridge s2 sflow=@sflow -- set bridge s3 sflow=@sflow -- set bridge s4 sflow=@sflow')

# CLI
CLI( net )

# Clean up
net.stop()
