#A DNS cache to keep the record of the URLs visited to reduce the traffic.

import sys
import os
import platform
import socket

import json
from collections import defaultdict
import glob

# For checking the version of IPv4 or IPv6
from IPy import IP

DNS_DIR_NAME = "dnscache"
DNS_FILE_NAME = "dnscache"
DNS_BLOCK_LIST_DIR = "blacklists"

class DNSCache:
    """DNSCache for the Optimization"""
    def __init__(self):
        self.data = {} # A dictionary with Domain Name as key and IP address list as resolved addresses.
        self.cur_ip_ddr = "" 
        self.is_cur_ipv4 = True
        self.is_cur_ipv6 = False
        self.dns_file_path = ""
        self.dns_dir_path = ""
        # File Handling
        dns_dir = ""
        file_name = ""
        if(platform.system() == 'Linux'):
            dns_dir = os.getcwd()+"/"+ DNS_DIR_NAME
            file_name = dns_dir + "/" + DNS_FILE_NAME
        if(platform.system() == 'Windows'):
            dns_dir = os.getcwd()+"\\"+ DNS_DIR_NAME
            file_name = dns_dir + "\\" + DNS_FILE_NAME
        if not (os.path.exists(dns_dir)):
            os.mkdir(dns_dir)
        self.dns_file_path = file_name
        self.dns_dir_path = dns_dir

        
    def storeIPAddress(self,hostname):
        hostname_ret,alias_list,ipaddr_list = socket.gethostbyname_ex(hostname)
        print "XXXXXXXXXXXXXXXXXXXXX",ipaddr_list
        print "XXXXXXXXXXXXXXXXXXXXX",alias_list
        print "XXXXXXXXXXXXXXXXXXXXX",hostname_ret
        self.data [hostname_ret] = ipaddr_list 
        self.cur_ip_addr =  ipaddr_list[0]
        if(IP(self.cur_ip_addr).version() == 4):
            self.is_cur_ipv4 = True
            self.is_cur_ipv6 = False
        elif(IP(self.cur_ip_addr).version() == 6):
            self.is_cur_ipv4 = False
            self.is_cur_ipv6 = True

    def getIPAddress(self,hostname):
        if(self.data.has_key(hostname)):
            ip_addr = self.data[hostname]
            return ip_addr
        else:
            self.storeIPAddress(hostname)
            return self.cur_ip_addr
        pass
    
    def dumpDNSRecord(self):
        f= None
        #if(os.path.isfile(self.dns_file_path)):
        #    f = open(self.dns_file_path, 'a')
        #else:
        f = open(self.dns_file_path,'w')

        json.dump(self.data, f, indent = 0)
        if(f):
            f.close()

    def readDNSRecords(self):
        f=None
        if(os.path.isfile(self.dns_file_path)):
            f = open(self.dns_file_path, 'r')
            temp = json.load(f)
            # Load the dictioanries back 
            for k,v in temp.iteritems():
                self.data[k]=v
                pass
            pass
        pass
        print self.data
        if(f):
            f.close()


class LoadCache:
	"""LoadCache for laoding the blocked domain names."""
	def __init__(self):
		self.data = defaultdict(list) # A dictionary with Domain Name as key and IP address list as resolved addresses.
		self.block_dir = DNS_BLOCK_LIST_DIR
		self.block_domain_dict = {}

	def _list_files(self):
		file_list = [] 
		for infile in glob.glob(self.block_dir+"/*/domains"):
			file_list.append(infile)
		return file_list

    # This function loads the blacklists file.
	def load_files(self):
		for item in self._list_files():
			f = open(item,'r')
			for domain in f.readlines():
				self.block_domain_dict[domain] = True
			pass
		pass
		#print "Length of domain names: " ,len(self.block_domain_dict)

	def is_blocked_domain(self,domin_name):
		if(self.block_domain_dict.has_key(domain_name)):
			return True
		else:
			return False

##################################################################################################################
# Test Code
##################################################################################################################
def main(argv):
	#Store IP Address Test
	dns_cache = DNSCache()
	hostname = "www.google.com"
	dns_cache.storeIPAddress(hostname)
	print dns_cache.cur_ip_addr
	if(dns_cache.cur_ip_addr == dns_cache.data[hostname][0]):
		print "Store IP Address: Test passed"
	else:
		print "Store IP Address: Test failed"
	hostname = "www.yahoo.com"
	ip_addr = dns_cache.getIPAddress(hostname)
	print ip_addr
	print dns_cache.data[hostname][0]
	dns_cache.readDNSRecords()
	dns_cache.dumpDNSRecord()
	load_cache = LoadCache()
	load_cache.load_files()

if __name__ == "__main__":
    main(sys.argv[1:])
