# Code to start the middlebox instances on the element instances.
import os
import sys
import time
from signal import SIGINT
from sets import Set
from collections import defaultdict
import subprocess, shlex
import xml.etree.ElementTree as ET

from mininet.util import custom, pmonitor
from mininet.log import setLogLevel, info, warn, error, debug

import patterns
import plot_graphs

from subprocess import Popen, PIPE
import multiprocessing
from monitor.monitor import monitor_devs_ng

"""
    Traffic Pattern Identifier:
        1: Make all the hosts ping/wget to a domain name such that the DNS lookup
           request is generated and then measure the latency.
        2: fetch a webpage from webserver inside the network.
            a- Creates webserver on specified hosts.
            b- Makes clients fetch webpages.
"""

def load_shims(network, slick_controller,  mblist):
    """List of middlebox names.
    Loads shim for host names provided."""
    if not slick_controller:
	slick_controller = "192.168.56.101"
	print ("Using the default IP Address %s for the slick controller." % slick_controller)
	print "Please use -s option to specify the slick controller IP address."
    # To get the output of the opened process; maintain handles.
    popens = { }
    for mbhost in mblist:
        mb = network.getNodeByName(mbhost)
        print "Starting shim on host:", mbhost
        #cmd = ("sudo python /home/bilal/middlesox/shim/shim.py -c %s" % (slick_controller))
        #popens[ mbhost ] = mb.popen(cmd, shell=True)
        #popens[ mbhost ] = mb.popen("sudo python /home/mininet/middlesox/shim/shim.py", stdout=subprocess.PIPE, shell=True)
        #popens[ mbhost ] = mb.popen("sudo python /home/mininet/middlesox/shim/shim.py", stdout=subprocess.PIPE) # Does not work on FatTree
        #cmd = ("sudo python /home/mininet/middlesox/shim/shim.py -c %s &" % (slick_controller))
        cmd = ("sudo python ../shim/shim.py -c %s &" % (slick_controller))
	print cmd
	mb.cmd(cmd)
        # Wait for n seconds to bring up one element instance.
        print "Waiting for shim layer to be started."
        time.sleep(1)

### Start ping between hosts
def startpings( host, target, wait_time, attach_str):
  "Tell host to repeatedly ping targets"

  # Simple ping loop
  cmd = ( 'while true; do '
          ' echo -n %s "->" %s ' % (host.IP(), target) + 
          ' `ping %s -i %s -W 1.0 >> ../results/%s_%s__%s`;' % (target, str(wait_time), host.IP(), target, attach_str) + 
          ' break;'
          'done &' )
  print '%s is pinging %s -i %s -W 1.0' \
           % (  host.IP(),target, str(wait_time) )  
  host.cmd( cmd )

def execute_command_ping1(network, hosts, command, time_between_commands = 1, single_command_timeoutms=1000, kill_wait_sec=15):
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
        print "Pinging from host:", hostname, " with command:" ,command
        ping_result = host.cmd(command)
        output_array = ping_result.split("\n")
        for line in output_array:
            output.append( '<%s>: %s' % ( hostname,  line ))
            print '<%s>: %s' % ( hostname,  line )
        time.sleep(time_between_commands)
    return output

