#######################################################################
# This file has different Slick applications present for now.
# TODO: Move the applications to another folder and into separate files.
# TODO: AFTER_SLICK: Algorithmize writing of applications.
# TODO: AFTER_SLICK: Make it compatible with another language like click/Procera etc.
#######################################################################
import os
import sys
from collections import defaultdict
from pox.lib.addresses import IPAddr, EthAddr
import pox.lib.packet as pkt
import pox.openflow.libopenflow_01 as of

from utils.packet_utils import *

"""
    Trigger handling code.
"""
class Triggers():

    def handle_trigger(self,event):
        '''Override this with DPI Box specific code and actions'''
        raise NotImplementedError( "Must Implement")

    def configure_triggers(self):
        '''Override this with DPI Box specific code'''
        raise NotImplementedError( "Must Implement")


class DNSHandlers(Triggers):
    def __init__(self,inst):
        self.cntxt = inst
        self.installed = False
	self.DNS_BLOCK_TIMEOUT = 1000#0xffff
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

    def handle_trigger(self,msg):
        if(msg["type"] == "BadDomainEvent"):
            del msg["type"]
            json_str = json.dumps(msg)
            data = jsonpickle.decode(json_str)
            print type(data) # Its a dict
            self.handle_BadDomainEvent(data)

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
	src_ip = s_ip
	for item in domain_ip_list:
            print type(src_dpid)
            print src_dpid
	    dst_ip = item
	    print src_ip,dst_ip
	    ## Make sure we get the full DNS packet at the Controller
	    #actions = []
	    #self.cntxt.install_datapath_flow(src_dpid, 
	    #    		{ core.DL_TYPE : ethernet.IP_TYPE,
	    #    		    core.NW_SRC : src_ip,
	    #    		   core.NW_DST:dst_ip },
            #                       self.DNS_BLOCK_TIMEOUT,self.DNS_BLOCK_TIMEOUT, #
            #                       actions,buffer_id = None, priority=0xffff)
            msg = of.ofp_flow_mod()
            msg.priority = 42
            msg.match.dl_type = 0x800
            msg.match.nw_src = IPAddr(src_ip)
            msg.match.nw_dst = IPAddr(dst_ip)
            dst_port = of.OFPP_NONE
            msg.actions.append(of.ofp_action_output(dst_port))
            self.cntxt.connection.send(msg)




"""
    LoggerUnitTest One Application One Function Instance.
    We use this application to create two instances of the same application and two function instances.
"""
class LoggerUnitTest():
    def __init__(self,inst,AD,file_name,count_thresh,flow):
        self.cntxt = inst
        self.app_d = AD
        self.installed = False # To check if the app is installed
        self.conf = False # Set this to true to update the configure
        #Configuration specified parameters
        self.flow = flow
        # Conf parameters
        self.file_name = file_name
        self.count_thresh = count_thresh
        self.fd =None # Its the list of function descriptors used by the application.


    def configure_user_params(self):
        if not self.conf:
            params = {"file_name":self.file_name,"count_thresh":self.count_thresh}
            self.cntxt.configure_func(self.app_d,self.fd,params)
            self.conf = True
    def handle_trigger(self,fd,msg):
        print "Logger handle_trigger function descriptor",fd
        print "Logger handle_trigger called",msg
    def init(self):
        # read this from policy file.
        file_name = self.file_name
        parameters = {"file_name":file_name}
        #Incrementing app_d since we'll create 2 applications 
        fd= self.cntxt.apply_elem(self.app_d,self.flow,"Logger",parameters,self) 
        print fd
        if((fd >0)):#=> we have sucess
            #self.func_descs.append(fd)
            self.fd = fd
            self.installed = True
            print "Logger Installed."
