# This class provides code to read the machine and functions specification code and provide 
# function to match the specification.

import os,sys

class MatchSpec():
    def __init__(self,machine_specs_path=None,elements_path=None):
        self.machine_specs_path = machine_specs_path
        self.elements_path = elements_path
    
    #
    def load_function_specs(self):
        if(os.path.isfile(self.machine_specs_path)):
            pass
        pass

    def load_machine_specs(self):
        if(self.machine_specs_path)
        pass

    """
    Description:
        Function to lookup the machine specification.
    @args:
        function_spec: Its the function specification

    @returns:
        list of mac addresses of machines whose spec match with function_spec.
    """
    def lookup_machines(self,function_spec):
        pass
