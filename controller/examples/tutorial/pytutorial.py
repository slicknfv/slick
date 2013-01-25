# Tutorial Controller
# Starts as a hub, and your job is to turn this into a learning switch.

import logging

from nox.lib.core import *
import nox.lib.openflow as openflow
from nox.lib.packet.ethernet import ethernet
from nox.lib.packet.ipv4 import ipv4
from nox.lib.packet.packet_utils import mac_to_str, mac_to_int
from nox.lib.packet.dns import dns #importing from the dns class.

# Need this code for topology discovery.
from nox.netapps.discovery import discovery
from nox.lib.netinet.netinet import datapathid
from nox.netapps.topology import pytopology # Uses the discovery module.
from nox.lib.netinet.netinet import create_datapathid_from_host

log = logging.getLogger('nox.coreapps.tutorial.pytutorial')
from collections import defaultdict
from collections import namedtuple
import json

from time import time
import socket, struct

# Timeout for cached MAC entries
CACHE_TIMEOUT = 5

# Prerequisite:
# 	Middleboxes are IP Addressable and can establish a connection with the controller. 


#Module 1 that populates the function_map.json file. # For now its only file reading and lets keep it that way.
#Module 2 that provides the flow iformation so that we know where does the packet need to go from point A to point B.
# Example1: Take the access-list file from the OIT.
# 		Using these rules Take three actions:
#		0- Setup paths from the controller -> switch -> firewall to send middlebox rule installation packets. 
# 		1- install rule on the firewall{Each middlebox needs its own drivers} Do not categorize as one middlebox can have multiple functions.
#		1.5- Install rule on the middlebox whose location is closest to the IP address that we are protecting. [Its not optimized]
#		2- Install two rules on the openFlow switch.
# There should not be anything installed on the firewall that installs the rule.

#Rule Installation Flow:
# 0- Install rule on the switch and the middlebox attached to it.

"""
util functions
"""
# Copied

"""
	This class provides the function map for each dpid
	What functions are connected with which dpid
"""
class FunctionMap():
	def __init__(self,function_map_file):
		self.function_map_file = function_map_file
		self.function_map = defaultdict(dict)

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

	# Add a newly discovered function on the switch's port.
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

	def replace_port(self,dpid,port,function):
		pass
"""
# Tell which machines are hanging to which switches.
# This is not the topology.
"""
class MachineMap():
	def __init__(self):
		self.machine_ip_map = defaultdict(dict) # key=dpid:value=IP address 
		self.machine_mac_map = defaultdict(dict) # key=dpid:value=mac address of the machine.

	# Load the machine map from a file or from another module that 
	# is responsible for routing the packets.
	def _load_map(self,file_name):
		if(file_name != None):
			json_data = open(file_name)
			machine_map = json.load(json_data)
			json_data.close() # Close the file and return
		return machine_map # heavy 

	# Returnt the machine map for the whole network.
	def get_machine_map(self):
		self.machine_ip_map = self._load_map("/home/openflow/noxcore/src/nox/coreapps/examples/tutorial/machine_map.json")
		if(len(self.machine_ip_map) > 0):
			return self.machine_ip_map
		else:
			raise Exception("Machine Map not present")

	# Given the MAC/IP address return the dpid of the machine.
	def get_machine_dpid(self,mac_addr,ip_addr):
		if(mac_addr):
			return '1'
		if(ip_addr):
			return '1'

	# Return the list IP addresses attached to the machines.
	def get_machine_ips(self,dpid):
		machine_ips = []
		if(dpid):
			for port,ip in self.machine_ip_map[dpid].iteritems():
				# Copied http://stackoverflow.com/questions/6291238/how-can-i-find-the-ips-in-network-in-python
				ip_addr = reduce(lambda x,y: (x<<8) + y, [ int(x) for x in ip.split('.') ])
				#print "Conversion:",ip,ip_addr
				machine_ips.append(ip_addr)
			return machine_ips		 

    	# @args:datapath ID and Destination addr
    	# Return the port # for the desintation addr.
    	def get_dest_addr_port(self,dpid,addr):
		switch_addr_list =  self.get_machine_ips(str(dpid))
		if(addr in switch_addr_list):
			ip_str = "%d.%d.%d.%d" % (addr >> 24,(addr & 0xffffff) >> 16,(addr & 0xffff) >> 8,(addr & 0xff))
			for port,ip in self.machine_ip_map[dpid].iteritems():
				if(ip == ip_str):
					return int(port)