"""
# ############################################################################################################################################
# One Apllication with Two TriggerAll Functions
# Creates two function instances with one application. Based on the flow to function descriptor mapping, shim should handle packet to the
# right function instance. And correct function instance should raise an event.
# ############################################################################################################################################
"""
class TriggerAllUnitTest():
    def __init__(self,inst):
        self.cntxt = inst
        self.app_d = 100
        self.fd =[]# Its the list of function descriptors used by the application.
        self.installed = False # To check if the app is installed
        self.conf = 0 # Set this to true to update the configure
        self.flows = []
        flow1 = {}
        #Function hard coded taken from policy 
        flow1["dl_src"] = None
        flow1["dl_dst"] = None
        flow1['dl_vlan'] = None
        flow1['dl_vlan_pcp'] = None
        flow1['dl_type'] = None
        flow1['nw_src'] = None
        flow1['nw_dst'] = None
        flow1['nw_proto'] = None 
        flow1['tp_src'] = None
        flow1['tp_dst'] = 53
        self.flows.append(flow1)

        flow2 = {}
        flow2["dl_src"] = None
        flow2["dl_dst"] = None
        flow2['dl_vlan'] = None
        flow2['dl_vlan_pcp'] = None
        flow2['dl_type'] = None
        flow2['nw_src'] = None
        flow2['nw_dst'] = None
        flow2['nw_proto'] = None 
        flow2['tp_src'] = None
        flow2['tp_dst'] = 80
        self.flows.append(flow2)
        self.f1 = open("1_trigger.txt","w")
        self.f2 = open("2_trigger.txt","w")

    def configure_user_params(self):
        if (self.conf < 2): # Need to call configure_func twice since this application has two functions instantiated
            params = {}
            self.cntxt.configure_func(self.app_d,self.fd[self.conf],params) # Call connfigure_func with same app if and different function descriptors.
            self.conf +=1

    # This handle Trigger will be called twice for 2 functions.
    def handle_trigger(self,fd,msg):
        if(fd == self.fd[0]):
            print "TriggerAll handle_trigger function descriptor",fd
            print "TriggerAll handle_trigger called",msg
            self.f1.write(str(msg))
            self.f1.write('\n')
        if(fd == self.fd[1]):
            print "TriggerAll handle_trigger function descriptor",fd
            print "TriggerAll handle_trigger called",msg
            self.f2.write(str(msg))
            self.f2.write('\n')

    def init(self):
        for flow_item in self.flows:
            parameters = {}
            fd = self.cntxt.apply_elem(self.app_d,flow_item,"TriggerAll",parameters,self) #sending the object 
            if((fd >0)):#=> we have sucess
                self.fd.append(fd)
                self.installed = True
                print "TriggerAll Installed with FD", fd



"""
# --
# This application creates two instances of the same function with different flows and dumps those flows in two diffrent files on the Function Box.
# --
"""
class LoggerUnitTest2():
    def __init__(self,inst,AD,file_names,flows): # These are user defined parameters.
        self.cntxt = inst
        self.app_d = AD
        self.installed = False # To check if the app is installed
        self.conf = 0 # Set this to 0 and increment for each call of configure_func
        self.flows = flows # Its a list.
        # Conf parameters
        self.file_names = file_names
        self.fd =[] # Its the list of function descriptors used by the application.
        self.num_functions = 2 # How many functions this one app instantiates.


    def configure_user_params(self):
        if (self.conf < self.num_functions): # Need to call configure_func twice since this application has two functions instantiated
            params = {"file_name":self.file_names[self.conf]}
            self.cntxt.configure_func(self.app_d,self.fd[self.conf],params)
            self.conf +=1


    def handle_trigger(self,fd,msg):
        print "Logger handle_trigger function descriptor",fd
        print "Logger handle_trigger called",msg

    def init(self):
        for index in range(0,self.num_functions): # If the flows are same then it will overwrite the flow to function descriptor
            # read this from policy file.
            parameters = {"file_name":self.file_names[index]}
            fd= self.cntxt.apply_elem(self.app_d,self.flows[index],"Logger",parameters,self) 
            if((fd >0)):#=> we have sucess
                self.fd.append(fd)
                self.installed = True
                print "Logger Installed."
            
