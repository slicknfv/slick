"""
    Event class that is derviced by all the classes that need to generate the trigger events for the controller.
    TODO: Add more documentation here.
"""
import socket
class Event(object): # Need object for using jsonpickle
        def __init__(self,eid,name,flow):
            self.eid = eid
            self.name = name
            """
                Flow that triggered the event.
                Might be needed to settle between multiple triggers.
            """
            self.flow = flow

        def set_flow(self,src_mac,dst_mac,vlan_id,src_ip,dst_ip,proto,src_port,dst_port):
            self.flow.src_mac = src_mac
            self.flow.dst_mac = dst_mac
            self.flow.vlan_id = vlan_id
            self.flow.src_ip = src_ip
            self.flow.dst_ip = dst_ip
            self.flow.proto = proto
            self.flow.src_port = src_port
            self.flow.dst_port = dst_port

        def set_flow(self,flow):
            self.flow = flow

        def get_flow(self):
            return self.flow

        def set_event_id(self,event_id):
            self.eid = event_id

        def get_event_id(self):
            return self.eid

        def set_name(self,name):
            self.name = name

        def get_name(self):
            return self.name

"""
    Class for defining a flow for the architecture.
"""
class Flow():
    def __init__(self,src_mac,dst_mac,vlan_id,src_ip,dst_ip,proto,src_port,dst_port):
        self.src_mac = src_mac
        self.dst_mac = dst_mac,
        self.vlan_id = vlan_id
        self.src_ip = socket.inet_ntoa(src_ip)
        self.dst_ip = socket.inet_ntoa(dst_ip)
        self.proto = proto
        self.src_port = src_port
        self.dst_port = dst_port



# --
# These events are related to DNS 
# --

"""
    @description:
        Generate this event if the bad domain name is looked up.
"""
class BadDomainEvent(Event):
    def __init__(self,domain_name,src_ip,domain_ip_list,level,domain_category,eid,name,flow):
        Event.__init__(self,eid,name,flow)
        self.domain_name = domain_name
        self.src_ip = src_ip
        self.domain_ip_list = domain_ip_list
        self.level = level
        self.domain_category = domain_category # gambling, porn, social media etc.

"""
    @description:
        Generate this event if multiple bad domain names are requested by client.
"""
class MultipleBadDomainRequestEvent(Event):
    def __init__(self,domain_name,src_ip,num_requests,eid,name,flow):
        Event.__init__(self,eid,name,flow)
        self.domain_name = domain_name
        self.src_ip = src_ip
        self.num_requests = num_requests # Number of times self.src_ip requested the self.domain_name
"""
    @description:
        Generate this event if the DNS request size increases from a certain limit for the packets.
"""
class DNSPacketSizeEvent(Event):
    def __init__(self,domain_name,packet_size,eid,name,flow):
        Event.__init__(self,eid,name,flow)
        self.domain_name = domain_name
        self.packet_size = packet_size

"""
    @description:
        Generate this event if the DNS queries from a certain client increase from a certain threshold.
        To warn the controller..
"""
class DNSRequestExceedEvent(Event):
    def __init__(self):
        self.domain_name = None
        self.src_ip = None
        self.frequency = None # Tell the controller if the frequency increases beyond a certain limit.

"""
    @description:
        Generate this event if we see DNS traffic going to port 53 of enterprise hosts that are not DNS servers.
        OR 
        Traffic is going to one of the DNS servers that is not authorized. e.g, if an enterprise is using OpenDNS service to block some sites and if someone uses another DNS 
        generate this event.
"""
class IllegalDNSServer(Event):
    def __init__(self):
        self.illegal_host_ip = None 

# --
# These events are related to p0f
# --

"""
    There can be multiple OSes for the same IP
"""
class OSDetectEvent(Event):
    def __init__(self,ip_addr,os,os_flavor,eid,name,flow):
        Event.__init__(self,eid,name,flow)
        self.ip_addr = ip_addr
        self.os = os
        self.os_flavor = None
        self.client = False
        self.sever = False

"""
    There can be multiple browsers for the same host.
"""
class BrowserDetectEvent(Event):
    def __init__(self,ip_addr,browser,eid,name,flow):
        Event.__init__(self,eid,name,flow)
        self.ip_addr = ip_addr
        self.browser = browser
    
# --
# These triggers are related to nDPI
# --
"""
    There can be multiple OSes for the same IP
"""
class ProtocolDetectEvent(Event):
    def __init__(self,ip_addr,protocl,eid,name,flow):
        Event.__init__(self,eid,name,flow)
        self.ip_adddr = ip_addr
        self.protocol = protocol

