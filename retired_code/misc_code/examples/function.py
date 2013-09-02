# Single domain example.
# i.e. send BadDomainEvent if we see one domain.
class DNSPayload():
    def init_function():
        interfaces = probe_ethernet_interface()
        connected_interfaces = get_connected_interfaces_to_network(interfaces)
        sniff_on_interface(connected_interfaces)


    def process_packet():
        flow = extract_flow()
        for each_dns_packet:
            if(bad_domain_name()):
                send_to_controller(BadDomainDetectionEvent)
        
    def send_to_controller(BadDomainDetectionEvent):
        controller_ip = lookup_controller_ip()
        send(BadDomainDetectionEvent)


# 10 domain example, i.e. only send event if we see 10 bad domains from same ip.
class DNSPayload10():
    def __init__(self):
        self.ip_to_bad_domain = defaultdict(int)
        pass

    def init_function():
        interfaces = probe_ethernet_interface()
        connected_interfaces = get_connected_interfaces_to_network(interfaces)
        sniff_on_interface(connected_interfaces)


    def process_packet():
        flow = extract_flow()
        src_ip = flow.src_ip 
        for each_dns_packet:
            if(bad_domain_name()):
                self.ip_to_bad_domain[src_ip] += 1
                if(self.ip_to_bad_domain[src_ip] >= 10):
                    send_to_controller(BadDomainDetectionEvent)
        
    def send_to_controller(BadDomainDetectionEvent):
        controller_ip = lookup_controller_ip()
        send(BadDomainDetectionEvent)


