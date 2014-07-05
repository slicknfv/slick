"""
    MoreLessTest App: One Application testing less element instance.
"""
from slick.Application import Application

class LessTestApp(Application):
    def __init__( self, controller, ad ):
        Application.__init__( self, controller, ad )

    def init(self):
        # Start the Logger
        parameters = [{"file_name":"/tmp/less_elem_log", "drop_count":3}]
        flow = self.make_wildcard_flow()
        flow['tp_dst'] = 53
        flow['nw_proto'] = 17
        ed = self.apply_elem( flow, ["Less"], parameters) 

        if(self.check_elems_installed(ed)):
            self.installed = True
            print "LessTestApp: created element with element descriptor", ed
        else:
            print "Failed to install the LessTestApp application"
