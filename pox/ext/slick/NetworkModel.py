"""
    NetworkModel class, which captures all of the state needed by the Placement, Steering, and Routing modules 
"""

from specs import MachineSpec
from specs import ElementSpec
from slick.overlay_network import OverlayNetwork

class ElementInstance():
    def __init__(self, name, app_desc, elem_desc, location):
        self.name = name
        self.app_desc = app_desc
        self.elem_desc = elem_desc
        self.location = location

    def __str__ (self):
        return "ElementInstance(name:" + self.name + ", app_desc:" + str(self.app_desc) + ", elem_desc:" + str(self.elem_desc) + ", location:" + str(self.location) + ")"

class MachineLoad(object):
    def __init__(self, mac):
        self.mac = mac
        self.cpu_percent = None
        self.bytes_mem = None
        self.max_mem = None
        self.num_flows = None
        self.max_flows = None

class ElementInstanceLoad(object):
    def __init__(self, ed, max_load = 0):
        self.ed = ed
        self.max_flows = 0
        self.num_flows = 0

class LinkLoad(object):
    def __init__(self, link):
        # link = (src_mac, dst_mac)
        self.link = link
        self.link_capacity = None
        self.link_bandwidth = None


class NetworkLoad(object):
    def __init__(self, controller):
        self.controller = controller
        self._machine_load = {}         # machine mac -> load
        self._elem_inst_load = {}       # element desc -> load
        self._link_congestion = {}      # [mac,mac] -> congestion

    def update_machine_load(self, mac, flow):
        """Args:
            mac: integer mac address
           packetin_event:
            MachineLoad object of the machine.
           Returns:
             None
        """
        self._machine_load[mac] = machine_load

    def update_element_instance_load(self, ed, flow):
        if ed not in self._elem_inst_load:
            elem_instance_load = ElementInstanceLoad(ed)
            elem_instance_load.num_flows += 1
            self._elem_inst_load[ed] = elem_instance_load

    def update_link_load(self, link):
        pass

