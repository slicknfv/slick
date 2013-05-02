# This calss should be used to read the element specifications by the 
# slick controller to call apply_func on the required code segment.

from collections import defaultdict
import os,sys
import json

class FunctionSpec():
    def __init__(self):
        self.element_specs = {} # function_name to element specification dictionary
        #self.elements_path = os.getcwd() + "/"+"ext/slick/elements/"
        self.elements_path = os.getcwd() + "/"+"elements/"
        self._load_specs()

    def _load_specs(self,path = None):
        files = os.listdir(self.elements_path)
        for item in files:
            file_path = self.elements_path + "/" + item + "/"+item+".spec"
            with open(file_path) as f:
                json_data_dict = json.load(f)
                print json_data_dict
                self.element_specs[item] = json_data_dict

    # Returns a dictionary
    def get_element_specs(self,element_name):
        if(self.element_specs.has_key(element_name)):
            return self.element_specs[element_name]


def main(argv):
    func_spec = FunctionSpec()
    func_spec._load_specs()
    print func_spec.element_specs
    print func_spec.get_element_specs("logger")

if __name__ == "__main__":
    main(sys.argv[1:])
