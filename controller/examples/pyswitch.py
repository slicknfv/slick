# Copyright 2008 (C) Nicira, Inc.
# 
# This file is part of NOX.
# 
# NOX is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# NOX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with NOX.  If not, see <http://www.gnu.org/licenses/>.
# Python L2 learning switch 
#
# ----------------------------------------------------------------------
#
# This app functions as the control logic of an L2 learning switch for
# all switches in the network. On each new switch join, it creates 
# an L2 MAC cache for that switch. 
#
# In addition to learning, flows are set up in the switch for learned
# destination MAC addresses.  Therefore, in the absence of flow-timeout,
# pyswitch should only see one packet per flow (where flows are
# considered to be unidirectional)
#

from nox.lib.core     import *

from nox.lib.packet.ethernet     import ethernet
from nox.lib.packet.packet_utils import mac_to_str, mac_to_int

from twisted.python import log

import logging
from time import time
from socket import htons
from struct import unpack
from nox.lib.packet.ipv4 import ipv4

#Need this routing module
from nox.netapps.authenticator.pyflowutil import Flow_in_event
from nox.netapps.routing import pyrouting
#Need this for locations.
from nox.netapps.authenticator import pyauth

from nox.coreapps.messenger.pyjsonmsgevent import JSONMsg_event
#from nox.coreapps.messenger.pymsgevent import Msg_event
import json

from msmessageproc import MSMessageProcessor
from networkmaps import FunctionMap,MachineMap,Policy
from nox.lib.netinet.netinet import ethernetaddr, ipaddr, create_eaddr,create_bin_eaddr, create_ipaddr, c_htonl, c_ntohl
#routing
from nox.lib.netinet import netinet
from socket import ntohs, htons
import socket
U32_MAX = 0xffffffff
DP_MASK = 0xffffffffffff
PORT_MASK = 0xffff

BROADCAST_TIMEOUT   = 2 # was 60
FLOW_TIMEOUT        = 0xffff

logger = logging.getLogger('nox.coreapps.examples.pyswitch')

# Global pyswitch instance 
inst = None

# Timeout for cached MAC entries
CACHE_TIMEOUT = 5

# --
# Responsible for timing out cache entries.
# Is called every 1 second.
# --
#def timer_callback():
#    global inst
#
#    curtime  = time()
#    for dpid in inst.st.keys():
#        for entry in inst.st[dpid].keys():
#            if (curtime - inst.st[dpid][entry][1]) > CACHE_TIMEOUT:
#                log.msg('timing out entry'+mac_to_str(entry)+str(inst.st[dpid][entry])+' on switch %x' % dpid, system='pyswitch')
#                inst.st[dpid].pop(entry)
#
#    inst.post_callback(1, timer_callback)
#    return True

