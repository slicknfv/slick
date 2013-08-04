

class DNSHandlers(Triggers):
    def __init__(self,inst):
        self.cntxt = inst
        self.installed = False
	self.DNS_BLOCK_TIMEOUT = 1000#0xffff
        #set the configuration variables here:
        self.visit_threshold = 3 
        # TODO: for function specification.
        #self.func_spec = load_func_spec("DNS-DPI")


    def handle_BadDomainEvent(self,event):
        #src_ip = socket.inet_aton(event["src_ip"])
        src_ip = event["src_ip"]
        domain_ip_list = event["domain_ip_list"]
        src_dpid = self.cntxt.route_compiler.mmap.get_dpid(src_ip)# Bilal idiot.
        self._block_ip_list(src_dpid,src_ip,domain_ip_list)

    def handle_trigger(self,msg):
        if(msg["type"] == "BadDomainEvent"):
            del msg["type"]
            json_str = json.dumps(msg)
            data = jsonpickle.decode(json_str)
            print type(data) # Its a dict
            self.handle_BadDomainEvent(data)

    def initialize(self):
        #get the function 
        pass

    # Set all the configurations based on the paramters inside the conf 
    def configure_trigger(self):
        pass
        # get the location of mb from the controller. from function_map
        # get the ip address of the mb from the controller. machine_map
        # There is already the function installed on the machine 
        # set the variables on the controller.
        pass

    def _block_ip_list(self,src_dpid,s_ip,domain_ip_list):
        src_dpid = 5 # Hardcoded for testing the trigger module as self.mmap.update_ip_dpid_mapping() is not called with trigger module.  REMOVE it with live traffic.
	src_ip = s_ip
	for item in domain_ip_list:
            print type(src_dpid)
            print src_dpid
	    dst_ip = item
	    print src_ip,dst_ip
	    ## Make sure we get the full DNS packet at the Controller
	    #actions = []
	    #self.cntxt.install_datapath_flow(src_dpid, 
	    #    		{ core.DL_TYPE : ethernet.IP_TYPE,
	    #    		    core.NW_SRC : src_ip,
	    #    		   core.NW_DST:dst_ip },
            #                       self.DNS_BLOCK_TIMEOUT,self.DNS_BLOCK_TIMEOUT, #
            #                       actions,buffer_id = None, priority=0xffff)
            msg = of.ofp_flow_mod()
            msg.priority = 42
            msg.match.dl_type = 0x800
            msg.match.nw_src = IPAddr(src_ip)
            msg.match.nw_dst = IPAddr(dst_ip)
            dst_port = of.OFPP_NONE
            msg.actions.append(of.ofp_action_output(dst_port))
            self.cntxt.connection.send(msg)



class DnsDpiFunctionApp():
    def __init__(self,inst,AD,flows):
        self.cntxt = inst
        self.num_functions = 1
        self.app_d = AD
        self.fd = [] #List of functions used by this application.
        self.conf = 0
        self.installed = False
	self.DNS_BLOCK_TIMEOUT = 1000#0xffff
        #set the configuration variables here:
        self.visit_threshold = 3 
        self.flows = flows
        self.trigger_function_installed = False


    def init(self):
        for index in range(0,self.num_functions): # If the flows are same then it will overwrite the flow to function descriptor
            print "apply_elem"
            parameters = {}
            fd= self.cntxt.apply_elem(self.app_d,self.flows[index],"DNS_DPI",parameters,self) 
            if((fd >0)):#=> we have sucess
                self.fd.append(fd)
                self.installed = True
                print "DNS_DPI Function Installed."

    def configure_user_params(self):
        if (self.conf < self.num_functions): # Need to call configure_func twice since this application has two functions instantiated
            params = {}
            self.cntxt.configure_func(self.app_d,self.fd[self.conf],params) # Call connfigure_func with same app if and different function descriptors.
            self.conf +=1

    def handle_BadDomainEvent(self,fd,event):
        #src_ip = socket.inet_aton(event["src_ip"])
        src_ip = ipstr_to_int(event["src_ip"])
        bad_domain_name = event["bad_domain_name"]
        src_dpid = self.cntxt.route_compiler.mmap.get_dpid(src_ip)
        # DROP-FUNCTION
        flow = {}
        flow["dl_src"] = None; flow["dl_dst"] = None; flow['dl_vlan'] = None; flow['dl_vlan_pcp'] = None; flow['dl_type'] = None; flow['nw_src'] = src_ip; flow['nw_dst'] = None;flow['nw_proto'] = None ;flow['tp_src'] = None;flow['tp_dst'] = None
        parameters = {}
        if not self.trigger_function_installed:
            fd= self.cntxt.apply_elem(self.app_d,flow,"DROP",parameters,self) 
            if((fd >0)):#=> we have sucess
                self.fd.append(fd)
                self.trigger_function_installed = True
        #####################################################################
        # Use Below code to block the ip address
        #####################################################################
        #actions = []
        #print type(src_dpid)
        #print src_dpid
        #src_dpid = 5
        #self.cntxt.install_datapath_flow(src_dpid, { core.DL_TYPE : ethernet.IP_TYPE,core.NW_SRC : src_ip},
        #                       self.DNS_BLOCK_TIMEOUT,self.DNS_BLOCK_TIMEOUT, #
        #                       actions,buffer_id = None, priority=0xffff)

    def handle_trigger(self,fd,msg):
        if(msg["dns_dpi_type"] == "BadDomainEvent"):
            self.handle_BadDomainEvent(fd,msg)

    # Set all the configurations based on the paramters inside the conf 
    def configure_trigger(self):
        pass
        # get the location of mb from the controller. from function_map
        # get the ip address of the mb from the controller. machine_map
        # There is already the function installed on the machine 
        # set the variables on the controller.
        pass

    def _block_ip_list(self,src_dpid,s_ip,domain_ip_list):
        src_dpid = 5 # Hardcoded for testing the trigger module as self.mmap.update_ip_dpid_mapping() is not called with trigger module.  REMOVE it with live traffic.
	#src_ip = ipstr_to_int(s_ip)
        src_ip = s_ip
	for item in domain_ip_list:
            print type(src_dpid)
            print src_dpid
	    dst_ip = item
	    print src_ip,dst_ip
            msg = of.ofp_flow_mod()
            msg.priority = 42
            msg.match.dl_type = pkt.ethernet.IP_TYPE
            msg.match.nw_src = IPAddr(src_ip)
            msg.match.nw_dst = IPAddr(dst_ip)
            msg.idle_timeout = self.DNS_BLOCK_TIMEOUT 
            msg.hard_timeout = self.DNS_BLOCK_TIMEOUT
            # Not specifying action to drop the packets.
            #dst_port = of.OFPP_NONE
            #msg.actions.append(of.ofp_action_output(dst_port))
            connection = self.cntxt.get_connection(src_dpid)
            connection.send(msg)
