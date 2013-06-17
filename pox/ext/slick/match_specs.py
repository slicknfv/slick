# This class provides code to read the machine and functions specification code and provide 
# function to match the specification.

import os,sys
import utils.util

class MatchSpec():
    def __init__(self,machine_specs_path=None,elements_path=None):
        self.machine_specs_path = machine_specs_path
        self.elements_path = elements_path
        
        self.machine_specs = {}# Key is the MAC address and the Value are the specs of that machine. 
        self.function_specs = {} 
    
    #
    def load_function_specs(self):
        if(os.path.isfile(self.machine_specs_path)):
            machine_specs  = util.load_json(self.machine_specs_path) 
        elif(os.path.isdir(self.machine_specs_path)):
            #explore dir stub code here
            pass

    def load_machine_specs(self):
        if(os.path.isdir(self.elements_path)):
        pass

