import struct
from collections import defaultdict
from sets import Set

from pox.core import core
# This is required as l2_multi_slick as MACs as 00-00-00-xx-xx-xx
# instead of 00:00:00:xx:xx:xx
import string

from msmessageproc import MSMessageProcessor

import networkx as nx

log = core.getLogger()

# Modifying the already available utility function from here:
# from pox.lib.util import dpid_to_str
def dpid_to_str (dpid, separator, alwaysLong = False):
  """
  Convert a DPID from a long into into the canonical string form.
  dpid: is the mac address
  separator: is the separator to be used for mac fields. e.g, ':' or '-'
  """
  if type(dpid) is long or type(dpid) is int:
    # Not sure if this is right
    dpid = struct.pack('!Q', dpid)
  assert len(dpid) == 8
  r = separator.join(['%02x' % (ord(x),) for x in dpid[2:]])
  if alwaysLong or dpid[0:2] != (b'\x00'*2):
    r += '|' + str(struct.unpack('!H', dpid[0:2])[0])
  return r

class LinkWeight(object):
    """This is the overlay link weight class.

    It can have different properties that can be 
    read from different slick modules and updated here
    to be served to Steering and placement modules.
    """
    def __init__(self, hop_count=None, bandwidth=None, latency=None):
        # Physical hop count that corresponds to virtual
        # overlay link.
        self.hop_count = hop_count
        self.avail_bandwidth = bandwidth
        self.latency = latency

    def __str__(self):
        s = 'phsyical_hop_count: ' + str(self.physical_hop_count) + ' avail_bandwidth: ' + str(self.avail_bandwidth) + ' latency: ' + str(self.latency)
        return s

