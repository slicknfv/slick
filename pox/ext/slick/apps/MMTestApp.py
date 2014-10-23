"""
    MMTestApp: One Application, Two elements and one chain
"""
from slick.Application import Application

class MMTestApp(Application):
    def __init__( self, controller, ad ):
        Application.__init__( self, controller, ad )

    def init(self):
        # Start the first Logger:
        parameters = [{"file_name":"/tmp/more_elem_log", "inflation_rate":2}, {"file_name":"/tmp/more_elem_log", "inflation_rate":2}]
        flow = self.make_wildcard_flow()
        flow['nw_proto'] = 17
        flow['dl_type'] = 0x800
        eds = self.apply_elem( flow, ["More", "More"], parameters) 

        if(self.check_elems_installed(eds)):
            self.installed = True
            print "MMTestApp: created two elements with eds", eds[0], "and", eds[1]
        else:
            print "Failed to install the MMTestApp application"
