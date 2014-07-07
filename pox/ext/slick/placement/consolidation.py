# This module implements the consolidation related functions.

import copy
import itertools
from collections import OrderedDict

import networkx as nx

from partitionsets import ordered_set
from partitionsets import partition


class Consolidate():
    def __init__(self, network_model):
        self.network_model = network_model

    def get_leg_factors(self, element_names):
        """Return an array of elem_name to leg_factor."""
        leg_factors = [ ]
        for elem_name in element_names:
            leg_factor = self.network_model.get_elem_leg_factor(elem_name)
            leg_factors.append((elem_name, leg_factor))
        return leg_factors

    def _is_valid_partition(self, element_names, partition):
        """ Return True/False if the partition is valid or not.
        Args:
            element_names: List of element names.
            List of lists: where each element in the list is and element name.
        Returns:
            True/False
        """
        partition_list = [ ]
        for item_list in partition:
            for item in item_list:
                if item in element_names:
                    partition_list.append(item)
        if partition_list == element_names:
            return True
        else:
            return False

    def generate_consolidation_combinations(self, element_names):
        """Return list of lists. Where each list is a valid assignment."""
        # Generate set partitions
        # remove invalid set partitions, which are not in order.
        # 
        # List of list of valid partitions
        valid_partitions = [ ]
        an_ordered_set = ordered_set.OrderedSet(element_names)
        #http://en.wikipedia.org/wiki/Partition_of_a_set
        a_partition = partition.Partition(an_ordered_set)
        for a_part in a_partition:
            if self._is_valid_partition(element_names, a_part):
                valid_partitions.append(a_part)
                #print a_part
        return valid_partitions

    def _get_single_element_assignment(self, element_name, leg_factor):
        min_cost_partition = [[element_name]]
        min_cost_combination = None
        leg_type = self.network_model.get_elem_leg_type(element_name)
        if leg_type == 'E':
            min_cost_combination = ['ANY'] 
        if leg_type == 'L':
            min_cost_combination = ['DESTS'] 
        if leg_type == 'G':
            min_cost_combination = ['SRCS'] 
        return min_cost_partition, min_cost_combination

    def _translate_virtual_locs_to_place(self, element_names, virtual_locs_to_place):
        """Given the virtual location assignment. Translate it into:
        LEG for the consolidated element and return the resulting translated list
        of the same size as virtual_locs_to_place."""
        leg_translation = [ ]
        for pos_to_place_element in virtual_locs_to_place:
            if pos_to_place_element == 0:
                leg_translation.append('SRCS') # Its a consolidated element with type G
            if pos_to_place_element == len(element_names)-1:
                leg_translation.append('DESTS') # Its a consoldiated element with type L
            if (pos_to_place_element != len(element_names)-1) and (pos_to_place_element != 0):
                leg_translation.append('ANY') # Its a non-consolidated element with E.
        return leg_translation

    def get_least_cost_assignment(self, valid_partitions, element_names, leg_factors):
        """valid partitions: Its a list of list of valid partitions.
        leg_factors: Its a list of LEG factos for the element instances.
        Returns: One least cost assignment based on leg_factor.
        """
        min_combination_cost = 1000000000
        min_cost_combination = None
        min_cost_partition = None
        links = OrderedDict() # list of tuples src->elem1 -> elem2 -> elem3 ->dst
        total_links = len(element_names) + 2
        if len(element_names) == 1:
            min_cost_partition, min_cost_combination =  self._get_single_element_assignment(element_names[0], leg_factors[0])
            return min_cost_partition, min_cost_combination
        for index, elem_name in enumerate(element_names):
            if index == 0:
                # This is the first link from source hosts to switch so 
                # the cost is always 1 over here. This is the original traffic 
                # coming in.
                links[("src", elem_name)] = 1
            else:
                links[(element_names[index-1], elem_name)] = 0
        links[(element_names[-1], "dst")] = 0
        num_possible_places = len(element_names)
        locs = [ ]
        for i in range(num_possible_places):
            locs.append(i)
        count = 0
        for partition in valid_partitions:
            r = len(partition)
            combos = itertools.combinations(locs, r)
            print "Calculating best possible assignment of elemnts for partition: ", partition
            for c in combos:
                combination_cost = self._calculate_combinations_link_cost(locs, links, c, leg_factors, partition)
                print "Cost for combination: ",c," =",combination_cost
                # We want to check if even the same cost combination requires less consolidation or not.
                # Hence equal to  in lte(less than or equal to) comparison.
                if combination_cost <= min_combination_cost:
                    min_combination_cost = combination_cost
                    min_cost_combination = c
                    # We prefer more distributed nodes than more consolidated nodes.
                    if min_cost_partition:
                        if len(partition) > len(min_cost_partition):
                            min_cost_partition = partition
                    else:
                        min_cost_partition = partition
            print "Min. Cost combination:", min_cost_combination, min_combination_cost
        print "Partition of Elements, min_cost_partition", min_cost_partition, min_cost_combination
        min_cost_combination = self._translate_virtual_locs_to_place(element_names, min_cost_combination)
        return min_cost_partition, min_cost_combination

    def _get_cost_change(self, starting_cost, leg_factors, consolidated_element):
        link_cost = starting_cost
        for elem in consolidated_element:
            for leg in leg_factors:
                if leg[0] == elem:
                    elem_leg_factor = leg[1]
                    link_cost = link_cost/elem_leg_factor
        return link_cost

    def _calculate_combinations_link_cost(self, locs, links_orig, locs_to_place_elements, leg_factors, partition):
        """
            locs: List of virtual locations where the elements can be placed between the source and destination. e.g, [0,1,2,3] 
                This is equal to the number of elements in the chain.
            links_orig: A dict of links where keys are link in tuples (i,j) and value is cost of the link for particular partition assignment.

        """
        links = copy.deepcopy(links_orig)
        prev_link_cost = 1
        link_number = 0
        location_num = 0
        for link, cost in links.iteritems():
            # only start calculating cost on the link that has an element instance before it.
            # if i has a consolidated element instance than calculate its impact on the link (i.j)
            if link_number == locs_to_place_elements[location_num]+1:
                #print "XXXXXX", link_number, locs_to_place_elements[location_num], prev_link_cost
                links[link] = self._get_cost_change(prev_link_cost, leg_factors, partition[location_num])
                if location_num+1 <  len(locs_to_place_elements):
                    location_num +=1
            else:
                links[link] = prev_link_cost
            prev_link_cost = links[link]
            link_number += 1
        pass
        #print links
        total_cost = 0
        for link, cost in links.iteritems():
            total_cost += cost
        #print total_cost
        return total_cost

