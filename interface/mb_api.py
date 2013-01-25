import os,sys
import getopt
import rpyc

from dns_sensor import DNSSensor

"""
    These are the functions supported by the Client  and are used to talk with controller.
"""
class ClientService():
    def __init__(self):
        pass

    """
        Removing this as controller already has this information.
        Returns events to controller supported by the DPI box.
    def get_supported_events():
        pass
    """


    """
        Initialized and configures the DPI box.
        with the function name provided and the 
    """
    def exposed_install_function(self,pid,function_name):
        #find the code and run the program.
        pass


    # Utilituy function used by install function to get the function code downloaded from the controller in case its not present.
    def __get_function_code(self,function_name):
        pass

    """
        Enable event
    """
    def exposed_enable_trigger(self,pid,trigger):
        pass

    """
        Disable event
    """
    def exposed_disable_trigger(self,pid,trigger):
        pass

    """
     Stop the pid.
        Kill the process
        Remove executables
        Remove Logic
    """
    def exposed_stop_function(self,pid):
        pass



"""
    NON-API
"""
class ControllerClient()
    def __init__(self):
        self.mbserver_ip = constants.MB_CONTROLLER_IP 
        self.mbserver_port = constants.MB_CONTROLLER_PORT
        self.conn = None

    def connect_server(self):
        try:
            self.conn = rpyc.connect(self.mbserver_ip,self.mbserver_port)
        except Exception:
            print "Unable to connect"
            self.conn = None

    """
        Not the API but are used to communicate with controller
    """
    def sent_event(self,event):
        pass


# This is the main file to be used for DNS Sensor
def usage():
    pass


MAIN_DEBUG = False
# --
# Main function calls from here
# TODO: sanitize input.
# --
def main(argv):
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdi:f:", ["help","debug","iface","file"])
    except getopt.GetoptError:
        print "Option error!"
        sys.exit(2)
    for opt, arg in opts:
        print opt
        if opt in ("-h","--help"):
            usage()
            sys.exit()
        else:
            assert False, "Unhandled Option"
            usage()
    dns_sensor = DNSSensor(mode,str(iface),file_name)
    dns_sensor.initiate()

if __name__ == "__main__":
    main(sys.argv[1:])




