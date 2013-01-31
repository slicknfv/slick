import os,sys
import getopt
import rpyc

from collections import defaultdict
from shim_table import ShimTable

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,parentdir) 
from logger.logger_func import Logger
from trigger_all.trigger_all import TriggerAll
from dns_dpi_func.dns_dpi_function import DnsDpiFunction
from p0f.p0ftriggers import P0F
from drop.drop import Drop
from bloomfilter.bloomfilter import BloomFilter

"""
    These are the functions supported by the Shim  to the controller.
"""
class ClientService(rpyc.Service):
    def __init__(self,shim):
        #self.flow_to_fd_map = defaultdict(int)
        self.fd_to_object_map = {}
        self.shim_table = ShimTable()
        # Need this handle for application to call trigger.
        self.shim = shim

    def on_connect(self):
        # code that runs when a connection is created
        # (to init the serivce, if needed)
        print "Connection from controller..."

    def on_disconnect(self):
        # code that runs when the connection has already closed
        # (to finalize the service, if needed)
        print "Disconnection from controller..."

    """
        Initialize the code.
        params is used to provide boot time paramter for the function installation.
    """
    def exposed_install_function(self,msg):
        fd = int(msg["fd"])
        flow = msg["flow"]
        function_name = str(msg["function_name"])
        params_dict = msg["params"]
        #self.flow_to_fd_map[flow] = fd
        function_handle = None
        if(function_name == "Logger"):
            function_handle = Logger(self.shim)#start the function but pass the shim reference to invoke trigger.
            function_handle.init(fd,params_dict)# init invoked on the application.
        if(function_name == "TriggerAll"):
            function_handle = TriggerAll(self.shim)#start the function
            function_handle.init(fd,params_dict)# init invoked on the application.
        if(function_name == "DNS-DPI"):
            print "DNS-DPI Installed"
            function_handle = DnsDpiFunction(self.shim)#start the function
            function_handle.init(fd,params_dict)# init invoked on the application.
        if(function_name == "DROP"):
            function_handle = Drop(self.shim)#start the function
            function_handle.init(fd,params_dict)# init invoked on the application.
        if(function_name == "p0f"):
            function_handle = P0F(self.shim)
            function_handle.init(fd,params_dict)
        if(function_name == "BF"):
            function_handle = BloomFilter(self.shim)
            function_handle.init(fd,params_dict)

        try:
            if(isinstance(flow['nw_src'],unicode)): #BAD HACK
                flow['nw_src'] = flow['nw_src'].encode('ascii','replace')
                #flow['nw_src'] = socket.inet_aton(flow['nw_src'])
                print flow['nw_src']
                print type(flow['nw_src'])
            self.shim_table.add_flow(0,flow,fd) #Update flow to fd mapping.
            self.fd_to_object_map[fd] =function_handle
            print "Function Handle added for fd",fd,function_handle
        except Exception:
            print "WARNING: Unable to create handle for the function", function_name ,"with function descriptor", fd
            del self.fd_to_object_map[fd]
            del self.flow_to_fd_map[flow]
            return False
        return True


    # Utilituy function used by install function to get the function code downloaded from the controller in case its not present.
    # def __get_function_code(self,function_name):

    """
        Enable event
    """
    def exposed_configure_function(self,msg):
        fd = int(msg["fd"])
        params = msg["params"]
        # Call the respective configure function.
        print "Calling the configure funtion for function:",fd
        if(self.fd_to_object_map.has_key(fd)):
            self.fd_to_object_map[fd].configure(params)
            return True
        else:
            return False


    """
     Stop the pid.
        Kill the process
        Remove executables
        Remove Logic
    """
    def exposed_stop_function(self,msg):
        fd = int(msg["fd"])
        if(self.fd_to_object_map[fd].shutdown()):
            # We need process killing wrappers or garbage collectors.
            # A process sets up particular resources.
            del self.fd_to_object_map[fd]
            return True


    def raise_trigger(self,trigger_message):
        #self.shim.client.send_msg(trigger_message)
        trigger_message["type"]= "trigger" #Adding flag for the controller to identify the trigger message
        self.shim.client.send_data_basic(trigger_message)

    def fwd_pkt(self,packet):
        #print "Forwarding Packet............."
        self.shim.forward_data_sock.send(packet)

    # --
    # get_function_handle_from_flow
    # Return the object for the flow
    # --
    def get_function_handle_from_flow(self,flow):
        #fd = self.flow_to_fd_map[flow]
        fd = self.shim_table.lookup_flow(flow) #Update flow to fd mapping.
        if(fd != None):
            pass
            #print flow
            #print fd #fd == None means no match.
            #print flow
        if(fd !=None):
            if not (self.fd_to_object_map.has_key(fd)):
                return None
            else:
                return self.fd_to_object_map[fd]
"""
    NON-API
"""
#class ControllerClient()
#    def __init__(self):
#        self.mbserver_ip = constants.MB_CONTROLLER_IP 
#        self.mbserver_port = constants.MB_CONTROLLER_PORT
#        self.conn = None
#
#    def connect_server(self):
#        try:
#            self.conn = rpyc.connect(self.mbserver_ip,self.mbserver_port)
#        except Exception:
#            print "Unable to connect"
#            self.conn = None
#
#    """
#        Not the API but are used to communicate with controller
#    """
#    def sent_event(self,event):
#        pass


# This is the main file to be used for DNS Sensor
def usage():
    pass


def start_rpyc(port):
    from rpyc.utils.server import ThreadedServer
    t = ThreadedServer(ClientService, port = 18861)
    #t = ThreadedServer(ClientService, port)
    t.start()

"""Module docstring.
"""
def main(argv):
    DEFAULT_PORT = 18861
    #Parse options and arguments
    port = None
    mode =None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hsp:m:", ["help","start","port","mode="])
    except getopt.GetoptError, err:
        print "Option error!"
        print str(err)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h","--help"):
            usage()
            sys.exit()
        elif opt in ("-s","--start"):
            start_rpyc(port)
        elif opt in ("-p","--port"):
            port = arg
            print "Connecting on the port:",port
        elif opt in ("-m","--mode"):
            mode = str(arg)
            print "starting shim in the mode: ",mode
    if(not port):
        print "Setting default values."
        port = DEFAULT_PORT 
    start_rpyc(port)

if __name__ == "__main__":
    main(sys.argv[1:])

