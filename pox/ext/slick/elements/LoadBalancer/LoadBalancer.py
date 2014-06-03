"""
    LoadBalancer: Dummy LoadBalancer module.
"""
import os.path
import datetime
from slick.Element import Element

class LoadBalancer(Element):
    def __init__( self, shim, ed ):
        Element.__init__(self, shim, ed )
        self.file_handle = None

    def init( self, params ):
        filename = params["file_name"]
        filename += str(self.ed)
        if(filename):
            self.file_handle = open( filename, 'a+' , 0)

    def process_pkt( self, buf ):
        flow = self.extract_flow( buf )
        timestamp = datetime.datetime.now()
        self.file_handle.write( str(self.__class__.__name__) +' '+ str(timestamp) + ' ' + str(flow) + '\n' )
        return buf

    def shutdown( self ):
        print "Shutting down", self.__class__.__name__ ," element with descriptor:", self.ed
        self.file_handle.close()
        return True


if __name__ == "__main__":
    main()
