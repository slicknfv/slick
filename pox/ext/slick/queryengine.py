from pox.lib.util import dpid_to_str
"""

    query:
        elements
    machines:
        middlbox mac addresses.
    apps:
        applications running.
    flows:
"""
class QueryEngine(object):
    def __init__(self, controller, query):
        """Given the controller and query prase it and provide the
        informtion asked by the user."""
        self.controller = controller
        self.query = query

    def process_query(self):
        if self.query == "summary":
            print "*"*50
            self.process_summary_request()
            print "*"*50
        if self.query == "details":
            print "*"*50
            self.process_details_request()
            print "*"*50

    def process_summary_request(self):
        """Show active number of middleboxes, element instances, element types and apps."""
        num_apps = 0;
        num_mbs = 0;
        num_elem_descs = 0;
        num_elems = 0;

        num_mbs = len(self.controller.get_all_registered_machines())
        app_descs = self.controller.elem_to_app.get_app_descs()
        num_apps = len(app_descs)
        num_elem_descs = len(self.controller.network_model.get_elem_descs())
        num_elems = len(self.controller.network_model.get_elem_names())
        print "Num Apps: ", num_apps, " Num Middleboxes: ", num_mbs, " Num Element Descs: ", num_elem_descs, " Num Element Types: ", num_elems

    def process_details_request(self):
        middlebox_macs = self.controller.get_all_registered_machines()
        for mac in middlebox_macs:
            middlebox_line = ""
            middlebox_line += "Middlebox Machine: "
            middlebox_line += dpid_to_str(mac)
            elem_descs = self.controller.elem_to_mac.get_elem_descs(mac)
            elem_name = None
            elem_desc = None
            for ed in elem_descs:
                elem_desc = ed
                elem_name = self.controller.network_model.get_elem_name(ed)
                middlebox_line += " -> {element_name:"
                middlebox_line += elem_name
                middlebox_line += " ,element_descriptor:"
                middlebox_line += str(elem_desc)
                middlebox_line += "}"
            if len(elem_descs):
                print middlebox_line + "\n"
