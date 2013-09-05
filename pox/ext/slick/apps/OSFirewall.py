"""
    Application that uses P0f element to detect OS using TCP streams.
"""
import collections

from pox.lib.addresses import IPAddr, EthAddr
import pox.lib.packet as pkt
import pox.openflow.libopenflow_01 as of

from slick.Application import Application

class OSFirewall(Application):
    def __init__(self, controller, ad):
        Application.__init__( self, controller, ad )
        self.flow = self.make_wildcard_flow()
        self.flow['tp_dst'] = 80
        self.ed1 = None

    def init(self):
        ed = self.apply_elem(self.flow, ["P0f"]) 
        if self.check_elems_installed(ed):
            self.ed1 = ed[0]
            self.installed = True
            print "P0f Element Installed."

    def configure_user_params(self):
        params = {}
        self.configure_elem(self.ed1, params)

    def handle_trigger(self, ed, msg):
        if(msg.has_key("p0f_trigger_type")):
            if(msg["p0f_trigger_type"] == "OSDetection"):
                self._handle_OSDetection(msg)

    def _handle_OSDetection(self, msg):
        if(msg.has_key("p0f_trigger_type")):
            if(msg["OS"] == "Linux"): #Don't have windows traffic. 
                src_ip = msg["src_ip"]
                print("Detected Linux OS at %s" % src_ip)

