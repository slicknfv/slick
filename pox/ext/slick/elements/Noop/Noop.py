"""
	Noop : an element that simply forwards packets along
"""

from slick.Element import Element

class Noop(Element):
    def __init__( self, shim, ed ):
        Element.__init__( self, shim, ed )

    def process_pkt( self, buf ):
        self.fwd_pkt( buf )
