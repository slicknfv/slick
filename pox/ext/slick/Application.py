"""
    Application: Base class (do not instantiate; treat it like an abstract base class)
"""
class Application():
    def __init__( self, controller, application_descriptor ):
        self.controller = controller
        self.ad = application_descriptor
        self.installed = False  # Set this to True once init() has succeeded

    def configure_user_params( self ):
        pass

    def handle_trigger( self, fd, msg ):
        pass

    def apply_elem( self, flow, element_names, params=[{}], controller_params=[{}] ):
        return self.controller.apply_elem( self.ad, flow, element_names, params, controller_params, self )

    def configure_elem( self, element_descriptor, params ):
        return self.controller.configure_elem( self.ad, element_descriptor, params )

    def make_wildcard_flow( self ):
        flow = {
                 'dl_src':None,
                 'dl_dst':None,
                 'dl_vlan':None,
                 'dl_vlan_pcp':None,
                 'dl_type':None,
                 'nw_src':None,
                 'nw_dst':None,
                 'nw_proto':None,
                 'tp_src':None,
                 'tp_dst':None
               }
        return flow

    def check_elems_installed(self, eds):
        """ Return true if after checking element descriptors

        Args:
            eds: List of element descriptors.
        Returns:
            True/False
        """
        installed = True
        for ed in eds:
            if (ed < 0):
                installed = False
        return installed
