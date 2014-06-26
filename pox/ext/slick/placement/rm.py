# This file has code to get the routing matrix for the given time period.


class RoutingMatrix():
    def __init__(self, network_model):
        self.network_model = network_model

    def get_routing_matrix(self):
        """
        Builds the routing matrix using routing module and returns
        the binary matrix.(We assume symmteric routing.)
        Returns the routing matrix for the network.
        Returns:
            A dictionary of routing matrix where key: (i,j) and value: 0/1 meaning if the
            link is part of the path or not.
        """
        from slick.l2_multi_slick import switches
        from slick.l2_multi_slick import _get_path
        from slick.l2_multi_slick import adjacency
        # traffic matrix maintained in the dictionary.
        switch_macs = self.network_model.overlay_net.get_all_forwarding_devices()
        dict_matrix = { }
        print adjacency
        for sw1_mac in switch_macs:
            for sw2_mac in switch_macs:
                # port from dpid1 to dpid2
                d1_port = adjacency[sw1_mac][sw2_mac]
                # port from dpid2 to dpid1
                d2_port = adjacency[sw2_mac][sw1_mac]
                print sw1_mac, sw2_mac, d1_port, d2_port, "1022222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222",switch_macs
                #if (d1_port == None) or (d2_port == None):# Check if the link is there or not.
                #    continue
                path = _get_path(sw1_mac, sw2_mac, d1_port, d2_port)
                #links = [ ]
                if path:
                    print path
                    path_dpids = [ ]
                    for index in range(0, len(path)-1):
                        switch1 = path[index][0].dpid
                        #port1 = path[index][2]
                        switch2 = path[index+1][0].dpid
                        #port2 = path[index+1][1]
                        #link = Link(switch1, port1, switch2, port2)
                        #links.append(link)
                        path_dpids.append(switch1, switch2)
                    print "Path DPIDs::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::", path_dpids
        return dict_matrix

    def get_sources_and_destinations(self, traffic_matrix):
        """Given the traffic matrix return the list of sources 
        and destinations for the flowsapce.
        Args:
            traffic_matrix: A dict of traffic matrix.
        Returns:
            Two lists.
        """
        sources = [ ]
        destinations =  [ ]
        for key, value in traffic_matrix.iteritems():
            if value != 0:
                if key[0] not in sources:
                    sources.append(key[0])
                if key[1] not in destinations:
                    destinations.append(key[1])
        return sources, destinations

