# This file reads the triggers from the p0f detector and generates the triggers for the controller.
import os.path
import dpkt
import socket

import p0f

from slick.Element import Element


class P0f(Element):
    def __init__(self, shim, ed):
        Element.__init__(self, shim, ed )


    def init(self, ed, params):
	pass

    def configure(self,params):
        pass

    def process_pkt(self, buf):
        trigger = {"ed":self.ed}
        eth = dpkt.ethernet.Ethernet(buf)
        pkt_len = len(buf)
        if(eth.type== dpkt.ethernet.ETH_TYPE_IP):
            ip = eth.data
            dst_ip = socket.inet_ntoa(ip.dst)
            src_ip = socket.inet_ntoa(ip.src)
            if(ip.p == dpkt.ip.IP_PROTO_TCP):
		# Call the actual p0f module to make the 
		# decision for the packets.
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
                        

#Testing
def main():
    dropper = Drop(None)
    dropper.init(100,{})

if __name__ == "__main__":
    main()
