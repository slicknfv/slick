# This file reads the triggers from the p0f detector and generates the triggers for the controller.
import os.path
import dpkt
import p0f
import socket


class P0F():
    def __init__(self,shim):
        self.function_desc =  None #
        # Need this to call the trigger.
        self.shim = shim


    def init(self,fd,params):
        self.function_desc =  fd

    def configure(self,params):
        pass

    def process_pkt(self, buf):
        #print "Inside p0f"
        trigger = {"fd":self.function_desc}
        eth = dpkt.ethernet.Ethernet(buf)
        pkt_len = len(buf)
        if(eth.type== dpkt.ethernet.ETH_TYPE_IP):
            ip = eth.data
            dst_ip = socket.inet_ntoa(ip.dst)
            src_ip = socket.inet_ntoa(ip.src)
            if(ip.p == dpkt.ip.IP_PROTO_TCP):
                result = p0f.p0f(buf)
                if(len(result)):
                    item = result[0] # Assign highest confience result.
                    if(len(item) >=3): 
                        trigger["type"] = "trigger"
                        trigger["p0f_trigger_type"] = "OSDetection"
                        trigger["OS"] = item[0]
                        trigger["OSVersion"] = item[1]
                        trigger["src_ip"] = src_ip
                        self.shim.client_service.raise_trigger(trigger)
        # This must be called.
        self.shim.client_service.fwd_pkt(buf)
                        

    def shutdown(self):
        print "Shutting down function with function descriptor:",self.fd
        return True



#Testing
def main():
    dropper = Drop(None)
    dropper.init(100,{})
    print dropper.function_desc

if __name__ == "__main__":
    main()




