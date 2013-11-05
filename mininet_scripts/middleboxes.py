# Code to start the middlebox instances on the element instances.
import time

from mininet.util import custom, pmonitor

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

def start_iperf(network, mblist):
    pass
