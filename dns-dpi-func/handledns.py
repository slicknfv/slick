# Correlate DNS information based on application ID.
# Use TTL to keep the record and then expire it. later on
# TODO: Handle the case where you should block all forms 
# domain.com and www.domain.com and xyz.domain.com
from collections import defaultdict
import socket

import dpkt

from loadcache import LoadCache
from events import Flow
from dns_state import DNSState


class HandleDNS():
	def __init__(self):
		# Key is IP addr and DNS Transaction ID. Tuple  and value is the dpid where first packet came.
		self.request_cache = {} 
		# Block domains list
		self.load_cache = LoadCache()
		self.load_cache.load_files()
		self.DNS_BLOCK_TIMEOUT = 0xffff
                self.dns_state = DNSState() # Use this to update the state.

	def _has_been_requested(self,ip_addr,dns_id):
		ip_trans_id_tuple = (ip_addr,dns_id)
		if(self.request_cache.has_key(ip_trans_id_tuple)):
			#print "Reply for blocked domain with id:",dnsh.id ," and blcoked domain reply is going to this IP: ",ipv4h.dstip
			return True

	
	def _block_ip_tuples(self,src_dpid,src_dst_ip_block_list):
        	global inst
		for item in src_dst_ip_block_list:
			src_ip = item[0]
			dst_ip = ipstr_to_int(item[1])
			print src_ip,dst_ip
			# XXX Send the packet to controller for blocking the tuple.

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
                            print domain_name
                            for ans in dns.an:
                                if(ans.type == 1):
                                    #print "A request",ans.name,"\tresponse",socket.inet_ntoa(ans.rdata)
                                    #ip_addr = socket.inet_ntoa(ans.rdata)
                                    ip_addr = ans.rdata
                                    # Since this is the response
				    src_dst_tuple = (dst_ip,ip_addr)
				    if(src_dst_tuple not in src_dst_ip_block_list):
				        src_dst_ip_block_list.append(src_dst_tuple) 
                                    pass
                                pass
                            pass
                            print src_dst_ip_block_list
                            self.dns_state.update_domain_ips(domain_name,flow,src_dst_ip_block_list)
			    #self._block_ip_tuples(src_dpid,src_dst_ip_block_list)

    	def handle_dns_request(self, src_ip,dst_ip,proto,sport,dport,data):
                #request_id,domain_name  = self.extract_domain_name(packet)
                dns = dpkt.dns.DNS(data)
        	if not dns:
        	    print 'received invalid DNS packet'
        	    return 
                if ((dns.qr == dpkt.dns.DNS_Q) and (dns.opcode == dpkt.dns.DNS_QUERY) and (len(dns.qd) == 1)): ### ADD OTHER CONDITIONS also
        	    for question in dns.qd:
                        if(self.load_cache.is_blocked_domain(question.name)):
                            # This flow triggered the event.
                            flow = Flow(None,None,None,src_ip,dst_ip,proto,sport,dport)
                            print "This domain name is blocked.",question.name,dns.id ," and blcoked domain is accessed from this IP: ",socket.inet_ntoa(src_ip)
                            # This code should be on controller for keeping track of dpid
                            # as a sensor can't know this.
                            if not (self.request_cache.has_key((src_ip,dns.id))):
			        self.request_cache[(src_ip,dns.id)] = (question.name,flow)

	def _sanitize_domain_lookups(self,domain_name):
		print domain_name
        """
            Extracts the domain name from the packets.
        """
        def extract_domain_name(self,data):
            dns = dpkt.dns.DNS(data)
            # validate the DNS query
            if ((dns.qr == dpkt.dns.DNS_Q) and (dns.opcode == dpkt.dns.DNS_QUERY) and (len(dns.qd) == 1)): ### ADD OTHER CONDITIONS also
                print "Query: ",dns.id
                domain_name = dns.qd[0].name
                return (dns.id,domain_name)

        """
         This function gets the list of severs that are returned for the DNS query
         http://www.iana.org/assignments/dns-parameters 
        """
        def get_ip(self,pkt):
            ip_list = []
            dns = dpkt.dns.DNS(pkt)
            if((dns.qr ==  dpkt.dns.DNS_R) and (dns.rcode == dpkt.dns.DNS_RCODE_NOERR) and (dns.opcode == dpkt.dns.DNS_QUERY)): # Its a DNS response and no error 
                if (len(dns.an) >= 1):
                    for ans in dns.an:
                        if(ans.type == 1):
                            #print "A request",ans.name,"\tresponse",socket.inet_ntoa(ans.rdata)
                            ip_addr = socket.inet_ntoa(ans.rdata)
                            ip_list.append(ip_addr)
            
