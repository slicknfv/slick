# This file has utility functions that can be used by other files to perform generic operations
import string
import os

import json

# --
def getmac(ethdev):
    import socket
    s = socket.socket(socket.AF_PACKET,socket.SOCK_RAW)
    s.bind((ethdev,9999))
    rawmac = s.getsockname()[-1]
    return rawtohex(rawmac)



# --
# This function can be used to read a file from the provided path.
# @args:
#   filename: Fully qualified path that should be used to read a json file.
#   debug: If debug is true then display the debug messages
# @returns:
#   returns a dictionary that should be read and returned.
# --
def read_json(filename,debug=None):
    if(debug):
        print "Loading data from file: " +filename
    f = open(filename,'r')
    data = json.load(f)
    if(debug):
        print "Loaded global dictionary size" + str(len(data))
    return data

