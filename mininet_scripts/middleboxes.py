# Code to start the middlebox instances on the element instances.
import time
from signal import SIGINT
from sets import Set

from mininet.util import custom, pmonitor

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
    if traffic_pattern == 1:
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
        output = execute_command(network, hosts, command, 10000, kill_wait_sec)
        latency_dict = _get_latency(output)
        print latency_dict

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
