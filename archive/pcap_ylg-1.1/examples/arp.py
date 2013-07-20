#!/usr/bin/env python

import argparse, os.path, struct, sys, time

from socket import inet_ntop, AF_INET

sys.path.append('..')
import pcap

ETHER_ADDR_LEN = struct.calcsize('6B')
ETHER_TYPE_LEN = struct.calcsize('H')
ETHER_VLAN_TYPE_LEN = struct.calcsize('2H')
ETHER_HDR_LEN = 2 * ETHER_ADDR_LEN + ETHER_TYPE_LEN
ETHERTYPE_IP = 0x0800
ETHERTYPE_VLAN = 0x8100

IPV4_ADDR_LEN = struct.calcsize('I')

class EtherAddr(str):
    def __new__(cls, addr):
        if len(addr) != ETHER_ADDR_LEN:
            raise Exception, \
                  '%s.__new__(): malformed Ethernet MAC address' % cls.__name__
        return super(EtherAddr, cls).__new__(cls, addr)

    def __str__(self):
        return ':'.join(['%02x' % b for b in struct.unpack('6B', self)])

    def is_bcast(self):
        return self.__have_all_bytes(0xff)

    def is_unspec(self):
        return self.__have_all_bytes(0x00)

    def __have_all_bytes(self, byte):
        return len([b for b in struct.unpack('6B', self) if b == byte]) == 6

class ARP(str):
    HARDWARE_ETHER = 0x0001
    PROTOCOL_IP = 0x0800
    OP_REQUEST = 0x0001
    OP_REPLY = 0x0002
    
    def __new__(cls, pkt, bflag):
        mlen = struct.calcsize('2H2BH')
        if len(pkt) < mlen + 2 * (ETHER_ADDR_LEN + IPV4_ADDR_LEN):
            raise Exception, '%s.__new__(): truncated ARP packet' % cls.__name__
        ha_len, pa_len, op_code = struct.unpack('!4x2BH', pkt[:mlen])
        if ha_len != ETHER_ADDR_LEN or pa_len != IPV4_ADDR_LEN or \
           op_code not in (ARP.OP_REQUEST, ARP.OP_REPLY):
            raise Exception, '%s.__new__(): malformed ARP packet' % cls.__name__
        arp = super(ARP, cls).__new__(cls, pkt)
        arp.__op_code = op_code
        offset = mlen
        arp.__sha = EtherAddr(pkt[offset:offset + ha_len])
        offset += ha_len
        arp.__spa = pkt[offset:offset + pa_len]
        offset += pa_len
        arp.__tha = EtherAddr(pkt[offset:offset + ha_len])
        offset += ha_len
        arp.__tpa = pkt[offset:offset + pa_len]
        arp.__gratuitous = False
        if bflag is True and arp.__spa == arp.__tpa:
            if arp.__sha == arp.__tha or arp.__tha.is_unspec():
                arp.__gratuitous = True
        return arp

    def __repr__(self, i=' '):
        if self.__gratuitous is False:
            if self.__op_code == ARP.OP_REQUEST:
                return '%sWho has %s? Tell %s' % (i, self.tpa, self.spa)
            else:
                return '%s%s is at %s' % (i, self.spa, self.sha)
        return '%sGratuitous ARP for %s (%s)' % (i, self.spa, self.op_code)

    def __str__(self, i = ' '):
        ret = '%sHardware type: 0x%04x\n' % (i, ARP.HARDWARE_ETHER)
        ret += '%sProtocol type: 0x%04x\n' % (i, ARP.PROTOCOL_IP)
        ret += '%sHardware size: %d\n' % (i, ETHER_ADDR_LEN)
        ret += '%sProtocol size: %d\n' % (i, IPV4_ADDR_LEN)
        ret += '%sOpCode: %s\n [Is gratuitous: %s]\n' % \
              (i, self.op_code, self.is_gratuitous)
        ret += '%sSender MAC address: %s\n' % (i, self.sha)
        ret += '%sSender IP address: %s\n' % (i, self.spa)
        ret += '%sTarget MAC address: %s\n' % (i, self.tha)
        ret += '%sTarget IP address: %s' % (i, self.tpa)
        return ret

    @property
    def spa(self):
        return inet_ntop(AF_INET, self.__spa)

    @property
    def sha(self):
        return str(self.__sha)

    @property
    def tpa(self):
        return inet_ntop(AF_INET, self.__tpa)

    @property
    def tha(self):
        return str(self.__tha)

    @property
    def op_code(self):
        if self.__op_code == ARP.OP_REQUEST:
            return 'Request'
        return 'Reply'

    @property
    def is_gratuitous(self):
        return self.__gratuitous