class pyswitch(Component):
    def __init__(self, ctxt):
        global inst
        Component.__init__(self, ctxt)
        self.st = {}

        inst = self
        self.function_descriptor = int(1)
        #self.application_descriptor = int(1)
        self.prev_time = 0
        #routing
        self.route_compiler =  RouteCompiler(inst)
        # JSON Messenger Handlers
        self.json_msg_events = {}
        self.ms_msg_proc = MSMessageProcessor(inst)
        self.app_initialized = False
	# Use this module for routing.
        #routing = self.resolve(pyrouting.PyRouting)
	#self.route_compiler =  RouteCompiler(routing)

    def install(self):
        inst.register_for_packet_in(self.packet_in_callback)
        inst.register_for_datapath_leave(self.datapath_leave_callback)
        inst.register_for_datapath_join(self.datapath_join_callback)
        inst.post_callback(1, self.timer_callback)
        print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
	self.app_installations()

    def app_installations(self):
        # For the  MSManager for JSONMsgs
        JSONMsg_event.register_event_converter(self.ctxt)
        self.register_handler(JSONMsg_event.static_get_name(), self.json_message_handler)
        #self.register_handler(pyauth.Host_join_event.static_get_name(), self.host_join_event_handler)
        #routing
        self.register_handler(Flow_in_event.static_get_name(),self.route_compiler.handle_flow_in)              
        self.register_for_barrier_reply(self.route_compiler.handle_barrier_reply)     

    def timer_callback(self):
        global inst
        curtime  = time()

        # initialize the applications.
        for app in self.ms_msg_proc.app_handles:
            if not (app.installed):
                app.init()
                print app

        #Configure
        for fd in self.route_compiler.application_handles:
            app_handle = self.route_compiler.get_application_handle(fd)
            app_handle.configure_user_params()
            if (curtime - self.prev_time > CACHE_TIMEOUT):
                self.prev_time = curtime
        inst.post_callback(5, self.timer_callback)
        return True

    def json_message_handler(self,pyevent):
        rcvd_msg = json.loads(pyevent.jsonstring)
        reply = self.ms_msg_proc.process_msg(pyevent,rcvd_msg)#Takes a dict  and reference to pyswitch object and returns dict
        if(reply):
            #print "YYYYYYYYYYYYYYYY",reply
            if(reply.has_key("dummy")): # Discard this reply to keep the connection up.
                return STOP
            pyevent.reply(json.dumps(reply))
            return STOP
	# --
	# Packet entry method.
	# Drop LLDP packets (or we get confused) and attempt learning and
	# forwarding
	# --
    def packet_in_callback(self,dpid, inport, reason, len, bufid, packet):
	if not packet.parsed:
	    log.msg('Ignoring incomplete packet',system='pyswitch')
	if not inst.st.has_key(dpid):
	    log.msg('registering new switch %x' % dpid,system='pyswitch')
	    inst.st[dpid] = {}
	# don't forward lldp packets    
	if packet.type == ethernet.LLDP_TYPE:
	    return CONTINUE

        flow = extract_flow(packet)
        
	return CONTINUE


    """
    Controller to Application Functions
    """
    # return function descriptor.
    def apply_func(self, app_desc,flow, function_name,parameters,application_object):
        self.function_descriptor += 1
        #self.application_descriptor = app_desc#+= 1 # App is providing the right application descriptor to the controller.
        if(self.route_compiler.is_installed(app_desc)):# We have the application installed
            print "Creating another function for application: ",app_desc
        ip_addr = self.route_compiler.fmap.get_machine_for_function()
        if(ip_addr == None): # There is no machine registerd for function installation.
            print "Could not find the Middlebox"
            return -1
        msg_dst = ip_addr
        mac_addr = self.route_compiler.fmap.fd_machine_map[ip_addr]
        self.route_compiler.fmap.update_function_machine(ip_addr,mac_addr,self.function_descriptor)
        self.route_compiler.policy.add_flow(None,flow,{self.function_descriptor:function_name}) #Function descriptor 
        self.route_compiler.update_application_handles(self.function_descriptor,application_object,app_desc)
        #msg = {"type":"install", "fd":self.function_descriptor, "flow":flow,"function_name":function_name,"params":{"k1":"dummy"}}
        if(self.ms_msg_proc.send_install_msg(self.function_descriptor,flow,function_name,parameters,msg_dst)):
            return self.function_descriptor
        else:
            return -1

                
    #This function takes the src dpid, dst dpid and list of machines .. the
    #
    def pickMBMachine(self, src, dst, machinelist):
        shortestPath = 0
        shortestPath_MB = machinelist[0]
        for mb in machinelist:
            mb_dpid = XXXXXXXXXXXXXXXXXXXXXX
            route1 = pyrouting.Route()
            route1.id.src = src
            route1.id.dst = mb_dpid
            route2 = pyrouting.Route()
            route2.id.src = mb_dpid
            route2.id.dst = dst
            if( len(route1.path) + len(route2.path) < shortestPath):
                shortestPath = len(route1.path) + len(route2.path)
                shortestPath_MB = mb
    return mb

    def configure_func(self,app_desc,fd,application_conf_params):
        if(self.route_compiler.application_handles.has_key(fd)):
            if(self.route_compiler.is_allowed(app_desc,fd)):
                msg_dst = self.route_compiler.fmap.get_ip_addr_from_func_desc(fd)
                app_handle = self.route_compiler.get_application_handle(fd) # not requied by additional check 
                #print "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV",str(msg_dst)
                if((msg_dst != None) and (app_handle != None)):
                    self.ms_msg_proc.send_configure_msg(fd,application_conf_params,msg_dst)

    #TODO:
    def remove_func(self,app_desc,fd):
        # roll back
        #self.route_compiler.fmap.update_function_machine(ip_addr,None,self.function_descriptor)
        desc_removed = self.route_compiler.fmap.del_function_desc(fd)
        #self.route_compiler.policy.del_flow(None,flow,{self.function_descriptor:function_name})
        #self.route_compiler.update_application_handles(self.function_descriptor,application_object,self.application_descriptor)

    def datapath_leave_callback(self,dpid):
	logger.info('Switch %x has left the network' % dpid)
	
    def datapath_join_callback(self,dpid, stats):
	logger.info('Switch %x has joined the network' % dpid)
	# Make sure we get the full DNS packet at the Controller
	#self.install_datapath_flow(dp_id=dpid, 
	#    attrs = { core.DL_TYPE : ethernet.IP_TYPE,
	#        core.NW_PROTO : ipv4.UDP_PROTOCOL,
	#        core.TP_SRC : 53 },
	#        idle_timeout = openflow.OFP_FLOW_PERMANENT, hard_timeout = openflow.OFP_FLOW_PERMANENT,priority=0xffff,
	#        actions = [[openflow.OFPAT_OUTPUT, [9000, openflow.OFPP_CONTROLLER]]])
	#return CONTINUE


    def getInterface(self):
        return str(pyswitch)

