"""Stream Compression Element
"""
from dpkt import ethernet
from dpkt import ip
from dpkt import udp
from dpkt import tcp
import logging
import dumbnet
import zlib
import base64

from slick.Element import Element

class Compress(Element):
    """Element that can be used to Compress packet streams.
    """

    def __init__(self, shim, ed):
        Element.__init__(self, shim, ed )


    def init(self, params):
        self.base64 = "base64" in params
        self.compressing = not "decompress" in params

    def process_pkt(self, buf):
        """Compress the packet payload and forword it."""
        eth_packet = ethernet.Ethernet(buf)
        if(eth_packet.type == ethernet.ETH_TYPE_IP):
            ip_packet = eth_packet.data
            ret_ip = ip.IP(id=ip_packet.id,src=ip_packet.src,dst=ip_packet.dst,p=ip_packet.p)
            if(ip_packet.p == ip.IP_PROTO_TCP):
                tcp_packet = ip_packet.data
                payload = self.compress(str(tcp_packet.data))
                #TODO
            elif(ip_packet.p == ip.IP_PROTO_UDP):
                udp_packet = ip_packet.data
                payload = self.compress(str(udp_packet.data))
                ret_udp = udp.UDP(sport=udp_packet.sport,dport=udp_packet.dport)
                ret_udp.data = payload
                ret_udp.ulen += len(ret_udp.data)
                ret_ip.data = ret_udp
                ret_ip.len += len(ret_udp)
                ret_eth = ethernet.Ethernet(src=eth_packet.src,dst=eth_packet.dst)
                ret_eth.data = dumbnet.ip_checksum(str(ret_ip))
                return str(ret_eth)

    def compress(self, payload):
        if self.base64:
            if self.compressing:
                return base64.b64encode(zlib.compress(payload))
            else:
                return zlib.decompress(base64.b64decode(payload))
        else:
            if self.compressing:
                return zlib.compress(payload)
            else:
                return zlib.decompress(payload)


