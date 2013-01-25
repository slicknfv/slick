import os,sys
from time import time
from socket import htons
from struct import unpack
from collections import defaultdict
from collections import namedtuple
# NOX 
from nox.lib.core     import *
from nox.lib.packet.packet_utils import mac_to_str, mac_to_int,ipstr_to_int,ip_to_str
"""
	This class provides the function map for each dpid.
        We need to update the location of functions once they are installed or removed.
	What functions are connected with which dpid

    There needs to be a mapping between:
        machine location [dpid,port] -> Machine IP addresses.
        machine IP addresse -> function descriptor.

        This code assumes one IP address per port.
"""
class FunctionMap():
    def __init__(self,function_map_file):
    	self.function_map_file = function_map_file
    	self.function_map = defaultdict(dict)
        self.fd_map = defaultdict(list) # Machine IP Address to function descriptor mapping, if the list is empty then we have shim only.
    
    def read_json(self):
    	print self.function_map_file
    	json_data = open(self.function_map_file);
    	json_data_dict = json.load(json_data)
    	json_data.close() # Close the file and return
    	self.function_map = json_data_dict
    	return self.function_map
    
    # Return the list of connected ports.
    def get_connected_ports(self,dpid):
    	if(self.function_map.has_key(str(dpid))):
    		return self.function_map.keys() 
    
    def init_switch(self,dpid,port,function):
    	self.function_map[dpid][port] = function

    # Add a newly discovered/added function on the switch's port.
    def add_port(self,dpid,port,function):
    	if(self.function_map.has_key(str(dpid))):
    		if not self.function_map[dpid].has_key(port):
    			self.function_map[dpid][port] = function
    		else:
    			raise Exception("Switch ",dpid," and port ",port," has an existing function")
    	else:
    		raise Exception("Switch ",dpid," does not have any middlebox attached to it")

    # Remove a function from the port
    def del_port(self,dpid,port):
    	if(self.function_map.has_key(str(dpid))):
    		if (self.function_map[dpid].has_key(port)):
    			del self.function_map[dpid][port] 
    		else:
    			raise Exception("Switch ",dpid," and port ",port," has NO existing function")
    	else:
    		raise Exception("Switch ",dpid," does not have any middlebox attached to it")
    """
    # Given the function name.
    # returns function_locations[(dpid,port)] = function_name dict where we have function available.
    # Instead of function_names dict it should be dictionary of function descriptors.
    # Thus we can have multiple instances of the same function on the same dpid,port
    """
    def get_function_locations(self,function_name):
        function_locations = {}
        for dpid,dictionary in self.function_map.iteritems():
            for port,f_list in dictionary.iteritems():
                #print "VVVVVVVVVVVVVVVVVVVV",f_list
                if(len(f_list) >= 1):
                    if(f_list[0] == function_name):
                        function_locations[(dpid,port)] = function_name
                    pass
                pass
            pass
        return function_locations

    # TODO: Implement the closest box optimization.
    # or placement optimization here.
    # return the dpid with the function_name installed on it.
    def get_closest_location(self,dpid,function_name):
        return dpid
    
    # -- 
    # Given the dpid and function name return the port number.
    # --
    def get_function_port(self,dpid,function_name):
        func_locs = self.get_function_locations(function_name)
        for item in func_locs:
            if(item[0] == dpid):
                return item[1]
    # --
    # Simply get different functions available in the network.
    # --
    def get_available_functions(self):
        func_list = []
        for dpid,dictionary in self.function_map.iteritems():
            for port,flist in dictionary.iteritems():
                if(len(f_list) > 1):
                    if(f_list[0] not in func_list):
                        func_list.append(f_list[0])
                    pass
                pass
            pass
        return func_list


    # IP address should be a string and function_desc is an integer.
    def update_function_desc(self,ip_addr,machine_mac,function_desc):
        if(function_desc == None):
            self.fd_map[ip_addr].append(function_desc)
        else:
            self.fd_map[ip_addr] = []


    # Returns the shim machine with the ip _addr
    def add_function_desc(self,ip_addr,machine_mac,function_desc):
        if(ip_addr == None):
            for item in self.fd_map[ip_addr]:
                if (len(self.fd_map[ip_addr]) == 0):
                    # TODO: Add optimization algorithm here.
                    self.fd_map[ip_addr].append(function_desc) # add the function on the first empty machine
                    return ip_addr

