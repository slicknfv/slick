# This file has utility functions that can be used by other file
# to perform generic operations
import constants
import string
import os

import json
# --
# Reads the /proc file system and returns a list of interfaces.
# /proc/net/dev
# --
def read_netdev_file():
    file_path = constants.PROC_NET_DEV; #file_name
    net_file_ref = open(file_path,"r")
    net_file = ""
    for line in net_file_ref:
        net_file += line
    net_file_ref.close()
    return net_file

# --
# Returns the number of network interfaces. Returns the integer
# /proc/net/dev
# Usage
#		print get_if_count(constants.WIRELESS_STR)
# --
def get_if_count(intf_type):
    if_list = find_interfaces(intf_type) 
    return len(if_list)

# --
# This function generates a list of 'X' interfaces present on the machine.
# argument: 
# 			intf_type: WIRELESS_STR or ETH_STR or etc.
# Usage
#		print find_interfaces(constants.WIRELESS_STR)
#		print find_interfaces(constants.ETH_STR)
# --
def find_interfaces(intf_type):
    if_list = []
    netdev_file = read_netdev_file()
    net_list = netdev_file.split('\n')
    for item in net_list:
        item_list = item.split(':')
        if(string.find(item_list[0],intf_type) != -1):
            if_list.append(item_list[0])
    return if_list
#--
# Converts a raw mac address to hex
#--
def rawtohex(raw):
    return ":".join(["%02X" % (ord(ch),) for ch in raw])

#--
# Generator
#--
def getethdevs_proc():
    lines = open(constants.PROC_NET_DEV).readlines()
    for line in lines:
        if ":" in line:
           ethdev = line.split(":", 1)[0].strip()
           yield ethdev

# -- 
# For the given interface get the mac address
# --
def getmac(ethdev):
    import socket
    s = socket.socket(socket.AF_PACKET,socket.SOCK_RAW)
    s.bind((ethdev,9999))
    rawmac = s.getsockname()[-1]
    return rawtohex(rawmac)

# -- 
# Rrturns a ditionary of interfaces and their respective MAC addresses 
# --
def getmacs():
    macs = {}
    for ethdev in getethdevs_proc():
        mac = getmac(ethdev)
        if mac:
            #yield mac
            if not macs.has_key(ethdev):
	            macs[ethdev] = mac
            else:
				print "There are two devices with the same ethernet interface name"
            pass
        pass
    pass
    return macs

# --
# This function is copied
# This function accepts a 12 hex digit string and converts it to a colon separated string
# -- 
def add_colons_to_mac( mac_addr ):
    s = list()
    for i in range(12/2) :  # mac_addr should always be 12 chars, we work in groups of 2 chars
        s.append( mac_addr[i*2:i*2+2] )
    r = ":".join(s)     # I know this looks strange, refer to http://docs.python.org/library/stdtypes.html#sequence-types-str-unicode-list-tuple-bytearray-buffer-xrange
    return r


# --
# Function to write the data dictionary to the json file
# @args:
# 		filename: name of the file to be written
#		data_dict: Python dictionary with key value pair to store the information
# --
def store_cache(f,data_dict):
	data_dir = "conf/"
	if not (os.path.exists(data_dir)):
		os.makedirs(data_dir)
	filename = data_dir + f # put all the data inside the data folder                                                                            
	f = open(filename,'w')
	json.dump(data_dict, f, indent = 0)
	#print "Stored dictionary size: " + str(len(data_dict))

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


# --
# This function can be used to keep the TLDs only not 
# all the servers so that we know exactly the numer of unique domain names 
# being looked up.
# --
def keepTLDs(domain_name):
    #print "Inside keepTLDs"
    tlds = ['aero','asia','biz','com','coop','edu','gov','info','intl','jobs','mil','museum','name','net','org','pro','tel','travel','xxx']
    # Brits
    tlds.append('co')
    dn_list = domain_name.split('.')
    dn_list.reverse()
    #print dn_list
    str_list = []
    count = 0
    threshold = 2
    three_levels = False
    for item in dn_list:
        str_list.append(item)
        count = count + 1
        if(count== threshold):
            #if((dn_list[1] == 'com') or (dn_list[1] == 'co')): 
            if(dn_list[1] in tlds): 
                if(three_levels == True):
                    break
                threshold = 3
                three_levels = True
                continue
            elif(three_levels == False):# There can be .co.uk or .com.au etc.
                break
        pass
    pass
    str_list.reverse()
    domain = '.'.join(str_list)
    return domain

