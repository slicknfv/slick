"""
    LoggerReplicas: One Application, Two Element instances, and one flow to operate.
    Based on the optimization of steering algorithm traffic will be redirected.
"""
from slick.Application import Application

class LoggerReplicas(Application):
    def __init__( self, controller, ad ):
        Application.__init__( self, controller, ad )

    def init(self):
        # Start the first Logger:

        parameters = [{"file_name":"/tmp/dns_log1"}]
        flow = self.make_wildcard_flow()
        flow['tp_dst'] = 53
        ed1 = self.apply_elem( flow, ["Logger"], parameters ) 

        # Start the second Logger.
        parameters = [{"file_name":"/tmp/dns_log2"}] # Keeping different filename as its on mininet.
        flow = self.make_wildcard_flow()
        flow['tp_dst'] = 53
        ed2 = self.apply_elem( flow, ["Logger"], parameters ) 

        if(self.check_elems_installed(ed1) and self.check_elems_installed(ed2)):
            self.installed = True
            print "TwoLoggers: created two elements with fds", ed1, "and", ed2
        else:
            print "Failed to install the TwoLoggers application"
