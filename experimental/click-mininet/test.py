#!/usr/bin/python

import time
#from mininet.net import init, Mininet
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import Node
from mininet.node import RemoteController
from mininet.log import lg, info, error, debug, output
from mininet.cli import CLI

from click import ClickKernelSwitch

def test_wget(ip="127.0.0.1",port="6633"):
    net = Mininet(switch=ClickKernelSwitch,
                  controller=lambda n: RemoteController(n,
                                                        defaultIP=ip, port=int(port)))

    net.addController('c0')
    h1 = net.addHost('h1', ip='144.0.3.1')
    h2 = net.addHost('h2', ip='144.0.3.2')
    print "Creating Click Switch."
    sw = net.addSwitch("click", dpid = 1)
    sw.linkAs(h1, "h1")
    sw.linkAs(h2, "h2")

    net.start()
    net.staticArp()

    output("Network ready\n")
    time.sleep(3)

    # Run a simple file transfer test
    output(h1.cmd("./serve.sh"))
    output(h2.cmd("wget 144.0.3.1"))

    time.sleep(1)
    CLI(net)
    net.stop()

if __name__ == "__main__":
    print "Running wget test"
    test_wget()
    print "Wget test complete. Retrieved file should be in index.html"

