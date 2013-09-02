# Reusing code from controller side.
from collections import namedtuple
#from collections import defaultdict
from collections import OrderedDict
import struct 
import socket
"""
TODO: Policy Overlap and Union of actions.
TODO: Policy Conflict and pick them up based on some user defined criteria, security over performance. Or throughput over latency.
"""

def mac_to_int(mac):
    value = 0
    for byte in struct.unpack('6B', mac):
        value = (value << 8) | byte
    return long(value)

def ipstr_to_int(a):
    octets = a.split('.')
    return int(octets[0]) << 24 |\
           int(octets[1]) << 16 |\
           int(octets[2]) <<  8 |\
           int(octets[3]);
"""
	Description: 
		Keeps a flow to function mapping.
"""
class ShimTable():
    def __init__(self):
        self.FlowTuple = namedtuple("FlowTuple",["in_port","dl_src","dl_dst","dl_vlan","dl_vlan_pcp","dl_type","nw_src","nw_dst","nw_proto","tp_src","tp_dst"])
        self.flow_to_function_mapping = OrderedDict() # key:FlowTuple value:[functions]
    
    #return named tuple.
    def convert_flow(self,in_port,flow):
        if(len (flow) != 11):
            return None
        src_mac = None
        dst_mac = None
        if(flow['dl_src'] != None):
            src_mac = mac_to_int(flow['dl_src'])
        if(flow['dl_dst'] != None):
            dst_mac = mac_to_int(flow['dl_dst'])
        f = self.FlowTuple(in_port=in_port,
                           dl_src=src_mac,
                           dl_dst=dst_mac,
                           dl_vlan=flow['dl_vlan'],
                           dl_vlan_pcp=flow['dl_vlan_pcp'],
                           dl_type= flow['dl_type'],
                           nw_src=flow['nw_src'],
                           nw_dst=flow['nw_dst'],
                           nw_proto=flow['nw_proto'],
                           tp_src=flow['tp_src'],
                           tp_dst=flow['tp_dst'])
        return f
    """
     These three functions: 
        add_flow,del_flow
        are required to add,del flows and corresponsing actions.
    """
    def add_flow(self, in_port, flow, ed):
        flow['in_port'] = 0#hack, send 11 tuples from start i.e. at controller.
        f = self.convert_flow(in_port,flow)
        if(f == None):
            return False
        # TypeError: unhashable type: 'array.array'
        if not self.flow_to_function_mapping.has_key(f):
            self.flow_to_function_mapping[f] = [ed]
            return True
        else:
            # Same flow needs to be processed by multiple element instances.
            self.flow_to_function_mapping[f].append(ed)
            return True

    # Given a in_port,flow and dictionary of functions{key=number:value=function_name}
    def del_flow(self, in_port, flow):
        f = self.convert_flow(in_port, flow)
        if(f == None):
            return False
        if (self.flow_to_function_mapping.has_key(f)):
            del self.flow_to_function_mapping[f]
            return True
        else:
            return False

    """
        Dummy matching function returns True if the first wild card entry matches.
    """
    def lookup_flow(self,flow):
        result_list = []
        in_port = 0
        ft = self.convert_flow(in_port,flow)
        if(ft == None):
            return None
        for item in self.flow_to_function_mapping:
            item_match = False
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
            	if(item.nw_src == ipstr_to_int(ft.nw_src)):
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
                result_list.append(item)
            pass
        if(len(result_list) > 0):
            if(len(result_list) > 1):
                print "RESULT LIST IS BIG"
            flow_tuple = result_list[-1] # Since we have ordered list.
            return self.flow_to_function_mapping[flow_tuple]
        return None

