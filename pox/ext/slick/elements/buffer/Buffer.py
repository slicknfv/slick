"""
    Buffer: An element that buffers the packet and until a trigger is received from the controller it starts forwarding the packets.
"""
import os.path
import datetime
from slick.Element import Element

class Buffer(Element):
    def __init__( self, shim, ed ):
        Element.__init__(self, shim, ed )
        self.buffer = [ ]
        self.file_handle = None
        self.enable_buffer = True
        self.enable_forwarding = False

    def init( self, params ):
        filename = params["file_name"]
        filename += str(self.ed)
        if(filename):
            self.file_handle = open( filename, 'a+' , 0)

    def configure(self, params):
        if "enable_forwarding" in params:
            if params["enable_forwarding"]:
                self.enable_forwarding = False
        if "disable_buffering" in params:
            if params["disable_buffering"]:
                self.enable_buffer = False

    def process_pkt( self, buf ):
        flow = self.extract_flow( buf )
        timestamp = datetime.datetime.now()
        self.file_handle.write( str(timestamp) + ' ' + str(flow) + '\n' )
        if self.enable_buffer:
            self.buffer.append(buf)
        if self.enable_forwarding:
            self.enable_buffer = False
            self.forward_packets()
        return buf

    def forward_packets():
        for buf in buffer:
            pass

    def shutdown( self ):
        print "Shutting down Buffer with element descriptor:", self.ed
        self.file_handle.close()
        return True


#Testing
def main():
    # XXX This is broken
    logger = Logger()
    logger.install(12,'/tmp/msox.txt')
    logger.configure('/tmp/msox1.txt')
    flow = {}
    flow["dl_src"] = 1 
    flow["dl_dst"] = 2
    packet = None
    logger.process_pkt(flow,packet)

if __name__ == "__main__":
    main()
