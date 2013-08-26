# Correlate DNS information based on application ID.
# Use TTL to keep the record and then expire it later on
# TODO: Handle the case where you should block all forms 
# domain.com and www.domain.com and xyz.domain.com
from collections import defaultdict
import socket
import logging

import dpkt

from loadcache import LoadCache
from events import Flow
from dns_state import DNSState


class HandleDNS():
	def __init__(self,ld):
		# Key is IP addr and DNS Transaction ID. Tuple  and value is the dpid where first packet came.
		self.request_cache = {} 
		# Block domains list
		self.load_cache = ld #LoadCache()
		self.DNS_BLOCK_TIMEOUT = 0xffff
                self.dns_state = DNSState() # Use this to update the state.

	def _has_been_requested(self,ip_addr,dns_id):
		ip_trans_id_tuple = (ip_addr,dns_id)
		if(self.request_cache.has_key(ip_trans_id_tuple)):
			return True

	
	def _block_ip_tuples(self,src_dpid,src_dst_ip_block_list):
        	global inst
		for item in src_dst_ip_block_list:
			src_ip = item[0]
			dst_ip = ipstr_to_int(item[1])

    	def handle_dns_response(self, src_ip,dst_ip,proto,sport,dport,data):
                dns = dpkt.dns.DNS(data)
        	if not dns:
        	    log.err('received invalid DNS packet',system='pyswitch')
        	    return 
		#list of tuples
		src_dst_ip_block_list = []
                if((dns.qr ==  dpkt.dns.DNS_R) and (dns.rcode == dpkt.dns.DNS_RCODE_NOERR) and (dns.opcode == dpkt.dns.DNS_QUERY)): # Its a DNS response and no error 
                    if (len(dns.an) >= 1):
		        if(self._has_been_requested(dst_ip,dns.id)): #Handle replies for requested and blocked domain names only.
                            if(len(self.request_cache[(dst_ip,dns.id)]) == 2):
                                domain_name = self.request_cache[(dst_ip,dns.id)][0]
                                flow = self.request_cache[(dst_ip,dns.id)][1]
                            else:
                                raise Exception("Domain Name or Flow Information Missing")
                            for ans in dns.an:
                                if(ans.type == 1):
                                    ip_addr = ans.rdata
                                    # Since this is the response
				    src_dst_tuple = (dst_ip,ip_addr)
				    if(src_dst_tuple not in src_dst_ip_block_list):
				        src_dst_ip_block_list.append(src_dst_tuple) 
                                    pass
                                pass
                            pass
                            self.dns_state.update_domain_ips(domain_name,flow,src_dst_ip_block_list)

    	def handle_dns_request(self, src_ip,dst_ip,proto,sport,dport,data):
                domain_blocked = False
                blocked_domain_name = None
                dns = dpkt.dns.DNS(data)
        	if not dns:
        	    logging.warn('received invalid DNS packet')
        	    return 
                if ((dns.qr == dpkt.dns.DNS_Q) and (dns.opcode == dpkt.dns.DNS_QUERY) and (len(dns.qd) == 1)): ### ADD OTHER CONDITIONS also
        	    for question in dns.qd:
                        if(self.load_cache.is_blocked_domain(question.name)):
                            # This flow triggered the event.
                            flow = Flow(None,None,None,src_ip,dst_ip,proto,sport,dport)
                            print "This domain name is blocked.",question.name,dns.id ," and blcoked domain is accessed from this IP: ",socket.inet_ntoa(src_ip)
                            domain_blocked = True
                            blocked_domain_name = question.name
                            # This code should be on controller for keeping track of dpid
                            # as a sensor can't know this.
                            if not (self.request_cache.has_key((src_ip,dns.id))):
			        self.request_cache[(src_ip,dns.id)] = (question.name,flow)
                return (domain_blocked,src_ip,blocked_domain_name) #Its a really bad hack will only send the last domain name.
        """
            Extracts the domain name from the packets.
        """
        def extract_domain_name(self,data):
            dns = dpkt.dns.DNS(data)
            # validate the DNS query
            if ((dns.qr == dpkt.dns.DNS_Q) and (dns.opcode == dpkt.dns.DNS_QUERY) and (len(dns.qd) == 1)): ### ADD OTHER CONDITIONS also
                domain_name = dns.qd[0].name
                return (dns.id,domain_name)

        def get_ip(self,pkt):
            """This function gets the list of severs that are returned for the DNS query
             http://www.iana.org/assignments/dns-parameters 
            """
            ip_list = []
            dns = dpkt.dns.DNS(pkt)
            if((dns.qr ==  dpkt.dns.DNS_R) and (dns.rcode == dpkt.dns.DNS_RCODE_NOERR) and (dns.opcode == dpkt.dns.DNS_QUERY)): # Its a DNS response and no error 
                if (len(dns.an) >= 1):
                    for ans in dns.an:
                        if(ans.type == 1):
                            ip_addr = socket.inet_ntoa(ans.rdata)
                            ip_list.append(ip_addr)
