# This file exposes methods that can be used by the 
# slick controller to download the files on the remote hosts.
from paramiko import SSHClient
from scp import SCPClient

from conf import *

from collections import defaultdict

class Download():
    def __init__(self):
        # Middlebox's has one control interface.
        self.mb_hosts = {} #MAC to IP address mapping. MAC is used for middlebox ID and IP is used for to connect to middlebox.
        self.ssh_clients = {} # Middlebox MAC to ssh client object mapping
        self.mb_settings = defaultdict(dict) #Middlebox MAC -> middlebox settings mapping.

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

    
    # return the SSH client for the host name with the provided information.
    def create_MB_ssh_client(self,server, port, user, password):
        ssh = SSHCLient()
        ssh.load_system_host_keys()
        ssh.connect(server, port, user, password)
        return ssh

    def add_mb_client(self,server,port,username,password):
        if(username == None):
            user = MB_USERNAME
        if(password == None):
            password = MB_PASSWORD
        ssh = create_MB_ssh_client(server,port,user,password)
        scp = SCPClient(ssh.get_transport())

    # Need to call it in the apply_func before installing the code.
    def put_file(self,filename,username=None,password=None):
        pass

    def get_file(self,filename,username);
        pass