"""
	Class for the setup of control path from controller->switch->middlebox.
	1- This control path is used to install rule on the middlebox.
"""
class MiddleboxControlPath():
	def __init__(self,switch_function_map):
		self.switch_function_map = switch_function_map

	def install_first_rules(self):
		pass 

	# This channel establishment is dependent on the middlebox 
	# and can be different from middlebox to middlebox.
	# Create comm class objects based on the middlebox type.
	def establish_control_channel(self):
		pass

"""
	Description: 
		Keeps a flow to function mapping.
"""
class Policy():
	def __init__(self,policy_filename):
		self.policy_file_name = policy_filename
		self.FlowTuple = namedtuple("FlowTuple",["in_port","dl_src","dl_dst","dl_vlan","dl_vlan_pcp","dl_type","nw_src","nw_dst","nw_proto","tp_src","tp_dst"])
		self.flow_to_function_mapping = defaultdict(dict) # key:FlowTuple value:[functions]
		attr = {}

	# Given a in_port,flow and dictionary of functions{key=number:value=function_name}
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
	def init_tuples(self):
		f = self.FlowTuple(in_port=1,dl_src=None,dl_dst=None,dl_vlan=None,dl_vlan_pcp=None,dl_type= None,nw_src=167772162,nw_dst=167772163,nw_proto=None,tp_src=None,tp_dst=None)
		self.flow_to_function_mapping[f] = {1:"NAT"}
		"""KISS
		f = self.FlowTuple(in_port=2,dl_src=None,dl_dst=None,dl_vlan=None,dl_vlan_pcp=None,dl_type= None,nw_src=167772163,nw_dst=167772162,nw_proto=None,tp_src=None,tp_dst=None)
		self.flow_to_function_mapping[f] = {1:"Firewall",2:"RateLimit",3:"IDS"}
		"""
		print self.flow_to_function_mapping

	# Dummy matching function returns True if the first wild card entry matches.
	def _lookup_flow(self,ft):
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
		return []


	# Function that returns the corresponding functions dict to the flow.
	def get_functions(self,inport,flow):
		# Based on the flow figure out the functions and then return a list of functipons available on the port.
		src_mac = mac_to_int(flow['dl_src'])
		dst_mac = mac_to_int(flow['dl_dst'])
		f = self.FlowTuple(in_port=inport,dl_src=src_mac,dl_dst=dst_mac,dl_vlan=flow['dl_vlan'],dl_vlan_pcp=flow['dl_vlan_pcp'],dl_type= flow['dl_type'],nw_src=flow['nw_src'],nw_dst=flow['nw_dst'],nw_proto=flow['nw_proto'],tp_src=flow['tp_src'],tp_dst=flow['tp_dst'])
		print f
		function_dict = self._lookup_flow(f)
		ret_list = []
		if(len(function_dict) > 0):
			print "There is a match"
			""" The order of this list is important as it tells in what order functions should be applied"""
			for k,v in function_dict.iteritems():
				ret_list.append(v)
			return ret_list
		else:
			#print "There is not a match.XXXXXXXXXXXXXXXXXXXXXXXXXX"
			return ret_list

