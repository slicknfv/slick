# This calss should be used to read the element specifications by the 
# slick controller to call apply_func on the required code segment.

from collections import defaultdict
import os,sys
import json

class ElementSpec():
    def __init__(self):
        self.element_specs = {} # function_name to element specification dictionary
        self.elements_path = os.getcwd() + "/"+"ext/slick/elements/"
        #self.elements_path = os.getcwd() + "/"+"elements/"
        self._load_specs()

    def _load_specs(self,path = None):
        files = os.listdir(self.elements_path)
        for item in files:
            if not item.startswith('.'):
                file_path = self.elements_path + "/" + item + "/"+item+".spec"
                with open(file_path) as f:
                    print file_path
                    json_data_dict = json.load(f)
                    print json_data_dict
                    self.element_specs[item] = json_data_dict

    # Returns a dictionary
    def get_element_spec(self,element_name):
        if(self.element_specs.has_key(element_name)):
            return self.element_specs[element_name]


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
    func_spec = FunctionSpec()
    func_spec._load_specs()
    print func_spec.element_specs
    print func_spec.get_element_specs("logger")
    # Machine Specification 
    machine_spec = MachineSpec()
    machine_spec.load_information()

if __name__ == "__main__":
    main(sys.argv[1:])