def execute_command_ping(network, hosts, command, time_between_commands = 1, single_command_timeoutms=1000, kill_wait_sec=15):
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
        print "Pinging from host:", hostname, " with command:" ,command
        popens[ hostname ] = host.popen(command, stdout=subprocess.PIPE) # Does not work on FatTree
        time.sleep(time_between_commands)
    print "Monitoring output for", kill_wait_sec, "seconds"
    endTime = time.time() + kill_wait_sec
    print endTime
    print popens
    for h, line in pmonitor( popens, timeoutms=single_command_timeoutms ):
        if h:
            if len(line) > 10: # This is due to a bug where new lines are printed.
                output.append( '<%s>: %s' % ( h,  line )),
        if time.time() >= endTime:
            for p in popens.values():
                p.send_signal( SIGINT )
            break
    print output
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
    if traffic_pattern == 12345:
        target = "www.google.com"
        attach_str = 'TEMP'
        wait_time = 1
        for host in network.hosts:
            startpings(host, target, wait_time, attach_str)
   
        time.sleep(30)

        # Stop pings
        for host in network.hosts:
          host.cmd( 'kill %while' )
          host.cmd( 'pkill ping' )

        print "c. Stopping Mininet"
        network.stop()
    if traffic_pattern == patterns.PING_SINGLE_DOMAIN_OUTSIDE_NETWORK:
        seconds = kill_wait_sec
        # Returns the list of host names.
        for h in network.hosts:
	    all_hosts.add(h.name)
	    break
        time.sleep(5)
        command = "ping -c 20 www.google.com"
        output = execute_command_ping1(network, all_hosts, command, 12, 1000, kill_wait_sec)# This will work for FatTree Topo
        latency_dict = _get_latency(output)
        min_lat = sys.maxint #1234567890
        max_lat = 0
        total_lat = 0

        for host in all_hosts:
            print host,',',int(latency_dict[host])
        for host, avg_host_latency in latency_dict.iteritems():
            if avg_host_latency < min_lat:
                min_lat = avg_host_latency
            if avg_host_latency > max_lat:
                max_lat = avg_host_latency
            total_lat += avg_host_latency
        avg_lat = total_lat/len(network.hosts)
        print "Average Latency experiment:", avg_lat
	print "Demo is complete. Please check the log file in /tmp/dns_logX to see if the TwoLoggers application is working correctly."
    if traffic_pattern == patterns.PING_SINGLE_IP_OUTSIDE_NETWORK:
        seconds = kill_wait_sec
        if hstar == True:
            print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
            # Returns the list of host names.
            for h in network.hosts:
                all_hosts.add(h.name)
            #hosts = all_hosts - Set(middleboxes)
        print all_hosts
        print Set(middleboxes)
        print hosts
        print network.hosts
        #command = "ping -c 50 www.google.com"
        #command = "ping -c 3 143.215.129.1"
        #command = "wget -S www.google.com"
        time.sleep(15)
        # Performing single pings to create new instances.
        command = "ping -c 1 192.168.56.101"# Please change this to the IP address of vboxnetX IP corresponding to virtual machines.
        #output = execute_command_ping(network, hosts, command, 1, 1000, 30) # This will work for other Topos
        output = execute_command_ping1(network, hosts, command, 1, 1000, 30) # This will work for FatTree Topo
        time.sleep(15)
        command = "ping -i 0.5 -c 10 192.168.56.101"# Please change this to the IP address of vboxnetX IP corresponding to virtual machines.
        #output = execute_command_ping(network, hosts, command, 12, 1000, kill_wait_sec)# This will work for other Topos
        output = execute_command_ping1(network, hosts, command, 12, 1000, kill_wait_sec)# This will work for FatTree Topo
        latency_dict = _get_latency(output)
        print latency_dict
        min_lat = 1234567890
        max_lat = 0
        total_lat = 0

        all_latencies = [ ]
        for host in hosts:
            print host,',',int(latency_dict[host])
            all_latencies.append(int(latency_dict[host]))
        for host, avg_host_latency in latency_dict.iteritems():
            if avg_host_latency < min_lat:
                min_lat = avg_host_latency
            if avg_host_latency > max_lat:
                max_lat = avg_host_latency
            total_lat += avg_host_latency
        avg_lat = total_lat/len(network.hosts)
        print "Average Min. Latency experiment:", avg_lat
        print "Total number of hosts:", len(network.hosts)
        #plot_graphs.plot_cdf("icmp_log.eps", all_latencies)
    if traffic_pattern == patterns.PING_SINGLE_IP_OUTSIDE_NETWORK_ONCE:
        seconds = kill_wait_sec
        if hstar == True:
            # Returns the list of host names.
            for h in network.hosts:
                all_hosts.add(h.name)
        time.sleep(15)
        # Performing single pings to check number of rules installed.
        command = "ping -c 1 192.168.56.101"# Please change this to the IP address of vboxnetX IP corresponding to virtual machines.
        output = execute_command_ping1(network, hosts, command, 1, 1000, 30) # This will work for FatTree Topo
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
    if traffic_pattern == patterns.UDP_SINGLE_IP_OUTSIDE_NETWORK:
        hosts = network.hosts
        exp_time_duration = 35 # seconds
        time_duration = exp_time_duration
        input_file = "traffic_data/ns_all_to_one"
        #input_file = "traffic_data/tree_ns_all_switches_to_one"
        output_dir = "traffic_data/"
        start_iperfTrafficGen(input_file, output_dir, time_duration, hosts, network)

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
            #print output_array
            min_lat = float(output_array[7])
            avg_lat = float(output_array[8])
            host_name = output_array[0].strip('<').strip('>:')
            #latency_dict[host_name] = avg_lat
            latency_dict[host_name] = min_lat
        if ("transmitted" in line):
            line.rstrip()
            output_array = line.split(" ")
            print output_array
            if output_array[6] != "0%":
                print "Error: There was a packet drop."
    return latency_dict

