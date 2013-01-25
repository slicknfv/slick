import os,sys
import getopt
import rpyc

from collections import defaultdict

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,parentdir) 
from logger.logger_func import Logger
#from dns_handler import DHSHandler

"""
    These are the functions supported by the Client  and are used to talk with controller.
"""
class ClientService(rpyc.Service):
    def __init__(self):
        self.flow_to_fd_map = defaultdict(int)
        self.fuction_code_map = {} # dictionrry which keeps track what code is downloaded on the machine hard disk and what is not present.
        self.fd_to_object_map = {}

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
    def exposed_install_function(self,flow,fd,function_name,*params):
        # assuming the  code base is present on the machine.
        #find the code and run the program.
        self.flow_to_fd_map[flow] = fd
        function_handle = None
        if(function_name == "Logger"):
            function_handle = Logger(fd)
        if(function_name == "DNS-DPI"):
            #function_handle = DNSWrapper(fd,*params)
            pass
        if(function_name == "p0f"):
            #function_handle = P0fWrapper(fd,*params)  
            pass

        try:
            self.fd_to_object_map[fd] =function_handle
        except Exception:
            print "WARNING: Unable to create handle for the function", function_name ,"with function descriptor", fd
            del self.fd_to_object_map[fd]
            del self.flow_to_fd_map[flow]


    # Utilituy function used by install function to get the function code downloaded from the controller in case its not present.
    # def __get_function_code(self,function_name):

    """
        Enable event
    """
    def exposed_configure(self,fd,*params):
        # Call the respective configure function.
        self.fd_to_object_map[fd].configure(*params)


    """
     Stop the pid.
        Kill the process
        Remove executables
        Remove Logic
    """
    def exposed_stop_function(self,fd):
        # We need process killing wrappers or garbage collectors.
        # A process sets up particular resources.
        pass



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

