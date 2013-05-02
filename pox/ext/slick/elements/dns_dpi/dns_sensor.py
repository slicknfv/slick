"""
This is inefficient DNS sensor that is used to implement the functionality required to 
perform the homework for different events defined in the DNS events file
"""
import collect_data
import constants

class DNSSensor():
    def __init__(self,mode,iface,file_name):
        self.mode = mode
        self.iface = iface
        self.file_name = file_name
        self.pcap_file = ""



    def initiate(self):
        print "Starting Activity Recognition System"
    	# --
    	# Enable this code segment for live traffic
    	# --
        if(self.mode == constants.RUN_MODE):
            cd_pcap = collect_data.CollectData(self.iface,self.file_name)
            cd_pcap.sniff() # hopefully you have done all the hw
    	# --
    	# -- This code can be used to test the pcap fils based data 
    	# --
        if(self.mode ==constants.DEBUG_MODE):
            cd_pcap = collect_data.CollectData(self.iface,self.file_name)
            cd_pcap.loadpcap()
            #cd_pcap.printpcap()
