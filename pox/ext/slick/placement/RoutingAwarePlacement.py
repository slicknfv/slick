""" RoutingAware Placement."""

from collections import defaultdict
from consolidation import Consolidate
from tm import TrafficMatrix
from rm import RoutingMatrix

from slick.placement.Placement import Placement

from pox.core import core
import networkx as nx
import metis # required for graph partitioning
log = core.getLogger()


PREFER_CONSOLIDATION = True

class RoutingAwarePlacement(Placement):
    def __init__ (self, network_model):
        log.debug("RoutingAware Placement Algorithm")
        Placement.__init__ (self, network_model)
        self._used_macs = [ ]
        # This is the first installation of the elements by the policy.
        self.partitioned_graph = None
        self.consolidate = Consolidate(network_model)
        traffic_matrix_dir = "/home/mininet/Abilene/2004/Measured/"
        traffic_matrix_file = "/home/mininet/Abilene/2004/Measured/tm.2004-04-11.23-40-00.dat"
        self.tm = TrafficMatrix(None, traffic_matrix_file)
        self.rm = RoutingMatrix(network_model)

    def get_placement (self, flowspace_desc, elements_to_install):
        """
            Inputs:
                - elements_to_install: list of elements to be placed (can have repeats)
            Outputs:
                - a list of mac addresses, of the same size as elements_to_install, providing a one-to-one mapping of where to install each element
                - return None if no placement is possible
        """
        rv = [ ]
        # Create appropriate number of partitions of the graph.
        self.network_model.physical_net.create_partitions()
        consolidated_chain, virtual_locs_to_place = self._consolidate_using_leg(elements_to_install)
        #print "SIGN"*100, consolidated_chain, virtual_locs_to_place
        rv = self._place_consolidated_chain(flowspace_desc, elements_to_install, consolidated_chain, virtual_locs_to_place)
        return rv

    def _place_consolidated_chain(self, flowspace_desc, elements_to_install, consolidated_chain, virtual_locs_to_place):
        rv = [ ]
        machines = None
        traffic_matrix = self.tm.get_traffic_matrix(flowspace_desc)
        sources, destinations = self.tm.get_sources_and_destinations(traffic_matrix)
        print "SIGN"*100, consolidated_chain, virtual_locs_to_place
        routing_matrix = self.rm.get_routing_matrix()

    def _consolidate_using_leg(self, element_names):
        """Given the list of element_names list. 
           Find the best possible partitioning of the elements
           that corresponds to minimum link cost for deployment.
           Args:
               element_names: List of element name chain.
           Returns:
               List of lists with best partitioning for the elements.
               Tuple for virtual assignment location.
        """
        # Get the ordered list of leg_factors corresponding to each element in the element_names.
        leg_factors = self.consolidate.get_leg_factors(element_names)
        consolidation_combinations = self.consolidate.generate_consolidation_combinations(element_names)
        least_cost_partition, least_cost_locs = self.consolidate.get_least_cost_assignment(consolidation_combinations, element_names, leg_factors)
        print "The least cost assignment for the element_names: ", element_names, " is: ", least_cost_partition, least_cost_locs
        return least_cost_partition, least_cost_locs
