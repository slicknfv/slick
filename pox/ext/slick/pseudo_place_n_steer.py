# This is not a code file but a file for pseudo code.

# Heuristics based.
What are the scenarios where place and route should only work.
1- When should controller steer over creating a new instance?
     If the link is the bottleneck than steer the traffic:
          congested_overlay_links = get_congested_overlay_links()
          #This can happen when the virtual link to be used is utilizing >=90% of
          #virtual link available bandwidth. In that case we can ask steering module to give us an alternate path.
          #if alternate_path_available(element_chain, element_descs_to_avoid):
          affected_element_instances = get_affected_element_instances(congested_overlay_links)
          if alternate_path_available(affected_element_instances):
              ed_list = provide_alternate_element_decs_list()
          else:
            # This is integration of placement and steering(Joint placement and steering)
            installed_ed = install_new_element_instance_that_provides_shortest_alternate_path([[ ], ... ,[ ]]_of_non_overloaded_element_instances)
            ed_list = get_steering(src,replica_sets,dst)

2- When should controller create a new instance than steering the traffic.
    If the middlebox machine is bottleneck than create new instance.
        loaded_middlebox_instances = self_controller.network_model.get_loaded_middlebox_instances()
        #This can happen when a middlebox instance is utilizing >=90% of middlebox resources.
        #In that case we need to create a new middlebox instance.
        loaded_element_instance_type = get_loadded_element_instance_type()
        if alternate_element_instance_available(loaded_element_instance_type):
            # This is where placement and steering are integreated.
            ed_list = provide_alternate_element_decs_list(loaded_element_instance_type)
            steer_through_alternate_element_instances()
        else:
            installed_ed = install_new_element_instance_that_provides_shortest_alternate_path([[ ], ... ,[ ]]_of_non_overloaded_element_instances)

maintain the list of loaded paths and instances to avoid or replicate...

# There can be:
# Loaded Links.
# Loaded Middlebox machines
# Loaded Loaded instances
# We assume that middlebox machines cannot be the bottleneck and the load on middlebox machines is similar to load
# on element instances.


Heuristics:
    if middlebox is loaded:
        create_new_element_instance_closest_to_existing_machine.
    if element_instance is loaded:
        create_new_element_instance_closest_to_hosts_being_served.u
    if link is loaded:
        reroute the traffic.

def oracle(self, physical_graph, overlay_graph, loaded_element_instances, overloaded_links, link_to_load_map, element_machine_mac_to_load_map):
    pass


def place_n_steer():
    """1- Steers Traffic
       2- Create new instances.
       3- Moves instances.
       4- Destroys intances.
    """
    # Return the list of congested middlebox machines.
    loaded_middleboxes = self._controller.network_model.get_loaded_middleboxes()
    # Get the list of element instances on the middlebox machine.
    loaded_middlebox_instances = self_controller.network_model.get_loaded_middlebox_instances()
    # Return the list of congested links
    congested_overlay_links = self._controller.network_model.get_congested_overlay_links()
    print loaded_middlebox_instances
    print loaded_overlay_links

#######################################################################
all_shortest_paths= get_k_shortest_paths(src, dst)
shortest_path = None
for path in all_possible_paths: 
    if is_path_loaded(path):
        continue
    else:
        shortest_path = path
        break

if not shortest_path:
    # We are screwed.
    pass

elem_macs = get_steering()
if no elem_macs:
    apply_elem()
