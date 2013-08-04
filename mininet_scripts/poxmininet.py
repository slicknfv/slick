from mininet.node import Controller
from os import environ

POXDIR = environ['HOME'] + '/middlesox/pox/pox'

class POX(Controller):
  def __init__(self, name, cdir=POXDIR,
               command='python pox.py',
               cargs=('openflow.of_01 --port=%s '
                      'forwarding.l2_learning' ),
               **kwargs ):
    Controller.__init__(self, name, cdir=cdir,
                        command=command,
                        cargs=cargs, **kwargs )

controllers = { 'pox': POX }