def getFactory():
    class Factory:
        def instance(self, ctxt):
            return pyswitch(ctxt)

    return Factory()

# Get source and destination of the flow.

class RouteCompiler():
    def __init__(self,cntxt):
        self.cntxt = cntxt
        # routing
        self.routing = self.cntxt.resolve(pyrouting.PyRouting)
        # list of routes installations that are waiting for barrier_replies
        # (holds barrier xids and packet out info)
        self.pending_routes = []
        # networkmaps
        self.fmap = FunctionMap(None)
        self.policy = Policy(None)
        self.mmap = MachineMap()
        self.application_handles = {}
        self.auth = self.cntxt.resolve(pyauth.PyAuth)

    # dumb function.
    def __convert_flow(self,event):
        import binascii
        import array
        src = str(event.dl_src) 
        dst = str(event.dl_dst)
        dl_src = array.array('B',binascii.unhexlify(src.replace(b":",b"")))
        dl_dst = array.array('B',binascii.unhexlify(dst.replace(b":",b"")))

        attrs = {}
        attrs[core.DL_SRC] = dl_src
        attrs[core.DL_DST] = dl_dst
        attrs[core.DL_TYPE] = event.dl_type
        attrs[core.DL_VLAN] = event.dl_vlan
        attrs[core.DL_VLAN_PCP] = event.dl_vlan_pcp

        attrs[core.NW_SRC] = event.nw_src
        attrs[core.NW_DST] = event.nw_dst
        attrs[core.NW_PROTO] = event.nw_proto
        #attrs[core.NW_TOS] = event.tos

        attrs[core.TP_SRC] = event.tp_src
        attrs[core.TP_DST] = event.tp_dst
        return attrs

    def handle_functions(self,event):
        dpid = netinet.create_datapathid_from_host(event.datapath_id)
        try:
            packet = ethernet(array.array('B', event.buf))
        except IncompletePacket, e:
            logger.error('Incomplete Ethernet header')
        flow = extract_flow(packet)
        #update ip to dpid mapping.
        #print "BILAL"*50,self.mmap.ip_dpid
        self.mmap.update_ip_dpid_mapping(dpid,flow)
        print flow
        #flow = self.__convert_flow(event.flow)
        inport = event.src_location['port']


        function_descriptors = self.policy.get_flow_functions(inport,flow) # Find the function descriptors.
        func_loc = None
        print "XXXXXXXXXXXXXXXXXXXXXX",function_descriptors
        for func_desc,function_name in function_descriptors.iteritems():
            print func_desc,function_name
            # This gives us function location
            ip_addr = self.fmap.get_ip_addr_from_func_desc(func_desc) 
            mac_addr = self.fmap.fd_machine_map[ip_addr] 
            nw_addr = socket.inet_ntoa(ip_addr) # already aton 
            dl_addr = create_eaddr(mac_addr) 
            print "L"*20,socket.inet_ntoa(ip_addr),dl_addr
            #self.auth.get_authed_locations(dl_addr,nw_addr)
            print event.datapath_id,type(event.datapath_id)
            func_loc = (event.datapath_id,2)#self.fmap.get_closest_location(event.datapath_id,function_name)
            #self.copy_flow(event,func_loc) 

        # REWRITE
        """
        # We have a flow what functions should we apply on it.
        functions_dict = self.policy.get_flow_functions(inport,flow) # For the given flow find the policy
        sorted(functions_dict, key=lambda key: functions_dict[key])
        print functions_dict
        for func_order,function_name in functions_dict.iteritems():
            print func_order,function_name
            self.fmap.init_switch(event.datapath_id,2,["DNS-DPI"]) # This is hard coded for now
            function_locations = self.fmap.get_function_locations(function_name)
            print function_locations # a dict with keys(dpid,port)
            if not function_locations:
                #location = install_function(function_name)
                self.update_function_desc
            else: # function is already present in the network.
                #location_dpid = self.fmap.get_closest_location(dpid,function_name)
                location_dpid = self.fmap.get_closest_location(event.datapath_id,function_name)
                location_port = None
                # Get the port of the closes_location dpid for the function requested.
                for key in function_locations:
                    print key # key is a tuple(dpid,port)
                    if(key[0] == location_dpid):
                        location_port = key[1]
                        pass
                    pass
                func_loc = (location_dpid,location_port)
                #self.install_route(event,func_loc)
                self.copy_flow(event,func_loc) 
                pass
            pass
        pass
        """
        self.install_route(event,func_loc)
        print "ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ"

    def update_application_handles(self,fd,application_object,app_desc):
        if not (self.application_handles.has_key(fd)):
            self.application_handles[fd]= (application_object,app_desc) 
        else:
            print "ERROR: This should not happen"

    # Given a function descriptor return the application handle.
    def get_application_handle(self,fd):
        if (self.application_handles.has_key(fd)):
            return self.application_handles[fd][0] 
        else:
            print "ERROR: There is no application for the function descriptor:",fd
            return None

    # Given a function descriptor return the application descriptor
    def get_application_descriptor(self,fd):
        if (self.application_handles.has_key(fd)):
            return self.application_handles[fd][1]
        else:
            print "ERROR: There is no application for the function descriptor:",fd
            return None
    # return True if app_desc is registered as application for fd
    def is_allowed(self,app_desc,fd):
        temp_app_desc = self.get_application_descriptor(fd)
        if(temp_app_desc == app_desc):
            return True
        else:
            return False

    # return True if app_desc is registered as application.
    def is_installed(self,app_desc):
        for fd,app in self.application_handles.iteritems():
            if(app[1] == app_desc):
                return True
        return False

    def handle_flow_in(self, event):
        if not event.active:
            return CONTINUE
        self.handle_functions(event)


    # does what the name says on the dpid in func_loc adds an entry for the traffic to be sent to the DNS-DPI box.
    def copy_flow(self,event,func_loc):
        print "CAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAALLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL"
        try:
            packet = ethernet(array.array('B', event.buf))
        except IncompletePacket, e:
            logger.error('Incomplete Ethernet header')
        flow = extract_flow(packet)
        inport = event.src_location['port']
        dpid = func_loc[0] # only add extra instruction of copying on the dpid where we want a copy.
        port = func_loc [1]
        
        flow[core.IN_PORT] = inport
        actions = [[openflow.OFPAT_OUTPUT, [0, port]]]
        inst.install_datapath_flow(dp_id=dpid, attrs=flow, idle_timeout=CACHE_TIMEOUT, 
                                   hard_timeout=openflow.OFP_FLOW_PERMANENT, actions=actions,
                                   #buffer_id = bufid, priority = 0x8000,#openflow.OFP_DEFAULT_PRIORITY,
                                   priority = openflow.OFP_DEFAULT_PRIORITY,
                                   inport = inport, packet=event.buf)
                           
    def install_route_helper(self,event,indatapath, src, inport, dst, outport):
        route = pyrouting.Route()
        route.id.src = src
        route.id.dst = dst
        if self.routing.get_route(route):
            checked = True
            if self.routing.check_route(route, inport, outport):
                logger.debug('Found route %s.' % hex(route.id.src.as_host())+\
                             ':'+str(inport)+' to '+hex(route.id.dst.as_host())+\
                             ':'+str(outport))
                if route.id.src == route.id.dst:
                    firstoutport = outport
                else:
                    firstoutport = route.path[0].outport
                
                p = []
                if route.id.src == route.id.dst:
                    #print "ROUTING222",route.id.src,route.id.dst,inport,indatapath,firstoutport
                    p.append(str(inport))
                    p.append(str(indatapath))
                    p.append(str(firstoutport))
                else:
                    s2s_links = len(route.path)
                    p.append(str(inport))
                    p.append(str(indatapath))
                    for i in range(0,s2s_links):
                        p.append(str(route.path[i].dst))
                    p.append(str(outport))
                
                print "SETTING UP Route:",route
                print "ROUTING",route.id.src,route.id.dst,inport,outport
                print type(inport),type(outport),inport,outport
                self.routing.setup_route(event.flow, route, inport, \
                                         outport, FLOW_TIMEOUT, [], True)
                
                # Send Barriers
                pending_route = []
                # Add barrier xids
                for dpid in p[1:len(p)-1]:
                    logger.debug("Sending barrier to %s", dpid)
                    pending_route.append(self.cntxt.send_barrier(int(dpid,16)))
                # Add packetout info
                pending_route.append([indatapath, inport, event])
                # Store new pending_route (waiting for barrier replies)
                self.pending_routes.append(pending_route)
                
                
                # Send packet out (do it after receiving barrier(s))
                if indatapath == route.id.src or \
                    pyrouting.dp_on_route(indatapath, route):
                    pass
                #self.routing.send_packet(indatapath, inport, \
                #    openflow.OFPP_TABLE,event.buffer_id,event.buf,"", \
                #    False, event.flow)
                else:
                    logger.debug("Packet not on route - dropping.")
                return True
            else:
                logger.debug("Invalid route between %s." \
                             % hex(route.id.src.as_host())+':'+str(inport)+' to '+\
                             hex(route.id.dst.as_host())+':'+str(outport))
        else:
            logger.debug("No route between %s and %s." % \
                (hex(route.id.src.as_host()), hex(route.id.dst.as_host())))
    #return CONTINUE

    # Use the func_loc to provide as a location for middlebox function.
    def install_route(self,event,func_loc):
        indatapath = netinet.create_datapathid_from_host(event.datapath_id)
        route = pyrouting.Route()

        sloc = event.route_source
        if sloc == None:
            sloc = event.src_location['sw']['dp']
            route.id.src = netinet.create_datapathid_from_host(sloc)
            inport = event.src_location['port']
            sloc = sloc | (inport << 48)
        else:
            route.id.src = netinet.create_datapathid_from_host(sloc & DP_MASK)
            inport = (sloc >> 48) & PORT_MASK
        if len(event.route_destinations) > 0:
            dstlist = event.route_destinations
        else:
            dstlist = event.dst_locations
        
    
        #if isinstance(func_loc,tuple):
        #    dstlist.append(func_loc)
        checked = False
        for dst in dstlist:
            """
            print "LOOOP"*20
            print dst
            print type(func_loc),func_loc
            """
            if isinstance(dst, dict):
                if not dst['allowed']:
                    continue
                dloc = dst['authed_location']['sw']['dp']
                #print "ROUTING111",type(dloc),dloc
                #print func_loc
                route.id.dst = netinet.create_datapathid_from_host(dloc & DP_MASK)
                #print type(route.id.dst),route.id.dst
                outport = dst['authed_location']['port']
                #print type(dloc),dloc
                #print type(outport),outport
                dloc = dloc | (outport << 48)
                print type(dloc),dloc
                print type(route.id.dst),route.id.dst
                print type(outport),outport
            else:
                dloc = dst
                route.id.dst = netinet.create_datapathid_from_host(dloc & DP_MASK)
                outport = (dloc >> 48) & PORT_MASK
            """
            elif (func_loc != None) and isinstance(dst, tuple):
                dloc = 99999999999#func_loc[0] # dpid
                out =  func_loc[1]
                route.id.dst = func_loc[0]#netinet.create_datapathid_from_host(dloc & DP_MASK)
                outport = out#(dloc >> 48) & PORT_MASK
                print type(dloc),dloc
                print type(route.id.dst),route.id.dst
                print type(outport),outport
                pass
            """
            if dloc == 0:
                continue
            src = route.id.src
            inport = inport 
            if(func_loc != None):
                mb = netinet.create_datapathid_from_host(func_loc[0] & DP_MASK)#func_loc[0]
                mb_port = func_loc[1]
                print "Function Location 1"
                ##THEO: call the helper function here
                checked = self.install_route_helper(event,indatapath,src,inport, mb,mb_port)
                print "Function Location 2"
                dst_loc = netinet.create_datapathid_from_host(dloc & DP_MASK)
                checked = self.install_route_helper(event,indatapath,mb,mb_port,dst_loc,outport)
            else:
                print "Direct Path"
                checked = self.install_route_helper(event,indatapath,src,inport, route.id.dst,outport)
        if not checked:
            if event.flow.dl_dst.is_broadcast():
                logger.debug("Setting up FLOOD flow on %s", str(indatapath))
                self.routing.setup_flow(event.flow, indatapath, \
                    openflow.OFPP_FLOOD, event.buffer_id, event.buf, \
                        BROADCAST_TIMEOUT, "", \
                        event.flow.dl_type == htons(ethernet.IP_TYPE))
            else:
                inport = ntohs(event.flow.in_port)
                logger.debug("Flooding")
                print "WARNING","FLOODING"*20
                self.routing.send_packet(indatapath, inport, \
                    openflow.OFPP_FLOOD, \
                    event.buffer_id, event.buf, "", \
                    event.flow.dl_type == htons(ethernet.IP_TYPE),\
                    event.flow)
        else:
            logger.debug("Dropping packet")

        return CONTINUE

    def handle_barrier_reply(self, dpid, xid):
        # find the pending route this xid belongs to
        intxid = c_ntohl(xid)
        for pending_route in self.pending_routes[:]:
            if intxid in pending_route:
                pending_route.remove(intxid)
                # If this was the last pending barrier_reply_xid in this route
                if len(pending_route) == 1:
                    logger.debug("All Barriers back, sending packetout")
                    indatapath, inport, event = pending_route[0]
                    self.routing.send_packet(indatapath, inport, \
                        openflow.OFPP_TABLE,event.buffer_id,event.buf,"", \
                        False, event.flow)

                    self.pending_routes.remove(pending_route)
                    
        return CONTINUE

