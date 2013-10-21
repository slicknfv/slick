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
middleboxes = [ ] #defaultdict(list)

buffer_sent = {} # Key = (middlebox_switch_id,buffer_id) Value= Boolean

# Time to not flood in seconds
FLOOD_HOLDDOWN = 5

# Flow timeouts
FLOW_IDLE_TIMEOUT = 10
FLOW_HARD_TIMEOUT = 30

# How long is allowable to set up a path?
PATH_SETUP_TIME = 4

GLOBAL_FLOW_ID = 0
# Three bits for the VLAN TTL. Assuming VLAN = 0x000 h and VLAN = 0xFFF h are invalid.
# Assuming a max. of 7 elements in a chain. 
# last 3-bits are for chaining and 9-bits are used for uniquely
# identifying the flow.
FLOW_ID_BITS = 9
HOP_BITS = 3
MAX_GLOBAL_FLOW_ID = 2**FLOW_ID_BITS

slick_controller_interface = core.slick_controller.controller_interface

def _calc_paths ():
  """
  Essentially Floyd-Warshall algorithm
  """

  def dump ():
    for i in sws:
      for j in sws:
        a = path_map[i][j][0]
        #a = adjacency[i][j]
        if a is None: a = "*"
        print a,
      print

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


def _get_raw_path (src, dst):
  """
  Get a raw path (just a list of nodes to traverse)
  """
  if len(path_map) == 0: _calc_paths()
  if src is dst:
    # We're here!
    return []
  if path_map[src][dst][0] is None:
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
    if adjacency[b[0]][a[0]] != b[2]:
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

  def _max_chain_length(self):
    return 7

  def _init_vlan_id(self, mb_locations, forward):
    """Given the number of middleboxes in the path
    return the appropriate VLAN header.

    Args:
        forward: If the vlan id is for forward path set True for reverse path set False.
        mb_locations: Middlebox machine mac addresses.
    Returns:
        12-bits of VLAN value for path installation."""
    global GLOBAL_FLOW_ID
    flow_id = GLOBAL_FLOW_ID + 1
    if flow_id >= MAX_GLOBAL_FLOW_ID: # wrap around
      GLOBAL_FLOW_ID = 0
      flow_id = GLOBAL_FLOW_ID + 1
    #9-bits are used for flow id
    #3-bits are used for number of elements in a chain.
    vlan_id = 0
    flow_id_bitmask = 0xFF8
    processing_bitmask = 0x007 # These are the TTL bits.
    if (len(mb_locations) > self._max_chain_length()):
      raise Exception("Number of middlebox locations is larger than max possible.")
    elif len(mb_locations): # only get vlan if there are middleboxes.
      # As long as the FLOW_ID_BITS are non-zero we can afford to
      # have hop bits as zero. But one middlebox machine means
      # there are two paths. Source -> MB -> Destination.
      hop_bits =  processing_bitmask & len(mb_locations) + 1
      flow_id_bits = flow_id_bitmask & (flow_id << HOP_BITS)
      vlan_id = flow_id_bits | hop_bits
      # Sanity check.
      if (vlan_id <= 0x000) or (vlan_id >= 0xFFF):
        raise Exception("Invalid VLAN ID value:" + str(vlan_id))
      return vlan_id

  def update_vlan_id(self, vlan_id, increment):
    """Given the VLAN ID, decrement the TTL bit
    and update the VLAN ID.

    Args:
        vlan_id: 12-bits of VLAN.
        increment: Bool for incrementing or decrementing the values.

    Returns:
        Updated VLAN header with only processings bits decreased.
    """
    flow_id = 0
    ttl_val = 0
    new_ttl_val = 0
    new_vlan_id = 0
    flow_id_bitmask = 0xFF8
    processing_bitmask = 0x007 # These are the TTL bits.

    flow_id = vlan_id & flow_id_bitmask
    ttl_val = vlan_id & processing_bitmask
    if increment:
      ttl_val = ttl_val + 1
    else:
      ttl_val = ttl_val - 1
    new_ttl_val = processing_bitmask & ttl_val 
    # we need to concatenate bits here.
    new_vlan_id = flow_id | new_ttl_val
    return new_vlan_id

  def _install (self, switch, in_port, out_port, match, buf = None):
    msg = of.ofp_flow_mod()
    msg.match = match # match should be fine as we are installing the in_port separately.
    msg.match.in_port = in_port
    msg.match.tp_src = None
    msg.idle_timeout = FLOW_IDLE_TIMEOUT
    msg.hard_timeout = FLOW_HARD_TIMEOUT
    msg.actions.append(of.ofp_action_output(port = out_port))
    msg.buffer_id = buf
    switch.connection.send(msg)

  def _vlan_install(self, switch , in_port, out_port, match, vlan_id, buf = None):
    msg = of.ofp_flow_mod()
    msg.match = match
    msg.match.in_port = in_port
    # update vlan ID for the new flow to match.
    msg.match.dl_vlan = vlan_id
    msg.match.dl_type = 0x8100
    msg.idle_timeout = FLOW_IDLE_TIMEOUT
    msg.hard_timeout = FLOW_HARD_TIMEOUT
    msg.actions.append(of.ofp_action_output(port = out_port))
    msg.buffer_id = buf
    switch.connection.send(msg)
    print "Simple VLAN Install. ", switch, match, msg.actions

  def _add_vlan_and_forward (self, switch, in_port, out_port, match, vid, buf = None):
    """Function to add the vlan header and forward the packet."""
    msg = of.ofp_flow_mod()
    msg.match = match # match should be fine as we are installing the in_port separately.
    msg.match.in_port = in_port
    msg.idle_timeout = FLOW_IDLE_TIMEOUT
    msg.hard_timeout = FLOW_HARD_TIMEOUT
    # actions are applied in order.
    vlan_id_action = of.ofp_action_vlan_vid()
    # Its vlan_vid [NOT vlan_id]
    vlan_id_action.vlan_vid = vid
    msg.actions.append(vlan_id_action)
    msg.actions.append(of.ofp_action_output(port = out_port))
    #print "VID*100", vid, vlan_id_action, vlan_id_action.vlan_vid,msg.actions[0].vlan_vid, "VLAN PCP Value:",vlan_pcp_action.vlan_pcp
    msg.buffer_id = buf
    switch.connection.send(msg)
    print "Add and forwrd: ",switch,match,msg.actions

  def _remove_vlan_and_forward (self, switch, in_port, out_port, match, vid, buf = None):
    """Function to remove the vlan header and forward the packet."""
    msg = of.ofp_flow_mod()
    msg.match = match # match should be fine as we are installing the in_port separately.
    msg.match.in_port = in_port
    # update vlan ID for the new flow to match.
    msg.match.dl_vlan = vid
    msg.match.dl_type = 0x8100
    msg.idle_timeout = FLOW_IDLE_TIMEOUT
    msg.hard_timeout = FLOW_HARD_TIMEOUT
    # actions are applied in order.
    # first remove the vlan and then forward to destination.
    msg.actions.append(of.ofp_action_strip_vlan())
    msg.actions.append(of.ofp_action_output(port = out_port))
    msg.buffer_id = buf
    switch.connection.send(msg)
    print "Remove and forward: ",switch,match,msg.actions

  def _install_path (self, p, match, packet_in=None):
    # If chain is not enabled we do the default path installation.
    wp = WaitingPath(p, packet_in)
    for sw,in_port,out_port in p:
      self._install(sw, in_port, out_port, match)
      msg = of.ofp_barrier_request()
      sw.connection.send(msg)
      wp.add_xid(sw.dpid,msg.xid)

  def _install_path_chain(self, p, match, first_pathlet,
                          middle_pathlet, last_pathlet, vlan_id, packet_in=None):
    if first_pathlet:
      if (middle_pathlet == True ) or (last_pathlet == True):
        raise Exception("Invalid pathlet identifiers passed.")
      wp = WaitingPath(p, packet_in)
      # p is a list of tuples (switch, in_port, out_port)
      for index,(sw,in_port,out_port) in enumerate(p):
        print p, sw, in_port, out_port
        if index == 0:
          # Check if its the first switch in the whole path..
          self._add_vlan_and_forward (sw, in_port, out_port, match, vlan_id)
          msg = of.ofp_barrier_request()
          sw.connection.send(msg)
          wp.add_xid(sw.dpid,msg.xid)
          continue
        else:
          self._vlan_install(sw, in_port, out_port, match, vlan_id)
          msg = of.ofp_barrier_request()
          sw.connection.send(msg)
          wp.add_xid(sw.dpid,msg.xid)
    if last_pathlet:
      if (middle_pathlet == True ) or (first_pathlet == True):
        raise Exception("Invalid pathlet identifiers passed.")
      wp = WaitingPath(p, packet_in)
      for index,(sw,in_port,out_port) in enumerate(p):
        if index == len(p)-1:
          # Check if its the last switch in the whole path..
          self._remove_vlan_and_forward (sw, in_port, out_port, match, vlan_id)
          msg = of.ofp_barrier_request()
          sw.connection.send(msg)
          wp.add_xid(sw.dpid,msg.xid)
          continue
        self._vlan_install(sw, in_port, out_port, match, vlan_id)
        msg = of.ofp_barrier_request()
        sw.connection.send(msg)
        wp.add_xid(sw.dpid,msg.xid)
    if middle_pathlet:
      if (first_pathlet == True ) or (last_pathlet == True):
        raise Exception("Invalid pathlet identifiers passed.")
      wp = WaitingPath(p, packet_in)
      for index,(sw,in_port,out_port) in enumerate(p):
        self._vlan_install(sw, in_port, out_port, match, vlan_id)
        msg = of.ofp_barrier_request()
        sw.connection.send(msg)
        wp.add_xid(sw.dpid,msg.xid)

  def install_path (self, dst_sw, last_port, match, event, mb_locations):
    """Attempts to install a path between this switch and some destination
    """
    src = (self, event.port)
    dst = (dst_sw, last_port)
    pathlets = slick_controller_interface.get_path(src, mb_locations, dst)
    # Determine if we need to install the chains for the given flow or not.
    enable_chain = slick_controller_interface.chain_required(mb_locations)
    #if match.nw_proto == 17:
    #if match.nw_proto == 1:
    #  enable_chain = True

    vlan_id_forward_path = self._init_vlan_id(mb_locations, True)
    vlan_id_reverse_path = self._init_vlan_id(mb_locations, False)

    #vlan_id_forward_path = 0xa #self._init_vlan_id(mb_locations, True)
    #vlan_id_reverse_path = 0xa #self._init_vlan_id(mb_locations, False)
    mb_locations = [src] + mb_locations + [dst]

    # Each iteration is used
    print "PATHLETSSSSSSSSSSSSSSSSSS:", pathlets, "Number of pathlets: ",len(pathlets)
    for index in range(0, len(pathlets)):
      # Place we saw this ethaddr   -> loc = (self, event.port) 
      switch1 = mb_locations[index][0]
      switch2 = mb_locations[index+1][0]
      switch1_port = mb_locations[index][1]
      switch2_port = mb_locations[index+1][1]
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

      print "MB_LOCATIONS   :", mb_locations
      if not enable_chain:
        print "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        # This is the case where there are no middleboxes
        # registered. The lenght 2 is because of source
        # and destination switches.
        self._install_path(p, match, event.ofp)
        # Now reverse it and install it backwards
        # (we'll just assume that will work)
        p = [(sw,out_port,in_port) for sw,in_port,out_port in p]
        self._install_path(p, match.flip())
      else:
        print "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"
        # Handle middlebox machines here.
        # Install forward pathlets
        first_pathlet = False
        middle_pathlet = False
        last_pathlet = False
        if index == 0:
          first_pathlet = True
          print "FIRST PATHLET BEING INSTALLED.",self,p
          self._install_path_chain(p, match,
                                   first_pathlet, middle_pathlet,
                                   last_pathlet, vlan_id_forward_path, event.ofp)
        elif index == len(pathlets)-1:
          last_pathlet = True
          print "LAST PATHLET BEING INSTALLED.",self,p
          self._install_path_chain(p, match,
                                   first_pathlet, middle_pathlet,
                                   last_pathlet, vlan_id_forward_path, event.ofp)
        else:
          middle_pathlet = True
          print "MIDDLE PATHLET BEING INSTALLED.",self,p
          self._install_path_chain(p, match,
                                   first_pathlet, middle_pathlet,
                                   last_pathlet, vlan_id_forward_path, event.ofp)

        # Get the reverse path here.
        p = [(sw,out_port,in_port) for sw,in_port,out_port in p]
        first_pathlet = False
        middle_pathlet = False
        last_pathlet = False
        if index == 0:
          # On reverse path the "first pathlet"=>SourceSwitch_to_M1X should be like 
          # last pathlet, where vlan is removed and forward action
          # is installed.
          last_pathlet = True
          print "REVERSE: FIRST PATHLET BEING INSTALLED.",self,p
          self._install_path_chain(p, match,
                                   first_pathlet, middle_pathlet,
                                   last_pathlet, vlan_id_reverse_path, event.ofp)
        elif index == len(pathlets)-1:
          # On reverse path the "last pathlet" -> MnX_to_DestinationSwitch
          # should be like first pathlet, where vlan is added and forward action
          # is installed.
          first_pathlet = True
          print "REVERSE: LAST PATHLET BEING INSTALLED.",self,p
          self._install_path_chain(p, match,
                                   first_pathlet, middle_pathlet,
                                   last_pathlet, vlan_id_forward_path, event.ofp)
        else:
          # On middle pathlets the path is installed with VLAN
          # tags.
          middle_pathlet = True
          print "REVERSE: MIDDLE PATHLET BEING INSTALLED.",self,p
          self._install_path_chain(p, match,
                                   first_pathlet, middle_pathlet,
                                   last_pathlet, vlan_id_reverse_path, event.ofp)
        # Update the VLAN IDs for next pathlet.
        vlan_id_forward_path = self.update_vlan_id(vlan_id_forward_path, False)
        vlan_id_reverse_path = self.update_vlan_id(vlan_id_reverse_path, False)
        """
        self._install_path(p, match, event.ofp)
        # Now reverse it and install it backwards
        # (we'll just assume that will work)
        p = [(sw,out_port,in_port) for sw,in_port,out_port in p]
        self._install_path(p, match.flip())
        """
        pass

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
    element_descriptors = slick_controller_interface.get_steering(mac_map.get(packet.src), mac_map.get(packet.dst), flow_match)
    # Order of this list is important.
    # This is the same order in which we want the packets to traverse.
    # TODO just return the list of mac addresses instead of this (unordered) dictionary FIXME
    mb_locations = [ ]
    for element_id,mac_addr in element_descriptors.iteritems():
        #print element_id,mac_addr
        #print type(mac_addr)
        temp_loc = mac_map.get(mac_addr) 
        #print temp_loc
        mb_locations.append(temp_loc)
        if(temp_loc[0] not in middleboxes):
            middleboxes.append(temp_loc[0]) # Need these to not send packet out as packet is not reached.

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
        log.warning("Packet %s from %s arrived at %s.%i without flow",
                    packet, packet.src, dpid_to_str(self.dpid), event.port)
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
            log.warning("For each New Packet: Packet %s from %s arrived at %s.%i without flow",
                packet, packet.src, dpid_to_str(self.dpid), event.port)
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
            self.install_path(dest[0], dest[1], match, event, mb_locations)
        else:
            self.install_path(dest[0], dest[1], match, event, mb_locations)

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
