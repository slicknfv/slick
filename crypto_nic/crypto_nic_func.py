# This class is used to implement a simple crypto nic, same as lego
import os.path
import dpkt
import random

class CryptoNIC():
    def __init__(self,shim):
        self.function_desc =  None # should not be oo dependent therefore moving it to install.
        self.shim = shim
        self.key = None


    def init(self,fd,params):
        self.function_desc =  fd
        self.key = params["key"]

    # Paramters
    def configure(self,params):
		pass

    # For DNS print fd and flow but for all other only print fd
    def process_pkt(self, buf):
        #print "INSIDE process_pkt"
        """
            NOTE: Calling extract_flow(packet) from shim, but it can easily be implemented in the Function.
            And it should be. 
            flow = self.extract_flow(packet)
        """
        eth = dpkt.ethernet.Ethernet(buf)
		if(eth.type == dpkt.ethernet.ETH_TYPE_IP):
			ip = eth.data
			# xor the ip data with the key
			for i in range(0, ip.data.__len__()):
				ip.data[i] = chr(ord(ip.data[i]) ^ ord(key[i]))
        self.shim.client_service.fwd_pkt(buf)

    def shutdown(self):
        print "Shutting down function with function descriptor:",self.fd
        return True


def usage():
    pass

#Testing
def main():
    cn = CryptoNIC()
	key = os.urandom(3000)	# bigger than any packet
    cn.install(12,key)
    flow = {}
    flow["dl_src"] = 1 
    flow["dl_dst"] = 2
    packet = os.urandom(1500)
    cn.process_pkt(flow,packet)

if __name__ == "__main__":
    main()



