"""
    DelayBuffer: takes a packet and delays it's transmission by a packet
"""
from slick.Element import Element
from collections import deque

class DelayBuffer(Element):
    def __init__( self, shim, ed ):
        Element.__init__(self, shim, ed )
        self.bufferSize = 1
        self.packetBuffer = deque()

    def init( self, params ):
        if "buffer_size" in params:
            self.bufferSize = params["buffer_size"]

    def process_pkt( self, buf ):
	self.packetBuffer.append(buf)
        if len(self.packetBuffer) > self.bufferSize:
		return self.packetBuffer.popleft()

    def shutdown( self ):
        print "Shutting down DelayBuffer with element descriptor:", self.ed
        return True

