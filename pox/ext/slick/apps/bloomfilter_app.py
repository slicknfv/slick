############
# BloomFilter Application
############
class BloomFilterFunctionApp():
    def __init__(self,inst,AD,flows):
        self.cntxt = inst
        self.num_functions = 1
        self.app_d = AD
        self.fd = [] #List of functions used by this application.
        self.conf = 0
        self.installed = False
        self.flows = flows
        #App specific
        self.trigger_function_installed = False


    def init(self):
        for index in range(0,self.num_functions): 
            print "APPLY_FUNC"
            parameters = {}
            fd= self.cntxt.apply_func(self.app_d,self.flows[index],"BF",parameters,self) #Bloom Filter
            print fd
            if((fd >0)):#=> we have sucess
                self.fd.append(fd)
                self.installed = True
                print "BF Function Installed."

    def configure_user_params(self):
        if (self.conf < self.num_functions): 
            print "CONFIGURE_CALLEDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
            params = {"bf_size":"1000","error_rate":"0.01"}
            print self.conf
            print self.fd
            self.cntxt.configure_func(self.app_d,self.fd[self.conf],params) 
            self.conf +=1

    def handle_trigger(self,fd,msg):
        #print msg
        if(msg.has_key("BF_trigger_type")):
            if(msg["BF_trigger_type"] == "VAL_DETECTED"):
                print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
                print "Bloom Filter Detected Value"