def start_tcpprobe():
    ''' Install tcp_probe module and dump to file '''
    os.system("rmmod tcp_probe; modprobe tcp_probe full=1;")
    Popen("cat /proc/net/tcpprobe > tcp.txt" , shell=True)

def stop_tcpprobe():
    os.system("killall -9 cat")

def start_iperfTrafficGen(input_file, output_dir, time_duration, hosts, net):
    '''Copied code 
    Generate traffic pattern using iperf and monitor all of thr interfaces
    
    input format:
    src_ip dst_ip dst_port type seed start_time stop_time flow_size r/e
    repetitions time_between_flows r/e (rpc_delay r/e)
    
    '''
    
    host_list = {} 
    for h in hosts:
        host_list[h.IP()] = h
    
    port = 5001
    
    data = open(input_file)
    
    start_tcpprobe()
    
    info('*** Starting iperf ...\n')
    for line in data:
        flow = line.split(' ')
        src_ip = flow[0]
        dst_ip = flow[1]
        if src_ip not in host_list:
            continue
        time.sleep(0.4)
        if dst_ip in host_list:
            server = host_list[dst_ip]
            server.popen('iperf -u -s -p %s > server.txt' % port, shell = True)

            client = host_list[src_ip]
            client.popen('iperf -u -c %s -p %s -t %d > client.txt' 
                    % (server.IP(), port, time_duration ), shell=True)
        else: # The case when server is hosted outside the network
	    print "Starting server on IP and on port:",str(dst_ip), str(port)
            Popen('iperf -u -s -p %s > server_%s.txt' % (port, port), shell = True)
            client = host_list[src_ip]
	    print "Starting client on IP and on port", str(src_ip), str(port), client
            #client.popen('iperf -u -b 1073741824 -c %s -p %s -t %d > client_%s.txt' 
            client.popen('iperf -c %s -u -b 1024 -p %s -t %d > client_%s.txt' 
                % (dst_ip, port, time_duration, port ), shell=True)
	    port += 1

    monitor = multiprocessing.Process(target = monitor_devs_ng, args =
                ('%s/rate.txt' % output_dir, 0.01))

    monitor.start()

    time.sleep(time_duration)

    monitor.terminate()
    
    info('*** stoping iperf ...\n')
    stop_tcpprobe()

    Popen("killall iperf", shell=True).wait()

''' Output of bwm-ng has the following format:
    unix_timestamp;iface_name;bytes_out;bytes_in;bytes_total;packets_out;packets_in;packets_total;errors_out;errors_in
    '''
from monitor.helper import *
from math import fsum
import numpy as np
def get_bandwidth(input_file, pat_iface):
    pat_iface = re.compile(pat_iface)
    
    data = read_list(input_file)

    rate = {} 
    column =4
        
    for row in data:
        try:
            ifname = row[1]
        except:
            break

        if ifname not in ['eth0', 'lo', 'eth1']:
            if not rate.has_key(ifname):
                rate[ifname] = []
            
            try:
                #rate[ifname].append(float(row[column]) * 8.0 / (1 << 20))
                rate[ifname].append(float(row[column])* 8.0/ (1024))
            except:
                break
    #print rate
    #print pat_iface
    vals = []
    vals1 =  {}
    for k in rate.keys():
        if pat_iface.match(k): 
	    #print rate[k]
            #avg_rate = avg(rate[k][10:-10])
            avg_rate = pc99(rate[k][10:-10])
	    print k, avg_rate
	    print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
            vals1[k] = avg_rate
	    vals.append(avg_rate)
    link_rates = { }
    f = open('interfaces.txt', 'r')
    for line in f.readlines():
        interfaces = line.split(',')
        if interfaces[0] in vals1.keys():
            print interfaces[0],',',interfaces[1],vals1[interfaces[0]]
	    #link_rates.append(vals1[interfaces[0]])
	    link_rates[(interfaces[0], interfaces[1])] = vals1[interfaces[0]]
    #print vals1
    #return fsum(vals)
    return link_rates

