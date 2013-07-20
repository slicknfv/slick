#!/usr/bin/env python

import sys
sys.path.append('..')

import pcap

def all_eth_dev(af=pcap.AF_INET):
    """find all ethernet devices which have at least one address
    in address family `af'"""
    
    ret = []
    for d in pcap.pcap_findalldevs():
        if d['flags'] & pcap.PCAP_IF_LOOPBACK:
            continue
        if d['addresses'] is None:
            continue
        ipv4 = [a['addr'][0] for a in d['addresses']
                if a['addr'][1] == pcap.AF_INET]
        if not ipv4:
            continue
        try:
            p = pcap.pcap(d['name'])
            if p.datalink() == pcap.DLT_EN10MB:
                ret.append((d['name'], ipv4))
            del p
        except pcap.error:
            continue
    return ret

if __name__ == '__main__':
    print all_eth_dev()

