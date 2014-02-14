"""
    DirectionLogger: One Application, Two Element Instance.
    For first element instance we tell controller to only use one direction while traversing the middlebox1.
    For second element instance we tell controller to use both directions traversing the middlebox2.
    This tests unidirection/bidirection and path affinity
"""
from slick.Application import Application

class DirectionLogger(Application):
    def __init__( self, controller, ad ):
        Application.__init__( self, controller, ad )

    def init(self):
        # Start the Logger
        parameters = [{"file_name":"/tmp/unidirection_log"}]
        admin_params = [{"bidirection":False,"affinity":True}]
        flow = self.make_wildcard_flow()
        flow['tp_dst'] = 53
        flow['nw_proto'] = 17
        ed1 = self.apply_elem( flow, ["Logger"], parameters, admin_params) 

        parameters = [{"file_name":"/tmp/bidirection_log"}]
        admin_params = [{"bidirection":True, "affinity":True}]
        flow = self.make_wildcard_flow()
        flow['tp_dst'] = 53
        flow['nw_proto'] = 17
        ed2 = self.apply_elem( flow, ["Logger1"], parameters, admin_params) 

        if(self.check_elems_installed(ed1) and self.check_elems_installed(ed2)):
            self.installed = True
            print "DirectionLogger: created Two elements with element descriptors", ed1, ed2
        else:
            print "Failed to install the DnsLogger application"
