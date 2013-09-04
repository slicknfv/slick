"""Use this application to block domain names.

This application uses two elements to detect and drop 
bad domain events.
"""
import logging

from slick.utils import packet_utils
from slick.Application import Application

class BlockDomains(Application):
    def __init__(self, controller, ad):
        Application.__init__( self, controller, ad )
        self.ed1 = None
        self.ed2 = None

    def init(self):
        # Provide the flow/flows that we want to process in the network
        flow = self.make_wildcard_flow()
        flow['tp_dst'] = 53
        fd= self.apply_elem(flow, ["DnsDpi"]) 
        if (fd >0):
            self.ed1 = fd
            self.installed = True
            logging.info("DnsDpi Element Installed.")

    def configure_user_params(self):
        params = {}
        # update the user provided configuration.
        self.configure_elem(self.ed1, params) 

    def handle_BadDomainEvent(self, fd, event):
        src_ip = packet_utils.ipstr_to_int(event["src_ip"])
        bad_domain_name = event["bad_domain_name"]
        # If we find a bad domain then we subject
        # the flow to Drop Element.
        flow = self.make_wildcard_flow()
        flow['nw_src'] = src_ip
        # Need to call it for new hosts that
        # lookup blocked domains.
        fd= self.apply_elem(flow, ["Drop"]) 
        if (fd > 0):
            self.ed2 = fd
        else:
            print "Error: Unable to install the Drop Element."

    def handle_trigger(self, fd, msg):
        if(msg["dns_dpi_type"] == "BadDomainEvent"):
            self.handle_BadDomainEvent(fd,msg)

    def configure_trigger(self):
        # get the location of mb from the controller. from function_map
        # get the ip address of the mb from the controller. machine_map
        # There is already the function installed on the machine 
        # set the variables on the controller.
        pass
