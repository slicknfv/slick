# This module has code that should decide if we need to place 
# and route or perform one of them.
# Following Type of Decisions are made: 
# Add Instance
# Move Instance
# Steer/Redirect traffic.

class PlacenSteer(object):
    def __init__(self, controller):
        self._controller = controller
        pass

    def add_element_instance(self, overloaded_machine_mac):
        # Get all the elements that are on the machine.
        element_descs = list(self.controller.elem_to_mac.get_elem_descs(overloaded_machine_mac))
        # TODO: After modifying apply_elem() and get_placement() make this call from get_placement()
        elem_descs = self.controller.network_model.get_loaded_elements(element_descs)
        # Move one element instance at a time.
        for ed in elem_descs:
            #print elem_descs
            element_names = [ ]
            app_desc = None
            application_object = None
            parameters = [ ]
            flow = None

            e_name = self.controller.network_model.get_elem_name(ed)
            element_names.append(e_name)
            app_desc = self.controller.elem_to_app.get_app_desc(ed)
            application_object = self.controller.elem_to_app.get_app_handle(ed)
            flow = self.controller.flow_to_elems.get_element_flow(ed)
            param_dict = self.controller.elem_to_app.get_elem_parameters(ed)
            parameters.append(param_dict)
            # Call apply_elem but first build all the arguments
            # for the function call.
            # For now duplicate all element instances on the machine.
            self.controller.apply_elem(app_desc, flow, element_names, parameters, application_object)

    def move_element_instance(self):
        pass

    def steer_traffic(self):
        pass

    def place_n_steer(self):
        """Decide should we add/move elements or steer traffic."""
        # Return the list of congested middlebox machines.
        loaded_middleboxes = self._controller.network_model.get_loaded_middleboxes()
        # Return the list of congested links
        congested_links = self._controller.network_model.get_congested_links()
        print loaded_middleboxes
        # Return the list of loaded element instances.
        #loaded_elements = self._controller.network_model.get_loaded_elements()
        #if self._middlebox_overloaded(trigger_msg):
        #    element_descs = list(self.controller.elem_to_mac.get_elem_descs(overloaded_machine_mac))
        #    available_element_instances = lookup_available_element_instances(element_descs)
        #    if len(available_element_instances) == 0:
        #        self.add_element_instance()
        #    else:
        #        # Either move element instance or steer traffic.
        #        # Decide to move or steer traffic to existing element instances.
        #        # Decision to steer traffic over placing an element instance should 
        #        # be made how much traffic do we need to steer. If we need to steer 
        #        # traffic more than certain volume then we place element instance in the
        #        # path else we steer traffic.
        #        # To calculate the traffic to steer, estimate the volume of 
        #        # traffic.
        #        calc_distance
        ## Possible options.
        #self.add_element_instance(overloaded_machine_mac)
        #self.move_element_instance(overloaded_machine_mac)
        #self.remove_element_instance(overloaded_machine_mac)

