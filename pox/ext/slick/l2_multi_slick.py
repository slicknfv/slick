# Copyright 2012 James McCauley
#
# This file is part of POX.
#
# POX is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# POX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with POX.  If not, see <http://www.gnu.org/licenses/>.
#
# Modifications by Bilal Anwer

"""
A shortest-path forwarding application.

This is a standalone L2 switch that learns ethernet addresses
across the entire network and picks short paths between them.

You shouldn't really write an application this way -- you should
keep more state in the controller (that is, your flow tables),
and/or you should make your topology more static.  However, this
does (mostly) work. :)

Depends on openflow.discovery
Works with openflow.spanning_tree
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.recoco import Timer
from collections import defaultdict
from pox.openflow.discovery import Discovery
from pox.lib.util import dpid_to_str
import time

import copy
import os
import networkx as nx

log = core.getLogger()

# Adjacency map.  [sw1][sw2] -> port from sw1 to sw2
adjacency = defaultdict(lambda:defaultdict(lambda:None))

# Switches we know of.  [dpid] -> Switch
switches = {}

# ethaddr -> (switch, port)
mac_map = {}

# [sw1][sw2] -> (distance, intermediate)
path_map = defaultdict(lambda:defaultdict(lambda:(None,None)))

# Waiting path.  (dpid,xid)->WaitingPath
waiting_paths = {}

# Middlebox MAC Addresses
middleboxes = [] #defaultdict(list)

buffer_sent = {} # Key = (middlebox_switch_id,buffer_id) Value= Boolean

# Time to not flood in seconds
FLOOD_HOLDDOWN = 5

# Flow timeouts
#FLOW_IDLE_TIMEOUT = 60
FLOW_IDLE_TIMEOUT = 6
FLOW_HARD_TIMEOUT = 120
#FLOW_HARD_TIMEOUT = 9

# How long is allowable to set up a path?
PATH_SETUP_TIME = 4


slick_controller_interface = core.slick_controller.controller_interface
flow_matrices = [ ]

def dump_tm (flow_matrix):
  sws = switches.values()
  for i in sws:
    print i,
  print
  for i in sws:
    print i,
    for j in sws:
      a = flow_matrix.flow_tm[i.dpid][j.dpid]# path_map[i][j][0]
      #a = adjacency[i][j]
      if a is None: a = "*"
      print a,
    print

def dump_flow_tms():
  for flow_matrix in flow_matrices:
    print flow_matrix.flow
    dump_tm(flow_matrix)
    print "*"*100

class FlowMatrix():
  def __init__(self, flow_match):
    self.flow = flow_match
    # table to keep the matrix
    self.flow_tm = defaultdict(lambda:defaultdict(lambda:None))
    self.flowspace_desc = slick_controller_interface.get_flowspace_desc(flow_match)

def get_tm_entry(flow_id, src_switch, dst_switch):
  assert flow_id != None
  assert src_switch != None
  assert dst_switch != None
  for flow_matrix in flow_matrices:
    if flow_id == flow_matrix.flowspace_desc:
      if flow_matrix.flow_tm[src_switch][dst_switch]:
        return flow_matrix.flow_tm[src_switch][dst_switch]
  
def is_traffic_present():
  """Return True if there is traffic for any flow"""
  for flow_matrix in flow_matrices:
    if len(flow_matrix.flow_tm):
      #print "1111"*1000
      return True
  return False


def _update_tm(match, src_switch, dst_switch):
  match_copy = copy.copy(match)
  flow_match = slick_controller_interface.get_generic_flow(match_copy)
  #print flow_match, flow_matrices
  raw_shortest_path = _get_raw_path(src_switch, dst_switch)
  print src_switch, dst_switch, raw_shortest_path
  if not raw_shortest_path:
    return
  shortest_path = [src_switch] + raw_shortest_path + [dst_switch] 
  for flow_matrix in flow_matrices:
    if flow_match == flow_matrix.flow:
      for index, node in enumerate(shortest_path):
	if index < len(shortest_path)-1:
	  sw1, sw2 = shortest_path[index].dpid, shortest_path[index+1].dpid
          if flow_matrix.flow_tm[sw1][sw2]:
             # get the list of switches
            flow_matrix.flow_tm[sw1][sw2] += 1
	    print "A"
            dump_flow_tms()
          else:
            flow_matrix.flow_tm[sw1][sw2] = 1
	    print "B"
            dump_flow_tms()
      return
  if flow_match:
    flow_matrices.append(FlowMatrix(flow_match))
    for index, node in enumerate(shortest_path):
      if index < len(shortest_path)-1:
	sw1, sw2 = shortest_path[index].dpid, shortest_path[index+1].dpid
        flow_matrices[-1].flow_tm[sw1][sw2] = 1
	print "C"
        dump_flow_tms()

def dump ():
  sws = switches.values()
  for i in sws:
    print i,
  print
  for i in sws:
    print i,
    for j in sws:
      a = path_map[i][j][0]
      #a = adjacency[i][j]
      if a is None: a = "*"
      print a,
    print

def _calc_paths ():
  """
  Essentially Floyd-Warshall algorithm
  """

  print "Recalculating the path."
  sws = switches.values()
  path_map.clear()
  for k in sws:
    for j,port in adjacency[k].iteritems():
      if port is None: continue
      path_map[k][j] = (1,None)
    path_map[k][k] = (0,None) # distance, intermediate

  #dump()

  for k in sws:
    for i in sws:
      for j in sws:
        if path_map[i][k][0] is not None:
          if path_map[k][j][0] is not None:
            # i -> k -> j exists
            ikj_dist = path_map[i][k][0]+path_map[k][j][0]
            if path_map[i][j][0] is None or ikj_dist < path_map[i][j][0]:
              # i -> k -> j is better than existing
              path_map[i][j] = (ikj_dist, k)

  #print "--------------------"
  #dump()
  #print "--------------------"


def _get_raw_path (src, dst):
  """
  Get a raw path (just a list of nodes to traverse)
  """
  if len(path_map) == 0: _calc_paths()
  if src is dst:
    # We're here!
    return []
  if path_map[src][dst][0] is None:
    print "Src, Dst:",src, dst, type(src), type(dst), "Vals:",path_map[src][dst]
    print "NONE"*100
    return None
  intermediate = path_map[src][dst][1]
  if intermediate is None:
    # Directly connected
    return []
  return _get_raw_path(src, intermediate) + [intermediate] + \
         _get_raw_path(intermediate, dst)


def _check_path (p):
  """
  Make sure that a path is actually a string of nodes with connected ports

  returns True if path is valid
  """
  for a,b in zip(p[:-1],p[1:]):
    if adjacency[a[0]][b[0]] != a[2]:
      return False
    #if adjacency[b[0]][a[0]] != b[2]:
    if adjacency[b[0]][a[0]] != b[1]:
      return False
  return True


def _get_path (src, dst, first_port, final_port):
  """
  Gets a cooked path -- a list of (node,in_port,out_port)
  """
  # Start with a raw path...
  if src == dst:
    path = [src]
  else:
    path = _get_raw_path(src, dst)
    if path is None: return None
    path = [src] + path + [dst]

  # Now add the ports
  r = []
  in_port = first_port
  for s1,s2 in zip(path[:-1],path[1:]):
    out_port = adjacency[s1][s2]
    r.append((s1,in_port,out_port))
    in_port = adjacency[s2][s1]
  r.append((dst,in_port,final_port))

  assert _check_path(r), "Illegal path!"

  return r


# Returns True if its the first time reference to buffer.
def _is_valid_buffer(mac_addr,buffer_id):
    for switch in middleboxes:
        if(switch.dpid == mac_addr):
            return True

class WaitingPath (object):
  """
  A path which is waiting for its path to be established
  """
  def __init__ (self, path, packet):
    """
    xids is a sequence of (dpid,xid)
    first_switch is the DPID where the packet came from
    packet is something that can be sent in a packet_out
    """
    self.expires_at = time.time() + PATH_SETUP_TIME
    self.path = path
    self.first_switch = path[0][0].dpid
    self.xids = set()
    self.packet = packet

    if len(waiting_paths) > 1000:
      WaitingPath.expire_waiting_paths()

  def add_xid (self, dpid, xid):
    self.xids.add((dpid,xid))
    waiting_paths[(dpid,xid)] = self

  @property
  def is_expired (self):
    return time.time() >= self.expires_at

  def notify (self, event):
    """
    Called when a barrier has been received
    """
    self.xids.discard((event.dpid,event.xid))
    if len(self.xids) == 0: # First wait for barrier replies and then send the packet out
      # Done!
      if self.packet:
        log.debug("Sending delayed packet out %s"
                  % (dpid_to_str(self.first_switch),))
        msg = of.ofp_packet_out(data=self.packet,
            action=of.ofp_action_output(port=of.OFPP_TABLE))
        core.openflow.sendToDPID(self.first_switch, msg)

      core.l2_multi_slick.raiseEvent(PathInstalled(self.path))


  @staticmethod
  def expire_waiting_paths ():
    packets = set(waiting_paths.values())
    killed = 0
    for p in packets:
      if p.is_expired:
        killed += 1
        for entry in p.xids:
          waiting_paths.pop(entry, None)
    if killed:
      log.error("%i paths failed to install" % (killed,))


class PathInstalled (Event):
  """
  Fired when a path is installed
  """
  def __init__ (self, path):
    Event.__init__(self)
    self.path = path


RULES_INSTALLED = 0
class Switch (EventMixin):
  def __init__ (self):
    self.connection = None
    self.ports = None
    self.dpid = None
    self._listeners = None
    self._connected_at = None

  def __repr__ (self):
    return dpid_to_str(self.dpid)

  def _install_back (self, switch, in_port, out_port, match, buf = None):
    msg = of.ofp_flow_mod()
    msg.match = match # match should be fine as we are installing the in_port separately.
    msg.match.in_port = in_port
    msg.match.tp_src = None
    msg.idle_timeout = FLOW_IDLE_TIMEOUT
    msg.hard_timeout = FLOW_HARD_TIMEOUT
    msg.actions.append(of.ofp_action_output(port = out_port))
    msg.buffer_id = buf
    print msg.match
    print msg.buffer_id
    print msg.actions
    print "Installing path for ",switch," and inport and out_port::::::::::::::::",in_port,out_port#,msg.match
    switch.connection.send(msg)

  def _install (self, switch, in_port, out_port, match, buf = None):
    global RULES_INSTALLED
    msg = of.ofp_flow_mod()
    # We need the switches to send the message when the flows
    # are expired, to help in element migration.
    msg.flags |= of.OFPFF_SEND_FLOW_REM
    msg.match = match # match should be fine as we are installing the in_port separately.
    msg.match.in_port = in_port
    #msg.match.tp_src = None
    msg.idle_timeout = FLOW_IDLE_TIMEOUT
    msg.hard_timeout = FLOW_HARD_TIMEOUT
    msg.actions.append(of.ofp_action_output(port = out_port))
    msg.buffer_id = buf
    print switch, "match.in_port",msg.match.in_port, in_port,"->", out_port,"Flow:",
    print "dl_type:",match.dl_type, "nw_proto:",match.nw_proto, "nw_src:",match.nw_src, "nw_dst:",match.nw_dst, "tp_src:",match.tp_src, "tp_dst:",match.tp_dst
    if match.nw_proto == 1:
        RULES_INSTALLED = RULES_INSTALLED + 1
        print "Total Rules Installed: ", RULES_INSTALLED
    switch.connection.send(msg)

  def _install_path (self, p, match, packet_in=None):
    wp = WaitingPath(p, packet_in)
    for sw,in_port,out_port in p:
      self._install(sw, in_port, out_port, match)
      msg = of.ofp_barrier_request()
      sw.connection.send(msg)
      wp.add_xid(sw.dpid,msg.xid)

  def _send_dest_unreachable(self, event, match, switch1, switch2, switch1_port, switch2_port):
    """Since path is not found send ICMP unreachable packet."""
    log.warning("Can't get from %s to %s", switch1, switch2)

    import pox.lib.packet as pkt

    if (match.dl_type == pkt.ethernet.IP_TYPE and
        event.parsed.find('ipv4')):
      # It's IP -- let's send a destination unreachable
      log.debug("Dest unreachable (%s -> %s)",
                switch1, switch2)
      from pox.lib.addresses import EthAddr
      e = pkt.ethernet()
      e.src = EthAddr(dpid_to_str(switch1.dpid)) #FIXME: Hmm...
      e.dst = match.dl_src
      e.type = e.IP_TYPE
      ipp = pkt.ipv4()
      ipp.protocol = ipp.ICMP_PROTOCOL
      ipp.srcip = match.nw_dst #FIXME: Ridiculous
      ipp.dstip = match.nw_src
      icmp = pkt.icmp()
      icmp.type = pkt.ICMP.TYPE_DEST_UNREACH
      icmp.code = pkt.ICMP.CODE_UNREACH_HOST
      orig_ip = event.parsed.find('ipv4')

      d = orig_ip.pack()
      d = d[:orig_ip.hl * 4 + 8]
      import struct
      d = struct.pack("!HH", 0,0) + d #FIXME: MTU
      icmp.payload = d
      ipp.payload = icmp
      e.payload = ipp
      msg = of.ofp_packet_out()
      msg.actions.append(of.ofp_action_output(port = switch1_port))
      msg.data = e.pack()
      self.connection.send(msg)
    return

  def get_reverse_mb_locs(self, mb_locations, element_descs):
    """This function removes the middlebox
    locations that should be removed on reverse path."""
    #print "INCOMING.",mb_locations
    for index, ed in enumerate(element_descs):
        if slick_controller_interface.is_unidirection_required(ed):
            mb_locations.pop(index)
    #print "OUTGOING.",mb_locations
    return mb_locations

  def detect_loop(self, pathlets):
    """Given the list of pathlets detect if there is a loop in the path.
    Args: List of pathlets where each entry is of the form (switch, in_port, out_port) e.g. (00-00-00-00-00-03, 2, 3)
    Returns: True/False
    """
    traversed_switches = [ ]
    for pathlet in pathlets:
      for sw,in_port,out_port in pathlet:
        # This situation arises when we have a middlebox attached
        # to a switch. One rule to send traffic to middlebox and other
        # to get traffic back.
        if sw == traversed_switches[-1]:
          continue
        else:
          traversed_switches.append(sw)
    # TODO: This will not work if we have  source and destination 
    # on the same switch.
    traversed_switches.pop(0)
    traversed_switches.pop()
    # Now we have removed the middlebox switches from path and traversed_switches
    # should not have any middlexbox attached switch. Now if there is a duplicate switch
    # we have cycle.
    seen_switches = [ ]
    for switch in traversed_switches:
      if switch in seen_switches:
        return True
      seen_switches.append(switch)
    return False

  def install_path_improved (self, dst_sw, last_port, match, event, mb_locations, element_descs):
    """
    Attempts to install a path between this switch and some destination
    """ 
    filename = "path_lengths.txt"
    if os.path.isfile(filename):
        file_handle = open(filename, 'a')
    else:
        file_handle = open(filename, 'w')
    print "MB_LOCATIONS,",mb_locations, "ELEMENT_DESCS:",element_descs
    src = (self, event.port)
    dst = (dst_sw, last_port) 
    #pathlets = slick_controller_interface.get_path(src, mb_locations, dst)
    pathlets = slick_controller_interface.get_path(src, mb_locations, dst)
    #dump()
    #print "FORWARD:",pathlets
    mb_locations_forward = [src] + mb_locations + [dst]
    print mb_locations_forward
    print element_descs
    total_fwd_path_length = 0
    total_bwd_path_length = 0

    for index in range(0, len(pathlets)):
      # Place we saw this ethaddr   -> loc = (self, event.port) 
      switch1 = mb_locations_forward[index][0]
      switch2 = mb_locations_forward[index+1][0]
      switch1_port = mb_locations_forward[index][1]
      switch2_port = mb_locations_forward[index+1][1]
      p = pathlets[index]
      if p is None:
        return self._send_dest_unreachable(event, match, switch1, switch2, switch1_port, switch2_port)
      log.debug("Installing forward paths for %s -> %s (%i hops)",
          switch1, switch2, len(p))
      total_fwd_path_length += len(p)
      self._install_path(p, match, event.ofp)
      # Now reverse it and install it backwards
      # (we'll just assume that will work)
      #p = [(sw,out_port,in_port) for sw,in_port,out_port in p]
      #self._install_path(p, match.flip())

    # 1- Reverse source destination switches. Reverse middlebox locs and corresponding elment descs.
    (dst, src) = (src, dst)
    mb_locations.reverse()
    element_descs.reverse()
    # 2- Remove unidirectional middleboxes.
    mb_locs = mb_locations
    mb_locations = self.get_reverse_mb_locs(mb_locs, element_descs)
    # 3- Get pathlets
    pathlets = slick_controller_interface.get_path(src, mb_locations, dst)
    #print "BACKWARD:",pathlets
    mb_locations_reverse = [src] + mb_locations + [dst]
    print mb_locations_reverse
    print element_descs
    # 4- Install pathlets.
    for index in range(0, len(pathlets)):
      # Place we saw this ethaddr   -> loc = (self, event.port) 
      switch1 = mb_locations_forward[index][0]
      switch2 = mb_locations_forward[index+1][0]
      switch1_port = mb_locations_forward[index][1]
      switch2_port = mb_locations_forward[index+1][1]
      p = pathlets[index]
      if p is None:
        return self._send_dest_unreachable(event, match.flip(), switch1, switch2, switch1_port, switch2_port)
      log.debug("Installing backward paths for %s -> %s (%i hops)",
          switch1, switch2, len(p))
      total_bwd_path_length += len(p)
      self._install_path(p, match.flip())
    log_string = str(total_fwd_path_length) + "," + str(total_bwd_path_length ) + "\n"
    file_handle.write(log_string)
    file_handle.close()

  def install_path (self, dst_sw, last_port, match, event, mb_locations):
    """
    Attempts to install a path between this switch and some destination
    """
    src = (self, event.port)
    dst = (dst_sw, last_port)
    pathlets = slick_controller_interface.get_path(src, mb_locations, dst)
    mb_locations = [src] + mb_locations + [dst]

    for index in range(0, len(pathlets)):
      # Place we saw this ethaddr   -> loc = (self, event.port) 
      switch1 = mb_locations[index][0]
      switch2 = mb_locations[index+1][0]
      switch1_port = mb_locations[index][1]
      switch2_port = mb_locations[index+1][1]
      print pathlets
      p = pathlets[index]

      if p is None:
        log.warning("Can't get from %s to %s", switch1, switch2)

        import pox.lib.packet as pkt

        if (match.dl_type == pkt.ethernet.IP_TYPE and
            event.parsed.find('ipv4')):
          # It's IP -- let's send a destination unreachable
          log.debug("Dest unreachable (%s -> %s)",
                    switch1, switch2)
          from pox.lib.addresses import EthAddr
          e = pkt.ethernet()
          e.src = EthAddr(dpid_to_str(switch1.dpid)) #FIXME: Hmm...
          e.dst = match.dl_src
          e.type = e.IP_TYPE
          ipp = pkt.ipv4()
          ipp.protocol = ipp.ICMP_PROTOCOL
          ipp.srcip = match.nw_dst #FIXME: Ridiculous
          ipp.dstip = match.nw_src
          icmp = pkt.icmp()
          icmp.type = pkt.ICMP.TYPE_DEST_UNREACH
          icmp.code = pkt.ICMP.CODE_UNREACH_HOST
          orig_ip = event.parsed.find('ipv4')

          d = orig_ip.pack()
          d = d[:orig_ip.hl * 4 + 8]
          import struct
          d = struct.pack("!HH", 0,0) + d #FIXME: MTU
          icmp.payload = d
          ipp.payload = icmp
          e.payload = ipp
          msg = of.ofp_packet_out()
          msg.actions.append(of.ofp_action_output(port = switch1_port))
          msg.data = e.pack()
          self.connection.send(msg)

        return

      log.debug("Installing forward and reverse paths for %s -> %s (%i hops)",
          switch1, switch2, len(p))

      self._install_path(p, match, event.ofp)

      # Now reverse it and install it backwards
      # (we'll just assume that will work)
      p = [(sw,out_port,in_port) for sw,in_port,out_port in p]
      self._install_path(p, match.flip())


  def _handle_PacketIn (self, event):
    def flood ():
      """ Floods the packet """
      if self.is_holding_down:
        log.warning("Not flooding -- holddown active")
      msg = of.ofp_packet_out()
      # OFPP_FLOOD is optional; some switches may need OFPP_ALL
      msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
      msg.buffer_id = event.ofp.buffer_id
      msg.in_port = event.port
      self.connection.send(msg)

    def drop ():
      # Kill the buffer
      if event.ofp.buffer_id is not None:
        msg = of.ofp_packet_out()
        msg.buffer_id = event.ofp.buffer_id
        event.ofp.buffer_id = None # Mark is dead
        msg.in_port = event.port
        self.connection.send(msg)

    ############################################################
    # Slick processing starts here

    packet = event.parsed
    #print packet.src, "->",packet.dst, "type:",packet.type#, packet.srcip,"->", packet.dstip, "proto:",packet.protocol
    flow_match = of.ofp_match.from_packet(packet) # extract flow fields

    ############################################################
    # Optimization should happen behind the scenes here
    # (takes information from placement, as well as steering)
    # TODO: Let's get the refactoring language straight here.  Is this module 2 or module 3?

    #element_descriptors = slick_controller_interface.get_element_descriptors(flow_match)
    src_switch = dst_switch = src_port = dst_port = None
    source_tuple = mac_map.get(packet.src)
    dest_tuple = mac_map.get(packet.dst)
    if source_tuple:
        src_switch = source_tuple[0].dpid
        src_port = source_tuple[1]
    if dest_tuple:
        dst_switch = dest_tuple[0].dpid
        dst_port = dest_tuple[1]
    #element_descriptors = slick_controller_interface.get_steering(mac_map.get(packet.src), mac_map.get(packet.dst), flow_match)
    element_descriptors = slick_controller_interface.get_steering((src_switch,src_port), (dst_switch,dst_port), flow_match)
    #_update_tm(flow_match, src_switch, dst_switch)
    if source_tuple and dest_tuple:
      _update_tm(flow_match, source_tuple[0], dest_tuple[0])
    #bidirection = slick_controller_interface.is_bidirectional_flow()
    # Order of this list is important.
    # This is the same order in which we want the packets to traverse.
    # TODO just return the list of mac addresses instead of this (unordered) dictionary FIXME
    mb_locations = [ ]
    element_descs = [ ]
    #for element_id,mac_addr in element_descriptors.iteritems():
    for element_id,mac_addr in element_descriptors:
        #print element_id,mac_addr
        #print type(mac_addr)
        temp_loc = mac_map.get(mac_addr) 
        #print temp_loc
        mb_locations.append(temp_loc)
        element_descs.append(element_id)
        if(temp_loc[0] not in middleboxes):
            middleboxes.append(temp_loc[0]) # Need these to not send packet out as packet is not reached.
    assert len(mb_locations) == len(element_descs) , 'Number of Element Descriptors != Number of Middlebox Locations'

    loc = (self, event.port) # Place we saw this ethaddr
    #print loc
    oldloc = mac_map.get(packet.src) # Place we last saw this ethaddr

    if packet.effective_ethertype == packet.LLDP_TYPE:
      drop()
      return

    if oldloc is None:
      if packet.src.is_multicast == False:
        mac_map[packet.src] = loc # Learn position for ethaddr
        log.debug("Learned %s at %s.%i", packet.src, loc[0], loc[1])
    elif oldloc != loc:
      # ethaddr seen at different place!
      if loc[1] not in adjacency[loc[0]].values():
        # New place is another "plain" port (probably)
        log.debug("%s moved from %s.%i to %s.%i?", packet.src,
                  dpid_to_str(oldloc[0].connection.dpid), oldloc[1],
                  dpid_to_str(   loc[0].connection.dpid),    loc[1])
        if packet.src.is_multicast == False:
          mac_map[packet.src] = loc # Learn position for ethaddr
          log.debug("Learned %s at %s.%i", packet.src, loc[0], loc[1])
      elif packet.dst.is_multicast == False:
        # New place is a switch-to-switch port!
        #TODO: This should be a flood.  It'd be nice if we knew.  We could
        #      check if the port is in the spanning tree if it's available.
        #      Or maybe we should flood more carefully?
        log.warning("Packet from %s arrived at %s.%i without flow",
                    packet.src, dpid_to_str(self.dpid), event.port)
        #drop()
        #return


    if packet.dst.is_multicast:
      log.debug("Flood multicast from %s", packet.src)
      flood()
    else:
      if packet.dst not in mac_map:
        log.debug("%s unknown -- flooding" % (packet.dst,))
        flood()
      else:
        dest = mac_map[packet.dst]
        match = of.ofp_match.from_packet(packet)
        match_copy = copy.copy(match)
        matched_flow_tuple = slick_controller_interface.get_generic_flow(match_copy)
        if(matched_flow_tuple != None):
            """
                dl_type,src_ip,dst_ip are the required field. Without these forwarding
                does not work.
            """
            match.dl_src = matched_flow_tuple.dl_src
            match.dl_dst = matched_flow_tuple.dl_dst
            match.dl_vlan = matched_flow_tuple.dl_vlan
            match.dl_vlan_pcp = matched_flow_tuple.dl_vlan_pcp
            #match.dl_type = matched_flow_tuple.dl_type
            match.nw_tos = None  #matched_flow_tuple.nw_tos
            match.nw_proto = matched_flow_tuple.nw_proto
            #match.nw_src = matched_flow_tuple.nw_src
            #match.nw_dst = matched_flow_tuple.nw_dst
            match.tp_dst = matched_flow_tuple.tp_dst
            match.tp_src = matched_flow_tuple.tp_src
            print "INSTALLING FOLLOWING RULE:",match
            self.install_path_improved(dest[0], dest[1], match, event, mb_locations, element_descs)
            #self.install_path(dest[0], dest[1], match, event, mb_locations)
        else:
            self.install_path_improved(dest[0], dest[1], match, event, mb_locations, element_descs)
            #self.install_path(dest[0], dest[1], match, event, mb_locations)

  def disconnect (self):
    if self.connection is not None:
      log.debug("Disconnect %s" % (self.connection,))
      self.connection.removeListeners(self._listeners)
      self.connection = None
      self._listeners = None

  def connect (self, connection):
    if self.dpid is None:
      self.dpid = connection.dpid
    assert self.dpid == connection.dpid
    if self.ports is None:
      self.ports = connection.features.ports
    self.disconnect()
    log.debug("Connect %s" % (connection,))
    self.connection = connection
    self._listeners = self.listenTo(connection)
    self._connected_at = time.time()

  @property
  def is_holding_down (self):
    if self._connected_at is None: return True
    if time.time() - self._connected_at > FLOOD_HOLDDOWN:
      return False
    return True

  def _handle_ConnectionDown (self, event):
    self.disconnect()


class l2_multi_slick (EventMixin):

  _eventMixin_events = set([
    PathInstalled,
  ])

  def __init__ (self):
    # Listen to dependencies
    def startup ():
      core.openflow.addListeners(self, priority=0)
      core.openflow_discovery.addListeners(self)
    core.call_when_ready(startup, ('openflow','openflow_discovery'))

  def _handle_LinkEvent (self, event):
    def flip (link):
      return Discovery.Link(link[2],link[3], link[0],link[1])

    l = event.link
    sw1 = switches[l.dpid1]
    sw2 = switches[l.dpid2]

    # Invalidate all flows and path info.
    # For link adds, this makes sure that if a new link leads to an
    # improved path, we use it.
    # For link removals, this makes sure that we don't use a
    # path that may have been broken.
    #NOTE: This could be radically improved! (e.g., not *ALL* paths break)
    clear = of.ofp_flow_mod(command=of.OFPFC_DELETE)
    for sw in switches.itervalues():
      if sw.connection is None: continue
      sw.connection.send(clear)
    path_map.clear()

    if event.removed:
      # This link no longer okay
      if sw2 in adjacency[sw1]: del adjacency[sw1][sw2]
      if sw1 in adjacency[sw2]: del adjacency[sw2][sw1]

      # But maybe there's another way to connect these...
      for ll in core.openflow_discovery.adjacency:
        if ll.dpid1 == l.dpid1 and ll.dpid2 == l.dpid2:
          if flip(ll) in core.openflow_discovery.adjacency:
            # Yup, link goes both ways
            adjacency[sw1][sw2] = ll.port1
            adjacency[sw2][sw1] = ll.port2
            # Fixed -- new link chosen to connect these
            break
    else:
      # If we already consider these nodes connected, we can
      # ignore this link up.
      # Otherwise, we might be interested...
      if adjacency[sw1][sw2] is None:
        # These previously weren't connected.  If the link
        # exists in both directions, we consider them connected now.
        if flip(l) in core.openflow_discovery.adjacency:
          # Yup, link goes both ways -- connected!
          adjacency[sw1][sw2] = l.port1
          adjacency[sw2][sw1] = l.port2

      # If we have learned a MAC on this port which we now know to
      # be connected to a switch, unlearn it.
      bad_macs = set()
      for mac,(sw,port) in mac_map.iteritems():
        #print sw,sw1,port,l.port1
        if sw is sw1 and port == l.port1:
          if mac not in bad_macs:
            log.debug("Unlearned %s", mac)
            bad_macs.add(mac)
        if sw is sw2 and port == l.port2:
          if mac not in bad_macs:
            log.debug("Unlearned %s", mac)
            bad_macs.add(mac)
      for mac in bad_macs:
        del mac_map[mac]
        #slick_controller_interface.del_machine_location(mac)

  def _handle_ConnectionUp (self, event):
    sw = switches.get(event.dpid)
    if sw is None:
      # New switch
      sw = Switch()
      switches[event.dpid] = sw
      sw.connect(event.connection)
    else:
      sw.connect(event.connection)

  def _handle_BarrierIn (self, event):
    wp = waiting_paths.pop((event.dpid,event.xid), None)
    if not wp:
      #log.info("No waiting packet %s,%s", event.dpid, event.xid)
      return
    #log.debug("Notify waiting packet %s,%s", event.dpid, event.xid)
    wp.notify(event)


def launch ():
  core.registerNew(l2_multi_slick)

  timeout = min(max(PATH_SETUP_TIME, 5) * 2, 15)
  Timer(timeout, WaitingPath.expire_waiting_paths, recurring=True)
