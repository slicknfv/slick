# This class is used to implement trigger generator.
import os.path

class TriggerAll():
    def __init__(self,shim):
        self.function_desc =  None # should not be oo dependent therefore moving it to install.
        # Need this to call the trigger.
        self.shim = shim

    def init(self,fd,params):
        self.function_desc =  fd

    # Paramters
    def configure(self,params):
        pass

    # For DNS print fd and flow but for all other only print fd
    def process_pkt(self, packet):
        """
            NOTE: Calling extract_flow(packet) from shim, but it can easily be implemented in the Function.
            And it should be. 
            flow = self.extract_flow(packet)
        """
        flow = self.shim.extract_flow(packet)
        trigger = {"fd":self.function_desc}
        self.shim.client_service.raise_trigger(trigger)

    def shutdown(self):
        print "Shutting down function with function descriptor:",self.fd
        return True


#Testing
def main():
    triggers = TriggerAll()
    triggers.init(12,None)
    triggers.configure('/tmp/msox1.txt')
    flow = {}
    flow["dl_src"] = 1 
    flow["dl_dst"] = 2
    packet = None
    logger.process_pkt(flow,packet)

if __name__ == "__main__":
    main()



