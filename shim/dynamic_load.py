# Use this code to dynamically loading the modules in the code.
# Uses python 

from imp import *

class MiddleboxModules():
    def __init__(self):
        self.module_names = [] # List of currently loaded modules
        self.modules = {} #Modules name to module object mapping

    # This module is provided by the shim layer that tells which module code to load.
    # If the module is already loaded then reaload the module using "reload" function.
    # @args:
    #   module_name
    # @returns
    # Module Object
    def load_module(self,module_name):
        self.module_names.append(module_name)
        try:
            if(module_name in self.module_names):
                module = reload(module_name)
                self.modules[module_name] = module
                return module
            else:
                module = __import__(module_name)
                self.modules[module_name] = module
                return module
        except:
            self.module_names.remove(module_name)
            del self.modules[module_name]
            print "WARNING: Unable to load the module",module_name
            return None
    # --
    # @args: list of module names
    # @returns: list of modules
    # --
    def load_modules(self,module_names):
        modules_to_load = []
        for mod in module_names:
            if(mod not in self.module_names):
                modules_to_load.append(mod)
        modules = map(__import__, modules_to_load)
        for index,module_name in enumerate(modules_to_load):
            self.modules[module_name] = modules[index]
        return modules

    def is_loaded(self,module_name):
        if(slef.modules.has_key(module_name)):
            return True
        else:
            return False

