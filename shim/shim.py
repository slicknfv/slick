# This class can be used to collect data from different sources.

import sys
import os
import commands # for getting the default interface
import signal


parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir) 
sys.path.insert(0, "/home/mininet/middlesox/pox/ext") 

sys.path.insert(0, '../lib/')
import pcap as pcap

import socket
import dpkt
import getopt
import time
import datetime
import string
import json

from uuid import getnode as get_mac

############################################################
# Slick Packages
from comm.clientcomm import ClientComm
from mb_api import ClientService
from shim_table import ShimTable
import shim

from dynamic_load import MiddleboxModules

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

def shim_loop_helper(sh, hdr, pkt):
	sh.decode(hdr, pkt)

def signal_handler(unused_signal, unused_frame):
    print 'Shutting Down Shim.'
    sys.exit(0)

class Shim:

    def __init__(self, iface, oface, filename):
        self.iface = iface
        self.oface = oface
        print self.iface
        self.filename = filename # Name of the file where to read pcap data
        self.pcap_file = ""
        self.start_time = datetime.datetime.now()
        self.prev_ts = 0

        # This IP Address is used to see if its a configure packet or data-plane packet.
        self.mb_ip = socket.gethostbyname(socket.gethostname())
        self.mac = get_mac()

        # Create new connection
        # HACK: This should not be hardcoded to the OF controller.
        self.client = ClientComm()
        self.register_machine()

        # These are needed to maintain the state.
        # dictionary that keeps track of what code is downloaded on the machine 
        # hard disk and what is not present.
        self.fuction_code_map = {} 
        self.fd_to_object_map = {}
        inst = self
        self.client_service = ClientService(inst)
        self.forward_data_sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)

        if(self.oface != None):
            self.forward_data_sock.bind((self.oface, 0))
        else:
            self.forward_data_sock.bind(("eth1", 0))

    def register_machine(self):
        """Registers the middlebox with slick controller."""
        print "Registering middlebox machine at MAC Address: ", self.mac, "and IP Address:", self.mb_ip
        register_msg = {"type":"register", "machine_mac":self.mac, "machine_ip":self.mb_ip}
        self.client.send_data_basic(register_msg)

    def loadpcap(self):
        """Opens and gives a handle of pcap file.
        """
        print 'Reading pcap dump from file:', self.filename
        if(self.filename):
            f = open(self.filename)
            self.pcap_file = dpkt.pcap.Reader(f)
            for ts, buf in self.pcap_file:
                self.decode(None, buf)
    

    def printpcap(self):
        """This function is for development and debugging from pcap files.
        """
        for ts, buf in self.pcap_file:
            print ts,len(buf)
            eth = dpkt.ethernet.Ethernet(buf)
            dst_mac = (eth.dst).encode("hex")
            src_mac = (eth.src).encode("hex")
            print "Source MAC:", util.add_colons_to_mac(src_mac)
            print "Dst MAC:",util.add_colons_to_mac(dst_mac)

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

    def sniff(self):
        """This function is used to sniff from wire
            TODO: Add Code for different formats of streams if required.
        """
        # <dave>
        try:
	    promiscuousMode = True
            pc = pcap.pcap(self.iface, pcap.PCAP_SNAPLEN_DFLT, promiscuousMode)  # true == promiscuous mod
            pc.setdirection(pcap.PCAP_D_IN)           # capture only incoming packets
	    cnt = 9999999                        # XXX How do we say "loop forever"?
            pc.loop(cnt, shim_loop_helper, self) # will this call our decode method?
        except KeyboardInterrupt:
            pc.breakloop()

		# </dave>

    def old_sniff(self):
        # For now sniffing on the Ethernet interface.
        # sniffing on "any" causes the packets to be received in cooked form
        # which looses the Ethernet frame information but gives rest of the information
        # For further details: http://wiki.wireshark.org/SLL or man page of packet 7

        pc = pcap.pcap(self.iface)
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
    
    def decode_msg_and_call(self, data):
        message_list = data.split('\n')
        print message_list
        for index, m in enumerate(message_list):
            if(index < len(message_list)-1):
                msg = json.loads(m)
                if(msg["type"] == "install"):
                    self.client_service.exposed_install_function(msg)
                if(msg["type"] == "configure"):
                    self.client_service.exposed_configure_function(msg)
                if(msg["type"] == "stop"):
                    self.client_service.exposed_stop_function(msg)

    # This function is used to decode the packets received from wire
    #   pc: pcap stream of packets
    def old_decode(self, pc):
        for ts, buf in pc:
            if(self.client):
                msg = self.client.recv_data_basic()
                if(msg):
                    self.decode_msg_and_call(msg)
                pass
            self.demux(buf)

    def decode(self, hdr, buf):
        if(self.client):
            msg = self.client.recv_data_basic()
            if(msg):
                self.decode_msg_and_call(msg)
        self.demux(buf)


    def demux(self, buf):
        """Demuxes the traffic. 

        It takes a packet and extracts the flow.
           If flow belongs to configure traffic then does not touch it and passes it up.
           else: look up the function handle using the flow information.
         Function handle is used to call process packet.
           Process packet can be another method of a class
           Can be a socket, where another process is reading the packets to depcrypt it.
           Can be shared memory pointer.
         What if MUX/DEMUX is implemented on a NIC.
           If implemented on NIC hardware then it can be interface Tx queue,
           where a process reads the interface for incoming packet.

        Args:
            buf: Ethernet frame from pcap library.
        Returns:
            None
        """
        packet = dpkt.ethernet.Ethernet(buf)
        flow = self.extract_flow(packet)
        if(flow[NW_DST] == socket.inet_aton(self.mb_ip)):
            print "NOT USING IT"
        else:
            func_handles = self.client_service.get_function_handles_from_flow(flow)
            if(func_handles):
                for func_handle in func_handles:
                    processed_pkt = func_handle.process_pkt(buf)
                    if processed_pkt:
                        buf = processed_pkt
                        continue
                    else:
                        break
                self.client_service.fwd_pkt(buf)
            # This is forwarding at the cost of computation.
            # This can be useful in future to show that number
            # rules can be reduced.
            #else:
            #    #try reverse_flow
            #    reverse_flow = self.get_reverse_flow(flow)
            #    func_handle = self.client_service.get_function_handles_from_flow(reverse_flow)
            #    if(func_handle):
            #        func_handle.process_pkt(buf)

    def extract_flow(self, eth):
        """Extracts and returns flow attributes from the given 'ethernet' packet.

        Args:
            Ethernet frame from pcap library.
        Retruns:
            Returns a flow dict.
        """
        attrs = {}
        attrs[DL_SRC] = eth.src
        attrs[DL_DST] = eth.dst
        attrs[DL_TYPE] = eth.type
        p = eth.data
    
        attrs[DL_VLAN] = 0xffff # XXX should be written OFP_VLAN_NONE
        attrs[DL_VLAN_PCP] = 0
    
        if(eth.type== dpkt.ethernet.ETH_TYPE_IP):
            ip = eth.data
            # "Source IP: ",int(ip.src.encode("hex"),16)
            # "Destination IP: ",int(ip.dst.encode("hex"),16)
            attrs[NW_SRC] = socket.inet_ntoa(ip.src)
            attrs[NW_DST] = socket.inet_ntoa(ip.dst)
            attrs[NW_PROTO] = ip.p
            attrs[NW_TOS] = ip.tos
            p = ip.data
    
            if((ip.p == dpkt.ip.IP_PROTO_TCP) or (ip.p ==dpkt.ip.IP_PROTO_UDP)): 
                attrs[TP_SRC] = p.sport
                attrs[TP_DST] = p.dport
            else:
                attrs[TP_SRC] = 0
                attrs[TP_DST] = 0
        else:
            attrs[NW_SRC] = 0
            attrs[NW_DST] = 0
        return attrs

    def get_reverse_flow(self, flow):
        """Return a reverse flow for the given flow.

        Args:
            flow: Flow dict
        Returns:
            Reverse flow dict.
        """
        attrs = {}
        attrs[DL_SRC] = flow[DL_DST]
        attrs[DL_DST] = flow[DL_SRC]
        attrs[DL_TYPE] = flow[DL_TYPE]

        attrs[DL_VLAN] = flow[DL_VLAN]
        attrs[DL_VLAN_PCP] = flow[DL_VLAN_PCP]

        attrs[NW_SRC] = flow[NW_DST]
        attrs[NW_DST] = flow[NW_SRC]
        if(flow.has_key(NW_PROTO)):
            attrs[NW_PROTO] = flow[NW_PROTO]
        if(flow.has_key(NW_TOS)):
            attrs[NW_TOS] = flow[NW_TOS]

        if(flow.has_key(TP_DST)):
            attrs[TP_SRC] = flow[TP_DST]
        if(flow.has_key(TP_SRC)):
            attrs[TP_DST] = flow[TP_SRC]
        return attrs


