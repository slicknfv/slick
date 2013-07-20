#!/usr/bin/env python

import argparse, os.path, struct, sys, textwrap
sys.path.append('..')

import pcap

from socket import AF_INET, inet_ntop, inet_pton

class EtherHdr(str):
    TYPE_VLAN = 0x8100
    TYPE_ARP = 0x0806
    ADDR_NULL = ':'.join(6 * ('00',))
    
    def __new__(cls, dst, src, type_, vlan_id=None):
        try:
            etype = struct.pack('!H', type_)
        except:
            raise Exception, "`%s': invalid ethernet type" % type_
        if vlan_id is not None:
            try:
                etype = struct.pack('!2H', EtherHdr.TYPE_VLAN, vlan_id) + etype
            except:
                raise Exception, "`%s': invalid vlan ID" % vlan_id
        return super(EtherHdr, cls).__new__(
            cls, cls.ether_aton(dst) + cls.ether_aton(src) + etype)

    @staticmethod
    def ether_aton(addr):
        try:
            return struct.pack(
                '!6B', *[int(b, 16) for b in str(addr).split(':')])
        except:
            raise Exception, "`%s': invalid ethernet MAC address" % addr

    @staticmethod
    def len_(pkt):
        l = struct.calcsize('12BH')
        t = struct.unpack('!12xH', pkt[:l])[0]
        if t == EtherHdr.TYPE_VLAN:
            l += struct.calcsize('2H')
        return l
    
class EtherDev(pcap.pcap):
    def __init__(self, dev, promisc=False, to_ms=0):
        found = False
        for d in pcap.pcap_findalldevs():
            if d['name'] == dev:
                found = True
                break
        if found is False:
            raise Exception, "`%s': no such device" % dev
        super(EtherDev, self).__init__(
            dev, pcap.PCAP_SNAPLEN_DFLT, promisc, to_ms
            )
        if self.datalink() != pcap.DLT_EN10MB:
            raise Exception, "`%s': not an ethernet device" % dev
        err  = "`%s': can't find ethernet MAC address" % dev
        if d['addresses'] is None:
            raise Exception, err
        found = False
        for a in d['addresses']:
            if a['addr'] is not None and a['addr'][1] == pcap.AF_LINK:
                found = True
                break
        if found is False:
            raise Exception, err
        self.__addr = a['addr'][0]
        if a['broadaddr'] is None:
            self.__broadaddr = ':'.join(6 * ('ff',))
        else:
            self.__broadaddr = a['broadaddr'][0]
        self.__ipv4 = []
        for a in d['addresses']:
            if a['addr'] is not None and a['addr'][1] == pcap.AF_INET:
                self.__ipv4.append((a['addr'][0], a['netmask'][0]))
            
    @property
    def addr(self):
        return self.__addr

    @property
    def broadaddr(self):
        return self.__broadaddr

    @property
    def ipv4(self):
        if not self.__ipv4:
            return None
        return self.__ipv4

    def sendpacket(self, pkt, dst, type_, vlan_id=None):
        data = EtherHdr(dst, self.addr, type_, vlan_id) + pkt
        return super(EtherDev, self).sendpacket(data)

class ARP(str):
    HARDWARE_ETHER = 0x0001
    PROTOCOL_IP = 0x0800
    OP_REQUEST = 0x0001
    OP_REPLY = 0x0002
    HDR_LEN = struct.calcsize('2H2BH')
    
    def __new__(cls, s_mac, s_ip, t_mac, t_ip, op):
        bs_mac = EtherHdr.ether_aton(s_mac)
        hlen = len(bs_mac)
        bs_ip = cls.__inet_pton(s_ip)
        plen = len(bs_ip)
        bt_mac = EtherHdr.ether_aton(t_mac)
        bt_ip = cls.__inet_pton(t_ip)
        return super(ARP, cls).__new__(
            cls,
            struct.pack('!H', ARP.HARDWARE_ETHER) +
            struct.pack('!H', ARP.PROTOCOL_IP) +
            struct.pack('!2BH', hlen, plen, op) +
            bs_mac + bs_ip + bt_mac + bt_ip)

    @staticmethod
    def __inet_pton(addr):
        try:
            return inet_pton(AF_INET, addr)
        except:
            raise Exception, "`%s': invalid IPv4 address" % addr

class ARPRequest(str):
    def __new__(cls, s_mac, s_ip, t_ip):
        return ARP(
            s_mac, s_ip, EtherHdr.ADDR_NULL, t_ip, ARP.OP_REQUEST)

class IPRange(object):
    def __init__(self, addr, netmask):
        a, n = [
            struct.unpack('!I', inet_pton(AF_INET, x))[0]
            for x in (addr, netmask)]
        self.__n = a & n
        self.__b = self.__n + (~n & 0xffffffff)
        self.__a = a
        
    def next(self):
        self.__n += 1
        if self.__n >= self.__b:
            raise StopIteration
        if self.__n == self.__a:
            return self.next()
        return inet_ntop(AF_INET, struct.pack('!I', self.__n))

    def __iter__(self):
        return self

