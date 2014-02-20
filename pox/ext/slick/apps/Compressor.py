"""
	Compressor : compresses IP traffic
"""
from slick.Application import Application

class Compressor(Application):
    def __init__( self, controller, ad ):
        Application.__init__( self, controller, ad )

    def init(self):
        flow = self.make_wildcard_flow()
        flow["dl_type"] = 0x800
        flow["nw_proto"] = 17
        flow["tp_dst"] = 8000
        ed = self.apply_elem( flow, ["Compress"]) 

        if(self.check_elems_installed(ed)):
            self.installed = True
            print "Compressor : compresses IP traffic", ed
        else:
            print "Failed to install the Compressor application"
