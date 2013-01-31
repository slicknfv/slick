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
        # These are the pplication initializations.
        self.app_handles = []
        #self._run_unit_tests()
        #def _run_unit_tests(self):
        flow1 = {}
        flow1["dl_src"] = None; flow1["dl_dst"] = None; flow1['dl_vlan'] = None; flow1['dl_vlan_pcp'] = None; flow1['dl_type'] = None; flow1['nw_src'] = None; flow1['nw_dst'] = None;flow1['nw_proto'] = None ;flow1['tp_src'] = None;flow1['tp_dst'] = 53
        flow2 = {}
        flow2["dl_src"] = None;flow2["dl_dst"] = None;flow2['dl_vlan'] = None;flow2['dl_vlan_pcp'] = None;flow2['dl_type'] = None;flow2['nw_src'] = None;flow2['nw_dst'] = None;flow2['nw_proto'] = None ;flow2['tp_src'] = 53;flow2['tp_dst'] = None
        flow3 = {}
        flow3["dl_src"] = None;flow3["dl_dst"] = None;flow3['dl_vlan'] = None;flow3['dl_vlan_pcp'] = None;flow3['dl_type'] = None;flow3['nw_src'] = None;flow3['nw_dst'] = None;flow3['nw_proto'] = None ;flow3['tp_src'] = None;flow3['tp_dst'] = 80
        flow4 = {}
        flow4["dl_src"] = None;flow4["dl_dst"] = None;flow4['dl_vlan'] = None;flow4['dl_vlan_pcp'] = None;flow4['dl_type'] = None;flow4['nw_src'] = None;flow4['nw_dst'] = None;flow4['nw_proto'] = None ;flow4['tp_src'] = 80;flow4['tp_dst'] = None
        flow5 = {}
        flow5["dl_src"] = None; flow5["dl_dst"] = None; flow5['dl_vlan'] = None; flow5['dl_vlan_pcp'] = None; flow5['dl_type'] = None; flow5['nw_src'] = None; flow5['nw_dst'] = None;flow5['nw_proto'] = None ;flow5['tp_src'] = 53;flow5['tp_dst'] = 53
        flow6 = {}
        flow6["dl_src"] = None; flow6["dl_dst"] = None; flow6['dl_vlan'] = None; flow6['dl_vlan_pcp'] = None; flow6['dl_type'] = None; flow6['nw_src'] = None; flow6['nw_dst'] = None;flow6['nw_proto'] = None ;flow6['tp_src'] = None;flow6['tp_dst'] = 40000
        flow7 = {}
        flow7["dl_src"] = None;flow7["dl_dst"] = None;flow7['dl_vlan'] = None;flow7['dl_vlan_pcp'] = None;flow7['dl_type'] = None;flow7['nw_src'] = None;flow7['nw_dst'] = None;flow7['nw_proto'] = 6 ;flow7['tp_src'] = None;flow7['tp_dst'] = None
        #self.dns_handlers = DNSHandlers(self.cntxt)
        dns_flows=[]
        dns_flows.append(flow1)
        self.dns_handlers = DnsDpiFunctionApp(self.cntxt,50,dns_flows)
        #########
        #p0f code
        #########
        p0f_flows = []
        p0f_flows.append(flow7) # All port80 traffic.[We need tcp only but lets only do http for now.
        self.p0f_handlers = P0fFunctionApp(self.cntxt,51,p0f_flows)

        self.logger_unit1 = LoggerUnitTest(self.cntxt,100,"/tmp/dns_log",100,flow6) # AD,file_name,threshold,user parameters
        self.logger_unit2 = LoggerUnitTest(self.cntxt,101,"/tmp/http_log",1000,flow3)

        self.trigger_all_test = TriggerAllUnitTest(self.cntxt)

        file_names = ["/tmp/dns_dst.txt","/tmp/dns_src.txt"]
        flows = []
        flows.append(flow1);flows.append(flow2);
        #print flows
        self.logger2_obj1 = LoggerUnitTest2(self.cntxt,1001,file_names,flows)
        file_names = ["/tmp/http_dst.txt","/tmp/http_src.txt"]
        flows1 = []
        flows1.append(flow3);flows1.append(flow4);
        #print flows1
        self.logger2_obj2 = LoggerUnitTest2(self.cntxt,1002,file_names,flows1)

        #self.app_handles.append(self.dns_handlers)
        self.app_handles.append(self.p0f_handlers)
        #self.app_handles.append(self.logger_unit1)
        #self.app_handles.append(self.logger_unit2)
        #self.app_handles.append(self.trigger_all_test)
        #self.app_handles.append(self.logger2_obj1)
        #self.app_handles.append(self.logger2_obj2)

    # --
    # Function processes the JSON messages and returns a reply.
    # @args;
    #   msg = dict
    # --
    def process_msg(self,pyevent,msg):
        reply = {}
        #print self.cntxt
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
                print "MAAAAAAAAAAAAAAAAAAAAAAAC",machine_ip,machine_mac
                self.json_msg_events[machine_ip] = pyevent # To keep the connection open
                #self.send_msg(machine_ip,msg)
                self.cntxt.route_compiler.fmap.update_function_machine(machine_ip,machine_mac,None) # Simply add the record of the shim.
                print self.cntxt.route_compiler.mmap.ip_dpid
                print self.cntxt.route_compiler.mmap.ip_port
                self.cntxt.route_compiler.fmap.fd_machine_map[machine_ip] = machine_mac # Simply add the record of the shim.
                reply["dummy"]="connected"
                return reply
            # if type is trigger call raise trigger.
            if(msg["type"] == "BadDomainEvent"):
                self.dns_handlers.handle_trigger(msg)
            if(msg["type"] == "trigger"):
                fd = msg["fd"]
                if(type(fd) == int):
                    application_handle = self.cntxt.route_compiler.get_application_handle(fd)
                    application_handle.handle_trigger(fd,msg)
                reply["dummy"]="connected"
                return reply


    # Return True for sucess False for failure
    def send_install_msg(self,fd,flow,function_name,params,msg_dst):
        print "I"*100 
        if((type(fd) == int) and isinstance(params, dict)):
            msg = {"type":"install", "fd":fd, "flow":flow,"function_name":function_name,"params":params}
            return self.send_msg(msg_dst,msg)

    def send_configure_msg(self,fd,params_dict,msg_dst):
        #print type(fd),fd,type(params_dict),params_dict
        if((type(fd) == int) and isinstance(params_dict, dict)):
            print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
            msg = {"type":"configure", "fd":fd,"params":params_dict}
            print msg
            print self.send_msg(msg_dst,msg)
            #print "Unable to send the message"
                

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
            pyevent.reply(json.dumps(msg)+'\n')
            return True
        else:
            return False