def gather_stats(files, regex, duration):
  start = 5
  end = min(duration, max(30, duration - 5))
  pat_iface = re.compile(regex)
  totals = []
  for f in files:
    data = read_list(f)[:-1]
    rate = {}
    column = 4
    for row in data:
      try:
        ifname = row[1]
      except:
        break
      if ifname not in ['eth0', 'lo', 'eth1']:
        if not rate.has_key(ifname):
          rate[ifname] = []
        try:
          rate[ifname].append(float(row[column]) * 8.0 / (1 << 10))
        except:
          break
    total = None
    for k in sorted(rate.keys()):
      if pat_iface.match(k):
        if total is None:
          total = [0] * len(rate[k])
	print k
        total = [i + j for i,j in zip(rate[k], total)]
        print total
    end = min(end, len(total))
    totals.append(total)
  print 'read [%d:%d] seconds' % (start, end)
  all_rates = []
  for total in totals:
    all_rates += total[start:end]
  print all_rates
  return sorted(all_rates)

#Regular expression for switches
sw = 's[1-9][0-9]-eth*|s[1-9]-eth*'
#Regex for FatTree switches`
#sw = '[0-3]h[0-1]h1'
#link_rates1 = get_bandwidth("traffic_data/nopart_rate_5d2f_tree.txt", sw)
#link_rates1 = get_bandwidth("../measurement/bw_util/nopart_rate_5d2f_tree.txt", sw).values()
#link_rates1 = get_bandwidth("../measurement/bw_util/nopart_rate_z5_fattree.txt", sw).values()
#link_rates1 = get_bandwidth("../measurement/bw_util/nopart_rate_y4_dcell.txt", sw).values()
#link_rates1 = get_bandwidth("../measurement/bw_util/nopart_rate_5d2f_tree.txt", sw)
#link_rates1 = get_bandwidth("../measurement/bw_util/nopart_rate_z5_fattree.txt", sw)
#link_rates1 = get_bandwidth("../measurement/bw_util/nopart_rate_y4_dcell.txt", sw)
#print "No Partition Link Rates: ",link_rates1
#print link_rates1
#link_rates2 = get_bandwidth("traffic_data/part_rate_5d2f_tree.txt", sw)
#link_rates2 = get_bandwidth("../measurement/bw_util/part_rate_5d2f_tree.txt", sw).values()
#link_rates2 = get_bandwidth("../measurement/bw_util/part_rate_z5_fattree.txt", sw).values()
#link_rates2 = get_bandwidth("../measurement/bw_util/part_rate_y4_dcell.txt", sw).values()
#link_rates2 = get_bandwidth("../measurement/bw_util/part_rate_5d2f_tree.txt", sw)
#link_rates2 = get_bandwidth("../measurement/bw_util/part_rate_z5_fattree.txt", sw)
#link_rates2 = get_bandwidth("../measurement/bw_util/part_rate_y4_dcell.txt", sw)
#print "Partition Link Rates: ",link_rates2

#plot_graphs.plot_two_cdfs("icmp_log.eps", all_latencies)
#plot_graphs.plot_two_cdfs("test_cdf.eps", link_rates1, link_rates2, "Link Utilization(Kbps)", "Links", "DCell Topology Utilization" )
#plot_graphs.plot_bar_graphs(link_rates1, link_rates2, x_label="Links", y_label="Link Utilization(Kbps)",title="DCell Network Link Utilization" )
#plot_graphs.plot_bar_graphs(link_rates1, link_rates2, x_label="Links", y_label="Link Utilization(Kbps)",title="Tree Network Link Utilization" )
#gather_stats(["traffic_data/rate_back.txt"], sw, 30)


# plot the bandwidth utilization with LEG.
#link_rates1 = get_bandwidth("../measurement/leg/rate_treefull_d4f2_1More_Random.txt", sw).values()
#link_rates2 = get_bandwidth("../measurement/leg/rate_treefull_d4f2_1More.txt", sw).values()
link_rates1 = get_bandwidth("../measurement/leg/rate_treefull_d4f2_1Less_Random.txt", sw).values()
link_rates2 = get_bandwidth("../measurement/leg/rate_treefull_d4f2_1Less.txt", sw).values()
plot_graphs.plot_two_cdfs("test_cdf.eps", link_rates1, link_rates2, "Link Utilization(Kbps)", "Links", "Tree Topology Utilization(Less Element)" )