def usage():
    pass


def main(argv):
    signal.signal(signal.SIGINT, signal_handler)
    default_interface = commands.getoutput("ifconfig -s | grep eth0 | awk '{print $1}'")
    iface = default_interface
    oface = default_interface
    freq = 0
    mode = 2
    file_name = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdi:f:o:", ["help", "debug", "iface", "file", "oface"])
    except getopt.GetoptError:
        print "Option error!"
        usage()
        sys.exit(2)
    # should change this to use the OptionParser class
    for opt, arg in opts:
        print opt
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in("-d", "--debug"):
            mode = constants.DEBUG_MODE
        elif opt in("-f", "--file"): 
            file_name = arg
        elif opt in("-i", "--iface"):
            iface = str(arg)
        elif opt in("-o", "--oface"):
            oface = str(arg)
            print "Listening on the interface: ", iface
        else:
            assert False, "Unhandled Option"
            usage()
    if(iface):
        print "Listening on the interface: ", iface
        print "Sending on the interface: ", oface
        cd_pcap = Shim(iface, oface, None)
        cd_pcap.sniff() # hopefully you have done all the hw
    if(file_name):
        print "Sending on the interface: ", oface
        cd_pcap = Shim(None, oface, file_name)
        cd_pcap.loadpcap()

if __name__ == "__main__":
    main(sys.argv[1:])
