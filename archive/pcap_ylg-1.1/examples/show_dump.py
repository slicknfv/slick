#!/usr/bin/env python

import os.path, sys, time

sys.path.append('..')
import pcap

def show_pkt(user, h, pkt):
    global __npkt
    
    t = time.strftime('%d/%m/%y %H:%M:%S', time.localtime(h['ts']['tv_sec']))
    t = '.'.join((t, str(h['ts']['tv_usec'])))
    sys.stdout.write('On %s, a packet of %d bytes\n' % (t, h['len']))
    __npkt += 1
    
if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.stderr.write(
            'usage: %s <dump_file>\n' % os.path.basename(sys.argv[0])
            )
        sys.exit(1)
    try:
        global __npkt
        
        p = pcap.pcap_open_offline(sys.argv[1])
        __npkt = 0
        p.loop(-1, show_pkt)
        sys.stdout.write('[Total number of packets #%d]\n' % __npkt)
        sys.exit(0)
    except pcap.error, msg:
        sys.stderr.write('%s\n' % msg)
        sys.exit(1)
    
