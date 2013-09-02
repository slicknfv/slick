"""
    TwoLoggers: One Application, Two Function Instances
"""
from slick.Application import Application

class TwoLoggers(Application):
    def __init__( self, controller, ad ):
        Application.__init__( self, controller, ad )

    def init(self):
        # Start the first Logger:
        parameters = {"file_name":"/tmp/dns_log"}
        flow = self.make_wildcard_flow()
        flow['tp_dst'] = 53
        ed1 = self.apply_elem( flow, "Logger", parameters ) 

        # Start the second Logger
        parameters = {"file_name":"/tmp/http_log"}
        flow = self.make_wildcard_flow()
        flow['tp_src'] = 80
        ed2 = self.apply_elem( flow, "Logger", parameters ) 

        if((ed1 > 0) and (ed2 > 0)):
            self.installed = True
            print "TwoLoggers: created two elements with fds", ed1, "and", ed2
        else:
            print "Failed to install the TwoLoggers application"