class ARPScan(EtherDev):
    def __init__(self, dev, promisc=False, to_ms=100):
        super(ARPScan, self).__init__(dev, promisc, to_ms)
        bpfp = self.compile(
            'ether dst %s and arp and arp[0:2] = %d and arp[2:2] = %d' %
            (self.addr, ARP.HARDWARE_ETHER, ARP.PROTOCOL_IP))
        self.setfilter(bpfp)

    def scan(self, out=sys.stdout, addr=None, netmask=None, vlan_id=None):
        if self.ipv4 is not None:
            for a in self.ipv4:
                self.__scan(out, *a, vlan_id=vlan_id)
        elif addr is None or netmask is None:
            raise Exception, \
                  'interface has no ipv4 address, ' + \
                  'you must provide an address/netmask'
        else:
            self.__scan(out, addr, netmask, vlan_id)
            
    def __scan(self, out, addr, netmask, vlan_id=None):
        for i in IPRange(addr, netmask):
            arp = ARPRequest(self.addr, addr, i)
            self.sendpacket(arp, self.broadaddr, EtherHdr.TYPE_ARP, vlan_id)
            ret = self.next_ex()
            if ret[0] == 0:
                continue
            elif ret[0] == 1:
                self.__process_pkt(out, *ret[1:])
            else:
                raise Exception, \
                      '%s.scan(): %s' % (self.__class__.__name__, ret[2])

    def __process_pkt(self, out, h, pkt):
        offset = EtherHdr.len_(pkt) + ARP.HDR_LEN
        ha = struct.unpack('!6B', pkt[offset:offset + 6])
        ha = ':'.join(['%02x' % b for b in ha])
        offset += 6
        pa = inet_ntop(AF_INET, pkt[offset:offset + 4])
        out.write('%-15s\t\t%s\n' % (pa, ha))

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
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""\
        %(prog)s is simple ARP scanner. If interface, given as argument, has
        IPv4 address(es), scanning is done for corresponding IP range(s).
        For example, if interface has IPv4 addresses 10.200.8.3/24 and
        172.28.0.10/25, ARP requests with following target IP addresses are
        sent: 10.200.8.1-2, 10.200.8.4-253, 172.28.0.1-9 and 172.28.0.11-126.
        IPv4 addresses are found by calling `pcap.pcap_findalldevs()'.
        
        If interface has no IPv4 address, you must provide one via
        `-a' and `-n' options. For example, on a Linux system, suppose
        you have a physical ethernet device eth0 with no IPv4 address
        assigned, and vlan-device eth0.2008 (vlan ID = 2008) attached to
        eth0 with IPv4 address 10.200.8.3/24. Then the commands:
          $ ./arp_scan.py eth0 -a 10.200.8.3 -n 255.255.255.0 -v 2008
        and:
          $ ./arp_scan.py eth0.2008
        are equivalent.

        %(prog)s output has following format:
          ddd.ddd.ddd.ddd  xx:xx:xx:xx:xx:xx
          ..................................
        and can be redirected via `-o' option
        """)
        )
    parser.add_argument(
        'interface', help='the interface to use for ARP scanning'
        )
    parser.add_argument(
        '-a', '--addr', dest='addr', default=None,
        help='IPv4 address if interface has no IPv4 address. See above'
        )
    parser.add_argument(
        '-n', '--netmask', dest='netmask', default=None,
        help="address netmask. See `-a option'"
        )
    parser.add_argument(
        '-o', '--output-file', metavar='FILE', dest='out', action=FileAction,
        default=sys.stdout,
        help="output file. Default is `sys.stdout'"
        )
    parser.add_argument(
        '-t', '--timeout', dest='to_ms', type=int, default=10,
        help='the timeout (in milliseconds) to wait for an ARP reply' +
        ' after sending an ARP request. Default is 10ms'
        )
    parser.add_argument(
        '-v', '--vlan-id', dest='vlan_id', type=int, default=-1,
        help='ethernet frame is tagged in vlan VLAN_ID. Default is no tag'
        )
    args = parser.parse_args()
    if args.vlan_id == -1:
        args.vlan_id = None
    elif not 1 <= args.vlan_id <= 4094:
        parser.exit(
            1, "%s: option `-v': invalid vlan ID:" % parser.prog +
            ' must be an integer in range [1-4094]\n'
            )
    return args

def main(args):
    try:
        dev = ARPScan(args.interface, to_ms=args.to_ms)
        dev.scan(args.out, args.addr, args.netmask, args.vlan_id)
        sys.exit(0)
    except Exception, msg:
        sys.stderr.write(
            '%s: fatal error: %s\n' % (os.path.basename(sys.argv[0]), msg)
            )
        sys.exit(1)
    finally:
        if args.out != sys.stdout:
            try:
                args.out.close()
                if os.stat(args.out.name).st_size == 0:
                    os.unlink(args.out.name)
            except:
                pass

if __name__ == '__main__':
    args = parse_args()
    main(args)
