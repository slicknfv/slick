"""
    Logger: Element that loggs all packets it receives to a specified file
"""
import os.path
from slick.Element import Element

class Logger(Element):
    def __init__( self, shim, ed ):
        Element.__init__(self, shim, ed )
        self.file_handle = None

    def init( self, params ):
        filename = params["file_name"]
        if(filename):
            if(os.path.isfile(filename)):
                self.file_handle = open( filename, 'a' )
            else:
                self.file_handle = open( filename, 'w' )

    # For DNS print fd and flow but for all other only print fd
    def process_pkt( self, buf ):
        print "INSIDE Logger's process_pkt"
        flow = self.extract_flow( buf )
        self.file_handle.write( str(flow) + '\n' )
        self.fwd_pkt( buf )

    def shutdown( self ):
        print "Shutting down Logger with element descriptor:", self.ed
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
