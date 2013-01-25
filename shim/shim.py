# This class can be used to collect data from different sources.

import socket
import dpkt
import sys
import pcap
import getopt

import re # Need this regular expression to search through 
import time
import datetime
import os

from collections import defaultdict
from collections import deque
from sets import Set

from time import gmtime, strftime
import string
from uuid import getnode as get_mac

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,parentdir) 
from comm.clientcomm import ClientComm
from mb_api import ClientService


IN_PORT    = "in_port"
DL_SRC     = "dl_src"
DL_DST     = "dl_dst"
DL_VLAN    = "dl_vlan"
DL_VLAN_PCP = "dl_vlan_pcp"
DL_TYPE    = "dl_type"
NW_SRC     = "nw_src"
NW_SRC_N_WILD = "nw_src_n_wild"
NW_DST     = "nw_dst"
NW_DST_N_WILD = "nw_dst_n_wild"
NW_PROTO   = "nw_proto"
NW_TOS     = "nw_tos"
TP_SRC     = "tp_src"
TP_DST     = "tp_dst"

DEBUG_COLLECTION = False

class Shim:
    def __init__(self,iface,filename):
        self.iface = iface
        self.filename = filename # Name of the file where to read pcap data
        self.pcap_file = ""
        self.start_time = datetime.datetime.now()
        self.prev_ts = 0
        # This IP Address is used to see if its a configure packet or data-plane packet.
        self.mb_ip = socket.gethostbyname(socket.gethostname())
        self.mac = get_mac()
        # Create new connection
        self.client = ClientComm()
        self.register_machine()
        # These are needed to maintain the state.
        self.fuction_code_map = {} # dictionary which keeps track what code is downloaded on the machine hard disk and what is not present.
        self.fd_to_object_map = {}
        self.client_service = ClientService()


    def register_machine(self):
        register_msg = {"type":"register","machine_mac":self.mac,"machine_ip":self.mb_ip}
        print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",register_msg
        self.client.send_data_basic(register_msg)

    # --
    # Opens and gives a handle of pcap file.
    # --
    def loadpcap(self):
        print self.filename
        f = open(self.filename)
        self.pcap_file = dpkt.pcap.Reader(f)
        self.decode(self.pcap_file)
    

    # --
    # This function is for development and debugging from pcap files.
    # --
    def printpcap(self):
        for ts, buf in self.pcap_file:
            print ts,len(buf)
            eth = dpkt.ethernet.Ethernet(buf)
            dst_mac = (eth.dst).encode("hex")
            src_mac = (eth.src).encode("hex")
            print "Source MAC:", util.add_colons_to_mac(src_mac)
            print "Dst MAC:",util.add_colons_to_mac(dst_mac)
            #print `dpkt.ethernet.Ethernet(pkt)`
            ip = eth.data
            print ip.p
            if(ip.p == dpkt.ip.IP_PROTO_TCP):
                tcp = ip.data
                print "source port:", tcp.sport
                print "dst port:", tcp.dport
            elif(ip.p == dpkt.ip.IP_PROTO_UDP):
                udp = ip.data
                print "source port:", udp.sport
                print "dst port:", udp.dport
                
            print "Source IP:", ip.src.encode("hex")
            print "Dst IP:",ip.dst.encode("hex")


    # --
    # This function is used to sniff from wire
    # TODO: Add Code for different formats of streams if required.
    # --
    def sniff(self):
        # For now sniffing on the Ethernet interface.
        # sniffing on "any" causes the packets to be received in cooked form
        # which looses the Ethernet frame information but gives rest of the information
        # For further details: http://wiki.wireshark.org/SLL or man page of packet 7
        #pc = pcap.pcap(self.iface)
        pc = pcap.pcap("eth0")
        print 'Listening on %s: With filter %s' % (pc.name, pc.filter)
        try:
            decode = {  pcap.DLT_LOOP:dpkt.loopback.Loopback,
                        pcap.DLT_NULL:dpkt.loopback.Loopback,
                        pcap.DLT_IEEE802:dpkt.ethernet.Ethernet,
                        pcap.DLT_EN10MB:dpkt.ethernet.Ethernet,
                        pcap.DLT_LINUX_SLL:dpkt.sll.SLL}[pc.datalink()]
        except KeyError:
            print pc.datalink()
            print "Please check if you are handling proper packet type"
        try:
            self.decode(pc)
        except KeyboardInterrupt:
            nrecv, ndrop, nifdrop = pc.stats()
            print '\n%d packets received by filter' % nrecv
            print '%d packets dropped by kernel' % ndrop
            
    


    # --
    # This function is used to decode the packets received from wire
    #   pc: pcap stream of packets
    # --
    def decode(self,pc):
        if(self.client):
            #msg = self.client.recv_data_basic()
            #print "YYYYYYYYYYYYYYYYYYYYYYYYYYYYY",msg
            pass
        for ts, buf in pc:
            eth = dpkt.ethernet.Ethernet(buf)
            self.demux(eth)

    # This method demuxes the traffic.
    # It takes a packet.
    # extracts the flow.
    #   If flow belongs to configure traffic then does not touch it and passes it up.
    #   else: look up the function handle using the flow information.
    # Function handle is used to call process packet.
    #   Process packet can be another method of a class
    #   Can be a socket, where another process is reading the packets to depcrypt it.
    #   Can be shared memory pointer.
    # What if MUX/DEMUX is implemented on a NIC.
    #   if implemented on NIC hardware then it can be interface Tx queue,where a process reads the interface for incoming packet.
    def demux(self,packet):
        flow = self.extract_flow(packet)
        if(flow[NW_DST] == socket.inet_aton(self.mb_ip)):
            print "NOT USING IT"
        else:
            #print "This is a data packet"
            func_handle = self.get_function_handle_from_flow(flow)
            if(func_handle):
                # Based on the function_hadle 
                func_handle.process_packet(packet)
            else:
                pass
                #print "WARNING: We don't have a handler for the packet"


    # --
    # get_function_handle_from_flow
    # --
    def get_function_handle_from_flow(self,flow):
        #fd = self.client_service.flow_to_fd_map[flow]
        fd = 1
        if not (self.client_service.fd_to_object_map.has_key(fd)):
            return None
        else:
            return self.client_service.fd_to_object_map[fd]

    # use this to extract openflow flow.
    def extract_flow(self,ethernet):
        """
        Extracts and returns flow attributes from the given 'ethernet' packet.
        The caller is responsible for setting IN_PORT itself.
        """
        attrs = {}
        attrs[DL_SRC] = ethernet.src
        attrs[DL_DST] = ethernet.dst
        attrs[DL_TYPE] = ethernet.type
        p = ethernet.data
    
        attrs[DL_VLAN] = 0xffff # XXX should be written OFP_VLAN_NONE
        attrs[DL_VLAN_PCP] = 0
    
        if(ethernet.type== dpkt.ethernet.ETH_TYPE_IP):
            ip = ethernet.data
            attrs[NW_SRC] = ip.src
            attrs[NW_DST] = ip.dst
            attrs[NW_PROTO] = ip.p
            attrs[NW_TOS] = ip.tos
            p = ip.data
    
            if((ip.p == dpkt.ip.IP_PROTO_TCP) or (ip.p ==dpkt.ip.IP_PROTO_UDP)): 
                attrs[TP_SRC] = p.sport
                attrs[TP_DST] = p.dport
            else:
                #if isinstance(p, icmp):
                #    attrs[TP_SRC] = p.type
                #    attrs[TP_DST] = p.code
                #else:
                attrs[TP_SRC] = 0
                attrs[TP_DST] = 0
        else:
            attrs[NW_SRC] = 0
            attrs[NW_DST] = 0
            #if isinstance(p, arp):
            #    attrs[NW_PROTO] = p.opcode
            #else:
            #    attrs[NW_PROTO] = 0
            #attrs[NW_TOS] = 0
            #attrs[TP_SRC] = 0
            #attrs[TP_DST] = 0
        #print attrs
        return attrs


def usage():
    pass


            
def main(argv):
    iface = ""
    freq = 0
    mode = 2
    file_name = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdi:f:", ["help","debug","iface","file"])
    except getopt.GetoptError:
        print "Option error!"
        usage()
        sys.exit(2)
    for opt, arg in opts:
        print opt
        if opt in ("-h","--help"):
            usage()
            sys.exit()
        elif opt in("-d","--debug"):
            mode = constants.DEBUG_MODE
        elif opt in("-f","--file"): 
            file_name = arg
            cd_pcap = Shim(None,file_name)
            cd_pcap.loadpcap()
        elif opt in("-i","--iface"):
            iface = str(arg)
            cd_pcap = Shim(iface,None)
            cd_pcap.sniff() # hopefully you have done all the hw
            print "Listening on the interface: ",iface
        else:
            assert False, "Unhandled Option"
            usage()
    #dns_sensor = DNSSensor(mode,str(iface),file_name)
    #dns_sensor.initiate()

if __name__ == "__main__":
    main(sys.argv[1:])




