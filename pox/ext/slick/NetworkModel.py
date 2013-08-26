"""
    NetworkModel class, which captures all of the state needed by the Placement, Steering, and Routing modules 
"""

class NetworkModel():
    def __init__( self ):
        self.element_instances = {}     # element name -> element descriptors
        self.element_placements = {}    # element descriptor -> machine mac/port
        self.element_names = {}         # element descriptor -> element name
        self.machine_load = {}          # machine mac -> load
        self.link_congestion = {}       # [mac,mac] -> congestion
        self.machines = []              # [mac,port] pairs, one for each known machine

        # TODO put this in the controller
        self.element_sequences = {}     # flow match -> [element names] XXX we may want this to map to descriptors

    def get_element_placements( self, element_name ):
        """
            Returns the list of (mac,port) pairs where the element named 'element_name' has been placed
        """
        rv = []
        for ed in self.element_instances[element_name].iteritems():
            rv.append( self.element_placements[ed] )

    def get_compatible_machines( self, element_name ):
        # TODO actually look up manifests. For now, just return all machines
        return self.machines

    def path_was_installed( self, flow_match, element_sequence, machine_sequence, path ):
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
    def add_placement( self, element_name, element_desc, place ):
        # TODO if ((element_desc in self.element_placements) and (self.element_placements[element_desc] != element_desc)) ... error

        if(element_name not in self.element_instances.keys()):
            self.element_instances[element_name] = set()

        self.element_instances[element_name].add( element_desc )
        self.element_placements[element_desc] = place
        self.element_names[element_desc] = element_name

    def remove_placement( self, element_desc ):
        # TODO search through self.placements for element_desc and remove it
        if(element_desc in self.element_names.keys())
            element_name = self.element_names[element_desc]
            self.element_instances[element_name].remove( element_desc )
            del self.element_names[element_desc]

    def get_placements( self, element_name ):
        if(element_name not in self.element_instances.keys()): pass
        rv = []
        for ed in self.element_instances[element_name].iteritems():
            rv.add(element_placements[ed])
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
