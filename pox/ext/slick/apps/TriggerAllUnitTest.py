"""
# ############################################################################################################################################
# One Apllication with Two TriggerAll Elements
# Creates two element instances with one application. Based on the flow to element descriptor mapping, shim should handle packet to the
# right element instance. And correct element instance should raise an event.
# ############################################################################################################################################
"""
from slick.Application import Application

class TriggerAllUnitTest(Application):
    def __init__( self, controller, application_descriptor ):
        Application.__init__( self, controller, application_descriptor )
        self.ed1 = None
        self.ed2 = None

    def init(self):
        flows = self.make_wildcard_flow()

        # Trigger on all port 53 traffic
        flows['tp_dst'] = 53
        self.ed1 = self.apply_elem( flows, ["TriggerAll"] )

        # Also trigger on all port 80 traffic
        flows['tp_dst'] = 80
        self.ed2 = self.apply_elem( flows, ["TriggerAll"] )

        # Make sure it all got set up correctly
        if(self.check_elems_installed(self.ed1) and self.check_elems_installed(self.ed2)):
            self.f1 = open("/tmp/1_trigger.txt","w", 0)
            self.f2 = open("/tmp/2_trigger.txt","w", 0)
            self.installed = True
            print "TriggerAllUnitTest Installed with element descriptors", self.ed1, self.ed2
        else:
            print "Failed to install the TriggerAllUnitTest application"
        

    # This handle Trigger will be called twice for 2 elements.
    def handle_trigger( self, ed, msg ):
        if self.installed:
            print "TriggerAllUnitTest handle_trigger (",ed,") msg:",msg
            if(ed == self.ed1):
                self.f1.write(str(msg) + '\n')
            elif(ed == self.ed2):
                self.f2.write(str(msg) + '\n')
            else:
                print "TriggerAllUnitTest got a trigger from an unknown instance:", ed
