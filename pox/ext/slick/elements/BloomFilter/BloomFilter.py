import os.path
import logging
import socket

import dpkt
import pybloomfilter

from slick.Element import Element

class BloomFilter(Element):
  """Example Element that can be used to match on TCP port field."""

  def __init__(self, shim, ed):
    Element.__init__(self, shim, ed )
    # Name of the file where sentinels are stored.
    self.filename = None
    # bloomfilder size and error rate
    self.bf_size = None
    self.error_rate = None
    # Handle for the pybloomfilter.BloomFilter class
    self.lib_object = None

  def init(self, params):
    """Sartup the element.

    Args:
      ed: Name of the element descriptor.
      params: Its a <key,value> dictionary that has params
      required by element to startup.
    Returns:
       None
    """
    if params.has_key("bf_size"):
      self.bf_size = params["bf_size"]
    if params.has_key("error_rate"):
      self.error_rate = params["error_rate"]
    self._bf_init(self.bf_size, self.error_rate, self.filename)

  def configure(self, params):
    """Update element state accoeding to user params.

    Args:
      params: Its a map of key and values.	
    """
    if params.has_key("sentinelfile"):
      self.filename = params["sentinelfile"]
    if params.has_key("addsentinel"):
      sentinel = params["addsentinel"]
      if self.lib_object:
        self.lib_object.add(sentinel) # Add the new value to the sentinel

  def _bf_init(self, bf_size, error_rate, filename='filter.bloom'):
    """Here we create the bloomfilter object.

    Args:
        bf_size: Bloom Filter size.
        error_rate: Error Rate allowed.
        filename: Name of the file.
    Returns:
        None
    """
    self.lib_object = pybloomfilter.BloomFilter(10000, 0.001, filename)
    # TODO:Clean up paths.
    with open("../pox/ext/slick/elements/BloomFilter/fieldvals",'r') as f: #One value per line.
      for val in f:
        logging.info("Inserting value into the bloom filter: %s",val)
        self.lib_object.add(val.rstrip())

  def process_pkt(self, buf):
    """Match the TCP port using bloom filters.

    Args:
        buf: Packet buffer.
    Returns:
        None
    """
    flow = self.extract_flow(buf)
    eth = dpkt.ethernet.Ethernet(buf)
    pkt_len = len(buf)
    if(eth.type == dpkt.ethernet.ETH_TYPE_IP):
      ip = eth.data
      dst_ip = socket.inet_ntoa(ip.dst)
      src_ip = socket.inet_ntoa(ip.src)
      if(ip.p == dpkt.ip.IP_PROTO_TCP):
        tcp =ip.data
        # bloom filters value to match
        val = str(tcp.dport)
        # Check if value is present in the filter
        val_present = val in self.lib_object
        logging.info('Matched the port number: %s', val)
        if(val_present):
          trigger = {"BF_trigger_type":"VAL_DETECTED"}
          # Call base class raise trigger.
          self.raise_trigger(trigger)
    # This must be called to forward the packet.
    self.fwd_pkt(buf)
