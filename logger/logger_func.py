# This class is used to implement a simple log function.
import os.path

class Logger():
    def __init__(self,fd):
        self.function_desc =  fd
        self.filename = None
        self.file_handle = None

    # Paramters
    def configure(self,*params):
        if(len(params) == 1):
            self.filename = params[0]
            if(self.filename):
                if(os.path.isfile(self.filename)):
                    self.file_handle=open(self.filename,'a')
                else:
                    self.file_handle=open(self.filename,'a')
        else:
            print "Wrong number of arguments used."

    # For DNS print fd and flow but for all other only print fd
    def process_pkt(self,flow, packet):
        self.file_handle.write(str(flow))
        self.file_handle.write('\n')


#Testing
def main():
    logger = Logger(12)
    logger.configure('/tmp/msox.txt')
    flow = {}
    flow["dl_src"] = 1 
    flow["dl_dst"] = 2
    packet = None
    logger.process_pkt(flow,packet)

if __name__ == "__main__":
    main()