class DnsDpiFunctionApp():
    def __init__(self,inst,AD,flows):
        self.cntxt = inst
        self.num_functions = 1
        self.app_d = AD
        self.fd = [] #List of functions used by this application.
        self.conf = 0
        self.installed = False
	self.DNS_BLOCK_TIMEOUT = 1000#0xffff
        #set the configuration variables here:
        self.visit_threshold = 3 
        self.flows = flows
        self.trigger_function_installed = False


    def init(self):
        for index in range(0,self.num_functions): # If the flows are same then it will overwrite the flow to function descriptor
            print "apply_elem"
            parameters = {}
            fd= self.cntxt.apply_elem(self.app_d,self.flows[index],"DNS_DPI",parameters,self) 
            if((fd >0)):#=> we have sucess
                self.fd.append(fd)
                self.installed = True
                print "DNS_DPI Function Installed."

    def configure_user_params(self):
        if (self.conf < self.num_functions): # Need to call configure_func twice since this application has two functions instantiated
            params = {}
            self.cntxt.configure_func(self.app_d,self.fd[self.conf],params) # Call connfigure_func with same app if and different function descriptors.
            self.conf +=1

    def handle_BadDomainEvent(self,fd,event):
        #src_ip = socket.inet_aton(event["src_ip"])
        src_ip = ipstr_to_int(event["src_ip"])
        bad_domain_name = event["bad_domain_name"]
        src_dpid = self.cntxt.route_compiler.mmap.get_dpid(src_ip)
        # DROP-FUNCTION
        flow = {}
        flow["dl_src"] = None; flow["dl_dst"] = None; flow['dl_vlan'] = None; flow['dl_vlan_pcp'] = None; flow['dl_type'] = None; flow['nw_src'] = src_ip; flow['nw_dst'] = None;flow['nw_proto'] = None ;flow['tp_src'] = None;flow['tp_dst'] = None
        parameters = {}
        if not self.trigger_function_installed:
            fd= self.cntxt.apply_elem(self.app_d,flow,"DROP",parameters,self) 
            if((fd >0)):#=> we have sucess
                self.fd.append(fd)
                self.trigger_function_installed = True
        #####################################################################
        # Use Below code to block the ip address
        #####################################################################
        #actions = []
        #print type(src_dpid)
        #print src_dpid
        #src_dpid = 5
        #self.cntxt.install_datapath_flow(src_dpid, { core.DL_TYPE : ethernet.IP_TYPE,core.NW_SRC : src_ip},
        #                       self.DNS_BLOCK_TIMEOUT,self.DNS_BLOCK_TIMEOUT, #
        #                       actions,buffer_id = None, priority=0xffff)

    def handle_trigger(self,fd,msg):
        if(msg["dns_dpi_type"] == "BadDomainEvent"):
            self.handle_BadDomainEvent(fd,msg)

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
	#src_ip = ipstr_to_int(s_ip)
        src_ip = s_ip
	for item in domain_ip_list:
            print type(src_dpid)
            print src_dpid
	    dst_ip = item
	    print src_ip,dst_ip
            msg = of.ofp_flow_mod()
            msg.priority = 42
            msg.match.dl_type = pkt.ethernet.IP_TYPE
            msg.match.nw_src = IPAddr(src_ip)
            msg.match.nw_dst = IPAddr(dst_ip)
            msg.idle_timeout = self.DNS_BLOCK_TIMEOUT 
            msg.hard_timeout = self.DNS_BLOCK_TIMEOUT
            # Not specifying action to drop the packets.
            #dst_port = of.OFPP_NONE
            #msg.actions.append(of.ofp_action_output(dst_port))
            connection = self.cntxt.get_connection(src_dpid)
            connection.send(msg)



