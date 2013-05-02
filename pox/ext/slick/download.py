# This file exposes methods that can be used by the 
# slick controller to download the files on the remote hosts.
from paramiko import SSHClient
from scp import SCPClient
import paramiko

from conf import *

from collections import defaultdict
import os

class Download():
    def __init__(self):
        # Middlebox's has one control interface.
        self.mb_hosts = {} #MAC to IP address mapping. MAC is used for middlebox ID and IP is used for to connect to middlebox.
        self.scp_clients = {} # Middlebox MAC to ssh client object mapping
        self.mb_settings = defaultdict(dict) #Middlebox MAC -> middlebox settings mapping.
        self.elem_name_to_files_mapping = {} #Function Name to File path on controller. 

    # its the string that is used specifiy the hostname
    def set_hostname(self,hostname):
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
        pass

    
    # return the SSH client for the host name with the provided information.
    def _create_MB_ssh_client(self,server, port, user, password):
        ssh = SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print "AAAAAAAAAAAAAAAAAAAAAAAA",server,port,user,password
        ssh.connect(server, port, user, password)
        return ssh

    def _update_record(self,mac_addr,server_ip,scp):
        if (not self.scp_clients.has_key(mac_addr)):
            self.scp_clients[mac_addr] = scp
        if (not self.mb_hosts.has_key(mac_addr)):
            self.mb_hosts[mac_addr] = server_ip

    #Return success after adding.
    def add_mb_client(self,mac_address,server_ip,username,password):
        if(username == None):
            user = MB_USERNAME
        if(password == None):
            password = MB_PASSWORD
        port = 22
        ssh = self._create_MB_ssh_client(server_ip,port,user,password)
        #scp = SCPClient(ssh.get_transport())
        self._update_record(mac_address,server_ip,ssh)
        return True

    # Return the location of file for the corresponding 
    def _lookup_function_files(self,function_name):
        print function_name
        print "CURRENT PATH", os.getcwd()
        elements_path = os.getcwd() + "/"+"ext/slick/elements/"
        files = os.listdir(elements_path)
        # assumes no directory in the element dir
        for item in files:
            if(item.lower() == function_name.lower()):
                return elements_path + "/" + item

    # Need to call it in the apply_func before installing the code.
    def put_file(self,mac_addr,function_name):
        scp = None
        file_path = self._lookup_function_files(function_name)
        if(os.path.exists(file_path)):
            if(os.path.isdir(file_path)):
                if(self.scp_clients.has_key(mac_addr)):
                    ssh = self.scp_clients[mac_addr]
                    scp = SCPClient(ssh.get_transport())
                    print scp
                    print file_path
                    scp.put(file_path,recursive=True)
                #files = os.listdir(file_path)
                ## assumes no directory in the element dir
                #for item in files:
                #    print item
                #    scp.put(file_path+'/'+item) #Not portable use os.path.join
            if(os.path.isfile(file_path)):
                if(self.scp_client.has_key(mac_addr)):
                    scp = self.scp_clients[mac_addr]
                scp.put(file_path)

    # Provide the full filename 
    def get_file(self,filename,username):
        try:
            scp.get(filename)
        except:
            print "Unable to get the file."
