class Event():
        def __init__(self):
            self.id = None
            self.name = None
            self.flow = EventFlow()


"""
    Class for defining a flow for the architecture.
"""
class EventFlow(self):
    self.src_mac = None
    self.dst_mac = None
    self.vlan = None
    self.src_ip = None
    self.dst_ip = None
    self.proto = None
    self.src_port = None
    self.dst_port = None

"""
    @description:
        Generate this event if the bad domain nameis looked up.
"""
class BadDomainDetectionEvent(Event):
    def __init__(self):
        self.domain_name = None
        self.src_ip = None
        self.domain_ip_list = []
        self.level =-None 
