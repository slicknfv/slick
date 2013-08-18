"""
    TwoLoggers: One Application, Two Function Instances
"""
from Application import Application

class TwoLoggers(Application):
    def __init__(self,controller,ad):
        Application.__init__( self, controller, ad )

        self.conf = False   # Set this to true to update the configure
        self.count_thresh = 9999
        self.fd = None      # Its the list of function descriptors used by the application.


    def configure_user_params(self):
        print "TwoLoggers: got configure_user_params -- nothing to do"

    def handle_trigger( self, ed, msg):
        print "TwoLoggers: handle_trigger element descriptor",fd,"called with message",msg

    def init(self):
        # Start the first Logger:
        parameters = {"file_name":"/tmp/dns_log"}
        flow = {}
        flow["dl_src"] = None; flow["dl_dst"] = None; flow['dl_vlan'] = None; flow['dl_vlan_pcp'] = None; flow['dl_type'] = None; flow['nw_src'] = None; flow['nw_dst'] = None;flow['nw_proto'] = None ;flow['tp_src'] = None;flow['tp_dst'] = 53

        self.fd1 = self.apply_elem( flow, "Logger", parameters ) 
        
        # Start the second Logger
        parameters = {"file_name":"/tmp/http_log"}
        flow['tp_src'] = 80
        flow['tp_dst'] = None
        self.fd2 = self.apply_elem( flow, "Logger", parameters ) 
        
        if((self.fd1 > 0) and (self.fd2 > 0)):     #=> we have sucess
            self.installed = True
            print "TwoLoggers: created two elements with fds",self.fd1,"and",self.fd2
