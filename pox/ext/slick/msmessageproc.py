import jsonpickle
import json
from collections import defaultdict
import socket

from pox.core import core as core
from pox.lib.revent import *
log = core.getLogger()


class ElementMachineUp(Event):
    def __init__(self, machine_mac, machine_ip):
        """Event raised when a middlebox machine
        goes live in the network."""
        Event.__init__(self)
        self.mac = machine_mac
        self.ip = machine_ip

class ElementMachineDown(Event):
    def __init__(self, machine_mac, machine_ip):
        """Event raised when a middlebox machine
        goes down in the network."""
        Event.__init__(self)
        self.mac = machine_mac
        self.ip = machine_ip

class ElementInstanceEvent(Event):
    def __init__(self, machine_mac, machine_ip, element_descriptor, element_name,
                 created = False, destroyed = False, moved = False):
        """Event raised when an element instance
        is created, destroyed or moved in the network."""
        Event.__init__(self)
        self.mac = machine_mac
        self.ip = machine_ip
        self.ed = element_descriptor
        self.element_name = element_name
        self.created = created
        self.removed = destroyed
        self.moved = moved

#Priorities: ShowStopper, High,Med.Low.
class MSMessageProcessor(EventMixin):
    def __init__(self,context):
        self.cntxt = context
        # TCP Connection handlers
        self.tcp_conn_handlers = {}
        # These are the application initializations.
        self.app_handles = [ ]

    # Raise these events.
    _eventMixin_events = set([
        ElementMachineUp,
        ElementMachineDown,
        ElementInstanceEvent,
    ])

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
                # dml
                #self.cntxt.fmap.update_element_machine(machine_ip,machine_mac,None) # Simply add the record of the shim.
                self.cntxt.register_machine(machine_ip, machine_mac)
                log.debug("Registering element machine: " + str(machine_mac))
                print "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
                print self.cntxt.elem_to_mac._mac_to_elems
                # Raising the event
                self.raiseEvent(ElementMachineUp, machine_mac, machine_ip)
                reply["dummy"]="connected"
                return reply
            # if type is trigger call raise trigger.
            if(msg["type"] == "BadDomainEvent"):
                self.dns_handlers.handle_trigger(msg)
            if(msg["type"] == "trigger"):
                elem_desc = msg["ed"]
                if(type(elem_desc) == int):
                    application_handle = self.cntxt.elem_to_app.get_app_handle(elem_desc)
                    application_handle.handle_trigger(elem_desc,msg)
                reply["dummy"]="connected"
                return reply

    ### Messages for Controller -> Element

    # Return True for sucess False for failure
    def send_install_msg(self,fd,flow,function_name,params,msg_dst):
        """Send the install message and generate the required 
        ElementInstance created events."""
        if((type(fd) == int) and isinstance(params, dict)):
            # we are sending the lists now.
            msg = {"type":"install", "fd": [fd], "flow":flow, "function_name": [function_name],"params": [params]}
            if self.send_msg(msg_dst,msg):
                for ed in [fd]:
                    # Raise event for each element instance created.
                    # TODO: Do this once the SUCCESS is returned from shim.
                    machine_ip = self.cntxt.mac_to_ip.get(msg_dst)
                    self.raiseEvent(ElementInstanceEvent, msg_dst, machine_ip, ed, function_name, created=True)
                return True
            else:
                return False

    # msg_dst == Middlebox MAC address
    def send_configure_msg(self,fd,params_dict,msg_dst):
        if((type(fd) == int) and isinstance(params_dict, dict)):
            msg = {"type":"configure", "fd":fd,"params":params_dict}
            self.send_msg(msg_dst,msg)

    def send_remove_msg(self,fd,params_dict,msg_dst):
        if((type(fd) == int) and isinstance(params_dict, dict)):
            msg = {"type":"remove", "fd":fd,"params":params_dict}
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