############
# p0f
############
class P0fFunctionApp():
    def __init__(self,inst,AD,flows):
        self.cntxt = inst
        self.num_functions = 1
        self.app_d = AD
        self.fd = [] #List of functions used by this application.
        self.conf = 0
        self.installed = False
        self.flows = flows
        #App specific
        self.trigger_function_installed = False
        self.block_ports = defaultdict(list)
        self.block_ports["WindowsXP"]=[137,138,139]
        self.block_ports["FreeBSD"].append(40000)#rand()
        self.block_ports["Linux"].append(50000)#rand()


    def init(self):
        for index in range(0,self.num_functions): 
            print "apply_elem"
            parameters = {}
            fd= self.cntxt.apply_elem(self.app_d,self.flows[index],"p0f",parameters,self) 
            if((fd >0)):#=> we have sucess
                self.fd.append(fd)
                self.installed = True
                print "p0f Function Installed."

    def configure_user_params(self):
        if (self.conf < self.num_functions): 
            params = {}
            self.cntxt.configure_func(self.app_d,self.fd[self.conf],params) 
            self.conf +=1

    def handle_trigger(self,fd,msg):
        #print msg
        if(msg.has_key("p0f_trigger_type")):
            if(msg["p0f_trigger_type"] == "OSDetection"):
                self._handle_OSDetection(fd,msg)

    def _handle_OSDetection(self,fd,msg):
        if(msg.has_key("p0f_trigger_type")):
            if(msg["OS"] == "Linux"): #Don't have windows traffic. 
                src_ip = msg["src_ip"]
                if(self.block_ports.has_key("Linux")):
                    self._block_ports(src_ip,self.block_ports["Linux"])

    def _block_ports(self,s_ip,port_numbers):#port numbers is a list
        src_dpid = 5 # Hardcoded for testing the trigger module as self.mmap.update_ip_dpid_mapping() is not called with trigger module.  REMOVE it with live traffic.
	src_ip = s_ip
	## Make sure we get the full DNS packet at the Controller
	actions = []
        for port_number in port_numbers:
            # This is the API provided by OpenFlow switch.
            #PROBLEM: This rule is not installing the port number.
	    #self.cntxt.install_datapath_flow(src_dpid, 
	    #		{ core.DL_TYPE : ethernet.IP_TYPE,
	    #		    core.NW_DST : src_ip, #Block incoming netbios traffic.
	    #		   core.TP_DST: port_number },
            #                   120,120, #
            #                   actions,buffer_id = None, priority=0xffff)

            #PROBLEM: This rule is not installing the port number.
            msg = of.ofp_flow_mod()
            msg.priority = 42
            msg.match.dl_type = pkt.ethernet.IP_TYPE
            msg.match.nw_dst = IPAddr(src_ip)
            msg.match.tp_dst = port_number # Block all ports 1-by-1
            msg.idle_timeout = 120 
            msg.hard_timeout = 120
            # Not specifying action to drop the packets.
            connection = self.cntxt.get_connection(src_dpid)
            connection.send(msg)

    # how to drop packet.
    def drop (self,duration = None):
      if duration is not None:
        if not isinstance(duration, tuple):
          duration = (duration,duration)
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match.from_packet(packet)
        msg.buffer_id = event.ofp.buffer_id
        self.connection.send(msg)


############
# BloomFilter Function
############
class BloomFilterFunctionApp():
    def __init__(self,inst,AD,flows):
        self.cntxt = inst
        self.num_functions = 1
        self.app_d = AD
        self.fd = [] #List of functions used by this application.
        self.conf = 0
        self.installed = False
        self.flows = flows
        #App specific
        self.trigger_function_installed = False


    def init(self):
        for index in range(0,self.num_functions): 
            print "apply_elem"
            parameters = {}
            fd= self.cntxt.apply_elem(self.app_d,self.flows[index],"BF",parameters,self) #Bloom Filter
            print fd
            if((fd >0)):#=> we have sucess
                self.fd.append(fd)
                self.installed = True
                print "BF Function Installed."

    def configure_user_params(self):
        if (self.conf < self.num_functions): 
            params = {"bf_size":"1000","error_rate":"0.01"}
            self.cntxt.configure_func(self.app_d,self.fd[self.conf],params) 
            self.conf +=1

    def handle_trigger(self,fd,msg):
        #print msg
        if(msg.has_key("BF_trigger_type")):
            if(msg["BF_trigger_type"] == "VAL_DETECTED"):
                print "Bloom Filter Detected Value"

