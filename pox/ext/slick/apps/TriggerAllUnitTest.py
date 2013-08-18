"""
# ############################################################################################################################################
# One Apllication with Two TriggerAll Functions
# Creates two function instances with one application. Based on the flow to function descriptor mapping, shim should handle packet to the
# right function instance. And correct function instance should raise an event.
# ############################################################################################################################################
"""
class TriggerAllUnitTest():
    def __init__(self,inst,AD):
        self.cntxt = inst
        self.app_d = AD
        self.fd =[]# Its the list of function descriptors used by the application.
        self.installed = False # To check if the app is installed
        self.conf = 0 # Set this to true to update the configure
        self.flows = []
        flow1 = {}
        #Function hard coded taken from policy 
        flow1["dl_src"] = None
        flow1["dl_dst"] = None
        flow1['dl_vlan'] = None
        flow1['dl_vlan_pcp'] = None
        flow1['dl_type'] = None
        flow1['nw_src'] = None
        flow1['nw_dst'] = None
        flow1['nw_proto'] = None 
        flow1['tp_src'] = None
        flow1['tp_dst'] = 53
        self.flows.append(flow1)

        flow2 = {}
        flow2["dl_src"] = None
        flow2["dl_dst"] = None
        flow2['dl_vlan'] = None
        flow2['dl_vlan_pcp'] = None
        flow2['dl_type'] = None
        flow2['nw_src'] = None
        flow2['nw_dst'] = None
        flow2['nw_proto'] = None 
        flow2['tp_src'] = None
        flow2['tp_dst'] = 80
        self.flows.append(flow2)

    def configure_user_params(self):
        pass
        #if (self.conf < 2): # Need to call configure_func twice since this application has two functions instantiated
            #params = {}
            #self.cntxt.configure_func(self.app_d,self.fd[self.conf],params) # Call connfigure_func with same app if and different function descriptors.
            #self.conf +=1

    # This handle Trigger will be called twice for 2 functions.
    def handle_trigger(self,fd,msg):
        if self.installed:
            if(fd == self.fd[0]):
                print "TriggerAll handle_trigger function descriptor",fd
                print "TriggerAll handle_trigger called",msg
                self.f1.write(str(msg))
                self.f1.write('\n')
            if(fd == self.fd[1]):
                print "TriggerAll handle_trigger function descriptor",fd
                print "TriggerAll handle_trigger called",msg
                self.f2.write(str(msg))
                self.f2.write('\n')

    def init(self):
        for flow_item in self.flows:
            parameters = {}
            fd = self.cntxt.apply_elem(self.app_d,flow_item,"TriggerAll",parameters,self) #sending the object 
            if((fd >0)):#=> we have sucess
                self.fd.append(fd)
                if not self.installed:
                    self.f1 = open("1_trigger.txt","w")
                    self.f2 = open("2_trigger.txt","w")
                self.installed = True
                print "TriggerAll Installed with FD", fd

