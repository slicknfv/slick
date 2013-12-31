import os,sys
import logging
from time import time
from socket import htons
from struct import unpack
from collections import defaultdict
from collections import namedtuple
from collections import OrderedDict
from sets import Set

from conf import *
from utils.packet_utils import *
import slick_exceptions

"""
This file defines several classes that the controller uses to maintain state
about elements and applications:

    ElementToMac - maps an element instance (identified by its element
                   descriptor) to its location in the network

    MacToIP - maps MAC addresses the controller has learned about to their IP
              addresses

    FlowToElementsMapping - maps flow spaces to the elements that should be
                            applied to flows in that space

    ElementToApplication - maintains a mapping between elements and the apps
                           who own them
"""

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

    def add(self, machine_mac, element_desc):
        """IP address should be a string and element_desc is an integer.
        machine_mac: 
            MAC Address in the string format.
        element_desc:
            integer value.
        Returns:
            None
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

    def get_elem_descs(self, mac_addr):
        """Given mac address return all the element descriptors for the element_machine.

        Args:
            mac_addr:
                MAC address of element machine.
        Returns:
            List of element descriptors.
        Throws:
            KeyError if the mac addres is not found.
        """
        if mac_addr in self._mac_to_elems:
            return self._mac_to_elems[mac_addr]
        else:
            raise KeyError("Unable to find the mac addr in mac to element mapping.")

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

        # Earlier it was: FlowTuple -> {elem_desc:element_name}
        # Keys map to an OrderedDict of element_names
        # Single Table entry looks like this:
        # FlowTuple -> {element_name1: [e_11,e12,...], element_name2: [e_21, e22...]}
        # key:FlowTuple value:{element_name1: [e_11,e12,...], element_name2: [e_21, e22...]}
        #   where e_11, e_21 etc. are of type ElementInstance
        #   Limitation: This assumes that a single flow will be subjected to one type
        #               of element in one chain. For example it can be 
        #               subjected to LoadBalancer once in a chain.
        self.flow_to_element_mapping = defaultdict(list)
        self.flow_to_element_instance_mapping = defaultdict(list)

    """
     These three functions: 
        add_flow,del_flow,modify_flow 
        are required to add,del,and modify flow policies.
     A compiler that parses policy language and generates these flow to function mappings.
	# Given a in_port,flow and dictionary of functions{key=number:value=function_name}
    """
    # TODO in_port is always None
    def add_element(self,in_port,flow, element_instance):
        """This function is called to assign 
        and element to a flow."""
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
        element_name = element_instance.name
        if not self.flow_to_element_mapping.has_key(f):
            self.flow_to_element_mapping[f] = [element_name]#OrderedDict({element_name: [element_instance]})#append(element_instance)
            return True
        else: # we already have a flow
            if element_name not in self.flow_to_element_mapping[f]:
                self.flow_to_element_mapping[f].append(element_name)
            else:
                # We have a replica being create by application.
                # Therefore we don't add any new element_name.
                pass 
            return True

    def add_element_instance(self,in_port,flow, element_instance):
        """Once a new element instance is created we need to call
        this function."""
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
        element_name = element_instance.name
        if not self.flow_to_element_instance_mapping.has_key(f):
            self.flow_to_element_instance_mapping[f] = [element_instance]
            return True
        else: # we already have a flow
            self.flow_to_element_instance_mapping[f].append(element_instance)
            return True

    # Given an in_port,flow and dictionary of functions{key=number:value=function_name}
    # TODO this is not getting called anywhere, but should once we add the ability to remove elements
    def remove_flow(self, in_port, flow):
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
        if (self.flow_to_element_mapping.has_key(f)):
            del self.flow_to_element_mapping[f]
            del self.flow_to_element_instance_mapping[f]
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
    def _lookup_elements(self, inport, flow):
        """Given flow return the list of element names
        that correspond to the flow. This is an ordered list. """
        ft = self.get_flow_tuple(inport, flow)
        for item in self.flow_to_element_mapping:
            if(_flowtuple_equals(item,ft)):
                return self.flow_to_element_mapping[item]
        return [ ]

    def lookup_element_instances(self, inport, flow):
        """Given flow return the list of element instances
        that correspond to the flow."""
        ft = self.get_flow_tuple(inport, flow)
        for item in self.flow_to_element_instance_mapping:
            if(_flowtuple_equals(item, ft)):
                return self.flow_to_element_instance_mapping[item]
        return [ ]

    def get_flow_tuple(self, inport, flow):
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
        return f
    # Function that returns the corresponding element_desc lists to the flow(in order).
    # Returns:
    # [[e11,e12], [e21,e22,...], ...]
    # 
    def get(self,inport,flow):
        """Given the flow return the ordered list of element instances for 
        a given flow."""
        # Based on the flow figure out the functions and then return a list of functipons available on the port.
        element_names = self._lookup_elements(inport, flow)
        element_instances = self.lookup_element_instances(inport, flow)
        replica_sets = [ ]
        index = 0
        for e_name in element_names:
            replica_sets.append([ ])
            for elem_inst in element_instances:
                if elem_inst.name == e_name:
                    replica_sets[index].append(elem_inst.elem_desc)
            index += 1
        return replica_sets

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

        #print self.flow_to_element_mapping
        for item in self.flow_to_element_mapping.keys():
            if(_flowtuple_equals(item, ft)):
                return item
        return None

    def get_element_flow(self, ed):
        """Given the element descriptor integer return the corresponding flow.
        Args:
            ed = element_descriptor
        Returns:
            flow dictionary
        """
        for flowtuple, element_instance_list in self.flow_to_element_instance_mapping.iteritems():
            for e_inst in element_instance_list:
                if e_inst.elem_desc == ed:
                    flow = {
                             'dl_src':          flowtuple.dl_src,
                             'dl_dst':          flowtuple.dl_dst,
                             'dl_vlan':         flowtuple.dl_vlan,
                             'dl_vlan_pcp':     flowtuple.dl_vlan_pcp,
                             'dl_type':         flowtuple.dl_type,
                             'nw_src':          flowtuple.nw_src,
                             'nw_dst':          flowtuple.nw_dst,
                             'nw_proto':        flowtuple.nw_proto,
                             'tp_src':          flowtuple.tp_src,
                             'tp_dst':          flowtuple.tp_dst
                           }
                    return flow



"""
This class maintains a mapping between elements and the apps who own them
"""
class ElementToApplication():
    def __init__(self):
        # ed -> (application_object, app_desc, parameter_dict)
        self.application_handles = {}

    """TODO: This is inefficient memory wise to store parameters and controller parameters
    for each element descriptor.

    parameter and controller_param are specific to each element_name in one application id. 
    So for a given application and given element the parameter and controller_parameter are
    the same over a period a of time."""
    def update(self, ed, application_object, app_desc, parameter, controller_param):
        if not (self.application_handles.has_key(ed)):
            self.application_handles[ed] = (application_object, app_desc, parameter, controller_param) 
        else:
            print "ERROR: This should not happen"

    def get_elem_parameters(self, ed):
        """Given an element descriptor return the parameters passed to it.
        """
        if (self.application_handles.has_key(ed)):
            return self.application_handles[ed][2] 
        else:
            logging.error("No application for the element with element descriptor:", ed)
            raise slick_exceptions.InstanceNotFound("No parameters for element descriptor %d", ed)

    def get_app_handle(self, ed):
        """Given an element descriptor return the application handle.
        """
        if (self.application_handles.has_key(ed)):
            return self.application_handles[ed][0]
        else:
            logging.error("No application for the element with element descriptor:", ed)
            raise slick_exceptions.InstanceNotFound("No application handle for element descriptor %d", ed)

    def get_app_desc(self, ed):
        """Given an element descriptor return the application descriptor.

        Args:
            ed: Element descriptor
        Returns:
            Application descriptor
        """
        if (self.application_handles.has_key(ed)):
            return self.application_handles[ed][1]
        else:
            print "ERROR: There is no application for the function descriptor:",ed
            return None

    def contains_app(self, app_desc):
        """Return True if app_desc is registered as application.

        Args:
            app_desc =  Application descriptor to check its installation.
        Returns:
            True/False
        """
        for _, app in self.application_handles.iteritems():
            if(app[1] == app_desc):
                return True
        return False

    def get_app_descs(self):
        """Return Set([ ]) of all app descs."""
        app_descs = Set([ ])
        for ed, app in self.application_handles.iteritems():
            app_descs.add(app[1])
        return app_descs

    def get_controller_params(self, ed):
        """Given the element descriptor return the controller params dict."""
        if (self.application_handles.has_key(ed)):
            return self.application_handles[ed][3] 
        else:
            logging.error("No application for the element with element descriptor:", ed)
            raise slick_exceptions.InstanceNotFound("No parameters for element descriptor %d", ed)

class FlowAffinity():
    def __init__(self):
        self.flow_to_ed_mapping = { }

    def add_flow_affinity(self, flow, ed):
        src_ip = flow.nw_src
        self.flow_to_ed_mapping[src_ip] = ed

    def get_element_desc(self, flow):
        src_ip = flow.nw_src
        if src_ip in self.flow_to_ed_mapping:
            return self.flow_to_ed_mapping[src_ip]
        else:
            return None

    def dump(self):
        for flow, ed in self.flow_to_ed_mapping.iteritems():
            print flow, ed
