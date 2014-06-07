# This file has code to get the traffic matrix for the given time period.


traffic_matrix_dir = "/home/mininet/abiline/2004/"

class TrafficMatrix():
    def __init__(self, t_dir, t_file=None):
        self.t_dir = t_dir
        self.t_file = t_file

    def get_traffic_matrix(self, flowspce_desc):
        """flowspace_dec: int representing a flowspace descriptor. ( we are not using it to get the traffic matrix for now
        but based on Hederea paper. Given our Network Plane is based on OpenFlow we can 
        collect this information from OF switches as they have flow counters.

        This function simply reads the traffic matrix
        Returns:
            A dictionary of traffic matrix where key: (i,j) and value: GBytes/sec
        """
        # traffic matrix maintained in the dictionary.
        dict_matrix = { }
        lines_to_skip = 13# This will change based on what kind of file format we have.
        line_count = 0
        if self.t_file:
            fo = open(self.t_file, 'r')
            if fo:
                lines = fo.readlines()
                for line in lines:
                    if line_count < lines_to_skip:
                        line_count +=1
                        continue
                    else:
                        if len(line) >= 10:
                            data_rates_GBytes_per_sec = line.split(',')
                            print data_rates_GBytes_per_sec
                            for index, data_rate in enumerate(data_rates_GBytes_per_sec):
                                print index, float(data_rate)
                                row = (line_count%lines_to_skip)
                                print lines_to_skip, line_count
                                col = index
                                dict_matrix[(row, col)] = float(data_rate)
                                print (row,col), float(data_rate)
                            pass
                        pass
                        line_count +=1
        print dict_matrix
        return dict_matrix

    def get_sources_and_destinations(self, traffic_matrix):
        """Given the traffic matrix return the list of sources 
        and destinations for the flowsapce."""
        sources = [ ]
        destinations =  [ ]
        for key, value in traffic_matrix.iteritems():
            if value != 0:
                sources.append(key[0])
                destinations.append(key[1])
        return sources, destinations

# TESTING CODE
if __name__ == '__main__':
    traffic_matrix_dir = "/home/mininet/Abilene/2004/Measured/"
    traffic_matrix_file = "/home/mininet/Abilene/2004/Measured/tm.2004-04-11.23-40-00.dat"
    tm_obj = TrafficMatrix(None, traffic_matrix_file)
    traffic_matrix = tm_obj.get_traffic_matrix(0)
    print traffic_matrix
    tm_obj.get_sources(traffic_matrix)

