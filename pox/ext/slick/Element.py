"""
    Element: Base class (do not instantiate; treat it like an abstract base class)
"""
import dpkt

class Element():
    def __init__( self, shim, ed ):
        self.ed =  ed
        self.shim = shim

    def init( self, params):
        pass

    # Paramters
    def configure( self,params ):
        pass

    def process_pkt( self, buf ):
        pass

    def shutdown( self ):
        print "Shutting down element of type", self.__class__, "with element descriptor", self.ed
        return True

    def extract_flow( self, buf ):
        packet = dpkt.ethernet.Ethernet( buf )
        return self.shim.extract_flow( packet )

    def raise_trigger( self, trigger ):
        self.shim.client_service.raise_trigger( trigger )

    def fwd_pkt( self, packet ):
        self.shim.client_service.fwd_pkt( packet )
