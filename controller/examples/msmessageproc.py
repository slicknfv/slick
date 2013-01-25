import jsonpickle
import json

from collections import defaultdict
import socket

from nox.lib.packet.packet_utils import mac_to_str, mac_to_int,ipstr_to_int,ip_to_str
#Priorities: ShowStopper, High,Med.Low.
class MSMessageProcessor():
    def __init__(self,inst):
        #self.ms_rpc = MSRPC() #MiddleSoxRPC
        self.cntxt = inst
        # JSON Messenger Handlers
        self.json_msg_events = {}

        self.dns_handlers = DNSHandlers(self.cntxt)
        self.p0f_handlers = P0fHandlers(self.cntxt)
        self.logger_handlers = LoggerHandler(self.cntxt)
        # TODO: Make this application loading dynamic. [Priotiry: High]
        self.application_handles = []
        self.application_handles.append(self.dns_handlers)
        self.application_handles.append(self.p0f_handlers)
        self.application_handles.append(self.logger_handlers)

    # --
    # Function processes the JSON messages and returns a reply.
    # @args;
    #   msg = dict
    # --
    def process_msg(self,pyevent,msg):
        reply = {}
        print self.cntxt
        if(msg.has_key("type")):
            if(msg["type"] == "connect"):
                reply["dummy"]="connected"
                return reply
            if(msg["type"] == "disconnect"):
                reply["dummy"]="connected"
                return reply
            if(msg["type"] == "register"): # This machine has the shim installed
                machine_ip = socket.inet_aton(msg["machine_ip"]) 
                machine_mac = msg["machine_mac"]
                print "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",msg
                self.json_msg_events[machine_ip] = pyevent # To keep the connection open
                #self.send_msg(machine_ip,msg)
                #self.cntxt.fmap.update_function_desc(machine_mac,machine_ip,None) # Simply add the record of the shim.
                reply["dummy"]="connected"
                return reply
            if(msg["type"] == "BadDomainEvent"):
                self.dns_handler.handle_triggers(msg)



    # Two things to consider while installing the functions.
    # Does machine have the write specs.
    # Is machine location appropriate.
    def install_functions(self,msg):
        pass
    """
        Function to send messages to Middlebox through jsonmessenger.
        @args:
            mb_ip: Where the rule should be installed.
            reply: a dictionary that should be sent as json messge
    """
    def send_msg(self,mb_ip,msg):
        if (len(self.json_msg_events) >= 1):
            pyevent = self.json_msg_events[mb_ip]
            pyevent.reply(json.dumps(msg))
"""
    Trigger handling code.
"""
import os
import sys
class Triggers():

    def handle_triggers(self,event):
        '''Override this with DPI Box specific code and actions'''
        raise NotImplementedError( "Must Implement")

    def configure_triggers(self):
        '''Override this with DPI Box specific code'''
        raise NotImplementedError( "Must Implement")


from nox.lib.core     import *
from nox.lib.packet.ethernet     import ethernet
class DNSHandlers(Triggers):
    def __init__(self,inst):
        self.cntxt = inst
	self.DNS_BLOCK_TIMEOUT = 10#0xffff
        #set the configuration variables here:
        self.visit_threshold = 3 
        # TODO: for function specification.
        #self.func_spec = load_func_spec("DNS-DPI")


    def handle_BadDomainEvent(self,event):
        #src_ip = socket.inet_aton(event["src_ip"])
        src_ip = event["src_ip"]
        domain_ip_list = event["domain_ip_list"]
        src_dpid = self.cntxt.route_compiler.mmap.get_dpid(src_ip)# Bilal idiot.
        self._block_ip_list(src_dpid,src_ip,domain_ip_list)

    def handle_triggers(self,msg):
        if(msg["type"] == "BadDomainEvent"):
            del msg["type"]
            json_str = json.dumps(msg)
            data = jsonpickle.decode(json_str)
            print type(data) # Its a dict
            self.dns_handlers.handle_BadDomainEvent(data)

    def initialize(self):
        #get the function 
        pass

    # Set all the configurations based on the paramters inside the conf 
    def configure_trigger(self):
        pass
        # get the location of mb from the controller. from function_map
        # get the ip address of the mb from the controller. machine_map
        # There is already the function installed on the machine 
        # set the variables on the controller.
        pass

    def _block_ip_list(self,src_dpid,s_ip,domain_ip_list):
        src_dpid = 5 # Hardcoded for testing the trigger module as self.mmap.update_ip_dpid_mapping() is not called with trigger module.  REMOVE it with live traffic.
	src_ip = ipstr_to_int(s_ip)
	for item in domain_ip_list:
            print type(src_dpid)
            print src_dpid
	    dst_ip = ipstr_to_int(item)
	    print src_ip,dst_ip
	    ## Make sure we get the full DNS packet at the Controller
	    actions = []
	    self.cntxt.install_datapath_flow(src_dpid, 
				{ core.DL_TYPE : ethernet.IP_TYPE,
				    core.NW_SRC : src_ip,
				   core.NW_DST:dst_ip },
                                   self.DNS_BLOCK_TIMEOUT,self.DNS_BLOCK_TIMEOUT, #
                                   actions,buffer_id = None, priority=0xffff)




class LoggerHandler():
    def __init__(self,inst):
        self.cntxt = inst
        self.app_id = None
        self.file_name = "/tmp/dns_log.txt"
        self.app_desc = [] # Its the list of function descriptors used by the application.

    def handle_triggers(self,msg):
        pass

    def initialize(self):
        #Function hard coded taken from policy 
        flow["dl_src"] = None
        flow["dl_dst"] = None
        flow['dl_vlan'] = None
        flow['dl_vlan_pcp'] = None
        flow['dl_type'] = None
        flow['nw_src'] = None
        flow['nw_dst'] = None
        flow['nw_proto'] = None 
        flow['tp_src'] = None
        flow['tp_dst'] = 53
        func_desc = self.cntxt.route_compiler.apply_func(flow,"Logger",self) #sending the object 
        self.app_desc.append(func_desc)


class P0fHandlers():
    def __init__(self,inst):
        self.cntxt = inst
        pass
