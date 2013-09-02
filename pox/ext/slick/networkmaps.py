import os,sys
import logging
from time import time
from socket import htons
from struct import unpack
from collections import defaultdict
from collections import namedtuple

from conf import *
from utils.packet_utils import *

"""
	This class maps an element descriptor (an element instance) to where it's installed (a mac address)

    (old comment):
    There needs to be a mapping between:
        machine location [dpid,port] -> Machine IP addresses.
        machine IP addresse -> function descriptor.

        This code assumes one IP address per port.
"""
class ElementToMac():
    def __init__(self):
        self._mac_to_elems = defaultdict(list) # Machine MAC Address to function descriptor mapping, if the list is empty then we have shim only.

    def add(self, ip_addr, machine_mac, element_desc):
        """IP address should be a string and element_desc is an integer.
        """
        if (machine_mac == None):
            return

        if((element_desc != None)):
            self._mac_to_elems[machine_mac].append(element_desc)
            logging.info("_mac_to_elems: populating existing %s", self._mac_to_elems)
        else:
            logging.info("_mac_to_elems: Creating New %s",self._mac_to_elems)
            self._mac_to_elems[machine_mac] = [ ]

    def remove(self, element_desc):
        if(element_desc != None):
            if(element_desc in self._mac_to_elems[mac_addr]):
                self._mac_to_elems[mac_addr].remove(element_desc)
                return True
            else:
                logging.warn("Element descriptor does not exist:", element_desc)
                return False

    def get(self, element_desc):
        """Given the element desc. return the mac address.

        Args:
              element_desc: Element descriptor assidned for the element instance.
        Returns:
              MAC address at which the element instance exists.
        [used by configure function]
        """
        for mac_addr in self._mac_to_elems:
            if(element_desc in self._mac_to_elems[mac_addr]):
                return mac_addr


    """Returns the shim machine with the mac_addr
        Args:
            element_name: name of the element, eg, Drop, Noop etc.
        Returns:
            mac addr of the machine that has the element instance for element_name.
    """
    """
    # TODO this is no longer needed; it's handled by the Placement module
    def get_machine_for_element(self, element_name):
        element_spec = self.element_specs.get_element_spec(element_name)
        for mac_addr in self._mac_to_elems:
            if(mac_addr != None):
                # TODO: Add recurrent optimization algorithm call here.
                if (len(self._mac_to_elems[mac_addr]) < MAX_FUNCTION_INSTANCES): # 10 functions can be added per machine.
                    return mac_addr
    """

"""
	This class provides a mapping from a mac address to an IP address

    This code assumes one IP address per port.
"""
class MacToIP():
    def __init__(self):
        self._mac_to_ip = {} # Key= MAC -> ip_address

    def add(self, machine_mac, ip_addr):
        if(ip_addr != None):
            if (not self._mac_to_ip.has_key(machine_mac)):
                self._mac_to_ip[machine_mac] = ip_addr

    def get(self, mac):
        if(mac != None):
            return self._mac_to_ip[mac]

    def get_all_macs(self):
        return self._mac_to_ip.keys()


"""
    A helper function to allow flowtuple comparisons with "wildcards" (None)
"""
def _flowtuple_equals (ft1, ft2):
    return ((ft1.in_port == None or     ft1.in_port == ft2.in_port) and
            (ft1.dl_src == None or      ft1.dl_src == ft2.dl_src) and
            (ft1.dl_dst == None or      ft1.dl_dst == ft2.dl_dst) and
            (ft1.dl_vlan == None or     ft1.dl_vlan == ft2.dl_vlan) and
            (ft1.dl_vlan_pcp == None or ft1.dl_vlan_pcp == ft2.dl_vlan_pcp) and
            (ft1.dl_type == None or     ft1.dl_type == ft2.dl_type) and
            (ft1.nw_src == None or      ft1.nw_src == ft2.nw_src) and
            (ft1.nw_dst == None or      ft1.nw_dst == ft2.nw_dst) and
            (ft1.nw_proto == None or    ft1.nw_proto == ft2.nw_proto) and
            (ft1.tp_src == None or      ft1.tp_src == ft2.tp_src) and
            (ft1.tp_dst == None or      ft1.tp_dst == ft2.tp_dst))


"""
TODO: Policy Overlap and Union of actions.
TODO: Policy Conflict and pick them up based on some user defined criteria, 
security over performance. Or throughput over latency.
	Description: 
		Keeps a flow to function mapping.
"""

