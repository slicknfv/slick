# This is the main file to be used for DNS Sensor

import os,sys
import getopt
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,parentdir) 
import constants

from dns_sensor import DNSSensor


MAIN_DEBUG = False
# --
# Main function calls from here
# TODO: sanitize input.
# --
def main(argv):
    iface = ""
    freq = 0
    mode = 2
    file_name = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdi:f:", ["help","debug","iface","file"])
    except getopt.GetoptError:
        print "Option error!"
        doc.usage()
        sys.exit(2)
    for opt, arg in opts:
        print opt
        if opt in ("-h","--help"):
            doc.usage()
            sys.exit()
        elif opt in("-d","--debug"):
            mode = constants.DEBUG_MODE
        elif opt in("-f","--file"): 
            file_name = arg
        elif opt in("-i","--iface"):
            iface = str(arg)
            print "Listening on the interface: ",iface
        else:
            assert False, "Unhandled Option"
            doc.usage()
    if(MAIN_DEBUG):
        print freq
        print iface
        print mode
        print file_name
    dns_sensor = DNSSensor(mode,str(iface),file_name)
    dns_sensor.initiate()

if __name__ == "__main__":
    main(sys.argv[1:])