"""
	This is the main class.
"""
class pytutorial(Component):
    def __init__(self, ctxt):
        Component.__init__(self, ctxt)
	func_map = FunctionMap('/home/openflow/noxcore/src/nox/coreapps/examples/tutorial/function_map.json')
	self.switch_function_map = func_map.read_json()
	# Middlebox Control Path.
	self.mb_control_path = MiddleboxControlPath(self.switch_function_map)
	
	self.policy = Policy(None)
	self.policy.init_tuples()
	print self.switch_function_map

	self.machine_map = MachineMap()
	print self.machine_map.get_machine_map()
	
	self.st = {} # Basic switch tables for each machine.
	
	# Object to handle the topology
	discovery = self.resolve("nox.netapps.discovery.discovery.discovery")
	topology = self.resolve("nox.netapps.topology.pytopoloy.pytopology")
	print discovery
	print topology
	print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
	self.topo = Topology(discovery,topology)
	# DNS handler 
	self.dns_handler = DNSHandler() 

    def __update_mappings(self):
		pass
	
    # This function returns the list of ports that have middleboxes connected with them.
    def _get_function_ports(self,dpid):
	function_port_list = []
	for switch, port_func_dict in self.switch_function_map.iteritems():
		for port,func in port_func_dict.iteritems():
			function_port_list.append(port)
	return function_port_list
    
    def _is_destination_attached(self,dpid,ip_addr):
	switch_addr_list =  self.machine_map.get_machine_ips(str(dpid))
	if(ip_addr in switch_addr_list):
		return True
	else:
		return False


    def _lookup_destination(self,dpid,ip_addr):
		#For all the dpids:
		# get the IP list attached to them.
		# If _is_detination_attached: return port
		# else:
		# lookup_topology() 
		# Find next chain function(if needed) or shortest path and return the next hope port. 
		# return port for the next switch closer to destination. 
		pass

    def learn_and_forward(self, dpid, inport, packet, buf, bufid):
        """Learn MAC src port mapping, then flood or send unicast."""
	#extract_flow returns a dictionary.
	flow = extract_flow(packet)
	
	functions={1:"Firewall",2:"RateLimit",3:"IDS"}
	#self.policy.add_flow(inport,flow,functions)
       
    	dstaddr = packet.dst.tostring()
    	if ((not (ord(dstaddr[0]) & 1)) and (flow['dl_type'] != 2054)): # If not a mac broadcast
		# If the packet arrives at a switch where we have the requested function available. 
		if(self.switch_function_map.has_key(str(dpid))):
			#print "In Port: ",inport,type(inport)
			flow_func_list = self.policy.get_functions(inport,flow)#Lookup functions for the flow.	
			print flow_func_list
			for port,function in self.switch_function_map[str(dpid)].iteritems():
				"""Keep a list of port to function mapping for each OpenFlow switch inside the network."""
				if(function[0] in flow_func_list):#This switch provides the function on port 'port' which is needed by current flow. 
					#print "Output Port:",port,"Functions:",function
					#print function[0] ,"is provided on port", port
					out_port = 2#int(port)
					print "Packet Entering for Middlebox:",out_port
					self.send_openflow(dpid, bufid, buf, out_port, inport)
				pass
			pass
			function_ports = self._get_function_ports(dpid)# Packet is coming from the middlebox.
			nw_dst=flow['nw_dst']
			print "YYYYYYYYYYYYYYYYYYYYYY",nw_dst,inport
			if(inport in function_ports): # Packet is coming after processing. 
				#Lookup the original destination for the flow entering in the switch.
				# And send the flow to the output port.
    				if (_is_destination_attached(self,dpid,nw_dst)):
					out_port = self.get_dest_port_addr(dpid,nw_dst)
					print "XXXXXXXXXXXXXXXXXXXXXX",out_port 
					self.send_openflow(dpid, bufid, buf, out_port, inport)
 	elif(flow['dl_type'] == 2054): # ARP packets for updating 
		print "ARPPPP"
		self.forward_l2_packet(dpid,inport,packet,buf,bufid)
	else:#Flood it
        	self.send_openflow(dpid, bufid, buf, openflow.OFPP_FLOOD, inport)
	#self.topo.display_topology()
	#if(inport == 1):self.send_openflow(dpid, bufid, buf, 2, inport)
	#if(inport == 2):self.send_openflow(dpid, bufid, buf, 1, inport)

    # --
    # If we've learned the destination MAC set up a flow and
    # send only out of its inport.  Else, flood.
    # --
    def forward_l2_packet(self,dpid, inport, packet, buf, bufid):    
        dstaddr = packet.dst.tostring()
        if not ord(dstaddr[0]) & 1 and self.st[dpid].has_key(dstaddr):
            prt = self.st[dpid][dstaddr]
            if  prt[0] == inport:
                log.err('**warning** learned port = inport', system="pyswitch")
                self.send_openflow(dpid, bufid, buf, openflow.OFPP_FLOOD, inport)
            else:
                # We know the outport, set up a flow
                print 'installing flow for ' + str(packet), "pyswitch"
                flow = extract_flow(packet)
                flow[core.IN_PORT] = inport
                actions = [[openflow.OFPAT_OUTPUT, [0, prt[0]]]]
                self.install_datapath_flow(dpid, flow, CACHE_TIMEOUT, 
                                           openflow.OFP_FLOW_PERMANENT, actions,
                                           bufid, openflow.OFP_DEFAULT_PRIORITY,
                                           inport, buf)
        else:    
            # haven't learned destination MAC. Flood 
            self.send_openflow(dpid, bufid, buf, openflow.OFPP_FLOOD, inport)


	# --
	# Given a packet, learn the source and peg to a switch/inport 
	# --
    def do_l2_learning(self,dpid, inport, packet):
    	# learn MAC on incoming port
	srcaddr = packet.src.tostring()
	if ord(srcaddr[0]) & 1:
	    return
	#print self.st
	if self.st[dpid].has_key(srcaddr):
	    dst = self.st[dpid][srcaddr]
	    if dst[0] != inport:
	        log.debug('MAC has moved from '+str(dst)+'to'+str(inport), system='pyswitch')
	    else:
	        return
	else:
	    log.debug('learned MAC '+mac_to_str(packet.src)+' on %d %d'% (dpid,inport), system="pyswitch")
	
	# learn or update timestamp of entry
	self.st[dpid][srcaddr] = (inport, time(), packet)
	
	# Replace any old entry for (switch,mac).
	mac = mac_to_int(packet.src)


    def packet_in_callback(self, dpid, inport, reason, len, bufid, packet):
    	if not self.st.has_key(dpid):
        	log.debug('registering new switch %x' % dpid,system='pyswitch')
        	self.st[dpid] = {}
		# Needed by Topology
		self.topo.update_dpid(dpid,True)

    	if packet.type == ethernet.LLDP_TYPE:
        	return CONTINUE

        """Packet-in handler""" 
        if not packet.parsed:
            log.debug('Ignoring incomplete packet')
        else:
	    self.do_l2_learning(dpid,inport,packet)
            self.learn_and_forward(dpid, inport, packet, packet.arr, bufid)    

        return CONTINUE

    def datapath_leave_callback(self,dpid):
        logger.info('Switch %x has left the network' % dpid)
        if self.st.has_key(dpid):
            del self.st[dpid]
	    self.topo.update_dpid(dpid,False)
    
    def datapath_join_callback(self,dpid, stats):
        logger.info('Switch %x has joined the network' % dpid)
        logger.info('Switch %x has joined the network' % stats)


    def install(self):
        self.register_for_packet_in(self.packet_in_callback)
	# Registering for Req/Response, UDP Limited
        match_response = { core.DL_TYPE: ethernet.IP_TYPE,
                      core.NW_PROTO : ipv4.UDP_PROTOCOL,
                      core.TP_SRC : 53}
        self.register_for_packet_match(self.dns_handler.handle_dns_response, 0xffff, match_response)
    
    def getInterface(self):
        return str(pytutorial)

