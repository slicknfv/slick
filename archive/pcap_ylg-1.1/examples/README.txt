- all_ether_dev.py: a very simple example

- arp.py: a much more sophisticated example, showing many aspects of pcap
  module. Type `./arp.py -h' to start.

- show_dump.py: another simple example to use in conjunction with arp.py,
  $ ./arp.py -i eth0 -c 2 -t -o dump
  $ ./show_dump.py dump
  On 16/10/12 14:51:04.353318, a packet of 64 bytes
  On 16/10/12 14:51:04.714019, a packet of 64 bytes
  [Total number of packets #2]

- arp_scan.py: an ARP scanner. Type `./arp_scan.py -h' to start.

Note: you have to run examples as root
