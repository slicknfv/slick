"""
    TwoLoggers: One Application, Two Function Instances and two flowspaces.
"""
from slick.Application import Application

class TwoLoggers(Application):
    def __init__( self, controller, ad ):
        Application.__init__( self, controller, ad )

    def init(self):
        # Start the first Logger:
        parameters = [{"file_name":"/tmp/dns_log"}]
        flow = self.make_wildcard_flow()
        flow['tp_dst'] = 53
        # Parameters is an array of dicts that should be passed 
        # to apply_elem corresponding to the element_name
        # that we want to apply the parameters to.
        ed1 = self.apply_elem( flow, ["Logger"], parameters ) 

        # Start the second Logger
        parameters = [{"file_name":"/tmp/http_log"}]
        flow = self.make_wildcard_flow()
        flow['tp_src'] = 80
        ed2 = self.apply_elem( flow, ["Logger"], parameters ) 

        if(self.check_elems_installed(ed1) and self.check_elems_installed(ed2)):
            self.installed = True
            print "TwoLoggers: created two elements with fds", ed1, "and", ed2
        else:
            print "Failed to install the TwoLoggers application"
