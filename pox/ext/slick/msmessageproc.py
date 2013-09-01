import jsonpickle
import json
from collections import defaultdict
import socket

from pox.core import core as core

#Priorities: ShowStopper, High,Med.Low.
class MSMessageProcessor():
    def __init__(self,context):
        self.cntxt = context
        # TCP Connection handlers
        self.tcp_conn_handlers = {}
        # These are the pplication initializations.
        self.app_handles = []


    # --
    # Function adds an application to its app_handles for subsequent processing
    #       TODO make a remove_application when we want to handle multiple apps
    # @args:
    #   app = application
    # --
    def add_application(self,app):
        self.app_handles.append(app)

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
                self.cntxt.fmap.update_element_machine(machine_ip,machine_mac,None) # Simply add the record of the shim.
                self.cntxt.fmap.fd_machine_map[machine_ip] = machine_mac # Simply add the record of the shim.
                reply["dummy"]="connected"
                return reply
            # if type is trigger call raise trigger.
            if(msg["type"] == "BadDomainEvent"):
                self.dns_handlers.handle_trigger(msg)
            if(msg["type"] == "trigger"):
                fd = msg["ed"]
                if(type(fd) == int):
                    application_handle = self.cntxt.route_compiler.get_application_handle(fd)
                    application_handle.handle_trigger(fd,msg)
                reply["dummy"]="connected"
                return reply

    ### Messages for Controller -> Element

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
