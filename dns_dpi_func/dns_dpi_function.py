# This class is used to implement a simple log function.
import os.path
import dpkt
from dns_dpi_func.dns_sensor import DNSSensor
import collect_data

class DnsDpiFunction():
    def __init__(self,shim):
        # Need this to call the trigger.
        self.shim = shim
        self.function_desc =  None # should not be oo dependent therefore moving it to install.
        # internal state
        self.black_list_dir = None
        mode = 1 #read from the file
        file_name = "skype_youtube_dropbox_dns_http_tcpdump.pcap"
        iface = None
        #self.dns_sensor = DNSSensor(mode,str(iface),file_name)
        #self.dns_sensor.initiate()


    def init(self,fd,params):
        self.function_desc =  fd
        if(params.has_key("folder_name")):
            self.folder_name = params["folder_name"]

    # Paramters
    def configure(self,params):
        print "BILAL"
        if(params.has_key("count_thresh")):
            self.count_thresh = params["count_thresh"]

    def process_pkt(self, buf):
        print "INSIDE process_pkt"
        packet = dpkt.ethernet.Ethernet(buf)
        """
            NOTE: Calling extract_flow(packet) from shim, but it can easily be implemented in the Function. It should be. 
            flow = self.extract_flow(packet)
        """
        flow = self.shim.extract_flow(packet)
        self.shim.client_service.fwd_pkt(buf)

    def shutdown(self):
        print "Shutting down function with function descriptor:",self.fd
        self.file_handle.close()
        return True


