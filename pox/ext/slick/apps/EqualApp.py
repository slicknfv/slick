"""
    EqualApp: EqualApp, One element and one flowspace
"""
from slick.Application import Application

class EqualApp(Application):
    def __init__( self, controller, ad ):
        Application.__init__( self, controller, ad )

    def init(self):
        # Start the first Logger:
        parameters = [{"file_name":"/tmp/equal_log"}]
        flow = self.make_wildcard_flow()
	flow['nw_proto'] = 17
        flow['dl_type'] = 0x800
        # Parameters is an array of dicts that should be passed 
        # to apply_elem corresponding to the element_name
        # that we want to apply the parameters to.
        ed1 = self.apply_elem( flow, ["Equal"], parameters ) 

        if(self.check_elems_installed(ed1)):
            self.installed = True
            print "EqualApp: created one element with ed", ed1
        else:
            print "Failed to install the EqualApp application"
