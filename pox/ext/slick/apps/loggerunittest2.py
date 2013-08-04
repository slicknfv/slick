"""
# --
# This application creates two instances of the same function with different flows and dumps those flows in two diffrent files on the Function Box.
# --
"""
class LoggerUnitTest2():
    def __init__(self,inst,AD,file_names,flows): # These are user defined parameters.
        self.cntxt = inst
        self.app_d = AD
        self.installed = False # To check if the app is installed
        self.conf = 0 # Set this to 0 and increment for each call of configure_func
        self.flows = flows # Its a list.
        # Conf parameters
        self.file_names = file_names
        self.fd =[] # Its the list of function descriptors used by the application.
        self.num_functions = 2 # How many functions this one app instantiates.


    def configure_user_params(self):
        if (self.conf < self.num_functions): # Need to call configure_func twice since this application has two functions instantiated
            params = {"file_name":self.file_names[self.conf]}
            self.cntxt.configure_func(self.app_d,self.fd[self.conf],params)
            self.conf +=1


    def handle_trigger(self,fd,msg):
        print "Logger handle_trigger function descriptor",fd
        print "Logger handle_trigger called",msg

    def init(self):
        for index in range(0,self.num_functions): # If the flows are same then it will overwrite the flow to function descriptor
            # read this from policy file.
            parameters = {"file_name":self.file_names[index]}
            fd= self.cntxt.apply_elem(self.app_d,self.flows[index],"Logger",parameters,self) 
            if((fd >0)):#=> we have sucess
                self.fd.append(fd)
                self.installed = True
                print "Logger Installed."
