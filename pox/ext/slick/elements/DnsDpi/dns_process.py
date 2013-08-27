"""This class has packet decoding.
"""
import socket
import dpkt
import string

from loadcache import LoadCache

from handledns import HandleDNS

class DNSProcess:
    def __init__(self):
        self.load_cache = LoadCache()
        self.load_cache.load_files()
        self.dns_handler = HandleDNS(self.load_cache)

    def decode(self,buf):
        """ This function is used to decode the packets received from wire.
        It should be called by process_pkt
        """
        eth = dpkt.ethernet.Ethernet(buf)
        pkt_len = len(buf)
        if(eth.type== dpkt.ethernet.ETH_TYPE_IP):
            ip = eth.data
            dst_ip = socket.inet_ntoa(ip.dst)
            src_ip = socket.inet_ntoa(ip.src)
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
                elif(ip.p == dpkt.ip.IP_PROTO_UDP):
                    udp =ip.data
                    if((udp.dport == 53) or (udp.sport == 53)): # A request. 
                        if(udp.dport == 53): # A request. 
                            return self.dns_handler.handle_dns_request(ip.src,ip.dst,ip.p,udp.sport,udp.dport,udp.data)
                        if(udp.sport == 53): # A DNS response
                            self.dns_handler.handle_dns_response(ip.src,ip.dst,ip.p,udp.sport,udp.dport,udp.data)
                    else:
                        pass
