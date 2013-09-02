import os
import sys
from triggers import Triggers


class DNSHandlers(Triggers):
    def __init__(self,inst):
        self.cntxt = inst

    def handle_BadDomainEvent(self,event):
        pass

    def handle_triggers(self,event):
        if(event.name == "BadDNSEvent"):
            self.handle_BadDomainEvent(event)


    def configure_triggers(self):
        pass
