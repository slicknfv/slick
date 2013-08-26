import glob
from collections import defaultdict

class LoadCache:
	"""LoadCache for laoding the blocked domain names."""
	def __init__(self):
		DNS_BLOCK_LIST_DIR = "/tmp/blacklists" # Make it programmable.
		self.data = defaultdict(list) # A dictionary with Domain Name as key and IP address list as resolved addresses.
		self.block_dir = DNS_BLOCK_LIST_DIR
		self.block_domain_dict = {}

	def _list_files(self):
		file_list = [] 
		for infile in glob.glob(self.block_dir+"/*/domains"):
			file_list.append(infile)
		if (len(file_list) == 0 ):
			raise Exception,"ERROR: Could not find the domain names to block"
		return file_list

    	# This function loads the blacklists file.
	def load_files(self):
		for item in self._list_files():
			f = open(item,'r')
			for domain in f.readlines():
				self.block_domain_dict[domain.rstrip()] = True

	def is_blocked_domain(self,domain_name):
		if(self.block_domain_dict.has_key(domain_name)):
			return True
		else:
			return False