class FlowToElementsMapping():
    def __init__(self):
        self.FlowTuple = namedtuple("FlowTuple",
                                       ["in_port",
                                        "dl_src",
                                        "dl_dst",
                                        "dl_vlan",
                                        "dl_vlan_pcp",
                                        "dl_type",
                                        "nw_src",
                                        "nw_dst",
                                        "nw_proto",
                                        "tp_src",
                                        "tp_dst"])
        self.flow_to_function_mapping = defaultdict(dict) # key:FlowTuple value:{functions}
    
    """
     These three functions: 
        add_flow,del_flow,modify_flow 
        are required to add,del,and modify flow policies.
     A compiler that parses policy language and generates these flow to function mappings.
	# Given a in_port,flow and dictionary of functions{key=number:value=function_name}
    """
    # TODO in_port is always None
    # TODO 'functions' should be an array (though that doesn't seem to change the code here)
    # XXX Note that 'functions' is now a dictionary of {elem_desc : elem_name}
    def add(self,in_port,flow,functions):
        src_mac =None
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
        if not self.flow_to_function_mapping.has_key(f):
            self.flow_to_function_mapping[f] = functions    # TODO this needs to support taking multiple functions
            #print self.flow_to_function_mapping
            return True
        else:
            return False


	# Given a in_port,flow and dictionary of functions{key=number:value=function_name}
    # TODO this is not getting called anywhere, but should once we add the ability to remove elements
    def remove(self,in_port,flow):
        src_mac = mac_to_int(flow['dl_src'])
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
        if (self.flow_to_function_mapping.has_key(f)):
        	del self.flow_to_function_mapping[f]
        	return True
        else:
        	return False

    # TODO This should probably happen at some point, but it's not
    def modify(self,in_port,flow,elements):
        if(remove(in_port, flow)):
            return add(in_port, flow, elements)
        return False


    # TODO this should be elsewhere; it's not getting used for now
    # TODO This may be useful for bidrectional affinity
    def get_reverse_flow(self, flow):
        """
        Reverses the flow description of the given flow.

        This is the formula used:
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

        Returns:
            flow dict.
        """
        reverse_flow = self.FlowTuple(in_port = None,
                            dl_src = flow.dl_dst,
                            dl_dst = flow.dl_src,
                            dl_vlan = flow.dl_vlan,
                            dl_vlan_pcp = flow.dl_vlan_pcp,
                            dl_type = flow.dl_type,
                            nw_src = flow.nw_dst,       # Swap
                            nw_dst = flow.nw_src,       # Swap
                            nw_proto = flow.nw_proto,
                            tp_src = flow.tp_dst,       # Swap
                            tp_dst = flow.tp_src)       # Swap
        return reverse_flow
    """
        TODO:
            Add lookup code from file: ofmatch.py in project openfaucet.
        Dummy matching function returns True if the first wild card entry matches.
    """
    def _lookup(self,ft):
        for item in self.flow_to_function_mapping:
            if(_flowtuple_equals(item,ft)):
                return self.flow_to_function_mapping[item]
        return {}

    # Function that returns the corresponding functions dict to the flow.
    def get(self,inport,flow):
        # Based on the flow figure out the functions and then return a list of functipons available on the port.
        src_mac = mac_to_int(flow.dl_src.toRaw())
        dst_mac = mac_to_int(flow.dl_dst.toRaw())
        f = self.FlowTuple(in_port=inport,
                           dl_src=src_mac,
                           dl_dst=dst_mac,
                           dl_vlan=flow.dl_vlan,
                           dl_vlan_pcp=flow.dl_vlan_pcp,
                           dl_type= flow.dl_type,
                           nw_src=flow.nw_src,
                           nw_dst=flow.nw_dst,
                           nw_proto=flow.nw_proto,
                           tp_src=flow.tp_src,
                           tp_dst=flow.tp_dst)
        function_dict = self._lookup(f)
        if(len(function_dict) > 0):
        	return function_dict
        else:
        	return function_dict

    # Returns a matching flow of type ofp_match
    # else returns a None
    def get_matching_flow(self,in_flow):
        src_mac = in_flow.dl_src
        dst_mac = in_flow.dl_dst
        ft = self.FlowTuple(in_port=in_flow.in_port,
                           dl_src=src_mac,
                           dl_dst=dst_mac,
                           dl_vlan=in_flow.dl_vlan,
                           dl_vlan_pcp=in_flow.dl_vlan_pcp,
                           dl_type= in_flow.dl_type,
                           nw_src=in_flow.nw_src,
                           nw_dst=in_flow.nw_dst,
                           nw_proto=in_flow.nw_proto,
                           tp_src=in_flow.tp_src,
                           tp_dst=in_flow.tp_dst)

        #print self.flow_to_function_mapping
        for item in self.flow_to_function_mapping.keys():
            if(_flowtuple_equals(item, ft)):
                return item
        return None
