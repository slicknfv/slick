"""
    ReplicasChain: One Application, Two Element Types, Three Element instances and One flow to operate.
"""
from slick.Application import Application

class ReplicasChain(Application):
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

        # Start third instance
        #ed3 = self.apply_elem( flow, ["TriggerAll"] ) 
        ed3 = self.apply_elem( flow, ["Noop"] ) 

        if(self.check_elems_installed(ed1) and self.check_elems_installed(ed2)
                and self.check_elems_installed(ed3)):
            self.installed = True
            print "ReplicasChain: created three elements with eds", ed1, "and", ed2, "and", ed3
        else:
            print "Failed to install the ReplicasChain application"