# TESTING CODE
if __name__ == '__main__':
    elem_names = ['a','b','c','d']
    consolidate = Consolidate(None)
    print consolidate._is_valid_partition(['a','b','c','d'], [['a','b','c','d']])
    print consolidate._is_valid_partition(['a','b','c','d'], [['a','b','c'],['d']])
    print consolidate._is_valid_partition(['a','b','c','d'], [['a','b','d'],['c']])
    consolidation_combinations = consolidate.generate_consolidation_combinations(elem_names)
    #leg_factors = [ ('a',0.5),('b',1), ('c',1), ('d',1)]
    #                   L         E        E       E
    #leg_factors = [ ('a',0.5),('b',1), ('c',1), ('d',2)]
    #                   L        E         E        G
    leg_factors = [ ('a',1.5),('b',1), ('c',1), ('d',0.5)]
    # For this assignment the best combination for virtual locs to place elements is: (0,1,2,3)
    # even though (0,3) with consolidation has the same cost but has less freedom to place the
    # elements on the virtual locations.
    #                   G        E         E        L

    #leg_factors = [ ('a',1.5),('b',0.75), ('c',1.25), ('d',0.5)]
    #                   G        L           G            L
    #leg_factors = [ ('a',1.5),('b',0.75), ('c',1.25), ('d',0.5)]
    #                   G        L           G            L
    least_cost_assignment = consolidate.get_least_cost_assignment(consolidation_combinations, elem_names, leg_factors)

