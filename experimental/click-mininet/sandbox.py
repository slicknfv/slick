#!/usr/bin/python

"""
Netgaze experimental sandbox. Uses the Mininet virtualization platform to create
a network to demonstrate use of the Netgaze DSL.
"""

import sys, time, fileinput, shutil, os
from mininet.net import Mininet
from mininet.node import RemoteController

from mininet.log import lg, info, error, debug, output
from mininet.cli import CLI
from mininet.term import *

from click import ClickKernelSwitch

flush = sys.stdout.flush
START_TIME = 0
STATIC_ARP = True
DEBUG = False


def start(ip="127.0.0.1",port="6633",app="Netgaze"):
    net = Mininet(switch=ClickKernelSwitch)

    net.addController('c0')
    h1 = net.addHost('h1', ip='144.0.3.0')
    h2 = net.addHost('h2', ip='132.0.2.0')
    sw = net.addSwitch("click", dpid=1)
    sw.linkAs(h1, "h1")
    sw.linkAs(h2, "h2")

    net.start()
    net.staticArp()

    output("Network ready\n")
    time.sleep(3)
    # Enter CLI mode
    output("Press Ctrl-d or type exit to quit\n")

    lg.setLogLevel('info')
    CLI(net)
    lg.setLogLevel('output')
    net.stop()

start()
