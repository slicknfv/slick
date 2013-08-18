"""
    Drop: Simply drops all packets
"""
from slick.Element import Element

class Drop(Element):
    def __init__( self, shim, fd ):
        Element.__init__( self, shim, ed )

    def process_pkt( self, buf ):
        print "*** Drop element with descriptor", self.ed, "dropping packet ***"
        pass


#Testing
def main():
    dropper = Drop(None,100)
    print dropper.ed

if __name__ == "__main__":
    main()
