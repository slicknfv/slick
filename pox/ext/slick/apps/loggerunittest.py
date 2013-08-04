"""
    LoggerUnitTest One Application One Function Instance.
    We use this application to create two instances of the same application and two function instances.
"""
class LoggerUnitTest():
    def __init__(self,inst,AD,file_name,count_thresh,flow):
        self.cntxt = inst
        self.app_d = AD
        self.installed = False # To check if the app is installed
        self.conf = False # Set this to true to update the configure
        #Configuration specified parameters
        self.flow = flow
        # Conf parameters
        self.file_name = file_name
        self.count_thresh = count_thresh
        self.fd =None # Its the list of function descriptors used by the application.


    def configure_user_params(self):
        if not self.conf:
            params = {"file_name":self.file_name,"count_thresh":self.count_thresh}
            self.cntxt.configure_func(self.app_d,self.fd,params)
            self.conf = True
    def handle_trigger(self,fd,msg):
        print "Logger handle_trigger function descriptor",fd
        print "Logger handle_trigger called",msg
    def init(self):
        # read this from policy file.
        file_name = self.file_name
        parameters = {"file_name":file_name}
        #Incrementing app_d since we'll create 2 applications 
        fd= self.cntxt.apply_elem(self.app_d,self.flow,"Logger",parameters,self) 
        print fd
        if((fd >0)):#=> we have sucess
            #self.func_descs.append(fd)
            self.fd = fd
            self.installed = True
            print "Logger Installed."