"""
# Tell which machines are hanging to which switches.
# This is not the topology and not Functions Map, here manage machine specs. related information.
# Also maintain the machine specification of each of these machines which will be loaded from a database etc.
"""
class MachineMap():
    def __init__(self):
        self.machine_ip_map = defaultdict(dict) # key=dpid:value=IP address 
        self.ip_dpid = {} #keeps a record of the location of IP address. key:ip value: dpid
        #TODO: Add machine specs ability to read the files.
        self.machine_specs = {} # key:ip_address and value:machine spec json file.

    # Load the machine map from a file or from another module that 
    # is responsible for routing the packets.
    def _load_map(self,file_name):
	if(file_name != None):
	    json_data = open(file_name)
	    machine_map = json.load(json_data)
	    json_data.close() # Close the file and return
	return machine_map # heavy 

    # Return the machine map for the whole network.
    def get_machine_map(self):
	self.machine_ip_map = self._load_map("/home/openflow/noxcore/src/nox/coreapps/examples/tutorial/machine_map.json")
	if(len(self.machine_ip_map) > 0):
	    return self.machine_ip_map
	else:
	    raise Exception("Machine Map not present")


    # Return the list IP addresses attached to the dpid.
    def get_machine_ips(self,dpid):
        machine_ips = []
	if(dpid):
	    for port,ip in self.machine_ip_map[dpid].iteritems():
	        # Copied http://stackoverflow.com/questions/6291238/how-can-i-find-the-ips-in-network-in-python
		ip_addr = reduce(lambda x,y: (x<<8) + y, [ int(x) for x in ip.split('.') ])
		machine_ips.append(ip_addr)
	    return machine_ips		 

    """
    # @args:datapath ID and Destination addr
    # Return the port # for the desintation addr.
    """
    def get_dest_addr_port(self,dpid,ip_addr):
	switch_addr_list =  self.get_machine_ips(str(dpid))
	if(addr in switch_addr_list):
	    ip_str = "%d.%d.%d.%d" % (addr >> 24,(addr & 0xffffff) >> 16,(addr & 0xffff) >> 8,(addr & 0xff))
	    for port,ip in self.machine_ip_map[dpid].iteritems():
	        if(ip == ip_str):
		    return int(port)

    def update_ip_dpid_mapping(self,dpid,flow):
        #flow = extract_flow(packet)
        src_ip = flow[core.NW_SRC]
        if not (self.ip_dpid.has_key(src_ip)):
            self.ip_dpid[src_ip] = dpid
        else:
            if(self.ip_dpid[src_ip] != dpid):
                print src_ip, " changed the location, from:",self.ip_dpid[src_ip] ," to:",dpid
                self.ip_dpid[src_ip] = dpid
    
    def get_dpid(self,ip_addr):
        #debug
        if(self.ip_dpid.has_key(ip_addr)):
            return self.ip_dpid[ip_addr]
        else:
            return -1

    
    # Given a dictionary of machine specs, return a list of IP addresses machine with that spec.
    def get_machines(self,machine_specs_dict):
        return []
"""
TODO: Policy Overlap and Union of actions.
TODO: Policy Conflict and pick them up based on some user defined criteria, security over performance. Or throughput over latency.
"""

