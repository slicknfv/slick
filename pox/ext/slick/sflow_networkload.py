import json
import signal
import sys
import os
import re
from sets import Set

import requests

from pox.core import core
from pox.lib.util import dpid_to_str

from slick.networkload import NetworkLoad
log = core.getLogger()

#LINK_USAGE_THRESHOLD = 0.2 # This is percentage.
LINK_USAGE_THRESHOLD = 80 # This is percentage.
MACHINE_USAGE_THRESHOLD = 80 # This is percentage.

class SFlowNetworkLoad(NetworkLoad):
    def __init__(self, controller):
        log.debug("sflow Network Load Collector.")
        NetworkLoad.__init__(self, controller)
        self._machine_load = {}         # machine mac -> MachineLoad
        self._elem_inst_load = {}       # element desc -> ElementLoad
        self._link_congestion = {}      # [mac,mac] -> LinkLoad
        # TODO read this from command line
        server_name = "localhost"
        port = 8008
        self.prev_dump_result = None
        self._sflow_rt_url = self._get_server_name(server_name, port)
        self._link_to_sflowid = { }
        # "http://localhost:8008/dump/ALL/ifinoctets;ifoutoctets;ifindex;ifinutilization;ifoperstatus/json"
        self.collector_query = None

    def _get_server_name(self, server_name , port ):
        sflow_rt_url = ""
        if not server_name:
            sflow_rt_url = 'http://localhost:8008'
            log.debug("sflow server not specified. Using %s as address.", sflow_rt_url)
        else:
            sflow_rt_url = "http://" + server_name + ":" + str(port)
        return sflow_rt_url


    def _collect_interface_utilization(self):
        """Function to collect link utilization from network.
        Args: None
        Returns: A map between:
        ifindices -> (incoming, outgoing) bandwidth in mbps.
        on each interface in mbps."""
        try:
            #"/dump/ALL/ifinoctets;ifoutoctets;ifindex;ifoperstatus/json"
            r = requests.get(self._sflow_rt_url + "/dump/ALL/ifinoctets;ifoutoctets/json")
        except:
            log.warn("There was an exception while sending the request to sflow collector.")
            return
        if r.status_code != 200:
            log.warn("Collecting interface utilization returned: %d",r.status_code)
            return
        dump_result = r.json()
        ifindices = { }
        if dump_result != self.prev_dump_result:
            for result in dump_result:
                if "dataSource" in result:
                    data_source = result["dataSource"]
                    ifindices[data_source] = None
            for interface in ifindices:
                data_source = None
                metric_name = None
                in_bytes_p_sec = 0
                out_bytes_p_sec = 0
                for result_dict in dump_result:
                    if "dataSource" in result_dict:
                        data_source = result_dict["dataSource"]
                        if data_source == interface:
                            if "metricName" in result_dict:
                                metric_name = result_dict["metricName"]
                                if metric_name == 'ifinoctets':
                                    if 'metricValue' in result_dict:
                                        metric_value = result_dict['metricValue']
                                        in_bytes_p_sec = int(metric_value)
                                if metric_name == "ifoutoctets":
                                    if 'metricValue' in result_dict:
                                        metric_value = result_dict['metricValue']
                                        out_bytes_p_sec = int(metric_value)
                            #print data_source, metric_name, in_bytes_p_sec, out_bytes_p_sec
                        else:
                            continue
                # http://www.cisco.com/en/US/tech/tk648/tk362/technologies_tech_note09186a008009496e.shtml
                ifindices[interface] = (float(in_bytes_p_sec*8)/(1024*1024), float(out_bytes_p_sec*8)/(1024*1024))
                #ifindices[interface] = (float(in_bytes_p_sec), float(out_bytes_p_sec))
            return ifindices
        else:
            return None

    def _sflow_ifindex_to_of_port(self):
        """Copied from example of sflow-rt.
        Return:
            sflow interface index -> (switch_name, port_num)"""
        ifindexToPort = {}
        path = '/sys/devices/virtual/net/'
        for child in os.listdir(path):
          parts = re.match('(.*)-(.*)', child)
          if parts == None: continue
          ifindex = open(path+child+'/ifindex').read().split('\n',1)[0]
          ifindexToPort[ifindex] = {'switch':parts.group(1),'port':child}
        return ifindexToPort

    def _get_mb_capacity(self, mb_machine_mac):
        # This value depends on the middlebox machine capacity
        # and it can be updated based on the profiling agent t
        # that keeps track of intake and outtake bandwidth of the middlebox
        # machine to keep track of maximum load that can processed by the
        # middlebox machine.
        MAX_MB_BANDWIDTH = 1 # Mbps
        return MAX_MB_BANDWIDTH

    def get_loaded_elements(self):
        loaded_element_descs = [ ]
        loaded_macs = self.get_loaded_middleboxes ( )
        for mac in loaded_macs:
            # Get all the elements that are on the machine.
            element_descs = self.controller.elem_to_mac.get_elem_descs(mac)
            # For now we are assuming the limit of one element instance per middlebox machine.
            # Since we cannot get the element load on mininet for this we need to modify hsflowd
            # and add support for reading resource information for cgroups.
            # Or we need to have support for /proc in mininet.
            # Because of this limitation
            # we approximate the load on element with load on middlebox machine.
            if len(element_descs):
                loaded_element_descs.append(element_descs[0])
        return loaded_element_descs

    def get_loaded_middleboxes(self):
        """Return the list of overloaded middleboxes based on traffic 
        inflow and outflow from the port connected with the middlebox machine.
        """
        log.debug("Getting Loaded Middleboxes")
        # Mbps differential before calling it overloaded.
        processing_delta = 0.25
        # List of overloaded middlebox mac addresses.
        overloaded_middleboxes = [ ]
        link_util = { }
        # MB mac -> MB location.(dpid, port)
        middleboxes = { }
        ifindex_to_port = { }
        if_utilization_mbps = self._collect_interface_utilization()
        if not if_utilization_mbps:
            return link_util
        mb_mac_list = self.controller.get_all_registered_machines()
        for mac in mb_mac_list:
            try:
                middleboxes[mac] =  self.controller.network_model.get_host_loc(mac)
            except KeyError as ke:
                print ke
        ifindex_to_port = self._sflow_ifindex_to_of_port()
        for mb_mac, mb_loc in middleboxes.iteritems():
            mb_sflow_ifindex = self._get_interface_index(ifindex_to_port, mb_loc)
            if mb_sflow_ifindex in if_utilization_mbps:
                # Here interface's outoctects are inoctects for the middlebox machine
                # and inoctects of interface are the outoctects for the middlebox.
                mb_intake = if_utilization_mbps[mb_sflow_ifindex][1]
                mb_outtake = if_utilization_mbps[mb_sflow_ifindex][0]
                #if abs(mb_outtake - mb_instake) > processing_delta:
                #    overloaded_middleboxes.append(mb_mac)
                mb_capacity = self._get_mb_capacity(mb_mac)
                mb_usage = (float(mb_intake)/mb_capacity)*100
                print mb_mac, mb_usage
                if (mb_usage > MACHINE_USAGE_THRESHOLD):
                    overloaded_middleboxes.append(mb_mac)
        #for mb in overloaded_middleboxes:
        #    print mb
        return overloaded_middleboxes

    def _get_interface_index(self, ifindex_to_port, interface):
        """ ifindex_to_port dictionary.
        interface is a pair (switch_name, port_number)
        {"38056": {"switch": "s4", "port": "s4-eth2"}}
        """
        switch_dpid = interface[0]
        switch_port_num = int(interface[1])
        for ifindex, link_dict in ifindex_to_port.iteritems():
            switch_name = link_dict["switch"]
            port_interface = link_dict["port"]
            dpid = re.findall(r'\d+',switch_name)
            port_numbers = port_interface.split('-')
            port_number = re.findall(r'\d+', port_numbers[1])
            if (len(dpid) == 1 and len(port_number) == 1):
                if (int(dpid[0]) == switch_dpid) and (int(port_number[0]) == switch_port_num):
                    return ifindex

    def _collect_link_utilization(self):
        """
        Return a dict:
            Key= Link
            Value: Bandwidth Utilization.
        """
        link_util = { }
        if_utilization_mbps = self._collect_interface_utilization()
        if not if_utilization_mbps:
            return link_util
        ifindex_to_port = self._sflow_ifindex_to_of_port()
        #print if_utilization_mbps
        #print ifindex_to_port
        links = core.openflow_discovery.adjacency
        for link, _ in links.iteritems():
            intf1 = (link.dpid1, link.port1)
            intf2 = (link.dpid2, link.port2)
            sflow_ifindex1 = self._get_interface_index(ifindex_to_port, intf1)
            sflow_ifindex2 = self._get_interface_index(ifindex_to_port, intf2)
            if (sflow_ifindex1 in if_utilization_mbps) and (sflow_ifindex2 in if_utilization_mbps):
                #print sflow_ifindex1, sflow_ifindex2
                #print if_utilization_mbps[sflow_ifindex1], if_utilization_mbps[sflow_ifindex2]
                # For the bandwidth on a link between
                # (dpid1=3, port1=3) -> (dpid2=2, port2=1)
                # intf1 -> intf2
                # Find max(out_bytes_p_sec_intf1, in_bytes_p_sec_intf2)
                link_bandwidth = max(if_utilization_mbps[sflow_ifindex1][1], if_utilization_mbps[sflow_ifindex2][0])
                link_util[link] = link_bandwidth # , sflow_ifindex1, sflow_ifindex2
        switch_names = self.controller.network_model.get_all_forwarding_device_names()
        if len(links) != len(link_util):
            log.warn("Not all links' utilization was collected.")
        return link_util

    def _get_link_capacity(self, link):
        # This value depends on the mininet parameters.
        # On custom topology it will not be fixed so please be careful
        MAX_LINK_BANDWIDTH = 1 # Mbps
        return MAX_LINK_BANDWIDTH

    def get_congested_links(self):
        # Get latest links.
        log.debug("Getting Congested Links")
        congested_links = [ ]
        link_util = self._collect_link_utilization()
        for link, util in link_util.iteritems():
            link_capacity = self._get_link_capacity(link)
            link_usage = (float(util)/link_capacity)*100
            if (link_usage > LINK_USAGE_THRESHOLD):
                congested_links.append(link)
        return congested_links

    def get_link_utilizations(self):
        # Return percent utilization of the links.
        # link -> %_utilization
        link_utils = {}
        link_util = self._collect_link_utilization()
        for link, util in link_util.iteritems():
            link_capacity = self._get_link_capacity(link)
            link_usage = (float(util)/link_capacity)*100
            link_utils[link] = link_usage
        return link_utils

    def get_element_load(self, ed):
        element_load = ElementLoad()
        return element_load

    def get_link_load(self, link):
        """Given the link return the Link Load."""
        link_load = LinkLoad()
        return link_load

    def get_machine_load(self, machine_id):
        if machine_id not in self._machine_load:
            machine_load = MachineLoad(machine_id)
        return machine_load


    def _update_element_instance_load(self, ed, flow):
        if ed not in self._elem_inst_load:
            elem_instance_load = ElementLoad(ed)
            elem_instance_load.num_flows += 1
            self._elem_inst_load[ed] = elem_instance_load

class MachineLoad(object):
    def __init__(self, mac):
        self.mac = mac
        self.cpu_percent = 0
        self.net_io_percent = 0
        self.mem_percent = 0

class ElementLoad(object):
    def __init__(self, ed):
        self.ed = ed
        self.cpu_percent = 0
        self.net_io_percent = 0
        self.mem_percent = 0

class LinkLoad(object):
    def __init__(self, link):
        # link = (src_mac, dst_mac)
        self.link = link
        self.link_capacity = None
        self.link_bandwidth = None
