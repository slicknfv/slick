"""
    MoreLessTest App: One Application testing less element instance.
"""
from slick.Application import Application

class MoreTestApp(Application):
    def __init__( self, controller, ad ):
        Application.__init__( self, controller, ad )

    def init(self):
        # Start the Logger
        parameters = [{"file_name":"/tmp/more_elem_log", "inflation_rate":2}]
        flow = self.make_wildcard_flow()
        #flow['tp_dst'] = 53
        flow['nw_proto'] = 17
        flow['dl_type'] = 0x800
        ed = self.apply_elem( flow, ["More"], parameters) 

        if(self.check_elems_installed(ed)):
            self.installed = True
            print "MoreTestApp: created element with element descriptor", ed
        else:
            print "Failed to install the MoreTestApp application"