"""
    Trigger handling code.
"""
import os
import sys
class Triggers():

    def handle_trigger(self,event):
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
            print "CONFIGURE_CALLEDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
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
        fd= self.cntxt.apply_func(self.app_d,self.flow,"Logger",parameters,self) 
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
            print "CONFIGURE_CALLEDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
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
            fd = self.cntxt.apply_func(self.app_d,flow_item,"TriggerAll",parameters,self) #sending the object 
            if((fd >0)):#=> we have sucess
                #self.func_descs.append(fd)
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
        #Configuration specified parameters
        self.flows = flows # Its a list.
        # Conf parameters
        self.file_names = file_names
        #self.count_thresh = count_thresh
        self.fd =[] # Its the list of function descriptors used by the application.
        self.num_functions = 2 # How many functions this one app instantiates.


    def configure_user_params(self):
        if (self.conf < self.num_functions): # Need to call configure_func twice since this application has two functions instantiated
            print "CONFIGURE_CALLEDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
            params = {"file_name":self.file_names[self.conf]}
            self.cntxt.configure_func(self.app_d,self.fd[self.conf],params)
            self.conf +=1


    def handle_trigger(self,fd,msg):
        print "Logger handle_trigger function descriptor",fd
        print "Logger handle_trigger called",msg

    def init(self):
        for index in range(0,self.num_functions): # If the flows are same then it will overwrite the flow to function descriptor
            # read this from policy file.
            #file_name = self.file_name
            parameters = {"file_name":self.file_names[index]}
            #print self.flows[index],parameters
            fd= self.cntxt.apply_func(self.app_d,self.flows[index],"Logger",parameters,self) 
            #print fd
            if((fd >0)):#=> we have sucess
                self.fd.append(fd)
                self.installed = True
                print "Logger Installed."
            
