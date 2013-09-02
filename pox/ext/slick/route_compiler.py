# TODO This could use a renaming: it just maintains which apps own which elements
import logging

import networkmaps
import slick_exceptions

import pox.openflow.libopenflow_01 as of
from utils.packet_utils import *

class ElementToApplication():
    def __init__(self):
        self.application_handles = {}

    def update(self, ed, application_object, app_desc):
        if not (self.application_handles.has_key(ed)):
            self.application_handles[ed] = (application_object, app_desc) 
        else:
            print "ERROR: This should not happen"

    def get_app_handle(self, ed):
        """Given an element descriptor return the application handle.
        """
        if (self.application_handles.has_key(ed)):
            return self.application_handles[ed][0] 
        else:
            logging.error("No application for the element with element descriptor:", ed)
            raise slick_exceptions.InstanceNotFound("No application handle for element descriptor %d", ed)

    def get_app_desc(self, ed):
        """Given an element descriptor return the application descriptor.

        Args:
            ed: Element descriptor
        Returns:
            Application descriptor
        """
        if (self.application_handles.has_key(ed)):
            return self.application_handles[ed][1]
        else:
            print "ERROR: There is no application for the function descriptor:",ed
            return None

    def contains_app(self, app_desc):
        """Return True if app_desc is registered as application.

        Args:
            app_desc =  Application descriptor to check its installation.
        Returns:
            True/False
        """
        for _, app in self.application_handles.iteritems():
            if(app[1] == app_desc):
                return True
        return False
