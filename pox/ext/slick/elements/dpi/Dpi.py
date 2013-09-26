"""Simple DNS DPI Element.
"""
import os.path
import dpkt
import socket
import logging

#from slick.Element import Element

#import ndpi

#class Dpi(Element):
class Dpi():
    """Element that can be used to perform deep packet inspection.

    This element can be used to detect different protocols 
    in the network traffic and raise the respective event for
    slick applications to consume.
    """

    def __init__(self, shim, ed):
        #Element.__init__(self, shim, ed )
        pass

    def init(self, params):
        pass

    # Paramters
    def configure(self, params):
        pass

    def process_pkt(self, buf):
        print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        response = ndpi.process_packet(buf)
        print "This is the response we got: ", response
        # To allow for service chaining among elements
        # on the same machine we need to return the packet
        return buf
