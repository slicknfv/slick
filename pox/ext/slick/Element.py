"""
    Element: Base class (do not instantiate; treat it like an abstract base class)
"""
import dpkt

class Element():
    def __init__( self, shim, ed ):
        self.shim = shim
        self.ed =  ed

    def init( self, params):
        pass

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

    def raise_trigger( self, trigger_params ):
        """After attaching the required values send element trigger.

        Args:
          trigger:
            Key:Value pairs of the values to be sent to controller.
        """
        trigger = {"ed": self.ed, "type":"trigger"}
        for key, value in trigger_params.iteritems():
          trigger[key] = value
        self.shim.client_service.raise_trigger( trigger )

    def fwd_pkt( self, buf ):
        self.shim.client_service.fwd_pkt( buf )
