import os,sys
import getopt
import rpyc
import time

from collections import defaultdict
from shim_table import ShimTable

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
elements_path = parentdir +"/pox/ext/slick/elements" 
sys.path.insert(0, elements_path)

from Logger.Logger import Logger
from Logger1.Logger1 import Logger1
from TriggerAll.TriggerAll import TriggerAll
from DnsDpi.DnsDpi import DnsDpi
from P0f.P0f import P0f
from Drop.Drop import Drop
from Noop.Noop import Noop
from BloomFilter.BloomFilter import BloomFilter
from DelayBuffer.DelayBuffer import DelayBuffer
from Constant.Constant import Constant
from Compress.Compress import Compress
# Dummy
from Encrypt.Encrypt import Encrypt
from StatefulFirewall.StatefulFirewall import StatefulFirewall
from IDS.IDS import IDS
from LoadBalancer.LoadBalancer import LoadBalancer


"""
    These are the functions supported by the Shim  to the controller.
"""
class ClientService(rpyc.Service):
    def __init__(self, shim):
        self.fd_to_object_map = {}
        self.shim_table = ShimTable()
        # Need this handle for application to call trigger.
        self.shim = shim

    def on_connect(self):
        """code that runs when a connection is created
            (to init the serivce, if needed)
        """
        print "Connection from controller..."

    def on_disconnect(self):
        """Code that runs when the connection has already closed
            (to finalize the service, if needed)
        """
        print "Disconnection from controller..."

    def exposed_install_function(self, msg):
        """Function that calls the elements' init functions.

        Args:
            msg: Key:Value pairs from the Slick Controller.
        Returns:
            True/False
        """
        fds = msg["fd"]
        flow = msg["flow"]
        function_names = msg["function_name"]
        params_dicts = msg["params"]
        for i in range(0, len(fds)):
            fd = fds[i]
            function_name = function_names[i]
            params_dict = params_dicts[i]
            function_handle = None

            # from Logger.Logger import Logger
            package_name = function_name +'.'+function_name
            class_name = function_name
            elem_class = sys.modules[package_name].__dict__[class_name]
            elem_instance = elem_class( self.shim, fd )
            elem_instance.init(params_dict)
            try:
                if(isinstance(flow['nw_src'], unicode)): #BAD HACK
                    flow['nw_src'] = flow['nw_src'].encode('ascii', 'replace')
                self.shim_table.add_flow(0, flow, fd) #Update flow to fd mapping.
                # This is just for reference.
                self.fd_to_object_map[fd] = elem_instance
                reverse_flow = self.shim.get_reverse_flow(flow)
                self.shim_table.add_flow(0, reverse_flow, fd)
            except Exception:
                print "WARNING: Unable to create handle for the function", function_name ,"with function descriptor", fd
                self._cleanup_failed_install(fds, flow)
                return False
        return True

    def _cleanup_failed_install(self, eds, flow):
        for ed in eds:
            del self.fd_to_object_map[ed]
        del self.flow_to_fd_map[flow]

    def exposed_configure_function(self, msg):
        """Calls element's configure function based on element descriptor.

        Args:
            msg: Key:Value pairs from the Slick Controller.
        Returns:
            True/False
        """
        fd = int(msg["fd"])
        params = msg["params"]
        # Call the respective configure function.
        if(self.fd_to_object_map.has_key(fd)):
            self.fd_to_object_map[fd].configure(params)
            return True
        else:
            return False

    def exposed_stop_function(self, msg):
        """Stop the pid. Kill the process. Remove executables. Remove Logic
        """
        fd = int(msg["fd"])
        if(self.fd_to_object_map[fd].shutdown()):
            # We need process killing wrappers or garbage collectors.
            # A process sets up particular resources.
            del self.fd_to_object_map[fd]
            return True

    def raise_trigger(self, trigger_message):
        trigger_message["type"]= "trigger" #Adding flag for the controller to identify the trigger message
        self.shim.client.send_data_basic(trigger_message)

    def fwd_pkt(self, packet):
        self.shim.forward_data_sock.send(packet)

    def get_function_handles_from_flow(self, flow):
        """Return the objects for the flow.
        """
        element_handles = [ ]
        fds = self.shim_table.lookup_flow(flow) #Update flow to fd mapping.
        if fds: # A flow is not installed yet
            for fd in fds:
                if(fd != None):
                    if not (self.fd_to_object_map.has_key(fd)):
                        # If not a single handle is found for an element descriptor
                        # invalidate the service chain.
                        return None
                    else:
                        element_handles.append(self.fd_to_object_map[fd])
            return element_handles

class ShimResources(object):
    """Place it as an element in front of the chain."""
    def __init__(self, shim):
        self.shim = shim
        self.cpu_percentage = 0
        self.mem_percentage = 0
        self.trigger_time = 0
        self.max_flows = 1
        self.trigger_interval = 500 # seconds

    def calc_triggers(self, flow):
        active_flows = self.shim.get_active_flows()
        trigger_msg = { }
        if active_flows >= self.max_flows:
            cur_time = time.time()
            if (cur_time - self.trigger_time) > self.trigger_interval:
                trigger_msg = {"ed" : 0, "mac" : self.shim.mac, "max_flows" : True}
                self.shim.client_service.raise_trigger(trigger_msg)
                self.trigger_time = time.time()

def usage():
    pass

def start_rpyc(port):
    from rpyc.utils.server import ThreadedServer
    t = ThreadedServer(ClientService, port = 18861)
    t.start()

def main(argv):
    DEFAULT_PORT = 18861
    #Parse options and arguments
    port = None
    mode =None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hsp:m:", ["help", "start", "port", "mode="])
    except getopt.GetoptError, err:
        print "Option error!"
        print str(err)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-s", "--start"):
            start_rpyc(port)
        elif opt in ("-p", "--port"):
            port = arg
            print "Connecting on the port:", port
        elif opt in ("-m", "--mode"):
            mode = str(arg)
            print "starting shim in the mode: ", mode
    if(not port):
        print "Setting default values."
        port = DEFAULT_PORT 
    start_rpyc(port)

if __name__ == "__main__":
    main(sys.argv[1:])

