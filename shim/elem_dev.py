import sys
import os
import getopt
import dpkt
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir+"/pox/ext/slick/elements") 

from dpi.Dpi import Dpi

class PcapLoader(object):
    def __init__(self, filename):
        self.filename = filename # Name of the file where to read pcap data
        self.elem_handle = None

    def loadpcap(self):
        """Opens and gives a handle of pcap file.
        """
        print 'Reading pcap dump from file:', self.filename
        if(self.filename):
            f = open(self.filename)
            self.pcap_file = dpkt.pcap.Reader(f)
            for ts, buf in self.pcap_file:
                print "reading packet"
                self.decode(None, buf)

    def decode(self, hdr, buf):
        self.demux(buf)

    def demux(self, buf):
        packet = dpkt.ethernet.Ethernet(buf)
        if not self.elem_handle:
            self.elem_handle = Dpi(None, None)
        else:
            self.elem_handle.process_pkt(buf)
    
def main(argv):
    file_name = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:", ["help", "file"])
    except getopt.GetoptError:
        print "Option error!"
        usage()
        sys.exit(2)
    # should change this to use the OptionParser class
    for opt, arg in opts:
        print opt
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in("-f", "--file"): 
            file_name = arg
    if(file_name):
        cd_pcap = PcapLoader(file_name)
        cd_pcap.loadpcap()
        return

if __name__ == "__main__":
    main(sys.argv[1:])
