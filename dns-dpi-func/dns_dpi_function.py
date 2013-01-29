# This class is used to implement a simple log function.
import os.path
import dpkt

class DnsDpiFunction():
    def __init__(self,shim,iface,file_name):
        # Need this to call the trigger.
        self.shim = shim
        self.function_desc =  None # should not be oo dependent therefore moving it to install.
        # internal state
        self.black_list_dir = None
        self.dns_sensor = DNSSensor(mode,str(iface),file_name)
        self.dns_sensor.initiate()


    def init(self,fd,params):
        self.function_desc =  fd
        self.folder_name = params["folder_name"]
        if(self.folder_name):
            pass

    # Paramters
    def configure(self,params):
        print "BILAL"
        if(params.has_key("count_thresh")):
            self.count_thresh = params["count_thresh"]

    def process_pkt(self, buf):
        print "INSIDE process_pkt"
        """
            NOTE: Calling extract_flow(packet) from shim, but it can easily be implemented in the Function.
            And it should be. 
            flow = self.extract_flow(packet)
        """
        packet = dpkt.ethernet.Ethernet(buf)
        flow = self.shim.extract_flow(packet)
        self.file_handle.write(str(flow))
        self.file_handle.write('\n')
        self.count +=1
        self.shim.client_service.fwd_pkt(buf)

    def shutdown(self):
        print "Shutting down function with function descriptor:",self.fd
        self.file_handle.close()
        return True