class OverlayNetwork(object):
    def __init__(self, controller):
        self.controller = controller
        # Register listeners
        core.listen_to_dependencies(self)
        core.openflow.addListenerByName("ConnectionUp", self._handle_ConnectionUp)
        core.openflow.addListenerByName("ConnectionDown", self._handle_ConnectionDown)
        self.controller.ms_msg_proc.addListenerByName("ElementMachineUp", self._handle_ElementMachineUp)
        self.controller.ms_msg_proc.addListenerByName("ElementMachineDown", self._handle_ElementMachineDown)
        self.controller.ms_msg_proc.addListenerByName("ElementInstanceEvent", self._handle_ElementInstanceEvent)
        # Required to detect edge vs non-edge switches.
        # To keep track of middlebox machine location.
        core.host_tracker.addListenerByName("HostEvent", self._handle_host_tracker_HostEvent)

        # Data Structures.
        # Overlay Graph
        self.overlay_graph_nx = nx.Graph( )
        self.overlay_graph = defaultdict(Set) 
        # Set of Edge switches. This set is used to add edges.
        self.edge_switches = Set([ ])
        # Set of switches that have element machines attached to them.
        self.element_switches = Set([ ])
        # Set of all the switches in the network.
        self.switches = Set([ ])
        # List of MACs that are currently hosting the middleboxes.
        self.element_machines = Set([ ])
        # Keep track of hosts attached to the switches
        # This allows us to see which switch is attached to which MB machine.
        # mac -> (dpid, port)
        self.hosts = { }
        # Map of switch to middlebox element IDs.
        # so that we know when to remove the element_machine_switch
        # from the overlay graph.
        # dpid -> element descriptors.
        self.switch_to_elem_desc = defaultdict(list)

    def _handle_host_tracker_HostEvent(self, event):
        """Given the host join/leave event update the self.hosts map.
        Args:
            event: HostEvent
        Returns:
            None
        """
        host = str(event.entry.macaddr)
        #print host, type(host)
        switch = event.entry.dpid
        port = event.entry.port
        if event.leave:
            if host in self.hosts:
                del self.hosts[host]
        else:
            if host not in self.hosts:
                self.hosts[host] = (switch, port)
                if switch not in self.switches:
                    log.warn("Missing switch")

    def _handle_ConnectionUp(self, event):
        # Only keep switches in the graph that are edge switches
        # or middlebox machines.
        self.switches.add(event.dpid)

    def _handle_ConnectionDown(self, event):
        # Since we only keep switches in the graph that are edge switches
        # lets try not to remove switches that are not edge switches.
        self.switches.remove(event.dpid)

    def _handle_ElementMachineUp(self, event):
        self.element_machines.add(event.mac)

    def _handle_ElementMachineDown(self, event):
        self.element_machines.remove(event.mac)

    def _handle_ElementInstanceEvent(self, event):
        """Based on the event type add/remove/move the edge in the 
        overlay network.

        Raises:
            AssertionError: If required fields of the event are not set."""
        if event.created:
            self._add_element_machine(event.mac)
        elif event.destroyed:
            self._remove_element_machine(event.mac)
        elif event.moved:
            #TODO: self._move_element_machine(event.mac)
            pass
        else:
            raise AssertionError('Event raised without setting the event type.')

    def _update_edge_switches (self):
        """ This function should be called once we have 
        adjacency matrix build up in openflow_discovery."""
        for dpid in self.switches:
            if self._edge_switch(dpid):
                self.edge_switches.add(dpid)
            else:
                # dpid is not an edge switch.
                if dpid in self.edge_switches:
                    self.edge_switches.remove(dpid)

    def _add_element_machine(self, node_mac):
        """Given the element machine mac add it to the overlay graph.

        This function will be called multiple times
        for same middlebox machine.
        """

        # Create the list of edge switches
        # based on _edge_switch function.
        # We wait until an element_machine is registered
        # so that all the LinkEvents are in, to build the adjacency matrix 
        # in openflow_discovery.
        self._update_edge_switches()
        if node_mac in self.element_machines:
            elem_switch_mac = self._get_connected_switch(node_mac)
            # Add the switch to list of element switches
            self.element_switches.add(elem_switch_mac)
            # Update the overlay graph.
            self._update_overlay_graph()
            """
            print "X"*100
            print self.edge_switches
            print self.element_switches
            print self.overlay_graph
            print self.overlay_graph_nx.nodes()
            print self.overlay_graph_nx.edges()
            print "X"*100"""


    def _update_overlay_graph(self):
        """Update the overlay graph."""
        from slick.l2_multi_slick import switches
        # Maintain weights between the switches.
        for row_mac, row_switch in switches.iteritems():
            for col_mac, col_switch in switches.iteritems():
                # The network is between edge_switches and element_switches
                if (((row_mac in self.edge_switches) and (col_mac in self.edge_switches)) or # Make sure to add edge switches.
                    ((row_mac in self.element_switches) and (col_mac in self.element_switches))): # Make sure to add element machine switches.
                    #distance = path_map[row_switch][col_switch][0]
                    hop_count = self._get_hop_count(row_mac, col_mac)
                    link_weight = LinkWeight(hop_count=hop_count)
                    self.overlay_graph[row_mac].add((col_mac, link_weight))
                    edge_data = link_weight.__dict__
                    #print edge_data
                    self.overlay_graph_nx.add_edge(row_mac, col_mac, edge_data)

    def _remove_element_machine(self, node_mac):
        """Update the data structures and overlay graph when element instnace is removed.
        
        If the element is removed from the element machine.
        1- Check if there are any other element instnaces on the same machine.
        If yes, then no change in the graph and states.
        2- If no element instance is present then
            ii- remove the element_switch
            iii- remove the node from graph.

        Args:
            node_mac: MAC address of the machine.
        Returns:
            None
        """
        # Validate the MAC address.
        if node_mac in self.element_machines:
            elem_descs_list = self.controller.elem_to_mac.get_elem_descs(node_mac)
            # If there is an active elem descriptor on the element
            # machine than we don't need to change the graph.
            # else we remove the node.
            if len(elem_descs_list):
                return
            else:
                elem_switch_mac = self._get_connected_switch(node_mac)
                self.element_switches.remove(elem_switch_mac)
                #self.element_machines.remove(node_mac)
                self.overlay_graph_update(node_mac)
                # This should be called at the end.
                # In case the element_machine goes down 
                # we need to update the edge switches. 
                # If machine does not go down and simply element instance is removed
                # edge switches will not be updated.
                self._update_overlay_graph()

    def _get_hop_count(self, dpid1, dpid2):
        """Given the two vertices; return the hop count.

        Args:
            dpid1: Switch MAC address
            dpid2: Switch MAC address
        Returns:
            hop count integer.
        """
        from slick.l2_multi_slick import path_map
        from slick.l2_multi_slick import switches
        if (dpid1 in switches) and (dpid2 in switches):
            dpid1_switch = switches[dpid1]
            dpid2_switch = switches[dpid2]
            distance = path_map[dpid1_switch][dpid2_switch][0]
            return distance

    def _edge_switch(self, mac_addr):
        """Check if the switch is an edge switch or not an edge switch.

        Checks all the ports of the switch and if any of the ports
        is an edge-port we declare the switch to be edge switch.
        with the exception for gateway dpids.
        Args:
            mac_addr: MAC Address of the switch.
        Returns:
            True/False if edge or non-edge switch.
        """
        from slick.l2_multi_slick import switches
        edge_switch = False
        assert len(switches) == len(self.switches)
        #Simply validate if its a valid mac of a switch.
        if mac_addr in switches:
            gateway_dpids = self._get_gateway_dpids()
            if mac_addr in gateway_dpids:
                # For simiplicity we are assuming that the gateway
                # switches do not have middlebox attached to them.
                # Therefore they cannot be edge switches.
                # but this is a hack.
                return False
            switch_obj = switches[mac_addr]
            ports_to_check = [ ]
            for item in switch_obj.ports:
                port_number = item.port_no
                # excluding control port.
                if port_number < 65000:
                    ports_to_check.append(port_number)
            # assuming port numbers start from 1 on the switches.
            for port_num in ports_to_check:
                # If any of the ports of the switch is an
                # edge port; this is an edge switch.
                if core.openflow_discovery.is_edge_port(mac_addr, port_num ):
                    edge_switch = True
                    return edge_switch
            else:
                return edge_switch

    def _get_connected_switch(self, mac):
        """Given host mac address return the dpid for host
        tracker."""
        assert isinstance(mac_addr, basestring)
        mac_addr = dpid_to_str(mac, ':')
        if mac_addr in self.hosts:
            dpid_port_tuple = self.hosts[mac_addr]
            return dpid_port_tuple[0]
        else:
            raise KeyError("Host MAC Address is not registered with any switch.")

    def _get_total_ports(self, switch_mac):
        """Return total number of ports present on the switch.
           Args:
            switch_mac: Mac address of the switch.
           Returns:
            Total number of ports available on the switch.
        """
        max_switch_ports = 3
        return max_switch_ports

    def _get_gateway_dpids(self):
        """This is the root switch."""
        # Given _edge_switch detection does not work for gateway 
        # nodes. For now lets hardcode the list of gateway nodes.
        gateway_dpids = [1]
        return gateway_dpids

    def get_subgraph(self, src_switch_mac, dst_switch_mac, elem_descs):
        """Return a networkX subgraph for the element descriptors.

        Its a public function to be used by steering module
        to solve the subgraph.
        Args:
            elem_descs:Its a list of list of element descriptors where the order of the lists
            is the order to be applied to the flow.
        Returns:
            NetworkX Subgraph with weights.
        """
        switch_macs = [ ]
        switch_macs.append(src_switch_mac)
        switch_macs.append(dst_switch_mac)
        for ed_list in elem_descs:
            for ed in ed_list:
                # Get the element machine mac address.
                elem_machine_mac = self.controller.elem_to_mac.get(ed)
                # Get the dpid to which the element is attached.
                elem_switch_mac = self._get_connected_switch(elem_machine_mac)
                if elem_switch_mac in switch_macs:
                    print "DPID already has one element_machine present."
                else:
                    switch_macs.append(elem_switch_mac)
        subgraph = self.overlay_graph_nx.subgraph(switch_macs)
        #print subgraph.edges()
        return subgraph
