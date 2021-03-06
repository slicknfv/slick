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
        self.total_count = 0

    def init( self, params ):
        filename = params["file_name"]
        filename += str(self.ed)
        drop_count = params["drop_count"]
        if(filename):
            self.file_handle = open( filename, 'a+' , 0)
        if drop_count:
            self.drop_count = drop_count

    def process_pkt( self, packets ):
        dropped = False
        ret_packets = packets
        for index, buf in enumerate(packets):
            flow = self.extract_flow( buf )
            timestamp = datetime.datetime.now()
            self.pkt_count = self.pkt_count + len(packets)
            self.total_count = self.total_count + len(packets)
            if self.pkt_count >= self.drop_count:
                print "Dropping packet number:",self.total_count
                self.pkt_count = 0
                del ret_packets[index]
                dropped = True
                #return
            if not dropped:
                self.file_handle.write( str(self.total_count) + ' '+ str(timestamp) + ' ' + str(flow) + '\n' )
            else:
                self.file_handle.write( str(self.total_count) + ' DROPPED '+ str(timestamp) + ' ' + str(flow) + '\n' )
            print ret_packets
            return ret_packets

    def shutdown( self ):
        print "Shutting down Logger with element descriptor:", self.ed
        self.file_handle.close()
        return True
