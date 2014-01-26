import struct
from collections import defaultdict
from sets import Set

from pox.core import core
from pox.openflow.discovery import Discovery
from pox.openflow.discovery import Link
import pox.openflow.libopenflow_01 as of
# This is required as l2_multi_slick as MACs as 00-00-00-xx-xx-xx
# instead of 00:00:00:xx:xx:xx
import string

from msmessageproc import MSMessageProcessor

import networkx as nx
from pox.lib.revent import EventHalt
from pox.lib.recoco import Timer # For timer calls.

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
    def __init__(self, hop_count=None, utilization=None, latency=None):
        # Physical hop count that corresponds to virtual
        # overlay link.
        self.hop_count = hop_count
        # Percent utilization of the link.
        self.utilization = utilization
        self.latency = latency

    def __str__(self):
        s = 'phsyical_hop_count: ' + str(self.physical_hop_count) + ' utilization: ' + str(self.utilization) + ' latency: ' + str(self.latency)
        return s

class Vertex(object):
    def __init__(self, vertex_id, ed, element_name):
        """vertex_id must be an integer."""
        # Unique ID for the node in the graph.
        self.vertex_id = vertex_id
        # Element descriptor for the element instance.
        self.elem_desc = ed
        self.element_name = element_name

    # Need to make it hashable.
    def __hash__(self):
        return hash(self.vertex_id)

    def __eq__(self, other):
        return (self.vertex_id == other.vertex_id)

    def __str__(self):
        s = "Vertex ID: " + str(self.vertex_id) + " Element Desc: " + str(self.elem_desc) + " Element Name: " + str(self.element_name)
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
        def startup():
            core.openflow_discovery.addListeners(self)
        core.call_when_ready(startup, ('openflow_discovery'))

        # Data Structures.
        # Overlay Graph
        self.overlay_graph_nx = nx.DiGraph( )
        self.overlay_graph_eds = nx.DiGraph( )
        self.overlay_graph = defaultdict(Set)
        # Simple switch topology graph.
        self.topo_graph = nx.Graph()
        # Set of Edge switches. This set is used to add edges.
        self.edge_switches = Set([ ])
        # Set of switches that have element machines attached to them.
        self.element_switches = Set([ ])
        # Set of all the switches in the network.
        self.switches = { }# Set([ ])
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
        # Unique ID for the vertex.
        self.vertex_descriptor = 0 
        # Utilization of links 
        self.phy_link_utilizations = { }
        # Network state callback
        Timer(5, self.update_overlay_graph_link_weights, recurring = True)


    def _handle_host_tracker_HostEvent(self, event):
        """Given the host join/leave event update the self.hosts map.
        Args:
            event: HostEvent
        Returns:
            None
        """
        host = str(event.entry.macaddr)
        switch = event.entry.dpid
        port = event.entry.port
        ip_addrs = [ ]
        if len(event.entry.ipAddrs):
            ip_addrs = event.entry.ipAddrs.keys()
            print ip_addrs[0], type(ip_addrs[0])
            print host, type(host)
            self.controller.register_machine(ip_addrs[0], host)
        if event.leave:
            if host in self.hosts:
                del self.hosts[host]
        else:
            if host not in self.hosts:
                self.hosts[host] = (switch, port)
                if switch not in self.switches:
                    log.warn("Missing switch")

    def _handle_ConnectionUp(self, event):
        #self.switches.add(event.dpid)
        switch_name = event.connection.ports[of.OFPP_LOCAL].name
        self.switches[event.dpid] = switch_name

    def _handle_ConnectionDown(self, event):
        #self.switches.remove(event.dpid)
        switch_name = event.connection.ports[of.OFPP_LOCAL].name
        del self.switches[event.dpid]

    def _handle_LinkEvent (self, event):
        self.update_topo_graph()

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
            self._update_overlay_graph_eds(event.ed, event.element_name, join=True)
        elif event.destroyed:
            self._remove_element_machine(event.mac)
            self._update_overlay_graph_eds(event.ed, event.element_name, leave=True)
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
            elem_switch_mac = self.get_connected_switch(node_mac)
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
                    # Getting the dicts as edge weights can be stored as key value pairs not object.
                    edge_data = link_weight.__dict__
                    #print edge_data
                    self.overlay_graph_nx.add_edge(row_mac, col_mac, edge_data)

    def _get_vertex_id(self):
        self.vertex_descriptor += 1
        return self.vertex_descriptor

    def _update_overlay_graph_eds(self, ed, element_name, join=False, leave=False):
        """Args:
            Builds a graph between the element instances of the network.
            ed = Element descriptor to be used for the element instacen.
            element_name = Type of element instance node added to the graph.
            join = Default False; Set to True if the node joins
            leave = Default False; Set to True if the node leaves.
        """
        vertex_id = self._get_vertex_id()
        graph_vertex = Vertex(vertex_id, ed, element_name)
        if (join == leave):
            raise Exception("A node can be added or removed not both.")
        if join:
            print "Updating the Element Instance: " + str(ed) + element_name
            self._add_vertex(graph_vertex)
            print self.overlay_graph_eds.nodes()
            print self.overlay_graph_eds.edges()
        if leave:
            self._remove_vertex(graph_vertex)

    def _is_edge_allowed(self, src, dst):
        """Return True/False if the edge is allowed or not.
        Args:
            src: src vertex of possible edge of type Vertex.
            dst: dst vertex of possible edge of type Vertex.
        Returns:
            True/False if the edge is allowed or not."""
        # Check to not have self loop on a vertex
        if (src.vertex_id == dst.vertex_id):
            return False
        # No edges between the element descriptors of
        # same type.
        if (src.element_name == dst.element_name):
            return False
        element_desc = src_vertex.ed
        # Ordered list of element names.
        element_name_list = self.controller.get_element_order()
        if ((src.element_name in element_name_list) and (dst.element_name in element_name_list)):
            src_index = element_name_list.index(src.element_name)
            dst_index = element_name_list.index(dst.element_name)
            if (src_index == (dst_index-1)):
                return True
            else:
                return False
        else:
            raise Exception("Element Name is not present in element names for the policy.")

    def _add_vertex(self, graph_vertex):
        """Function to update the edges between all the nodes in the graph.
        Side Effect:
            Update the overlay graph between all the element instances
            in the network.
        """
        for v in self.overlay_graph_eds.nodes():
            if _is_edge_allowed(graph_vertex, v):
                self.overlay_graph_eds.add_edge(graph_vertex, v)
            if _is_edge_allowed(v, graph_vertex):
                self.overlay_graph_eds.add_edge(v, graph_vertex)
        # Ideally we should not be putting this constraint but for now
        # we have this constraint.
        # After adding a node please make sure that the graph is DAG.
        if nx.is_directed_acyclic_graph(self.overlay_graph_eds):
            return True
        else:
            return False

    def _remove_vertex(self, graph_vertex):
        self.overlay_graph_eds.remove_node(graph_vertex)
        if nx.is_directed_acyclic_graph(self.overlay_graph_eds):
            return True
        else:
            return False


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
                elem_switch_mac = self.get_connected_switch(node_mac)
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
        """Given the two vertices; return the hop count
        using shortest path.

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

    def _get_link_utilization(self, dpid1, dpid2):
        """Given the two vertices; return the link
        utilization of the shortest path

        Args:
            dpid1: Switch MAC address
            dpid2: Switch MAC address
        Returns:
            utilization percentage.
        """
        from slick.l2_multi_slick import switches
        from slick.l2_multi_slick import _get_path
        from slick.l2_multi_slick import adjacency
        if (dpid1 in switches) and (dpid2 in switches):
            dpid1_switch = switches[dpid1]
            dpid2_switch = switches[dpid2]
            # port from dpid1 to dpid2
            d1_port = adjacency[dpid1_switch][dpid2_switch]
            # port from dpid2 to dpid1
            d2_port = adjacency[dpid2_switch][dpid1_switch]
            #path = _get_raw_path(dpid1_switch, dpid2_switch)
            path = _get_path(dpid1_switch, dpid2_switch, d1_port, d2_port)
            #path = [dpid1_switch] + path + [dpid2_switch]
            links = [ ]
            for index in range(0, len(path)-1):
                #path[index]
                switch1 = path[index][0].dpid
                port1 = path[index][2]
                switch2 = path[index+1][0].dpid
                port2 = path[index+1][1]
                link = Link(switch1, port1, switch2, port2)
                links.append(link)
            #print path
            #print links
            max_utilization = 0.0 # Mbps
            for link in links:
                if link in self.phy_link_utilizations:
                    utilization = self.phy_link_utilizations[link]
                    if (utilization > max_utilization):
                        max_utilization = utilization
        return max_utilization

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
                #return False
                # But they always have source or destination attached to them.
                return True
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

    """ PUBLIC FUNCTIONS START HERE."""
    def get_all_machines(self):
        """Returns list of MAC address strings."""
        return self.hosts.keys()

    def get_all_forwarding_devices(self):
        """Returns list of switch MAC Addresses."""
        #return list(self.switches)
        return self.switches.keys()

    def get_subgraph(self, src_switch_mac, dst_switch_mac, elem_descs):
        """Return a copy of networkX subgraph for the element descriptors.

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
                elem_switch_mac = self.get_connected_switch(elem_machine_mac)
                # There can be multiple MB machines on one switch.
                # Or middlebox machine and source/dst might be attached to same switch.
                if elem_switch_mac in switch_macs: 
                    print "DPID:",elem_switch_mac, " already has one element_machine present."
                else:
                    switch_macs.append(elem_switch_mac)
        # Given the nodes get the subgraph.
        # .copy() is for deep copy of edge attributes.
        subgraph = nx.DiGraph(self.overlay_graph_nx.subgraph(switch_macs).copy())
        # print self.overlay_graph_nx.edges()
        # print subgraph.edges()
        return subgraph

    def get_placement_graph(self):
        return self.topo_graph

    def update_topo_graph(self):
        """Update topology graph if new element instance is added, 
        i.e. apply_elem is called. or a new link is discovered."""
        from slick.l2_multi_slick import switches
        from slick.l2_multi_slick import adjacency
        sws = switches.values()
        for i in sws:
            for j in sws:
                # Debug information
                # print i.dpid, j.dpid
                # print type(i.dpid), type(j.dpid)
                if i.dpid != j.dpid:
                    if adjacency[i][j] is not None:
                        self.topo_graph.add_edge(i.dpid, j.dpid)

    def get_connected_switch(self, mac):
        """Given host mac address return the dpid for host
        tracker."""
        if not isinstance(mac, basestring):
            mac_addr = dpid_to_str(mac, ':')
        else:
            mac_addr = mac
        assert isinstance(mac_addr, basestring)
        if mac_addr in self.hosts:
            dpid_port_tuple = self.hosts[mac_addr]
            return dpid_port_tuple[0]
        else:
            raise KeyError("Host MAC Address is not registered with any switch.")

    def update_overlay_graph_link_weights(self):
        """Use this function to update the weight for links of the overlay graph
        based on the utilization readings got from the NetworkLoad."""
        self.phy_link_utilizations = self.controller.network_model.get_physical_link_utilizations()
        for v1, v2, data in self.overlay_graph_nx.edges(data=True):
            utilization = self._get_link_utilization(v1,v2)
            self.overlay_graph_nx[v1][v2]['utilization'] = utilization

