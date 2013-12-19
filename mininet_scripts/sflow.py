# This script has the code to setup sflow for all the 
# switches; and potentially code for setting up
# hsflowd.
import sys
import json
import requests
from mininet.util import quietRun
import os
import subprocess
import signal
import time

def start_hsflowd( network, cmd='/usr/sbin/hsflowd', opts='-d' ):
    "Run hsflowd on all hosts."
    for host in network.hosts:
        host.cmd( cmd + ' ' + opts + '&' )
    print
    print "*** Hosts are running hsflowd***"
    print

def setup_switch_sflow_agents(switches, controller=None):
    """Given the list of switches; start sflow agent on the switches."""
    # Set interface for the agent.
    # Set the sampling rate.
    # set the polling rate
    # set the collector's ip address.
    # set the bridge name based on the switch.

    # Number of seconds to get a new sample for dump.
    polling_freq = 5
    if not controller:
        print "WARNING: No controller and port specified, using 127.0.0.1:6343"
        controller = "127.0.0.1:6343"
    for switch_name in switches:
        # Incase we need switch specific interface we need to use
        # s1-eth1 or s2-eth1 etc.
        #agent_interface = ("%s-eth1", switch_name)
        agent_interface = "eth0"
        target_str = '\"' + controller + '\"'
        #                                                          |
        #command = 'ovs-vsctl -- --id=@sflow create sflow agent=%s  target=%s sampling=10 polling=20 -- -- set bridge %s sflow=@sflow ' % (agent_interface, "127.0.0.1", switch_name)
        command = ('ovs-vsctl -- --id=@sflow create sflow agent=%s target=%s sampling=10 polling=%s -- -- set bridge %s sflow=@sflow' % (agent_interface, target_str, polling_freq, switch_name))
        print command
        ret = quietRun(command)
        if len(ret) != 37:
            print ret
            print "ERROR: Unable to start sflow on switch:", switch_name

def setup_host_sflow_metrics(network):
    """List of host names.
    Ideally we'll setup up hsflowd on each of the hosts. 
    But hsflowd uses /proc/ filesystem. 
    For mininet we need hsflowd to be able to read resources
    using cgroups instead of /proc/ or we need mininet to be
    able to support separate filesystem for each host.
    """
    rt = 'http://localhost:8008'
    for host in network.hosts:
        host_name = host.name
        host_ip = host.IP() # type(host_name)
        print host_ip, host_name
        command = ('curl -H "Content-Type:application/json" -X PUT --data "{value:\'bytes\',filter:\'ipdestination=%s\'}" http://localhost:8008/flow/%s/json' % (host_ip, host_name))
        command = 'curl -H "Content-Type:application/json" -X PUT --data \'{value:"bytes",filter:"ipdestination=192.168.100.18"}\' http://localhost:8008/flow/h8/json'
        filter_value = ("ipdestination=%s" % host_ip)
        metric_str = ('/flow/%s/json' % host_name)
        #metric_str = ('/flow/%s/json' % host_ip)
        params = {"value":"bytes", "filter":filter_value}
        r = requests.put(rt + metric_str, data=json.dumps(params))
        print r

def start_sflow_collector():
    """Start the sflow collector on 127.0.0.1:6343 in background"""
    path = os.path.dirname(os.path.abspath(__file__))
    sflow_collector_command =  path + "/sflow-rt/start.sh"
    print sflow_collector_command
    command = sflow_collector_command
    subprocess.Popen([command,"&"])

def stop_sflow():
    # Kill sflow_collector
    # WARNING: This will kill other java processes.
    process_name = "java"
    proc = subprocess.Popen(["pgrep", process_name], stdout=subprocess.PIPE) 
    # Kill process.
    for pid in proc.stdout:
        os.kill(int(pid), signal.SIGTERM)
        # Sending signal zero to a pid will raise OSError exception if 
        # pid does not exist. If it exists then we were unable to kill
        # the process.
        try:
            os.kill(int(pid), 0)
            time.sleep(2)
            print("""wasn't able to kill the process 
                    HINT:use signal.SIGKILL or signal.SIGABORT""")
        except OSError as ex:
            continue

#### Test Code. ####
def main(argv):
    switches = ["s1", "s2","s3","s4","s5","s6","s7"]
    controller = "127.0.0.1:6343"
    #setup_switch_sflow_agents(switches, controller)
    hosts = ["h1", "h2", "h3", "h4", "h5", "h6", "h7", "h8"]
    #setup_host_sflow_metrics(hosts)
    start_sflow_collector()

if __name__ == "__main__":
    main(sys.argv[1:])
