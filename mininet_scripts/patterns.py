# We use this file as configuration file.
# This file has information about the traffic patterns
# that can be used to generate in the code.



# 1-to-m relationship between the single host
# outside the network and the hosts sitting inside the network.
PING_SINGLE_IP_OUTSIDE_NETWORK = 1
OUTSIDE_IP_ADDRESS_LIST = ["143.215.129.1"] # This IP Address should be on the Internet.
# m-to-n relationship between many hosts
# outside the network and the hosts sitting inside the network.
PING_MULTIPLE_IPS_OUTSIDE_NETWORK = 2


# 1-to-m relationship between the single host
# outside the network and the hosts sitting inside the network.
HTTP_SINGLE_IP_OUTSIDE_NETWORK = 3
# m-to-n relationship between multiple hosts
# outside the network and the hosts sitting inside the network.
HTTP_MULTIPLE_IP_OUTSIDE_NETWORK = 4


# 1-to-m relationship between the single host
# outside the network and the hosts sitting inside the network.
UDP_SINGLE_IP_OUTSIDE_NETWORK = 5
# m-to-n relationship between multiple hosts
# outside the network and the hosts sitting inside the network.
UDP_MULTIPLE_IP_OUTSIDE_NETWORK = 6


# 1-to-m relationship between the single host
# outside the network and the hosts sitting inside the network.
TCP_SINGLE_IP_OUTSIDE_NETWORK = 7
# m-to-n relationship between multiple hosts
# outside the network and the hosts sitting inside the network.
TCP_MULTIPLE_IP_OUTSIDE_NETWORK = 8


# Harpoon traffic direction
HARPOON_EAST_WEST = 100
# NORTH-SOUTH (Traffic started by nodes outside the network)
HARPOON_NORTH_SOUTH = 101
# SOUTH-NORTH (Traffic started by nodes inside the network)
HARPOON_SOUTH_NORTH = 102
# This is the conf file for the harpoon to generate the traffic pattern.
HARPOON_SERVER_FILE = "tcp_server_ex2.xml"
HARPOON_CLIENT_FILE = "tcp_client_ex2.xml"
# Number of seconds to run the Harpoon Experiment.
# This value should be >=60 seconds 
HARPOON_NUM_SECONDS = 5