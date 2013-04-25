# This file exposes methods that can be used by the 
# slick controller to download the files on the remote hosts.
# It also provides the interface to exectue the code.



class Download():
    def __init__(self):
        self.hostname = None # host FQDN
        self.port= 22
        self.protocol = "ssh"
        self.ip_address = None

    # its the string that is used specifiy the hostname
    def set_hostname(self.hostname):
        self.hostname = hostname

    # machine ip address
    def set_ip_address(self,ip_address):
        self.ip_address = ip_address

    # protocol to use to connect with the machine. Only ssh fow now.
    def set_protocol(self,protocol):
        self.protocol = protocol
    
    # This argument is going to be the port number for the host ot be connected to.
    def set_port(self,port):
        self.port = port 

    # Based on the function_name this function should figure out the required files
    # and donload them to the provided hostname
    def send_file(self,function_name):
        for ite
        pass
