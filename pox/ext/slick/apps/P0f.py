############
# p0f
############
class P0f():
    def __init__(self,inst,AD,flows):
        self.cntxt = inst
        self.num_functions = 1
        self.app_d = AD
        self.fd = [] #List of functions used by this application.
        self.conf = 0
        self.installed = False
        self.flows = flows
        #App specific
        self.trigger_function_installed = False
        self.block_ports = defaultdict(list)
        self.block_ports["WindowsXP"]=[137,138,139]
        self.block_ports["FreeBSD"].append(40000)#rand()
        self.block_ports["Linux"].append(50000)#rand()


    def init(self):
        for index in range(0,self.num_functions): 
            print "apply_elem"
            parameters = {}
            fd= self.cntxt.apply_elem(self.app_d,self.flows[index],"p0f",parameters,self) 
            if((fd >0)):#=> we have sucess
                self.fd.append(fd)
                self.installed = True
                print "p0f Function Installed."

    def configure_user_params(self):
        if (self.conf < self.num_functions): 
            params = {}
            self.cntxt.configure_func(self.app_d,self.fd[self.conf],params) 
            self.conf +=1

    def handle_trigger(self,fd,msg):
        #print msg
        if(msg.has_key("p0f_trigger_type")):
            if(msg["p0f_trigger_type"] == "OSDetection"):
                self._handle_OSDetection(fd,msg)

    def _handle_OSDetection(self,fd,msg):
        if(msg.has_key("p0f_trigger_type")):
            if(msg["OS"] == "Linux"): #Don't have windows traffic. 
                src_ip = msg["src_ip"]
                if(self.block_ports.has_key("Linux")):
                    self._block_ports(src_ip,self.block_ports["Linux"])

    def _block_ports(self,s_ip,port_numbers):#port numbers is a list
        src_dpid = 5 # Hardcoded for testing the trigger module as self.mmap.update_ip_dpid_mapping() is not called with trigger module.  REMOVE it with live traffic.
	src_ip = s_ip
	## Make sure we get the full DNS packet at the Controller
	actions = []
        for port_number in port_numbers:
            # This is the API provided by OpenFlow switch.
            #PROBLEM: This rule is not installing the port number.
	    #self.cntxt.install_datapath_flow(src_dpid, 
	    #		{ core.DL_TYPE : ethernet.IP_TYPE,
	    #		    core.NW_DST : src_ip, #Block incoming netbios traffic.
	    #		   core.TP_DST: port_number },
            #                   120,120, #
            #                   actions,buffer_id = None, priority=0xffff)

            #PROBLEM: This rule is not installing the port number.
            msg = of.ofp_flow_mod()
            msg.priority = 42
            msg.match.dl_type = pkt.ethernet.IP_TYPE
            msg.match.nw_dst = IPAddr(src_ip)
            msg.match.tp_dst = port_number # Block all ports 1-by-1
            msg.idle_timeout = 120 
            msg.hard_timeout = 120
            # Not specifying action to drop the packets.
            connection = self.cntxt.get_connection(src_dpid)
            connection.send(msg)

    # how to drop packet.
    def drop (self,duration = None):
      if duration is not None:
        if not isinstance(duration, tuple):
          duration = (duration,duration)
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match.from_packet(packet)
        msg.buffer_id = event.ofp.buffer_id
        self.connection.send(msg)
