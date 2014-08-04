This document has been updated to work for mininet 2.1

Please check the FAQ first to search for common problems while following these instructions.
In case of problems please send an email to bilal@gatech.edu with the error description.

INSTALLING SLICK
----------------
1. VM Setup:
	- These instructions assume that you already have a mininet VM Image
	  running on VirtualBox.
	- It has been tested with the following image:
		http://onlab.vicci.org/mininet-vm/mininet-2.1.0p2-140718-ubuntu-14.04-server-amd64-ovf.zip
		OLD: https://github.com/downloads/mininet/mininet/mininet-2.0.0-113012-amd64-ovf.zip
	- Note that, since it is AMD64, if you are using an Intel machine,
	  you may have to modify your BIOS settings to turn on AMD
	  emulation
	- Also, you will want to be able to ssh into the mininet VM from
	  your host.  These resources may be helpful:
		http://www.youtube.com/watch?v=yNmv7GiHIKE
		http://dowdberry.blogspot.com/2013/07/virtualbox-host-only-networking.html
2. Code Download:
	- From within your mininet VM, in the default /home/mininet folder,
	  download the following:

		```git clone https://github.com/bilalanwer/slick.git```
    - This will download slick code and pox code that is required by slick.
3. Installing dependencies:
	- Run the following commands from within your mininet VM:

		```$ cd ~/slick```
	
		```$ ./install-slick.sh```
	- This will install various dependencies:
		* paramiko (for SSHv3 support)
		* scp.py module.
		* pcap (for shim)
		* rpyc (also for shim)
		* scapy (for p0f module)
		* pybloomfilter library
    		* other dependencies
	- The install-slick.sh script does not currently check exit
	  statuses; please scroll up and look for any failures, and address
	  accordingly (though, if your VM is set up correctly and you are
	  connected to the Internet, it should be fine).
	- As the script says at the end, add the following line to .bashrc
	  (or whatever shell you decide to use):
	    export PYTHONPATH=/home/mininet/slick/pox:/home/mininet/mininet/:/home/mininet/pox


RUNNING SLICK
-------------
The script to set up the topology and start running mininet treats our
controller as a "Remote Controller" (so as to play nice with mininet).  
When mininet starts up, it will try to contact the controller;
as a result, we need to start up the Slick controller (by means of
starting POX) first.

1. Slick Controller Configuration:
    - Please make sure that the configuration file at:
      slick/pox/ext/slick/conf.py
      has the correct username and password in the file.
    - For example if you are running the demo with user "mininet"
      and password "mininetpass".
      MB_USERNAME = "mininet"
      MB_PASSWORD = "mininetpass"
    - This is required to make sure that slick controller can log into
      the element machines and download the code on on them and run the 
      commands. Slick also assumes that this user has sudo access to run
      the shim code etc.

2. Starting the controller:
   - Open up a new terminal on your host machine and ssh into your
	  mininet VM (recall that the user/pass is mininet/mininet).
   - Running the following commands will start the Slick controller:

	```$ cd slick/pox/pox/```

	```$ sudo ./pox.py --verbose host_tracker slick.slick_controller --application=TwoLoggers --query=details messenger slick.tcp_transport --tcp_address=192.168.56.101 --tcp_port=7790 samples.spanning_tree --forwarding=l2_multi_slick```
   - Please make sure that you are giving the right address as argument to --tcp_address. The demo will not work if the address is wrong.
   - Alternatively, you can bind to the NAT IP address in the root context (--tcp_address=192.168.56.101)
3. Starting the network and experiment:
   - Open up another terminal on your host machine and again ssh into
     your mininet VM.  This time, be sure to include the -X option to
     ssh so that you can open up xterms for the various mininet hosts.
   - Running the following script will create a network topology, and 
     will set up NAT so that mininet hosts can communicate with hosts
     on the Internet. This script by default creates a tree topology
     and the fanout and depth of the tree can be specified with -f and -d 
     options respectively.:

	```$ sudo python internet_ssh_exp.py -i <interface> -d 2 -f 3 -s <second-interface-ip-address> -p 1 -k 60 -c exp.config -g s1```

	```$ sudo python internet_ssh_exp.py -i eth1 -d 2 -f 3 -s 192.168.57.104 -p 1 -k 60 -c exp.config -g s1```

   - where <interface> is your virtual Ethernet interface that connects to the Internet and -s option
     specifies the IP address where element machines should connect with the controller. This is the same 
     address that is specified in --tcp_address option for slick controller. Please note 
     -i and -s are two different interfaces. 

   - -p option tell the experiment number to run. Specifying "-p 1"
     automatically starts ping command on one of the hosts in the network and pings
     www.google.com 10 times. This command should result in logging of dns requests
     to the DNS server for www.google.com domain name, in file /tmp/dns_logX. Where
     X will be an integer.

   - Once the experiment is completed it will drop the terminal into a mininet CLI.


TROUBLESHOOTING SLICK:
---------------------

In case you do not see any dns flow logs in the /tmp/dns_logX file. It means that
the Slick setup is not working properly. In this section we'll try to perform some of the 
automatic steps to pin point the problem. 

1. Sanity checking the network
	- You should be able to ping hosts on the Internet from the mininet
	  hosts.  You do this from within the mininet CLI; the following
	  should return typical ping output:

	```mininet> h1 ping -c 10 google.com```

2. Setting up the shim
	- If you flip back over to the controller terminal, you'll see that
	  it is failing to find middlebox machines on which to place
	  elements.  This is because the shims aren't running on the
	  mininet hosts yet.

	- Open up a terminal to h3:
	```mininet> xterm h3```

	- From this terminal, run:

	```h3# python ~/slick/shim/shim.py -c <slick_controller_ip_address>```

	```h3# python ~/slick/shim/shim.py -c 192.168.56.101```

	This will start the shim layer and will register h3 as a
   	middlebox so that slick controller can redirect traffic to this
   	middlebox. Please not the slick controller ip address is the same address
   	that is used while starting the controller and provided as --tcp_address
   	option to pox controller command line. 
   	
   	You can optionally specify input and output interfaces (though the
      	default should do the right thing)
        This should print some debug output showing that it has 
      	successfully connected to the Slick controller.  The Slick
      	controller should by now say that it has successfully installed Logger.

3. Pinging hosts:
   - As a final test, you should be able to use h1 or h2 to ping
	  external hosts:

	```mininet> h1 ping google.com```

   - Please check:

	(1) that you get the ping replies back.
	
	(2) that h3:/tmp/dns_logX has logged the DNS messages (i.e.,
		that the Logger element worked)
		
	The dns_logX file should have the DNS flows that are being sent
	from host h1 or h2 to the Internet.

