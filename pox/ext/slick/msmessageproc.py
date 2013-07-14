import jsonpickle
import json
from collections import defaultdict
import socket

from pox.core import core as core

from applications import *

#Priorities: ShowStopper, High,Med.Low.
class MSMessageProcessor():
    def __init__(self,context):
        self.cntxt = context
        # TCP Connection handlers
        self.tcp_conn_handlers = {}
        # These are the pplication initializations.
        self.app_handles = []
        self._initialize()

    def _initialize(self):
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
        flow6["dl_src"] = None; flow6["dl_dst"] = None; flow6['dl_vlan'] = None; flow6['dl_vlan_pcp'] = None; flow6['dl_type'] = None; flow6['nw_src'] = None; flow6['nw_dst'] = None;flow6['nw_proto'] = None ;flow6['tp_src'] = None;flow6['tp_dst'] = 53
        flow7 = {}
        flow7["dl_src"] = None;flow7["dl_dst"] = None;flow7['dl_vlan'] = None;flow7['dl_vlan_pcp'] = None;flow7['dl_type'] = None;flow7['nw_src'] = None;flow7['nw_dst'] = None;flow7['nw_proto'] = None ;flow7['tp_src'] = None;flow7['tp_dst'] = 80
        # To be used for filter app.
        flow8 = {}
        flow8["dl_src"] = None;flow8["dl_dst"] = None;flow8['dl_vlan'] = None;flow8['dl_vlan_pcp'] = None;flow8['dl_type'] = None;flow8['nw_src'] = None;flow8['nw_dst'] = None;flow8['nw_proto'] = None ;flow8['tp_src'] = None;flow8['tp_dst'] = 80
        #flow9 = {}
        #flow9["dl_src"] = None;flow9["dl_dst"] = None;flow9['dl_vlan'] = None;flow9['dl_vlan_pcp'] = None;flow9['dl_type'] = None;flow9['nw_src'] = "10.0.0.4";flow9['nw_dst'] = None;flow9['nw_proto'] = None ;flow9['tp_src'] = None;flow9['tp_dst'] = None
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
        #########
        #BloomFilterFunctionApp code
        #########
        bf_flows = []
        bf_flows.append(flow8) # All port80 traffic.[We need tcp only but lets only do http for now.
        self.bf_handlers = BloomFilterFunctionApp(self.cntxt,52,bf_flows)

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
        #self.app_handles.append(self.p0f_handlers)
        self.app_handles.append(self.logger_unit1)
        #self.app_handles.append(self.logger_unit2)
        #self.app_handles.append(self.trigger_all_test)
        #self.app_handles.append(self.logger2_obj1)
        #self.app_handles.append(self.logger2_obj2)
        #self.app_handles.append(self.bf_handlers)

    # --
    # Function processes the JSON messages and returns a reply.
    # @args;
    #   msg = dict
    # --
    def process_msg(self,msg,socket_name):
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
                machine_ip = msg["machine_ip"]
                machine_mac = msg["machine_mac"]
                self.tcp_conn_handlers[machine_mac] = socket_name
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
        if((type(fd) == int) and isinstance(params, dict)):
            msg = {"type":"install", "fd":fd, "flow":flow,"function_name":function_name,"params":params}
            return self.send_msg(msg_dst,msg)

    # msg_dst == Middlebox MAC address
    def send_configure_msg(self,fd,params_dict,msg_dst):
        if((type(fd) == int) and isinstance(params_dict, dict)):
            msg = {"type":"configure", "fd":fd,"params":params_dict}
            print msg
            self.send_msg(msg_dst,msg)
                
    def send_remove_msg(self,fd,params_dict,msg_dst):
        if((type(fd) == int) and isinstance(params_dict, dict)):
            msg = {"type":"remove", "fd":fd,"params":params_dict}
            print msg
            return self.send_msg(msg_dst,msg)

    """
        Function to send messages to Middlebox through jsonmessenger.
        @args:
            mb_ip: Where the rule should be installed.
            reply: a dictionary that should be sent as json messge
    """
    #def send_msg(self,mb_ip,msg):
    #    if (len(self.json_msg_events) >= 1):
    #        pyevent = self.json_msg_events[mb_ip]
    #        pyevent.reply(json.dumps(msg)+'\n')
    #        return True
    #    else:
    #        return False
        
    # Use Middlebox MAC address instead of the IP address.
    # and the message for sending the information.
    def send_msg(self,mb_mac,msg):
        if (len(self.tcp_conn_handlers) >= 1):
            socket_name = self.tcp_conn_handlers[mb_mac]
            msg = json.dumps(msg)+'\n'
            core.TCPTransport.send_mb_msg(socket_name,msg)
            return True
        else:
            return False

    # socket_name is a string
    def update_connection(self,socket_name):
        pass
