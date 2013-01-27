# This file has the code responsible for communicating with 
# the controller and convying the messages for the OpenFlow controller.
import socket
import sys
import json
import jsonpickle
import constants

import select

import ast

LOCAL_DBG = False

class ClientComm():
    def __init__(self):
        self.host = constants.OPEN_FLOW_CONTROLLER_IP
        self.port = constants.OPEN_FLOW_CONTROLLER_PORT 
        self.size = constants.BUF_SIZE
        self.timeout = 3 # seconds?
        self.sock = self.establish_connection(self.timeout)
        print self.sock
        pass

    def establish_connection(self,timeout):
        print "Connecting with the Server: ",self.host," on port: ",self.port
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #self.sock.settimeout(0)
        except socket.error,msg:
            print "Socket creation failed"
            self.sock = None
        try:
            self.sock.connect((self.host,self.port))
        except socket.error,msg:
            print "Connect Failed",msg
            self.sock.close()
            self.sock = None
        return self.sock

    # sends a json object across the network.
    def send_data(self,obj):
        #data_dict = json.dumps(obj,default=lambda o:o.__dict__)
        data = json.loads(jsonpickle.encode(obj))
        data["type"] = obj.name # Needed for jsonmessenger
        data_dict = json.dumps(data)
        print data_dict
        if(LOCAL_DBG):
            print "Sending Data:",data_dict
        try:
            if(self.sock.send(data_dict) == 0):
                return False
            else:
                return True
        except:
            return False

    # received the data as a json and return object
    def recv_data(self):
        recvd_data = None
        if(self.sock):
            data = self.sock.recv(self.size)
            recvd_obj = jsonpickle.decode(data)
            if(LOCAL_DBG):
                print "Recevied this data: ",data
        return recvd_obj

    # returns the IP address.
    def get_ip_address(self):
        return self.sock.getsockname()[0]

    # sends a json object across the network.
    def send_data_basic(self,data):
        data_dict = json.dumps(data)
        if(LOCAL_DBG):
            print "Sending Data:",data_dict
        try:
            if(self.sock.send(data_dict) == 0):
                return False
            else:
                return True
        except:
            return False

    # received the data as a json
    def recv_data_basic(self):
        recvd_data = None
        if(self.sock):
            ready = select.select([self.sock], [], [], 0)
            #print ready
            if(ready[0]):
                recvd_data = self.sock.recv(self.size)
            if(LOCAL_DBG):
                print "Recevied this data: ",recvd_data
        if (recvd_data != None):
            #print recvd_data
            data = recvd_data#json.loads(recvd_data)
            return data
        else: 
            return None