"""
	Description: 
		Keeps a flow to function mapping.
"""
class Policy():
    def __init__(self,policy_filename):
        self.policy_file_name = policy_filename
        self.FlowTuple = namedtuple("FlowTuple",["in_port","dl_src","dl_dst","dl_vlan","dl_vlan_pcp","dl_type","nw_src","nw_dst","nw_proto","tp_src","tp_dst"])
        self.flow_to_function_mapping = defaultdict(dict) # key:FlowTuple value:[functions]
        self.init_tuples()
    
    """
     These three functions: 
        add_flow,del_flow,modify_flow 
        are required to add,del,and modify flow policies.
     A compiler that parses policy language and generates these flow to function mappings.
	# Given a in_port,flow and dictionary of functions{key=number:value=function_name}
    """
    def add_flow(self,in_port,flow,functions):
		""" Debug
		for k,v in flow.iteritems():
			print k,v
		"""
		# TypeError: unhashable type: 'array.array'
		src_mac = mac_to_int(flow['dl_src'])
		dst_mac = mac_to_int(flow['dl_dst'])
		f = self.FlowTuple(in_port=in_port,dl_src=src_mac,dl_dst=dst_mac,dl_vlan=flow['dl_vlan'],dl_vlan_pcp=flow['dl_vlan_pcp'],dl_type= flow['dl_type'],nw_src=flow['nw_src'],nw_dst=flow['nw_dst'],nw_proto=flow['nw_proto'],tp_src=flow['tp_src'],tp_dst=flow['tp_dst'])
		if not self.flow_to_function_mapping.has_key(f):
			self.flow_to_function_mapping[f] = functions
			print self.flow_to_function_mapping
			return True
		else:
			return False

	# Given a in_port,flow and dictionary of functions{key=number:value=function_name}
    def del_flow(self,in_port,flow,functions):
        src_mac = mac_to_int(flow['dl_src'])
        dst_mac = mac_to_int(flow['dl_dst'])
        f = self.FlowTuple(in_port=in_port,dl_src=src_mac,dl_dst=dst_mac,dl_vlan=flow['dl_vlan'],dl_vlan_pcp=flow['dl_vlan_pcp'],dl_type= flow['dl_type'],nw_src=flow['nw_src'],nw_dst=flow['nw_dst'],nw_proto=flow['nw_proto'],tp_src=flow['tp_src'],tp_dst=flow['tp_dst'])
        if (self.flow_to_function_mapping.has_key(f)):
        	del self.flow_to_function_mapping[f]
        	return True
        else:
        	return False

	def modify_functions(self,in_port,flow,functions):
		src_mac = mac_to_int(flow['dl_src'])
		dst_mac = mac_to_int(flow['dl_dst'])
		f = self.FlowTuple(in_port=in_port,dl_src=src_mac,dl_dst=dst_mac,dl_vlan=flow['dl_vlan'],dl_vlan_pcp=flow['dl_vlan_pcp'],dl_type= flow['dl_type'],nw_src=flow['nw_src'],nw_dst=flow['nw_dst'],nw_proto=flow['nw_proto'],tp_src=flow['tp_src'],tp_dst=flow['tp_dst'])
		if (self.flow_to_function_mapping.has_key(f)):
			del self.flow_to_function_mapping[f]
			return True
		else:
			return False

	# A function for initializing tuples.
	# TODO: read from the configuration file.
    # Take the policy file:
    # Verbal Description:
    #       Block all DNS traffic with gambling websites.
    #        ^        ^                     ^
    #        |        |                     |
    #    func:DROP  match:FLOW          func:DNS-DPI

    def init_tuples(self):
        f = self.FlowTuple(in_port=None,dl_src=None,dl_dst=None,dl_vlan=None,dl_vlan_pcp=None,dl_type= None,nw_src=None,nw_dst=None,nw_proto=None,tp_src=None,tp_dst=53) # For outgoing
        rf = self.FlowTuple(in_port=None,dl_src=None,dl_dst=None,dl_vlan=None,dl_vlan_pcp=None,dl_type= None,nw_src=None,nw_dst=None,nw_proto=None,tp_src=53,tp_dst=None) # For incoming.
        self.flow_to_function_mapping[f] = {1:"DNS-DPI",2:"DROP"}
        self.flow_to_function_mapping[rf] = {1:"DNS-DPI",2:"DROP"}
        #print self.flow_to_function_mapping

    # Return a reverse flow for the given flow.
    def get_reverse_flow(self,flow):
        """
        r_dl_src = flow.dl_dst
        r_dl_dst = flow.dl_src
        r_dl_vlan = flow.dl_vlan
        r_dl_vlan_pcp = flow.dl_vlan_pcp
        r_dl_type = flow.dl_type
        r_nw_src = flow.nw_dst
        r_nw_dst = flow.nw_src
        r_nw_proto = flow.nw_proto
        r_tp_src = flow.tp_dst
        r_tp_dst = flow.tp_src
        """
        reverse_flow = self.FlowTuple(in_port = None, dl_src = flow.dl_dst, dl_dst = flow.dl_src,
                                        dl_vlan = flow.dl_vlan, dl_vlan_pcp = flow.dl_vlan_pcp, dl_type = flow.dl_type,
                                        nw_src = flow.nw_dst, nw_dst = flow.nw_src, nw_proto = flow.nw_proto,
                                        tp_src = flow.tp_dst, tp_dst = flow.tp_src) 
        return reverse_flow
    """
        TODO:
            Add lookup code from file: ofmatch.py in project openfaucet.
        Dummy matching function returns True if the first wild card entry matches.
    """
    def lookup_flow(self,ft):
        for item in self.flow_to_function_mapping:
            item_match = False
            if(item.in_port!=None):#If its not a don't care.
            	if(item.in_port == ft.in_port):
            		item_match = True 
            	else: 
            		continue
            if(item.dl_src!=None):#If its not a don't care.
            	if(item.dl_src == ft.dl_src):
            		item_match = True 
            	else:# If its not a don't care and we have not matched then its not what we are looking for. 
            		continue
            if(item.dl_dst!=None):
            	if(item.dl_dst == ft.dl_dst):
            		item_match = True 
            	else:
            		continue
            if(item.dl_vlan!=None):
            	if(item.dl_vlan == ft.dl_vlan):
            		item_match = True 
            	else:
            		continue
            if(item.dl_vlan_pcp!=None):
            	if(item.dl_vlan_pcp == ft.dl_vlan_pcp):
            		item_match = True 
            	else:
            		continue
            if(item.dl_type!=None):
            	if(item.dl_type == ft.dl_type):
            		item_match = True 
            	else:
            		continue
            if(item.nw_src!=None):
            	if(item.nw_src == ft.nw_src):
            		item_match = True 
            	else:
            		continue
            if(item.nw_dst!=None):
            	if(item.nw_dst == ft.nw_dst):
            		item_match = True 
            	else:
            		continue
            if(item.nw_proto!=None):
            	if(item.nw_proto == ft.nw_proto):
            		item_match = True 
            	else:
            		continue
            if(item.tp_src!=None):
                if(item.tp_src == ft.tp_src):
                    item_match = True 
                else:
                    continue
            if(item.tp_dst!=None):
                if(item.tp_dst == ft.tp_dst):
                    item_match = True 
                else:
                    continue
            if(item_match == True):
                return self.flow_to_function_mapping[item]
        return {}

    # Function that returns the corresponding functions dict to the flow.
    def get_flow_functions(self,inport,flow):
        # Based on the flow figure out the functions and then return a list of functipons available on the port.
        src_mac = mac_to_int(flow['dl_src'])
        dst_mac = mac_to_int(flow['dl_dst'])
        f = self.FlowTuple(in_port=inport,dl_src=src_mac,dl_dst=dst_mac,dl_vlan=flow['dl_vlan'],dl_vlan_pcp=flow['dl_vlan_pcp'],dl_type= flow['dl_type'],nw_src=flow['nw_src'],nw_dst=flow['nw_dst'],nw_proto=flow['nw_proto'],tp_src=flow['tp_src'],tp_dst=flow['tp_dst'])
        #print f
        function_dict = self.lookup_flow(f)
        if(len(function_dict) > 0):
        	print "There is a match"
        	""" The order of this list is important as it tells in what order functions should be applied"""
        	return function_dict
        else:
        	return function_dict