class NetworkModel():
    def __init__ (self, controller):
        self._name_to_instances = {}    # element name -> element instances
        self._ed_to_instance = {}       # element descriptor -> element instance
        self._controller = controller
        self._elem_specs = ElementSpec()    # reads in the element manifests (.spec files)
        self._machine_specs = MachineSpec() # reads in the machine manifests (.spec files)

        # TODO put this in the controller
        self.element_sequences = {}     # flow match -> [element names] XXX we may want this to map to descriptors
        # Build the overlay network
        self.overlay_net = OverlayNetwork(controller)
        self.network_load = NetworkLoad(controller)


    def get_element_placements (self, app_desc, element_name):
        """
            Returns the list of (mac,port) pairs where the element named 'element_name' has been placed
        """
        rv = []
        for elem_instance in self._name_to_instances[element_name]:
            if(elem_instance.app_desc == app_desc):
                rv.append( elem_instance.location )
        return rv

    def get_element_descriptors(self, element_name):
        """ Return all the element_descriptors for an element_name.
        This can include element_desc from different apps.
        """
        element_descriptors = [ ]
        for element_name, element_instance in self._name_to_instances.iteritems():
            element_descriptors.append(element_instance.elem_desc)
        return element_descriptors

    def get_all_registered_machines (self):
        return self._controller.get_all_registered_machines()

    def get_compatible_machines (self, elem_name):
        # TODO uncomment the code below to make it actually get compatible machines
        # TODO for now, it just returns all machines

        # Return all the hosts inside the network
        all_hosts = self.overlay_net.get_all_machines()
        print all_hosts
        # Return all forwarding devices switches, routers.
        all_switches = self.overlay_net.get_all_forwarding_devices()
        print all_switches
        # Return all machines with shim running on them.
        registered_machines = self._controller.get_all_registered_machines()
        return registered_machines
        #return all_hosts
    """
        elem_spec = self._elem_specs.get_element_spec(elem_name)
        registered_machines = self._controller.get_all_registered_machines()
        matched_machines = []
        if (elem_spec.has_key("os") and 
            elem_spec.has_key("processor_type") and 
            elem_spec.has_key("os_flavor") and 
            elem_spec.has_key("os_flavor_version")):
            for mac,machine_spec in self.machine_specs:
                if (machine_spec.has_key("os") and 
                    machine_spec.has_key("processor_type") and 
                    machine_spec.has_key("os_flavor") and 
                    machine_spec.has_key("os_flavor_version")):
                    if ((machine_spec["os"] == elem_spec["os"]) and 
                        (machine_spec["processor_type"] == elem_spec["processor_type"]) and 
                        (machine_spec["os_flavor"] == elem_spec["os_flavor"]) and 
                        (machine_spec["os_flavor_version"] == elem_spec["os_flavor_version"])):
                        if(mac in registered_machines):
                            matched_machines.append(mac)
                else:
                    raise Exception("Invalid Machine Specification")
        else: 
            raise Exception(" Invalid Function Specification")
        return matched_machines
    """

    def path_was_installed (self, flow_match, element_sequence, machine_sequence, path):
        """
            Inputs:
                - flow_match: the flow that was installed
                - machine_sequence: the machines that Steering chose
                - path: the path that was installed
            Outputs:
                - None
            Side effects:
                - Uses 'element_sequence' and 'machine_sequence' to update:
                    - current load on the machines
                    - on which machines the elements are placed
                - Uses 'path' to update:
                    - per-link congestion
                    - the traffic matrix
        """
        pass

    # Placement state
    def add_placement (self, element_name, app_desc, element_desc, mac_addr):
        # TODO return an error if this app_desc has already placed this element_desc

        element_instance = ElementInstance(element_name, app_desc, element_desc, mac_addr)
        if(element_name not in self._name_to_instances.keys()):
            self._name_to_instances[element_name] = set()

        self._name_to_instances[element_name].add( element_instance )
        self._ed_to_instance[element_desc] = element_instance

    def remove_placement (self, element_desc):
        # TODO search through self.placements for element_desc and remove it
        if(element_desc in self._ed_to_instance.keys()):
            instance = self._ed_to_instance[element_desc]
            self._name_to_instances[instance.name].remove(instance)
            del self._ed_to_instance[element_desc]

    def dump (self):
        """
        Just some debug
        """
        rv = "\t_name_to_instances: { "
        for name,instance_set in self._name_to_instances.iteritems():
            rv = rv + name + ": ( "
            for inst in instance_set:
                rv = rv + str(inst) + " "
            rv = rv + ") "
        rv = rv + "}"

        rv = rv + "\n\t_ed_to_instance: { "
        for ed,inst in self._ed_to_instance.iteritems():
            rv = rv + str(ed) + ": " + str(inst) + " "
        rv = rv + "}"

        rv = rv + "\n\t_machine_load: " + str(self._machine_load) 
        rv = rv + "\n\t_link_congestion: " + str(self._link_congestion)
        return rv

    # Load state
    """
    def set_load( self, node, load ):
        self.load[node] = load

    def get_load( self, node ):
        return self.load[node]

    def get_traffic_matrix( self ):
        return None
    """

    # Wrapper for overlay_network function.
    def get_overlay_subgraph(self, src_switch, dst_switch, elem_descs):
        return self.overlay_net.get_subgraph(src_switch, dst_switch, elem_descs)

    def get_machine_mac (self, elem_desc):
        """Return the machine mac address for the 
        given element descriptor."""
        return self._controller.elem_to_mac.get(elem_desc)

    def get_connected_switch(self, machine_mac):
        """Return the dpid for the machine mac"""
        return self.overlay_net.get_connected_switch(machine_mac)

    def get_elem_names(self):
        """Return a list of active element names."""
        return self._name_to_instances.keys()

    def get_elem_descs(self):
        """Return a list of all elem descs."""
        return self._ed_to_instance.keys()

    def get_elem_name(self, ed):
        """Given the element_desc return elem name.
        Args:
            ed: element descriptor integer.
        Returns:
            element_name string.
        """
        elem_instance = None
        if ed in self._ed_to_instance:
            elem_instance = self._ed_to_instance[ed]
        return elem_instance.name

    def network_health(self):
        """Function to check the health of the network and take appropriate action."""
        pass

    def get_available_load(self, machine_mac):
        """Return percentage available of machine CPU."""
        pass

    # Functions to return the spec paramters from spec files and 
    # administrator.
    def get_elem_spec_placement(self, elem_name):
        """Given element_name string return the placement recommendation
        from the element specification."""
        spec_placement = None
        elem_spec = self._elem_specs.get_element_spec(elem_name)
        if elem_spec.has_key("placement"):
            spec_placement = elem_spec["placement"]
        return spec_placement

    def get_elem_admin_placement(self, elem_name):
        """Gievn the element name return the placement
        dictated by admin through application.
        TODO: Modify apply_elem and pass the parameters to network_model."""
        return None

    """
        Interface for loads.
    """
    def update_element_instance_load(self, ed, flow):
        pass

    def update_machine_load(self, mac, flow):
        pass

    def update_link_load(self, link):
        pass

    def get_loaded_elements(self, element_descs):
        """Given the element descs, return the top most loaded element instance."""
        # TODO Based on the flow load return the most loaded element instance/s.
        # with only one application descriptor.
        return element_descs
