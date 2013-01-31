import os.path
import dpkt
import socket
import pybloomfilter


class BloomFilter():
    def __init__(self,shim):
        self.function_desc =  None #
        # Need this to call the trigger.
        self.shim = shim
        self.filename = None
        self.bf_size = None
        self.error_rate = None
        self.bf = None


    def init(self,fd,params):
        self.function_desc =  fd
        if(params.has_key("bf_size")):
            self.bf_size = params["bf_size"]
        if(params.has_key("error_rate")):
            self.error_rate = params["error_rate"]
            pass
        self.BFInit(self.bf_size,self.error_rate,self.filename)
            

    def configure(self,params):
        if(params.has_key("sentinelfile")):
            self.filename = params["sentinelfile"]

    def BFInit(self,bf_size,error_rate,filename):
        self.bf = pybloomfilter.BloomFilter(10000, 0.001, 'filter.bloom')
        f = open("../bloomfilter/fieldvals") #One value per line.
        for val in f:
            print "Adding value:",val
            self.bf.add(val.rstrip())

    def process_pkt(self, buf):
        trigger = {"fd":self.function_desc}
        eth = dpkt.ethernet.Ethernet(buf)
        flow = self.shim.extract_flow(eth)
        pkt_len = len(buf)
        if(eth.type== dpkt.ethernet.ETH_TYPE_IP):
            ip = eth.data
            dst_ip = socket.inet_ntoa(ip.dst)
            src_ip = socket.inet_ntoa(ip.src)
            if(ip.p == dpkt.ip.IP_PROTO_TCP):
                tcp =ip.data
                #bloom filters match
                val = str(tcp.dport)
                #Check if value if present in the filter
                val_present = val in self.bf
                print val_present
                if(val_present):
                    trigger["type"] = "trigger"
                    trigger["BF_trigger_type"] = "VAL_DETECTED"
                    self.shim.client_service.raise_trigger(trigger)
        # This must be called.
        self.shim.client_service.fwd_pkt(buf)
                        

    def shutdown(self):
        print "Shutting down function with function descriptor:",self.function_desc
        return True

    


#Testing
def main():
    bf = BloomFilter(None)
    bf.init(100,{})
    print bf.function_desc

if __name__ == "__main__":
    main()




