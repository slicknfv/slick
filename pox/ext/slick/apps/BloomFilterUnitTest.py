############
# BloomFilter Application
############
import logging

from slick.Application import Application

class BloomFilterUnitTest(Application):
    def __init__( self, controller, ad ):
        Application.__init__( self, controller, ad )
        self.num_functions = 1
        self.eds = [] #List of functions used by this application.
        self.conf = 0

    def init(self):
        flow = self.make_wildcard_flow()
        flow['tp_dst'] = 80
        for index in range(0,self.num_functions): 
            ed = self.apply_elem( flow, "BloomFilter" )
            if( ed > 0 ):#=> we have sucess
                self.eds.append(ed)
                self.installed = True
                logger.info("BloomFilter application Installed.")

    def configure_user_params(self):
        if (self.conf < self.num_functions): 
            params = {"bf_size":"1000","error_rate":"0.01"}
            self.configure_elem( self.fd[self.conf], params ) 
            self.conf +=1

    def handle_trigger(self,fd,msg):
        #print msg
        if(msg.has_key("BF_trigger_type")):
            if(msg["BF_trigger_type"] == "VAL_DETECTED"):
                print "Bloom Filter Detected Value"