def getFactory():
    class Factory:
        def instance(self, ctxt):
            return pytutorial(ctxt)

    return Factory()

"""		
This class should be used to get the topology of the switches.
"""
class Topology():
	def __init__(self,discovery,topology):
		self.switch_dict = {}
		self.switch_table = defaultdict(list) # {key=dpid,value=[(dpid1,port1),(dpid2,port2)] 
		self._discovery = discovery
		self._topology = topology#pytopology
		print self._topology

	def update_dpid(self,dpid,join):
		if(join==True): #dpid is joining
			if not self.switch_dict.has_key(dpid):
				self.switch_dict[dpid] = time()
				
		else: #dpid is leaving
			if self.switch_list.has_key(dpid):
				del self.switch_list[dpid]
			else:
				raise Exception("Switch ",dpid," was not registered.")
			pass
		self._update_topology(dpid)

	def _get_dp_ports(self,dpid):
		return 48 # read them from the properties.

	def _update_topology(self,dpid):
		for dpid in self.switch_dict:
			for port in range(1,self._get_dp_ports(dpid)+1): # get the 
				if(self._discovery.is_switch_only_port(dpid,port)):
					print dpid, " is conneted with another switch on port: ",port
			pass
		print "DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
		for k,v in self._discovery.adjacency_list.iteritems():
			print "DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
			print k,v


	def display_topology(self):
		self.switch_dict = self._topology.get_datapaths()
		print "MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM"
		print self.switch_dict
		#for switch,neighbor_switches in self.switch_table.iteritems():
		#	print switch," is connected with: ",neighbor_switches 


# Correlate DNS information based on application ID.
# Use TTL to keep the record and then expire it. later on
class DNSHandler():
	def __init__(self):
		self.data = {}

    	def handle_dns_response(self, dpid, inport, ofp_reason, total_frame_len, buffer_id, packet):
        	dnsh = packet.find('dns')
        	if not dnsh:
        	    log.err('received invalid DNS packet',system='dnsspy')
        	    return CONTINUE
        	for answer in dnsh.answers:
            		if answer.qtype == dns.dns.rr.A_TYPE:
                		val = self.ip_records[answer.rddata]
                		if answer.name not in val:
                    			val.insert(0, answer.name)
                    			print "BILALBILALBILAL",answer.rddata, answer.name
		
