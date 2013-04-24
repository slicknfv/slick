import networkmaps
from networkmaps import FunctionMap,Policy,MachineMap

# Get source and destination of the flow.
class RouteCompiler():
    def __init__(self,cntxt):
        self.cntxt = cntxt
        # networkmaps
        self.fmap = FunctionMap(None)
        self.policy = Policy(None)
        self.mmap = MachineMap()
        self.application_handles = {}

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
        self.mmap.update_ip_dpid_mapping(dpid,0,flow)
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

