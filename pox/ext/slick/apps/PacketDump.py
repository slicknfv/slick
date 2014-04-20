"""
	PacketDump : dumps all packets to a file
"""
from slick.Application import Application

class PacketDump(Application):
    def __init__( self, controller, ad ):
        Application.__init__( self, controller, ad )

    def init(self):
        parameters = [{"file_name":"/tmp/packet_dump.pcap"}]
        flow = self.make_wildcard_flow()
        flow["tp_dst"] = 80
        ed = self.apply_elem( flow, ["Dump"], parameters ) 

        if(self.check_elems_installed(ed)):
            self.installed = True
            print "PacketDump: created element with element descriptor", ed
        else:
            print "Failed to install the PacketDump application"
