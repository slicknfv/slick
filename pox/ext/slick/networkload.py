"""NetworkLoad is the base class. Based on underlaying
infrastruture/technology, sflow, RMON-II, openflow, custom proto, we can
implement new classes."""
class NetworkLoad(object):
    def __init__(self, controller):
        self.controller = controller

    def get_link_load(self, link):
        """Given the link return the link load.
        Args:
            link: Its a tuple describing source and destination points of a link.
        Returns:
            LinkLoad object.
        """
        pass

    def get_machine_load(self, machine_id):
        """Given the middlebox machine id return the machine load.
        Args:
            machine_id: e.g, Middlebox machine mac address
        Returns:
            MachineLoad object.
        """
        pass

    def get_element_load(self, ed):
        """Given the element descriptor return the element instance load.
        Args:
            ed: Element Descriptor
        Returns:
            ElementLoad object.
        """
        pass

    def get_congested_links(self):
        """Return the list of congested links in network."""
        pass

    def get_loaded_elements(self):
        """Return the list of loaded element descs."""
        pass

    def get_loaded_middleboxes(self):
        """Return list of middlebox machines."""
        pass
