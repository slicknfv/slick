"""
    Logger: an element that copies each packet it receives to a configurable file, then forwards the packet along
"""
import os.path
import datetime
from slick.Element import Element

class Logger(Element):
    def __init__( self, shim, ed ):
        Element.__init__(self, shim, ed )
        self.file_handle = None

    def init( self, params ):
        filename = params["file_name"]
        filename += str(self.ed)
        if(filename):
            self.file_handle = open( filename, 'a+' , 0)

    def process_pkt( self, packets ):
        for buf in packets:
            flow = self.extract_flow( buf )
            timestamp = datetime.datetime.now()
            self.file_handle.write( str(timestamp) + ' ' + str(flow) + '\n' )
        return packets

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
