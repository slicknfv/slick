"""
    LLTestApp: One Application, Two elements and one chain
"""
from slick.Application import Application

class LLTestApp(Application):
    def __init__( self, controller, ad ):
        Application.__init__( self, controller, ad )

    def init(self):
        # Start the first Logger:
        parameters = [{"file_name":"/tmp/less_elem_log", "drop_count":3}, {"file_name":"/tmp/less_elem_log", "drop_count":3}]
        flow = self.make_wildcard_flow()
        flow['nw_proto'] = 17
        flow['dl_type'] = 0x800
        eds = self.apply_elem( flow, ["Less", "Less"], parameters) 

        if(self.check_elems_installed(eds)):
            self.installed = True
            print "LLTestApp: created two elements with eds", eds[0], "and", eds[1]
        else:
            print "Failed to install the LLTestApp application"
