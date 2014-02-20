"""
    Constant : replaces the message in a packet with a fixed message
    only works for udp
"""
from slick.Element import Element
from dpkt import ethernet
from dpkt import ip
from dpkt import udp
import dumbnet

class Constant(Element):
    def __init__( self, shim, ed ):
        Element.__init__( self, shim, ed )
        self.message = ""

    def init( self, params):
        if "message" in params:
            self.message = params["message"]

    def process_pkt( self, buf ):
        eth_packet = ethernet.Ethernet(buf)
        ip_packet = eth_packet.data
        udp_packet = ip_packet.data
        ret_udp = udp.UDP(sport=udp_packet.sport,dport=udp_packet.dport)
        ret_udp.data = self.message
        ret_udp.ulen += len(ret_udp.data)
        ret_ip = ip.IP(id=0,src=ip_packet.src,dst=ip_packet.dst,p=17)
        ret_ip.data = ret_udp
        ret_ip.len += len(ret_udp)
        ret_eth = ethernet.Ethernet(src=eth_packet.src,dst=eth_packet.dst)
        ret_eth.data = dumbnet.ip_checksum(str(ret_ip))
        return str(ret_eth)
