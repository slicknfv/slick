# This class can be used to collect data from different sources.

import socket
import dpkt
import sys
import pcap
import constants
import util
#import packet.dns

import re # Need this regular expression to search through 
import time
import datetime

import select
from collections import defaultdict
from collections import deque
from sets import Set

from time import gmtime, strftime
import string


from handledns import HandleDNS

DEBUG_COLLECTION = False
class CollectData:
    def __init__(self,iface,filename):
        self.iface = iface
        self.filename = filename # Name of the file where to read pcap data
        self.pcap_file = ""
        self.start_time = datetime.datetime.now()
        self.prev_ts = 0
        self.dns_handler = HandleDNS()

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
    # Print IP Header Info
    # --
    def print_ip_hdr(self,ip):
        print "Source IP: ",ip.src.encode("hex")
        print "Destination IP: ",ip.dst.encode("hex")
        print "Proto Type: " , ip.p
        pass

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
        pass
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
        for ts, buf in pc:
            # Packet Debugging
            #print `decode(buf)`
            #eth = `dpkt.sll.SLL(buf)`
            eth = dpkt.ethernet.Ethernet(buf)
            #print `eth` # debug
            dst_mac = util.add_colons_to_mac((eth.dst).encode("hex"))
            src_mac = util.add_colons_to_mac((eth.src).encode("hex"))
            #print "Source MAC:", util.add_colons_to_mac(src_mac)
            #print "Dst MAC:",util.add_colons_to_mac(dst_mac)
            pkt_len = len(buf)
            if(eth.type== dpkt.ethernet.ETH_TYPE_IP):
                ip = eth.data
                dst_ip = socket.inet_ntoa(ip.dst)
                octet_list = string.split(dst_ip,'.')
                broadcast =  False
                for o in octet_list:
                    if (o == "255"):
                        broadcast = True
                        break
                if((octet_list[0] == "224") or (octet_list[0] == "239")):
                    broadcast = True #Its multicast actually.
                
                if not broadcast:
                    if(ip.p == dpkt.ip.IP_PROTO_TCP):
                        pass
                        #tcp =ip.data
                    elif(ip.p == dpkt.ip.IP_PROTO_UDP):
                        udp =ip.data
                        #print "dst port:", udp.dport
                        if((udp.dport == 53) or (udp.sport == 53)): # A request. 
                            if(udp.dport == 53): # A request. 
                                self.dns_handler.handle_dns_request(ip.src,ip.dst,ip.p,udp.sport,udp.dport,udp.data)
                            if(udp.sport == 53): # A DNS response
                                self.dns_handler.handle_dns_response(ip.src,ip.dst,ip.p,udp.sport,udp.dport,udp.data)
                        else:
                            #ip_list = self.dns_data.get_connected_ip(src_mac)#Return the list of ip addresses returned tou
                            pass


