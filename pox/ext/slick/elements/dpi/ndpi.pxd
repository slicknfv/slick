
cdef extern from "pcapReader.c":
    cdef extern from "stdint.h":
        ctypedef unsigned long long u_int64_t
        ctypedef unsigned short u_int16_t
        ctypedef unsigned char u_char

    cdef extern from "../src/include/linux_compat.h":
        ctypedef struct ndpi_ip6_hdr:
            pass

        ctypedef struct ndpi_iphdr:
            pass

    cdef extern from "stdint.h":
        ctypedef struct pcap_pkthdr:
            pass

    void pcapReaderHello()
    #void pcap_packet_callback(unsigned char * args, struct pcap_pkthdr *header, const u_char * packet)
    void pcap_packet_callback(u_char * args, const pcap_pkthdr *header, const u_char * packet)
    unsigned int packet_processing(const u_int64_t time, const ndpi_iphdr *iph, ndpi_ip6_hdr *iph6, u_int16_t ip_offset, u_int16_t ipsize, u_int16_t rawsize)
    #unsigned int packet_processing(const u_int64_t time,u_int16_t ip_offset, u_int16_t ipsize, u_int16_t rawsize)
