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
        self.pkt_count = 0
        self.inflation_count = 0

    def init( self, params ):
        filename = params["file_name"]
        filename += str(self.ed)
        inflation_rate = params["inflation_rate"]
        if(filename):
            self.file_handle = open( filename, 'a+' , 0)
        if inflation_rate:
            if inflation_rate > 1:
                self.inflation_rate = inflation_rate
            else:
                print "Error: inflation rate should be >= 1"

    def process_pkt( self, packets ):
        self.total_count += len(packets)
        if self.inflation_rate >= 2:
            num_incoming_packets = len(packets)
            num_outgoing_packets = num_incoming_packets * self.inflation_rate
            packets = packets * self.inflation_rate
            for index, buf in enumerate(packets):
                #for index in range(0, outgoing_packets):
                flow = self.extract_flow( buf )
                timestamp = datetime.datetime.now()
                if index >= len(packets):
                    self.file_handle.write( str(timestamp) + ' INFLATED ' + str(flow) + '\n' )
                else:
                    self.file_handle.write( str(timestamp) + ' ' + str(flow) + '\n' )
            return packets
        elif self.inflation_rate >= 1 and self.inflation_rate < 2:
            # For now inflate traffic in increments of 10%
            starting_pkt = 10 - int((self.inflation_rate - 1)*10)
            # For now inflate traffic in increments of 10%
            self.inflation_count = int((self.inflation_rate-1) * 10) + 10
            self.pkt_count = self.pkt_count + len(packets)

            last_packet = None
            for buf in packets:
                flow = self.extract_flow( buf )
                timestamp = datetime.datetime.now()
                self.file_handle.write( str(timestamp) + ' ' + str(flow) + '\n' )
                last_packet = buf

            if self.pkt_count > starting_pkt:
                flow = self.extract_flow( last_packet )
                timestamp = datetime.datetime.now()
                self.file_handle.write( str(timestamp) + ' INFLATED ' + str(flow) + '\n' )
                packets.append(last_packet)
                if self.pkt_count >= self.inflation_count:
                    self.pkt_count = 0
            return packets
        else:
            print "Error: The packet inflation rate should be >=1"
            return None

    def shutdown( self ):
        print "Shutting down Logger with element descriptor:", self.ed
        self.file_handle.close()
        return True
