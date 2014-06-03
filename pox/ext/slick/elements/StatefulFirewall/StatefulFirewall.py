"""
    StatefulFirewall: Dummy Firewall that randomly drops packets.
"""
import os.path
import datetime
from slick.Element import Element

class StatefulFirewall(Element):
    def __init__( self, shim, ed ):
        Element.__init__(self, shim, ed )
        self.file_handle = None

    def init( self, params ):
        filename = params["file_name"]
        filename += str(self.ed)
        if(filename):
            self.file_handle = open( filename, 'a+' , 0)

    def process_pkt( self, buf ):
        flow = self.extract_flow( buf )
        timestamp = datetime.datetime.now()
        self.file_handle.write( str(timestamp) + ' ' + str(flow) + '\n' )
        return buf

    def shutdown( self ):
        print "Shutting down StatefulFirewall with element descriptor:", self.ed
        self.file_handle.close()
        return True

if __name__ == "__main__":
    main()
