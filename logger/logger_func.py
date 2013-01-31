# This class is used to implement a simple log function.
import os.path
import dpkt

class Logger():
    def __init__(self,shim):
        self.function_desc =  None # should not be oo dependent therefore moving it to install.
        self.filename = None
        self.file_handle = None
        # Need this to call the trigger.
        self.shim = shim
        # internal state
        self.count = 0
        self.count_thresh = 0


    def init(self,fd,params):
        self.function_desc =  fd
        self.filename = params["file_name"]
        if(self.filename):
            if(os.path.isfile(self.filename)):
                self.file_handle=open(self.filename,'a')
            else:
                self.file_handle=open(self.filename,'w')

    # Paramters
    def configure(self,params):
        if(params.has_key("count_thresh")):
            self.count_thresh = params["count_thresh"]
        print self.count_thresh

    # For DNS print fd and flow but for all other only print fd
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
        self.shim.client_service.fwd_pkt(buf)

    def shutdown(self):
        print "Shutting down function with function descriptor:",self.fd
        self.file_handle.close()
        return True


def usage():
    pass

#Testing
def main():
    logger = Logger()
    logger.install(12,'/tmp/msox.txt')
    logger.configure('/tmp/msox1.txt')
    flow = {}
    flow["dl_src"] = 1 
    flow["dl_dst"] = 2
    packet = None
    logger.process_pkt(flow,packet)

if __name__ == "__main__":
    main()



