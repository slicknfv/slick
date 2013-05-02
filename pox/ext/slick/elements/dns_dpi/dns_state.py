# Use this class to maintain state about DNS events.
from collections import defaultdict
from events import BadDomainEvent,MultipleBadDomainRequestEvent# Triggers cause events.
from comm.clientcomm import ClientComm

import uuid

import socket
import jsonpickle
import json


class DNSState():
    def __init__(self):
        self.domain_ips = defaultdict(list) # key:domain value:[(src_ip,dst_ip1),(src_ip,dst_ip2)]
	self.src_ip_lookup_count = defaultdict(int) # Keep a count of how many times a 'bad domain name' is requested by the ip.
        self.src_ip_dns_size_count = defaultdict(int)
	self.dns_ip = defaultdict(list) # dns to ip 
        # Communication
        #self.client = ClientComm()


    def update_domain_ips(self,domain_name,flow,src_dst_ip_block_list):
        self.domain_ips[domain_name] = src_dst_ip_block_list
        self.__send_event("BadDomainEvent",flow,domain_name,src_dst_ip_block_list)
        self.keep_domain_lookup_count(domain_name,flow,src_dst_ip_block_list)

    def keep_domain_lookup_count(self,domain_name,flow,src_dst_ip_block_list):
        src_ip = None
        if(len(src_dst_ip_block_list) > 0):
            src_ip = flow.src_ip
            self.src_ip_lookup_count[src_ip] += 1
            if(self.src_ip_lookup_count[src_ip] >= 10):
                self.__send_event("MultipleBadDomainEvent",flow,domain_name,src_dst_ip_block_list)
                pass
            pass
        pass

    # --
    # Build the object and send_data to controller.
    # --
    def __send_event(self,event_name,flow,*args):
        print "Sending Event"
        if(event_name == "BadDomainEvent"):#len(args) == 1
            src_ip = flow.src_ip
            eid = uuid.uuid1() # Machine's MAC address and the current time.
            domain_ip_list = []
            if(len(args) == 2):
                domain_name = args[0]
                for item in args[1]:#src_dst_ip_block_list
                    domain_ip_list.append(socket.inet_ntoa(item[1]))
                bad_domain_event = BadDomainEvent(domain_name,src_ip,domain_ip_list,None,None,eid,event_name,flow)
                print "XXXXXXXXXXXX"
                print "Sending BadDomainEvent"
                #self.client.send_data(bad_domain_event)
                pass
            pass
        pass
        if(event_name == "MultipleBadDomainEvent"):#len(args) == 1
            src_ip = flow.src_ip
            eid = uuid.uuid1() # Machine's MAC address and the current time.
            if(len(args) == 2):
                domain_name = args[0]
                num_requests = args[1]
                multiple_bad_domain_req_event = MultipleBadDomainRequestEvent(domain_name,src_ip,num_requests,eid,event_name,flow)
                #self.client.send_data(multiple_bad_domain_req_event)
                pass
            pass
        pass
    def get_event(self,event_name,flow,*args):
        if(event_name == "BadDomainEvent"):#len(args) == 1
            src_ip = ["src_ip"]
            eid = uuid.uuid1() # Machine's MAC address and the current time.
            domain_ip_list = []
            if(len(args) == 2):
                domain_name = args[0]
                for item in args[1]:#src_dst_ip_block_list
                    domain_ip_list.append(item)
                print domain_name,src_ip,domain_ip_list,eid,event_name,flow
                bad_domain_event = BadDomainEvent(domain_name,src_ip,domain_ip_list,0,0,123,event_name,flow)
                data = json.loads(jsonpickle.encode(bad_domain_event))
                # returns a dict
                return data
