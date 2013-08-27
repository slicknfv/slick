import os,sys
import getopt
import rpyc

from collections import defaultdict
from shim_table import ShimTable

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir+"/pox/ext/slick/elements") 
from Logger.Logger import Logger
from TriggerAll.TriggerAll import TriggerAll
from DnsDpi.DnsDpi import DnsDpi
from P0f.P0f import P0f
from Drop.Drop import Drop
from Noop.Noop import Noop
from BloomFilter.BloomFilter import BloomFilter

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
        fd = int(msg["fd"])
        flow = msg["flow"]
        function_name = str(msg["function_name"])
        params_dict = msg["params"]
        function_handle = None
        if(function_name == "Logger"):
            function_handle = Logger(self.shim, fd)#start the function but pass the shim reference to invoke trigger.
            function_handle.init(params_dict)# init invoked on the application.
        if(function_name == "TriggerAll"):
            function_handle = TriggerAll(self.shim, fd)#start the function
            function_handle.init(params_dict)# init invoked on the application.
        if(function_name == "DnsDpi"):
            function_handle = DnsDpi(self.shim, fd)#start the function
            function_handle.init(params_dict)# init invoked on the application.
        if(function_name == "Drop"):
            function_handle = Drop(self.shim, fd)#start the function
            function_handle.init(params_dict)# init invoked on the application.
        if(function_name == "P0f"):
            function_handle = P0f(self.shim, fd)
            function_handle.init(params_dict)
        if(function_name == "BloomFilter"):
            function_handle = BloomFilter(self.shim, fd)
            function_handle.init(params_dict)
        if(function_name == "Noop"):
            function_handle = Noop(self.shim, fd)#start the function
            function_handle.init(params_dict)# init invoked on the application.
        try:
            if(isinstance(flow['nw_src'], unicode)): #BAD HACK
                flow['nw_src'] = flow['nw_src'].encode('ascii', 'replace')
            self.shim_table.add_flow(0, flow, fd) #Update flow to fd mapping.
            self.fd_to_object_map[fd] =function_handle
            if params_dict.has_key("bidirectional"):
                reverse_flow = self.shim.get_reverse_flow(flow)
                self.shim_table.add_flow(0, reverse_flow, fd)
        except Exception:
            print "WARNING: Unable to create handle for the function", function_name ,"with function descriptor", fd
            del self.fd_to_object_map[fd]
            del self.flow_to_fd_map[flow]
            return False
        return True

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

    def get_function_handle_from_flow(self, flow):
        """Return the object for the flow.
        """
        fd = self.shim_table.lookup_flow(flow) #Update flow to fd mapping.
        if(fd !=None):
            if not (self.fd_to_object_map.has_key(fd)):
                return None
            else:
                return self.fd_to_object_map[fd]


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

