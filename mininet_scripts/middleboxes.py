# Code to start the middlebox instances on the element instances.
import time
from signal import SIGINT
from sets import Set
from collections import defaultdict
import xml.etree.ElementTree as ET

from mininet.util import custom, pmonitor

import patterns

"""
    Traffic Pattern Identifier:
        1: Make all the hosts ping/wget to a domain name such that the DNS lookup
           request is generated and then measure the latency.
        2: fetch a webpage from webserver inside the network.
            a- Creates webserver on specified hosts.
            b- Makes clients fetch webpages.
"""

def load_shims(network, mblist):
    """List of middlebox names.
    Loads shim for host names provided."""
    # To get the output of the opened process; maintain handles.
    popens = { }
    for mbhost in mblist:
        mb = network.getNodeByName(mbhost)
        print "Starting shim on host:", mbhost
        popens[ mbhost ] = mb.popen("sudo python /home/mininet/middlesox/shim/shim.py", shell=False)
        # Wait for n seconds to bring up one element instance.
        print "Waiting for shim layer to be started."
        time.sleep(0.25)

def execute_command_ping(network, hosts, command, single_command_timeoutms=1000, kill_wait_sec=15):
    """Args:
        hosts: List of hosts to execute the command.
        command: string of command to execute.
        single_command_timeoutms: timeout in ms for the command.
        kill_wait_sec: Time to wait in sec before sending SIGINT.
    Returns:
        A list of stdout line by line.
    """
    popens = { }
    output = [ ]
    for hostname in hosts:
        host = network.get(hostname)
        popens[ hostname ] = host.popen(command, shell=False)
    print "Monitoring output for", kill_wait_sec, "seconds"
    endTime = time.time() + kill_wait_sec
    for h, line in pmonitor( popens, timeoutms=single_command_timeoutms ):
        if h:
            if len(line) > 10: # This is due to a bug where new lines are printed.
                output.append( '<%s>: %s' % ( h,  line )),
        if time.time() >= endTime:
            for p in popens.values():
                p.send_signal( SIGINT )
    for line in output:
        if len(line) > 10:
            print line,
    print '\n'
    return output

def generate_traffic(network, hosts, middleboxes, traffic_pattern, kill_wait_sec):
    """network is the network object from mininet.
    hosts: List of hosts to use as clients for traffic generation.
    traffic_pattern: Identification of traffic pattern to generate."""
    hstar = True
    all_hosts = Set([ ])
    if len(hosts) == 0:
        # => All the hosts should be used as client.
        hstar = True
    if traffic_pattern == patterns.PING_SINGLE_IP_OUTSIDE_NETWORK:
        seconds = kill_wait_sec
        if hstar == True:
            # Returns the list of host names.
            for h in network.hosts:
                print h
                all_hosts.add(h.name)
            hosts = all_hosts - Set(middleboxes)
        print all_hosts
        print Set(middleboxes)
        print hosts
        print network.hosts
        #command = "ping -c 5 www.google.com"
        command = "ping -c 50 143.215.129.1"
        #command = "wget -S www.google.com"
        output = execute_command_ping(network, hosts, command, 10000, kill_wait_sec)
        latency_dict = _get_latency(output)
        print latency_dict
    if traffic_pattern == patterns.HARPOON_EAST_WEST:
        if hstar == True:
            # Returns the list of host names.
            for h in network.hosts:
                all_hosts.add(h.name)
            # Hosts that are acting as middleboxes
            # are not used as traffic generators/receivers
            hosts = list(all_hosts - Set(middleboxes))
            num_hosts = len(hosts)/2
            server_hosts = hosts[0 : num_hosts]
            client_hosts = hosts[num_hosts : len(hosts)]
            print "Server Hosts: ", server_hosts
            print "client hosts: ", client_hosts
            # -v is the verbosity level 0=min and 10=max
            # -w is number of seconds.
            # -c tell the server to cycle and keep on listening forever.
            print "Starting the harpoon servers..."
            server_command = ("/usr/local/harpoon/run_harpoon.sh -v10 -w%s -c -f tcp_server_ex2.xml &" % patterns.HARPOON_NUM_SECONDS)#"examples/tcp_server_ex2.xml"
            server_popens = { }
            for hostname in server_hosts:
                host = network.get(hostname)
                server_popens[ hostname ] = host.popen(server_command, shell=False)
            time.sleep(1)
            #output = execute_command(network, server_hosts, server_command, 10000, kill_wait_sec)
            # Code for the clients.
            print "Starting the harpoon clients..."
            #client_command = ("/usr/local/harpoon/run_harpoon.sh -v10 -w%s -c -f tcp_client_ex2.xml" % patterns.HARPOON_NUM_SECONDS)
            client_command = ("/usr/local/harpoon/run_harpoon.sh -v10 -w%s -f tcp_client_ex2.xml" % patterns.HARPOON_NUM_SECONDS)
            print client_command
            output = execute_command(network, client_hosts, client_command, 10000, kill_wait_sec)
            for h, output_lines in output:
                print output_lines

def execute_command(network, hosts, command, single_command_timeoutms=1000, kill_wait_sec=15):
    """Args:
        hosts: List of hosts to execute the command.
        command: string of command to execute.
        single_command_timeoutms: timeout in ms for the command.
        kill_wait_sec: Time to wait in sec before sending SIGINT.
    Returns:
        A list of stdout line by line.
    """
    popens = { }
    output = defaultdict(list) # host_name-> outputlist
    for hostname in hosts:
        host = network.get(hostname)
        popens[ hostname ] = host.popen(command, shell=False)
    #print "Monitoring output for", kill_wait_sec, "seconds"
    #endTime = time.time() + kill_wait_sec
    #print "End Time: ", endTime
    ##for h, line in pmonitor( popens, timeoutms = 15000):
    #for h, line in pmonitor( popens):
    #    print "XXXXXXXXXXXXXXXXXXXX"
    #    if h:
    #        print output
    #        if h in output:
    #            if len(line) > 10: # This is due to a bug where new lines are printed.
    #                output[h].append( '<%s>: %s' % ( h,  line )),
    #    if time.time() >= endTime:
    #        print "YYYYYYYYYYYYYYYYYYYYYYYYYYYYY"
    #        for p in popens.values():
    #            #p.send_signal( SIGINT )
    #            print "KILLING PROCESS"
    #            p.kill( )#send_signal( SIGINT )
    #for h, line in output.iteritems():
    #    if len(line) > 10:
    #        print line,
    #print '\n'
    return output

def _get_latency(output):
    """Given a list of strings where each entry is a line of ping output
        return a dict where keys are hostnames and values are latencies."""
    latency_dict = { }
    for line in output:
        if ("rtt min/avg/max/mdev" in line) or ("min/avg/max/stddev" in line):
            line.rstrip()
            output_array = line.replace("/"," ").split(" ")
            print output_array
            min_lat = float(output_array[7])
            avg_lat = float(output_array[8])
            host_name = output_array[0].strip('<').strip('>:')
            latency_dict[host_name] = avg_lat
    return latency_dict

def start_iperf(network, mblist):
    pass
