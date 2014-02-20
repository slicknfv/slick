"""
	DelayBuffer : delays packets by packets
"""
from slick.Application import Application

class DelayBuffer(Application):
    def __init__( self, controller, ad ):
        Application.__init__( self, controller, ad )

    def init(self):
        parameters = [{"buffer_size" : 5}]
        flow = self.make_wildcard_flow()
	flow['dl_type'] = 0x800
	flow['nw_proto'] = 17
        flow["tp_dst"] = 8000
        ed = self.apply_elem( flow, ["DelayBuffer"], parameters ) 

        if(self.check_elems_installed(ed)):
            self.installed = True
            print "DelayBuffer: created element with element descriptor", ed
        else:
            print "Failed to install the DelayBuffer application"
