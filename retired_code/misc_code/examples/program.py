class DNSPayloadControllerProgram():
    def __init__(self):
        self.blocked_ips = []

    def init_function():
        mb_loc = controller.lookup_machine_location()
        mb_ip = controller.get_ip_address(mb_loc)
        if(meets_function_spec(mb_ip))
            download_logic(mb_ip)
        else:
            raise Exception "Machine does not match spec"

    # I am assuming that the controller will have the definition of the event as well.
    def handle_trigger(BadDomainDetectionEvent event):
        if(type(event) == BadDomainDetectionEvent):
            ip_list = event.domain_ip_list
            src_ip = event.src_ip
            tuple_list = create_tuples(src_ip,ip_list)
            block_ips(tuple_list)

        
    def update_own_state(BadDomainDetectionEvent event):
        self.blocked_ip.append(event.src_ip)


class DNSPayloadControllerProgramNetworkWideView():
    def __init__(self):
        self.misbehaving_ips = []
        self.send_to_IPS = False

    def init_function():
        mb_loc = controller.lookup_machine_location()
        mb_ip = controller.get_ip_address(mb_loc)
        if(meets_function_spec(mb_ip))
            download_logic(mb_ip)
        else:
            raise Exception

    # I am assuming that the controller will have the definition of the event as well.
    def handle_trigger(event):
        if(type(event) == BadDomainDetectionEvent):
            ip_list = event.domain_ip_list
            src_ip = event.src_ip
            tuple_list = create_tuples(src_ip,ip_list)
            if(self.send_to_ips == True):
                redirect_traffic_to_ips(tuple_list)

        
    def update_own_state(BadDomainDetectionEvent event):
        self.misbehaving_ips.append(event.src_ip)
        if(len(self.misbehaving_ips) > 10):
            self.send_to_ips = True



