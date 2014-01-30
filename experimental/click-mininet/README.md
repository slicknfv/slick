# A Wrapper for Click switches in Mininet

This provides a simple wrapper for [Click software switches
](http://read.cs.ucla.edu/click/) in the [Mininet network virtualization
](http://yuba.stanford.edu/foswiki/bin/view/OpenFlow/Mininet) environment.

Currently it allows for Click kernel switches to be run as a virtual
switch. While this is a functional wrapper around Click, there are some
important limitations:

+ Only one Click configuration may be used
+ Path to the configuration file must be hard-coded into the class
+ You must manually map network interfaces in the Click config file to hosts connected
to the switch
+ I have not tested it with multiple Click switches yet

Please see the `test.py` and `sandbox.py` files for examples. Both construct a
simple topology of two hosts connected by a single switch:

Host 1 <--> Click router <--> Host 2

The router configuration just connects the two hosts together and passes on
traffic between them. Running `test.py` will set up the network and then use
`netcat` and `wget` to retrieve a file from Host 1 to Host 2.

The sandbox replicates the same network topology and then drops into the Mininet
command line interface.