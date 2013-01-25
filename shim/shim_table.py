# Reusing code from controller side.
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
        are required to add,del,and modify flows and their corresponsing actions.
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

    def init_tuples(self):
        f = self.FlowTuple(in_port=None,dl_src=None,dl_dst=None,dl_vlan=None,dl_vlan_pcp=None,dl_type= None,nw_src=None,nw_dst=None,nw_proto=None,tp_src=None,tp_dst=53) # For outgoing
        rf = self.FlowTuple(in_port=None,dl_src=None,dl_dst=None,dl_vlan=None,dl_vlan_pcp=None,dl_type= None,nw_src=None,nw_dst=None,nw_proto=None,tp_src=53,tp_dst=None) # For incoming.
        self.flow_to_function_mapping[f] = {1:"DNS"}
        self.flow_to_function_mapping[rf] = {1:"HTTP"}
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

