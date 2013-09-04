"""BloomFilter Application.

It show how bloomfilter Element can be used to raise trigger on packet field.
"""
import logging

from slick.Application import Application

class BloomFilterUnitTest(Application):
    def __init__( self, controller, ad ):
        Application.__init__( self, controller, ad )
        self.num_elements = 1
        self.eds = [] #List of functions used by this application.
        self.count = 0

    def init(self):
        flow = self.make_wildcard_flow()
        flow['tp_dst'] = 80
        for index in range(0, self.num_elements):
            ed = self.apply_elem( flow, ["BloomFilter"] )
            if( ed > 0 ):#=> we have success
                self.eds.append(ed)
                self.installed = True
                logging.info("BloomFilter application Installed.")

    def configure_user_params(self):
        if (self.count < self.num_elements): 
            params = {"bf_size":"1000", "error_rate":"0.01", "sentinelfile":'/tmp/fieldvals'}
            self.configure_elem( self.eds[self.count], params ) 
            self.count +=1

    def handle_trigger(self, ed, msg):
        if(msg.has_key("BF_trigger_type")):
            if(msg["BF_trigger_type"] == "VAL_DETECTED"):
                print "Detected port 80 traffic using bloom filters."


