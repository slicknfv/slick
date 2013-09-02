"""
    NetworkModel class, which captures all of the state needed by the Placement, Steering, and Routing modules 
"""

from specs import MachineSpec
from specs import ElementSpec

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
        self._machine_load = {}         # machine mac -> load
        self._link_congestion = {}      # [mac,mac] -> congestion
        self._controller = controller
        self._elem_specs = ElementSpec()    # reads in the element manifests (.spec files)
        self._machine_specs = MachineSpec() # reads in the machine manifests (.spec files)

        # TODO put this in the controller
        self.element_sequences = {}     # flow match -> [element names] XXX we may want this to map to descriptors

    def get_element_placements (self, app_desc, element_name):
        """
            Returns the list of (mac,port) pairs where the element named 'element_name' has been placed
        """
        rv = []
        for elem_instance in self._name_to_instances[element_name]:
            if(elem_instance.app_desc == app_desc):
                rv.append( elem_instance.location )
        return rv

    def get_compatible_machines (self, elem_name):
        # TODO uncomment the code below to make it actually get compatible machines
        # TODO for now, it just returns all machines
        return self._controller.get_all_registered_machines()

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

        element_instance = ElementInstance(element_name, app_desc, element_desc, location)
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
