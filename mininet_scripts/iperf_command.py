import time
from signal import SIGINT

from mininet.util import custom, pmonitor

def get_iperf_server_command(port_number, interval_sec, proto):
    """ Example Command: server_command = "iperf -s -u -p 11002 -i 1"
    """
    server_command = "iperf -s"
    if (not isinstance(port_number, int)) or (not isinstance(interval_sec, int)) or (not isinstance(proto, str)):
        raise Exception("Invalid arguments!")
    if proto == "u":
	server_command += " -u"
    elif proto == "t":
    	server_command += ""
    server_command = server_command + " -p "+ str(port_number) + " -i " + str(interval_sec)
    # Just for validation can be removed.
    command_list = server_command.split(" ")
    if len(command_list) != 7:
    	raise Exception("Invalid Command.")
    return server_command

def get_iperf_client_command(server_host, total_time, port_number, bandwidth, interval_sec, proto):
    """Exmaple Command: "iperf -c 127.0.0.1 -u -t 10 -i 1 -p 11002 -b 100m"
       Args:
       server_host: Mininet Host class object.
       total_time: Time the client should be sending the traffic.
       port_number: port number for iperf.
       bandwidth: bandwidth in mbps for sending the traffic.
       Returns:
	Command string
    """
    if (not isinstance(port_number, int)) or (not isinstance(interval_sec, int)) or (not isinstance(proto, str)) or (not isinstance(total_time, int)):
    	raise Exception("Invalid arguments!")
    client_command = "iperf -c " + str(server_host.IP()) + " -t "+str(total_time) + " -i "+str(interval_sec) + " -p "+str(port_number) + " -b "+str(bandwidth)+"m"
    return client_command

def perform_link_failures(network, links_to_fail):
    if links_to_fail:
	# TODO: Check if the link really exists.
        for link in links_to_fail:
	    print "Bringing ", link[0] , link[1], " link down."
            network.configLinkStatus(link[0], link[1], 'down')

def execute_iperf_command(network, hosts, single_command_timeoutms, total_time_sec, links_to_fail):
    """Args:
	network: Mininet network object
        hosts: source destination pair list
        single_command_timeoutms: timeout in ms for the command. 
		                  It should > the total time of iperf command.
        total_time_sec: Number of seconds to run the iperf command.
    Returns:
        A list of stdout line by line.
    """
    popens_client = { }
    popens_server = { }
    output = [ ]
    start_port_num = 11000
    for host_pair in hosts:
	start_port_num += 1
	#Client should be running on source.
	src = host_pair[0]
	# Server should be running on the destination.
	dst = host_pair[1]
	# Build the command
	interval_sec = 1
	proto = ""
	bandwidth = 1 # Bandwidth is in mbps.
	"""Total duration of iperf command."""
    	server_command = get_iperf_server_command(start_port_num, interval_sec, proto)
    	client_command = get_iperf_client_command(dst, total_time_sec, start_port_num, bandwidth, interval_sec, proto)
    	print dst.name, server_command
    	print src.name, client_command
        popens_server[ dst.name ] = dst.popen(server_command, shell=False)
        popens_client[ src.name ] = src.popen(client_command, shell=False)
    print "Monitoring output for ", total_time_sec+10, " seconds"
    # total_time_sec is the time to make the iperf run and we wait for extra 5 seconds to be sure.
    endTime = time.time() + total_time_sec + 10
    #perform_link_failures(network, links_to_fail)
    # We only need the output from the server to get any loss rate.
    for h, line in pmonitor( popens_server, timeoutms=single_command_timeoutms ):
        if h:
            if len(line) > 10: # This is due to a bug where new lines are printed.
                output.append( '<%s>: %s' % ( h,  line )),
        if time.time() >= endTime:
	    # Close both client and server.
            for ps in popens_server.values():
                ps.send_signal( SIGINT )
            for pc in popens_client.values():
                pc.send_signal( SIGINT )
    f = open('output/workfile', 'w')
    for item in output:
        f.write(item)
    f.close()
    # Debug
    for line in output:
        if len(line) > 10:
            print line,
    print '\n'
    return output
