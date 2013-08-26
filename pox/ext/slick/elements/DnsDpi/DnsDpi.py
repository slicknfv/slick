"""Simple DNS DPI Element.
"""
import os.path
import dpkt
import socket
import logging

from slick.Element import Element

from dns_process import DNSProcess

class DnsDpi(Element):
    """Element that can be used to lookup black listed domain names.

    This element can be used to detet black listed domain name
    lookups.
    """

    def __init__(self, shim, ed):
        Element.__init__(self, shim, ed )
        self.dns_proc = DNSProcess()


    def init(self, params):
        pass

    # Paramters
    def configure(self, params):
        pass

    def process_pkt(self, buf):
        isblocked = False
        src_ip = None
        bad_domain_name = None
        response = self.dns_proc.decode(buf)
        if isinstance(response, tuple):
            isblocked, src_ip, bad_domain_name = response
        else:
            logging.warn('Unable to decode the DNS request/response.')
        if isblocked:
            trigger = {}
            trigger["dns_dpi_type"] = "BadDomainEvent"
            trigger["src_ip"] = socket.inet_ntoa(src_ip)
            trigger["bad_domain_name"] = bad_domain_name
            self.raise_trigger(trigger)
        self.fwd_pkt(buf)
