"""
    LoggerStateful: an element that copies each packet it receives to a file, then forwards the packet along.
"""
import os.path
import datetime
from slick.Element import Element

class LoggerStateful(Element):
    def __init__( self, shim, ed ):
        Element.__init__(self, shim, ed )
        self.file_handle = None
        self._counter = 0

    def init( self, params ):
        filename = params["file_name"]
        filename += str(self.ed)
        if(filename):
            self.file_handle = open( filename, 'a+' , 0)

    def process_pkt( self, buf ):
        flow = self.extract_flow( buf )
        timestamp = datetime.datetime.now()
        self._counter += 1
        self.file_handle.write( str(self._counter) + ' ' + str(timestamp) + ' ' + str(flow) + '\n' )
        return buf

    def shutdown( self ):
        print "Shutting down Logger with element descriptor:", self.ed
        self.file_handle.close()
        return True


