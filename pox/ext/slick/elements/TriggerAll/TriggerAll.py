# This class is used to implement trigger generator.

from slick.Element import Element

class TriggerAll(Element):
    def __init__( self, shim, ed ):
        Element.__init__( self, shim, ed )

    # For DNS print fd and flow but for all other only print fd
    def process_pkt(self, buf):
        flow = self.extract_flow(buf)
        trigger = {
                    "type":"trigger",
                    "subtype":"trigger_all",
                    "ed":self.ed
                  }
        self.raise_trigger( trigger )
        self.fwd_pkt( buf )


#Testing
def main():
    pass
    triggers = TriggerAll(None,12)
    #triggers.configure('/tmp/msox1.txt')
    flow = {}
    flow["dl_src"] = 1 
    flow["dl_dst"] = 2
    packet = None
    triggers.process_pkt(flow,packet)

if __name__ == "__main__":
    main()



