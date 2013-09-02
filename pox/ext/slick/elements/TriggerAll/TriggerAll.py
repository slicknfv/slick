"""
	TriggerAll : an element that simply raises a trigger on every packet it gets, and forwards the packet along
"""

from slick.Element import Element

class TriggerAll(Element):
    def __init__( self, shim, ed ):
        Element.__init__( self, shim, ed )

    def process_pkt( self, buf ):
		# TODO Consider adding information about the flow into
		#      the trigger ("flow":self.extract_flow(buf))
        trigger = { "type":"trigger",
                    "subtype":"TriggerAll",
                    "ed":self.ed }
        self.raise_trigger( trigger )
        return buf


#Testing
def main():
    pass
    triggers = TriggerAll(None,12)
    flow = {}
    flow["dl_src"] = 1 
    flow["dl_dst"] = 2
    packet = None
    triggers.process_pkt(flow,packet)

if __name__ == "__main__":
    main()



