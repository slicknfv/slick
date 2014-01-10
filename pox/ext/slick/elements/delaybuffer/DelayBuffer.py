"""
    DelayBuffer: takes a packet and delays it's transmission by a packet
"""
from slick.Element import Element

class DelayBuffer(Element):
    def __init__( self, shim, ed ):
        Element.__init__(self, shim, ed )
        self.lastPacket = None

    def process_pkt( self, buf ):
	old = self.lastPacket
        if old:
		self.lastPacket = buf
		return old
	else:
		self.lastPacket = buf

    def shutdown( self ):
        print "Shutting down DelayBuffer with element descriptor:", self.ed
        return True
