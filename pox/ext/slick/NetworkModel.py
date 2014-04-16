"""
    NetworkModel class, which captures all of the state needed by the Placement, Steering, and Routing modules 
"""
from collections import defaultdict

from specs import MachineSpec
from specs import ElementSpec
from slick.overlay_network import OverlayNetwork
from slick.overlay_network import dpid_to_str
from slick.physical_network import PhysicalNetwork
from slick.sflow_networkload import SFlowNetworkLoad
from slick.element_demands import ElementDemands
from pox.openflow.discovery import Discovery
from pox.core import core


class ElementInstance():
    def __init__(self, name, app_desc, elem_desc, location):
        self.name = name
        self.app_desc = app_desc
        self.elem_desc = elem_desc
        self.location = location

    def __str__ (self):
        return "ElementInstance(name:" + self.name + ", app_desc:" + str(self.app_desc) + ", elem_desc:" + str(self.elem_desc) + ", location:" + str(self.location) + ")"

class NetworkModel():
    def __init__ (self, controller):
        self._name_to_instances = {}    # element name -> element instances
        self._ed_to_instance = {}       # element descriptor -> element instance
        self._controller = controller
        self._elem_specs = ElementSpec()    # reads in the element manifests (.spec files)
        self._machine_specs = MachineSpec() # reads in the machine manifests (.spec files)
        self._elem_name_to_loaded_descs = defaultdict(list) #elem_name -> [loaded-eds]

        # TODO put this in the controller
        self.element_sequences = {}     # flow match -> [element names] XXX we may want this to map to descriptors
        # Build the overlay network
        self.overlay_net = OverlayNetwork(controller)
        self.physical_net = PhysicalNetwork(controller)
        self.network_load = SFlowNetworkLoad(controller)
        # Element Decriptor to switch MAC address mapping.
        # Can be used in steering.
        self.elem_to_switch = { }
        #self.element_demands = ElementDemands( )

    def update_function_loads(self, loaded_elem_descs):
        """This function is used to update the load
        about functions and their corresponding loaded element 
        instances.
        Args:
            List of loaded element descs from NetworkLoad module.
        Side Effect:
            Update the map for function to instance load mapping.
        Returns: 
            None
        """
        for ed in loaded_elem_descs:
            element_name = self.get_elem_name(ed)
            if element_name in self._elem_name_to_loaded_descs:
                self._elem_name_to_loaded_descs[element_name].append(ed)
            else:
                self._elem_name_to_loaded_descs[element_name] = [ed]

    def get_not_loaded_element_descs(self, element_name):
        """Given the element name return the element descriptors
        that are not loaded fully.
        Args: 
            element_name: Element name string.
        Returns:
        """
        loaded_elem_descs = [ ]
        all_elem_descs = self.get_element_descriptors(element_name)
        if element_name in self._elem_name_to_loaded_descs:
            loaded_elem_descs = self._elem_name_to_loaded_descs[element_name]
        not_loaded_element_descs = list(set(all_elem_descs) - set(loaded_elem_descs))
        return not_loaded_element_descs

    def get_min_elem_descs(self, element_name):
        # TODO: The policy writer should provide these paramters in controller params.
        return 1

    def add_elem_to_switch_mapping(self, replica_sets):
        """Update the element descriptor to switch mac 
        addresses."""
        for replicas in replica_sets:
            for ed in replicas:
                machine_mac = self.get_machine_mac(ed)
                machine_switch_mac = self.overlay_net.get_connected_switch(machine_mac)
                self.elem_to_switch[ed] = machine_switch_mac

    def get_elem_descriptor(self, switch_mac):
        """Given the switch mac address return the element 
        descriptors.
        Args:
            Switch MAC address
        Retruns:
            element descriptors list attached with the switch."""
        ed_list = [ ]
        for ed, s_mac in self.elem_to_switch.iteritems():
            if s_mac == switch_mac:
                ed_list.append(ed)
        if len(ed_list) > 0:
            return ed_list[0]

    def remove_elem_to_switch_mapping(self, ed):
        """If the element is removed or in migration and
        is no longer to be used remove its mapping."""
        if ed in self.elem_to_switch:
            del self.elem_to_switch[ed]

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
        element_instances = set( )
        if element_name in self._name_to_instances:
            element_instances = self._name_to_instances[element_name]
        for inst in element_instances:
            element_descriptors.append(inst.elem_desc)
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
    def get_all_forwarding_device_names(self):
        """Returns list of switch names."""
        forwarding_device_names = [ ]
        for _, switch_name in self.overlay_net.switches.iteritems():
            forwarding_device_names.append(switch_name)
        return forwarding_device_names

    def get_overlay_subgraph(self, src_switch, dst_switch, elem_descs):
        return self.overlay_net.get_subgraph(src_switch, dst_switch, elem_descs)

    def get_machine_mac (self, elem_desc):
        """Return the machine mac address for the 
        given element descriptor."""
        return self._controller.elem_to_mac.get(elem_desc)

    def get_host_loc(self, machine_mac):
        """Return the (dpid,port) for the machine mac"""
        mac_addr = ""
        if not isinstance(machine_mac, basestring):
            mac_addr = dpid_to_str(machine_mac, ':')
        else:
            mac_addr = machine_mac
        assert isinstance(mac_addr, basestring)
        if mac_addr in self.overlay_net.hosts:
            dpid_port_tuple = self.overlay_net.hosts[mac_addr]
            return dpid_port_tuple
        else:
            raise KeyError("Host MAC Address is not registered with any switch.")

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
        else:
            return None

    def get_elem_descs(self, elem_name):
        """Given the element name return all the descriptors corresponding to the name."""
        elem_descs = [ ]
        for ed, ei in self._ed_to_instance.iteritems():
            if ei.name == elem_name:
                elem_descs.append(ed)
        return elem_descs

    def is_affinity_required(self, ed, element_name):
        """Given element instance check if the element affinity
        is requested by administrator else return the default affinity
        preference of the element."""
        #ed = elem_inst.elem_desc
        #element_name = elem_inst.name
        affinity = self.get_elem_admin_affinity(ed)
        print "Affinity:",affinity, type(affinity)
        if affinity:
            return True
        else:
            return self.get_elem_spec_affinity(element_name)

    def is_bidirection_required(self, ed):
        """Based on elem descriptor return the if bidirection is required or not."""
        elem_inst = None
        elem_name = ""
        if ed in self._ed_to_instance:
            elem_inst = self._ed_to_instance[ed]
            elem_name = elem_inst.name
            if self.get_elem_admin_direction(ed):
                return True
            else:
                return self.get_elem_spec_direction(elem_name)

    #
    # Functions to return the spec paramters from spec files and 
    # administrator.
    #
    def get_elem_spec_placement(self, elem_name):
        """Given element_name string return the placement recommendation
        from the element specification."""
        spec_placement = None
        elem_spec = self._elem_specs.get_element_spec(elem_name)[elem_name]
        if elem_spec.has_key("placement"):
            spec_placement = elem_spec["placement"]
        return spec_placement

    def get_elem_admin_placement(self, elem_name):
        """Gievn the element name return the placement
        dictated by admin through application.
        TODO: Modify apply_elem and pass the parameters to network_model."""
        return None

    def get_elem_placement_pref(self, elem_name):
        """resolve between admin preference and default preference for placement."""
        placement_pref = None
        spec_placement  = self.get_elem_spec_placement(elem_name)
        admin_placement = self.get_elem_admin_placement(elem_name)
        if admin_placement:
            placement_pref = admin_placement
        elif spec_placement:
            placement_pref = spec_placement
        return placement_pref

    def get_elem_leg_type(self, elem_name):
        """Given element_name string return the leg heuristic
        from the element specification."""
        spec_leg = None
        elem_spec = self._elem_specs.get_element_spec(elem_name)[elem_name]
        if elem_spec.has_key("leg"):
            spec_leg = elem_spec["leg"]
            print elem_spec
        return spec_leg

    def get_elem_spec_direction(self, element_name):
        """Return True/False for bidirection/unidirection,
        according to spec."""
        bidirection = None
        default_elem_spec = self._elem_specs.get_element_spec(element_name)[element_name]
        #print "Default Elem params: ", default_elem_spec
        if "bidirection" in default_elem_spec:
            bidirection = default_elem_spec["bidirection"]
            if not isinstance(bidirection, bool):
                raise slick_exceptions.ElementSpecificationError("\'bidirection\' feature of specification has wrong type %s ", type(bidirection))
            return bidirection
        else:
            raise slick_exceptions.ElementSpecificationError("\'bidirection\' feature of specification not present for element %s ", element_name)

    def get_elem_admin_direction(self, ed):
        """Return True/False for bidirection/unidirection,
        according to application."""
        bidirection = None
        controller_params = self._controller.elem_to_app.get_controller_params(ed)
        #print "Controller params: ",controller_params
        if "bidirection" in controller_params:
            bidirection = controller_params["bidirection"]
            if not isinstance(bidirection, bool):
                raise slick_exceptions.ElementSpecificationError("\'bidirection\' feature specified by application has wrong type %s ", type(bidirection))
        return bidirection

    def get_elem_spec_affinity(self, element_name):
        """This is the global spec of the element copied from the 
        element specification file. For all the applications this is the 
        one value to be used. Unless application specifically overrides it.

        Args:
            element_name: Element Name String.
        returns:
            True/False based on whatever is present in the <element_name>.spec file.
        """
        affinity_required = None
        default_elem_spec = self._elem_specs.get_element_spec(element_name)[element_name]
        #print "Default Elem params: ", default_elem_spec
        if "affinity" in default_elem_spec:
            affinity_required = default_elem_spec["affinity"]
            if not isinstance(affinity_required, bool):
                raise slick_exceptions.ElementSpecificationError("\'affinity\' feature of specification has wrong type %s ", type(affinity_required))
            return affinity_required
        else:
            raise slick_exceptions.ElementSpecificationError("\'affinity\' feature of specification not present for element %s ", element_name)

    def get_elem_admin_affinity(self, ed):
        """This is specific to the application, different apps (in future) can 
        have multiple options for the same element feature.
        Args:
            ed: elemenet descriptor integer.
        Returns:
            True/False based on the value dictated by the application writer.
        """
        affinity = False
        controller_params = self._controller.elem_to_app.get_controller_params(ed)
        #print "Controller params: ",controller_params
        if "affinity" in controller_params:
            affinity = controller_params["affinity"]
            if not isinstance(affinity, bool):
                raise slick_exceptions.ElementSpecificationError("\'affinity\' feature specified by application has wrong type %s ", type(affinity_required))
        return affinity

    def update_admin_elem_specs(self, element_names, admin_params):
        self._elem_specs.update_admin_elem_specs(element_names, admin_params)

    #
    # Machine, Element and Link Loads
    # 
    def get_loaded_elements(self):
        """Given the element descs, return the loaded element instance descriptors"""
        # TODO Based on the flow load return the most loaded element instance/s.
        # with only one application descriptor.
        #return [element_descs[0]]
        loaded_element_descs = [ ]
        loaded_element_descs = self.network_load.get_loaded_elements( )
        return loaded_element_descs

    def get_loaded_middleboxes(self):
        loaded_middlebox_machines = [ ]
        loaded_middlebox_machines = self.network_load.get_loaded_middleboxes( )
        return loaded_middlebox_machines

    def get_congested_links(self):
        loaded_links = [ ]
        loaded_links = self.network_load.get_congested_links( )
        return loaded_links

    def get_physical_link_utilizations(self):
        # Wrapper
        # Returns the %age utilization.
        return self.network_load.get_link_utilizations()

    def element_placement_allowed(self, mac):
        elem_descs = self._controller.elem_to_mac.get_elem_descs(mac)
        if len(elem_descs) < self.get_max_elements(mac):
            return True
        else:
            return False

    def get_max_elements(self, mac):
        #TODO With different specs of physical machines there can
        # be multiple max number of elements.
        # Maximum number of elements per machine.
        MAX_ELEMENTS_PER_MACHINE = 1
        return MAX_ELEMENTS_PER_MACHINE

    def place_n_steer(self):
        """A wrapper to call place_n_steer out of regular interval."""
        self._controller.place_n_steer.place_n_steer()

    def resolve_partitions(self, src, dst, eds):
        """Wrapper."""
        self._controller.place_n_steer.resolve_partitions(src, dst, eds)

    def get_updated_replicas(self, flow):
        """This is the function to get updated replicas if get_steering could
        not find elements in initial attempt."""
        replica_sets_temp = self._controller.flow_to_elems.get(flow.in_port, flow)
        return replica_sets_temp
