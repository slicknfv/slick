"""
    LoggerTriggerChain: One Application, Two Element Instances, Two Element Machines, One Flow
    Note: To allocate two element instances on two different machines we need to have two
    apply_elem calls such that RRPlacement has two calls and need to start two shim layers
    'simultaneously'.
"""
from slick.Application import Application

class LoggerTriggerChain(Application):
    def __init__( self, controller, ad ):
        Application.__init__( self, controller, ad )
        self.ed1 = None
        self.ed2 = None
        self.f = None

    def init(self):
        # Start the first Logger:

        parameters = [{"file_name":"/tmp/dns_log1"}]
        flow = self.make_wildcard_flow()
        flow['tp_dst'] = 53
        # Parameters is an array of dicts that should be passed 
        # to apply_elem corresponding to the element_name
        # that we want to apply the parameters to.
        self.ed1 = self.apply_elem( flow, ["Logger"], parameters ) 

        # We are starting it second time to 
        # allow placement on a different machine.
        self.ed2 = self.apply_elem( flow, ["TriggerAll"] ) 

        if(self.check_elems_installed(self.ed1) and self.check_elems_installed(self.ed2)):
            self.f = open("/tmp/trigger.txt","w", 0)
            self.installed = True
            print "LoggerTriggerChain: created two elements with fds", self.ed1, "and", self.ed2
        else:
            print "Failed to install the LoggerTriggerChain application"

    # This handle Trigger will be called once for one element.
    def handle_trigger( self, ed, msg ):
        """handle the triggers here.
        Args:
            ed: element desriptor  that raised the trigger.
            msg: dictionary that was returned.
        Returns:
            None
        """
        if self.installed:
            print "LoggerTriggerChain handle_trigger (",ed,") msg:",msg
            if(int(ed) == int(self.ed2[0])):
                self.f.write(str(msg) + '\n')
                print "Following trigger is received:", str(msg)
            else:
                print "LoggerTriggerChain got a trigger from an unknown instance:", ed
