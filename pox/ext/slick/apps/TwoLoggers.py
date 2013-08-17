"""
    TwoLoggers: One Application, Two Function Instances
"""
class TwoLoggers():
    def __init__(self,inst,AD):
        self.cntxt = inst
        self.app_d = AD
        self.installed = False # To check if the app is installed
        self.conf = False # Set this to true to update the configure

        self.count_thresh = 9999
        self.fd =None # Its the list of function descriptors used by the application.


    def configure_user_params(self):
        print "TwoLoggers: got configure_user_params -- nothing to do"

    def handle_trigger(self,fd,msg):
        print "TwoLoggers: handle_trigger function descriptor",fd
        print "TwoLoggers: handle_trigger called",msg

    def init(self):
        # Start the first Logger:
        parameters = {"file_name":"/tmp/dns_log"}
        flow = {}
        flow["dl_src"] = None; flow["dl_dst"] = None; flow['dl_vlan'] = None; flow['dl_vlan_pcp'] = None; flow['dl_type'] = None; flow['nw_src'] = None; flow['nw_dst'] = None;flow['nw_proto'] = None ;flow['tp_src'] = None;flow['tp_dst'] = 53

        self.fd1 = self.cntxt.apply_elem(self.app_d,flow,"Logger",parameters,self) 
        
        # Start the second Logger
        parameters = {"file_name":"/tmp/http_log"}
        flow['tp_src'] = 80
        flow['tp_dst'] = None
        self.fd2 = self.cntxt.apply_elem(self.app_d,flow,"Logger",parameters,self) 
        
        if((self.fd1 > 0) and (self.fd2 > 0)):     #=> we have sucess
            self.installed = True
            print "TwoLoggers: created two elements with fds",self.fd1,"and",self.fd2
