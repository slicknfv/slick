"""
    Application: Base class (do not instantiate; treat it like an abstract base class)
"""
class Application():
    def __init__( self, controller, application_descriptor ):
        self.controller = controller
        self.ad = application_descriptor
        self.installed = False  # Set this to True once init() has succeeded

    def configure_user_params(self):
        pass

    def handle_trigger(self,fd,msg):
        pass

    def apply_elem(self, flow, element_name, params):
        return self.controller.apply_elem( self.ad, flow, element_name, params, self )

    #def init(self):
        #raise NotImplementedError "The Application base class requires derived classes to implement init()"
