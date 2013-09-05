"""
    HttpLogger: One Application, One Element Instance
"""
from slick.Application import Application

class HttpLogger(Application):
    def __init__( self, controller, ad ):
        Application.__init__( self, controller, ad )

    def init(self):
        # Start the Logger
        parameters = [{"file_name":"/tmp/http_log"}]
        flow = self.make_wildcard_flow()
        flow['tp_dst'] = 80
        ed = self.apply_elem( flow, ["Logger"], parameters ) 

        if(self.check_elems_installed(ed)):
            self.installed = True
            print "HttpLogger: created element with element descriptor", ed
        else:
            print "Failed to install the HttpLogger application"
