"""
    Less: An element that is used to forward less packets than the incoming packets.
"""
import os.path
import datetime
from slick.Element import Element

class Less(Element):
    def __init__( self, shim, ed ):
        Element.__init__(self, shim, ed )
        self.file_handle = None
        # If this value is 2 => drop every 2nd packet or 5 out of 10
        # If this value is 1 => drop every packet.
        # If this value is 9 => drop 9 packets out of 10 and so on.
        self.drop_rate = 2
        self.pkt_count = 0

    def init( self, params ):
        filename = params["file_name"]
        filename += str(self.ed)
        pkt_count = params["pkt_count"]
        if(filename):
            self.file_handle = open( filename, 'a+' , 0)
        if pkt_count:
            self.pkt_count = pkt_count

    def process_pkt( self, buf ):
        flow = self.extract_flow( buf )
        timestamp = datetime.datetime.now()
        self.file_handle.write( str(timestamp) + ' ' + str(flow) + '\n' )
        self.pkt_count +=1
        if self.pkt_count >= self.drop_rate:
            self.pkt_count = 0
            return
        return buf

    def shutdown( self ):
        print "Shutting down Logger with element descriptor:", self.ed
        self.file_handle.close()
        return True
