# This class is used to implement a simple log function.
import os.path
import dpkt

class Drop():
    def __init__(self,shim):
        self.function_desc =  None # should not be oo dependent therefore moving it to install.
        # Need this to call the trigger.
        self.shim = shim


    def init(self,fd,params):
        self.function_desc =  fd

    def configure(self,params):
        pass

    # For DNS print fd and flow but for all other only print fd
    def process_pkt(self, buf):
        print "DROPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP"
        pass

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