from nox.lib.core     import *
from nox.lib.packet.ethernet     import ethernet
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
            print "APPLY_FUNC"
            # read this from policy file.
            #file_name = self.file_name
            parameters = {}
            #print self.flows[index],parameters
            fd= self.cntxt.apply_func(self.app_d,self.flows[index],"DNS-DPI",parameters,self) 
            if((fd >0)):#=> we have sucess
                self.fd.append(fd)
                self.installed = True
                print "DNS_DPI Function Installed."

    def configure_user_params(self):
        if (self.conf < self.num_functions): # Need to call configure_func twice since this application has two functions instantiated
            print "CONFIGURE_CALLEDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
            params = {}
            self.cntxt.configure_func(self.app_d,self.fd[self.conf],params) # Call connfigure_func with same app if and different function descriptors.
            self.conf +=1

    def handle_BadDomainEvent(self,fd,event):
        #src_ip = socket.inet_aton(event["src_ip"])
        src_ip = ipstr_to_int(event["src_ip"])
        bad_domain_name = event["bad_domain_name"]
        src_dpid = self.cntxt.route_compiler.mmap.get_dpid(src_ip)# Bilal idiot.
        print "HANDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDLING"
        #if(app_conf == block):
        #self._block_ip_list(src_dpid,src_ip,domain_ip_list)
        #if(app_conf == log)
        # new_flow[src_ip] = src_ip
        # DROP-FUNCTION
        flow = {}
        flow["dl_src"] = None; flow["dl_dst"] = None; flow['dl_vlan'] = None; flow['dl_vlan_pcp'] = None; flow['dl_type'] = None; flow['nw_src'] = src_ip; flow['nw_dst'] = None;flow['nw_proto'] = None ;flow['tp_src'] = None;flow['tp_dst'] = None
        parameters = {}
        if not self.trigger_function_installed:
            fd= self.cntxt.apply_func(self.app_d,flow,"DROP",parameters,self) 
            if((fd >0)):#=> we have sucess
                self.fd.append(fd)
                self.trigger_function_installed = True
        #####################################################################
        # Use Below code to block the ip address
        #####################################################################
        #print "BLOCKING THE IP ADDRESS", src_ip, "OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO"
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
            print "APPLY_FUNC"
            parameters = {}
            fd= self.cntxt.apply_func(self.app_d,self.flows[index],"p0f",parameters,self) 
            if((fd >0)):#=> we have sucess
                self.fd.append(fd)
                self.installed = True
                print "p0f Function Installed."

    def configure_user_params(self):
        if (self.conf < self.num_functions): 
            print "CONFIGURE_CALLEDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
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
            #if(msg["OS"] == "WindowsXP"): #This OS string matching should be done according to function which is p0f in this case.
            if(msg["OS"] == "Linux"): #Don't have windows traffic. 
                src_ip = msg["src_ip"]
                if(self.block_ports.has_key("Linux")):
                    self._block_ports(src_ip,self.block_ports["Linux"])

    def _block_ports(self,s_ip,port_numbers):#port numbers is a list
        src_dpid = 5 # Hardcoded for testing the trigger module as self.mmap.update_ip_dpid_mapping() is not called with trigger module.  REMOVE it with live traffic.
	src_ip = ipstr_to_int(s_ip)
        #print type(src_dpid)
        #print src_dpid
	## Make sure we get the full DNS packet at the Controller
	actions = []
        for port_number in port_numbers:
            # This is the API provided by OpenFlow switch.
            #PROBLEM: This rule is not installing the port number.
	    self.cntxt.install_datapath_flow(src_dpid, 
	    		{ core.DL_TYPE : ethernet.IP_TYPE,
	    		    core.NW_DST : src_ip, #Block incoming netbios traffic.
	    		   core.TP_DST: port_number },
                               120,120, #
                               actions,buffer_id = None, priority=0xffff)