def process_pkt(user, hdr, pkt):
    out, vflag = user
    t = time.strftime('%d/%m/%y %H:%M:%S', time.localtime(hdr['ts']['tv_sec']))
    t = '.'.join((t, str(hdr['ts']['tv_usec'])))
    out.write('\n' + t + ':\n')
    bflag = EtherAddr(pkt[:ETHER_ADDR_LEN]).is_bcast()
    offset = 2 * ETHER_ADDR_LEN
    eth_type = struct.unpack('!H', pkt[offset:offset + ETHER_TYPE_LEN])[0]
    eth_hlen = ETHER_HDR_LEN
    if eth_type == ETHERTYPE_VLAN:
        eth_hlen += ETHER_VLAN_TYPE_LEN
    try:
        a = ARP(pkt[eth_hlen:], bflag)
        if vflag is False:
            a = repr(a)
        else:
            a = str(a)
        out.write(a + '\n')
    except Exception, msg:
        out.write(str(msg) + '\n')
    out.flush()

def loop(ifname, pflag, cnt, out, tflag, vflag):
    try:
        if ifname is None:
            ifname = pcap.pcap_lookupdev()
        if tflag is False:
            out.write("Starting ARP packet capture on `%s':\n" % ifname)
            out.write(
                "[PCAP library version is: `%s']\n" % pcap.pcap_lib_version()
                )
        p = pcap.pcap(ifname, pcap.PCAP_SNAPLEN_DFLT, pflag)
        if p.datalink() != pcap.DLT_EN10MB:
            raise pcap.error, "`%s' is not an ethernet device" % ifname
        bpfp = p.compile(
            'arp and arp[0:2] = %d and arp[2:2] = %d' %
            (ARP.HARDWARE_ETHER, ARP.PROTOCOL_IP))
        p.setfilter(bpfp)
        if tflag is True:
            pd = p.dump_fopen(out)
            p.loop(cnt, pcap.pcap_dump, pd)
        else:
            p.loop(cnt, process_pkt, (out, vflag))
        sys.exit(0)
    except KeyboardInterrupt:
        p.breakloop()
        if tflag is False:
            out.write('\n\n<< Exiting on keyboard interrupt >>\n')
        sys.exit(0)
    except pcap.error, msg:
        out.write('%s: fatal error: %s\n' %
                  (os.path.basename(sys.argv[0]), msg)
                  )
        sys.exit(1)
    finally:
        if tflag is False:
            out.write(
                '\n[ARP packet(s): received ' +
                '#%(ps_recv)d, dropped #%(ps_drop)d]\n' % p.stats()
                )
            out.flush()
        if out != sys.stdout:
            try:
                out.close()
                if os.stat(out.name).st_size == 0:
                    os.unlink(out.name)
            except:
                pass
            
def parse_args():
    class FileAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            try:
                fd = open(values, 'wb')
            except IOError, msg:
                parser.exit(
                    1, "%s: option %s: can't open `%s': %s\n" %
                    (parser.prog, option_string, values, msg)
                    )
            setattr(namespace, self.dest, fd)

    parser = argparse.ArgumentParser(
        description='%(prog)s: a (small) ARP packet sniffer')
    parser.add_argument(
        '-c', '--count', metavar='COUNT', dest='count', type=int, default=-1,
        help='number of ARP packet(s) to be processed. Default is -1 (infinity)'
        )
    parser.add_argument(
        '-i', '--interface', metavar='IFNAME', dest='ifname', default=None,
        help="network device. Default is the result of `pcap.pcap_looukupdev()'"
        )
    parser.add_argument(
        '-o', '--output-file', metavar='FILE', dest='out', action=FileAction,
        default=sys.stdout,
        help="output file. Default is `sys.stdout'"
        )
    parser.add_argument(
        '-p', '--promiscuous', dest='pflag', action='store_true',
        default=False, help='put interface into promiscuous mode'
        )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-t', '--tcpdump', dest='tflag', action='store_true',
        default=False, help='ARP packets are printed in tcpdump format'
        )
    group.add_argument(
        '-v', '--verbose', dest='vflag', action='store_true',
        default=False, help='ARP packets are printed in details'
        )
    args = parser.parse_args()
    args.pflag = int(args.pflag)
    return args

if __name__ == '__main__':
    args = parse_args()
    loop(args.ifname, args.pflag, args.count, args.out, args.tflag, args.vflag)
