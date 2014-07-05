"""
    More: An element that is used to forward More packets than the incoming packets.
"""
import os.path
import datetime
from slick.Element import Element

class More(Element):
    def __init__( self, shim, ed ):
        Element.__init__(self, shim, ed )
        self.file_handle = None
        # If this value is 2 => double the number of packets.
        # If this value is 1 => simply forward the packet.
        # If this value is 9 => 9x the incoming packet.
        # For this element it can only be integer >= 2
        self.inflation_rate = 2
        self.total_count = 0

    def init( self, params ):
        filename = params["file_name"]
        filename += str(self.ed)
        inflation_rate = params["inflation_rate"]
        if(filename):
            self.file_handle = open( filename, 'a+' , 0)
        if inflation_rate:
            if inflation_rate >= 2:
                self.inflation_rate = inflation_rate
            else:
                print "Error: inflation rate should be >= 1"

    def process_pkt( self, packets ):
        num_incoming_packets = len(packets)
        num_outgoing_packets = num_incoming_packets * self.inflation_rate
        packets = packets * self.inflation_rate
        for buf in packets:
            #for index in range(0, outgoing_packets):
            self.total_count += 1
            flow = self.extract_flow( buf )
            timestamp = datetime.datetime.now()
            self.file_handle.write( str(timestamp) + ' ' + str(flow) + '\n' )
        return packets

    def shutdown( self ):
        print "Shutting down Logger with element descriptor:", self.ed
        self.file_handle.close()
        return True
