"""
    TwoLoggers: One Application, Two Element Instances, One Flow, One Element machine.
"""
from slick.Application import Application

class TwoLoggersChain(Application):
    def __init__( self, controller, ad ):
        Application.__init__( self, controller, ad )

    def init(self):
        # Start the first Logger:
        parameters = [{"file_name":"/tmp/dns_log_1"}, {"file_name":"/tmp/dns_log_2"}]
        flow = self.make_wildcard_flow()
        flow['tp_dst'] = 53
        # Parameters is an array of dicts that should be passed 
        # to apply_elem corresponding to the element_name
        # that we want to apply the parameters to.
        eds = self.apply_elem( flow, ["Logger", "Logger"], parameters )

        if self.check_elems_installed(eds):
            self.installed = True
            print "TwoLoggersChain: created two elements with eds: ", eds
        else:
            print "Failed to install the TwoLoggersChain application"
