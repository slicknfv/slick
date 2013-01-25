# This file has the code for populating the function map 
# from the middleboxes.
import sys

from collections import defaultdict
import json

class FunctionMap():
	def __init__(self,function_map_file):
		self.function_map_file = function_map_file
		self.function_map = defaultdict(dict)

	def read_json(self):
		json_data = self.function_map_file;#open('/home/openflow/noxcore/src/nox/coreapps/examples/tutorial/function_map.json')
		json_data_dict = json.load(json_data)
		json_data.close() # Close the file and return
		return json_data_dict

# For testing.
def usage():
	print "\n\n"
	print "-h or --help\n\tShows this usage guide"

def main(argv):
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hs:", ["help","source"])
	except getopt.GetoptError, err:
		print "Option error!"
		print str(err)
		sys.exit(2)

	for opt, arg in opts:
        	if opt in ("-h","--help"):
            		usage()
            		sys.exit()
        	elif opt in ("-s","--source"):
            		source_db_path =str(arg)
            		print "Reading Links from links JSON files at: "+ str(source_db_path)
    		else:
			print "Please provide args"

if __name__ == "__main__":
    main(sys.argv[1:])
