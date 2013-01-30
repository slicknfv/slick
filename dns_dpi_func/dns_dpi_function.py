# This class is used to implement a simple log function.
import os.path
import dpkt
from dns_dpi_func.dns_process import DNSProcess
#import collect_data
import socket

class DnsDpiFunction():
    def __init__(self,shim):
        # Need this to call the trigger.
        self.shim = shim
        self.function_desc =  None # should not be oo dependent therefore moving it to install.
        # internal state
        self.black_list_dir = None
        self.dns_proc = DNSProcess()


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
        isblocked = False
        src_ip = None
        domain_name = None
        isblocked,src_ip,bad_domain_name = self.dns_proc.decode(buf)
        if isblocked:
            print "Domain Blocked"
            packet = dpkt.ethernet.Ethernet(buf)

            flow = self.shim.extract_flow(packet)
            #trigger = self.dns_proc.dns_handler.dns_state.get_event("BadDomainEvent",flow,"www.dummy.com",["127.0.0.1"])
            trigger = {}
            trigger["type"] = "trigger"
            trigger["dns_dpi_type"] = "BadDomainEvent"
            trigger["fd"] = self.function_desc
            trigger["src_ip"] = socket.inet_ntoa(src_ip)
            trigger["bad_domain_name"] = bad_domain_name
            print trigger
            self.shim.client_service.raise_trigger(trigger)#first raise trigger
        self.shim.client_service.fwd_pkt(buf) #then forward.

    def shutdown(self):
        print "Shutting down function with function descriptor:",self.fd
        self.file_handle.close()
        return True


