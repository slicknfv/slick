"""Stream Compression Element
"""
import dpkt
import logging

import snappy

from slick.Element import Element

class Compress(Element):
    """Element that can be used to Compress packet streams.
    """

    def __init__(self, shim, ed):
        Element.__init__(self, shim, ed )
        self.snappy = Snappy()


    def init(self, params):
        pass

    # Paramters
    def configure(self, params):
        pass

    def process_pkt(self, buf):
        """Compress the packet payload and forwrd it."""
        payload = None
        eth = dpkt.ethernet.Ethernet(buf)
        if(eth.type == dpkt.ethernet.ETH_TYPE_IP):
            ip = eth.data
            if(ip.p == dpkt.ip.IP_PROTO_TCP):
                tcp = ip.data
                payload = tcp.data
            elif(ip.p == dpkt.ip.IP_PROTO_UDP):
                udp = ip.data
                payload = udp.data
        compressed_payload = snappy.compress(payload)
        compressed_buf = header + compressed_payload
        self.fwd_pkt(compressed_buf)
