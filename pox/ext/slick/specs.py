# This calss should be used to read the element specifications by the 
# slick controller to call apply_func on the required code segment.

from collections import defaultdict
import os,sys
import json
import logging
from slick_exceptions import *

_HISTORY_SIZE = 1

class ElementParams():
    def __init__(self, placement, affinity, bidirection, inline):
        self.placement = placemnt
        self.affinity = affinity
        self.bidirection = bidirection
        self.inline = inline

class ElementSpec():
    def __init__(self):
        self.element_specs = {} # element_name to element specification dictionary
        self.element_specs_history = [None] * _HISTORY_SIZE # element_name to element specification dictionary last state
        self.admin_element_specs = { } # element_name to element specification provided by admin.
        self.elements_path = os.getcwd() + "/"+"ext/slick/elements/"
        #self.elements_path = os.getcwd() + "/"+"elements/"
        self._load_specs()

    def _load_specs(self,path = None):
        files = os.listdir(self.elements_path)
        for item in files:
            if not item.startswith('.'):
                file_path = self.elements_path + "/" + item + "/"+item+".spec"
		try:
                	with open(file_path) as f:
                	    logging.debug("Loading Element Specification File: %s", file_path)
                	    json_data_dict = json.load(f)
                	    #self.element_specs[item] = json_data_dict
                	    self.element_specs[json_data_dict.keys()[0]] = json_data_dict
		except IOError:
			logging.fatal('Unable to load Element Specification File %s for %s element.', 
				      file_path, item)

    # Returns a dictionary
    # dml: I got rid of the check to see whether element_specs contained
    #      element_name so that the KeyError will just bump up (otherwise we
    #      get a difficult to track NoneType error later in the execution)
    def get_element_spec(self,element_name):
        return self.element_specs[element_name]

    def update_admin_elem_specs(self, elem_names, admin_parameters):
        """This function updates the element parameters using admin_params.

        Description:
            This helps us to keep track of any modification required by the applications.
        Args:
            elem_names: List of string of element name.
            admin_parameters: List of dict of administrator parameters.
        Returns:
            None

        TODO: This does not validate the parameter values.
        """
        for index, elem_name in enumerate(elem_names):
            admin_params = admin_parameters[index]
            # First store the elem specs from admin for debugging
            if not self.admin_element_specs.has_key(elem_name):
                self.admin_element_specs[elem_name] = admin_params
            if elem_name not in self.element_specs:
                raise ElementSpecificationError("Element \"%s\" specification not found." % elem_name)
            # now override the specs in the original dict.
            for feature_name, feature_value in admin_params.iteritems():
                print self.element_specs[elem_name]
                if feature_name not in self.element_specs[elem_name][elem_name]:
                    raise ElementSpecificationError(
                            "Mismatch in feature name \"%s\" between element specification file and application parameters." % feature_name)
                else:
                    self.element_specs[elem_name][elem_name][feature_name] = feature_value
            print self.element_specs[elem_name][elem_name]
        if len(self.element_specs_history) < _HISTORY_SIZE:
            self.element_specs_history.append(self.element_specs)
        else:
            self.element_specs_history.pop(0)
            self.element_specs_history.append(self.element_specs)
        #print self.element_specs_history


    def revert_elem_specs(self):
        """In case element installation is failed. Revert back the specs."""
        self.element_specs = self.element_specs_history.pop(0)

# This class is used to read the machine specifications.
# For now it reads information from json file about the machine specifications.
# But it can also be modified to get information from a central server that
# Maintains the information about different machines. 
#       One example of such a server is information collected using GENI Rspec.
#       Which collects information about the hardware through Advertisements.
class MachineSpec():
    def __init__(self):
        self.machine_id_to_spec = {}
        self.spec_path = os.getcwd() + "/"

    # Populate the class data
    def load_information(self):
        file_path = self.spec_path + "/" + "machine_specs.json"
        with open(file_path) as f:
            json_data_dict = json.load(f)
            print json_data_dict

    # get the list of machine macs that have the specifications same as provided element_specification
    def get_machines(self,element_spec):
        for key,value in element_spec:
            pass
        pass

# This is testing code
def main(argv):
    func_spec = ElementSpec()
    func_spec._load_specs()
    print func_spec.element_specs
    print func_spec.get_element_spec("Logger")
    func_spec.update_admin_elem_specs(["Logger"],[{"placement":"XXX"}])
    func_spec.revert_elem_specs()
    # Machine Specification 
    machine_spec = MachineSpec()
    #machine_spec.load_information()

if __name__ == "__main__":
    main(sys.argv[1:])
