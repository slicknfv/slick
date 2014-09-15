import numpy as np
import statsmodels.api as sm # recommended import according to the docs
import matplotlib.pyplot as plt


def plot_cdf(filename, data_list):
    """Given the data list plot a cdf"""
    nd_array = np.asarray(data_list)
    #sample = np.random.uniform(0, 1, 20)
    ecdf = sm.distributions.ECDF(nd_array)

    x = np.linspace(min(nd_array), max(nd_array))
    y = ecdf(x)
    #plt.step(x, y)
    plt.plot(x, y)
    plt.show()
    plt.savefig(filename)
    
#plot_cdf("test_cdf.eps", [1,2,3,4,56])

def plot_two_cdfs(filename, data_list1, data_list2):
    """Given the data list plot a cdf"""
    fig = plt.figure()

    nd_array1 = np.asarray(data_list1)
    nd_array2 = np.asarray(data_list2)
    ecdf1 = sm.distributions.ECDF(nd_array1)
    ecdf2 = sm.distributions.ECDF(nd_array2)

    x1 = np.linspace(min(nd_array1), max(nd_array1))
    y1 = ecdf1(x1)
    x2 = np.linspace(min(nd_array2), max(nd_array2))
    y2 = ecdf2(x2)
    p1 = plt.plot(x1, y1, 'b', label="No Partitioning")
    p2 =plt.plot(x2, y2, 'r', label = "Partitioning")
    plt.legend(loc="upper left",shadow=True, fancybox=True)
    plt.xlabel('Min. RTT(ms)')
    plt.ylabel('Clients')
    plt.title('DCell Topology')
    plt.show()
    plt.savefig(filename)




# -d 4, -f 2, tree, 16 hosts, 1Mbps and 1msec. delay
data_random_tree=[  28, 26, 36, 26, 17, 10, 22, 22, 36, 32, 39, 40, 33, 31, 31, 35]
data_partition_tree =[9, 16, 27, 21, 27, 31, 32, 26, 10, 16, 21, 20, 26, 25, 26, 29]
# -z =4, 16 hosts and 20 switches, 0_0_1 connected with gateway. 1 Mbps and 1msec delay
data_random_fattree =  [34, 27, 28, 30, 26, 24, 20, 12, 42, 28, 28, 27, 29, 31, 29, 27]
data_partition_fattree = [2, 8, 14, 13, 24, 17, 20, 17, 21, 21, 19, 21, 20, 21, 14, 23]
# hosts = 20, switches=25 , 1Mbps, and 1 msec delay
#        Average Min. Latency experiment: 21.09065
#        Total number of hosts: 20
data_random_dcell = [6, 16, 16, 19, 13, 23, 22, 20, 18, 21, 23, 32, 17, 23, 25, 25, 20, 24, 24, 27]
#        Average Min. Latency experiment: 20.46565
#        Total number of hosts: 20
data_partition_dcell = [16, 18, 18, 4, 18, 25, 24, 24, 19, 29, 14, 27, 23, 22, 26, 22, 12, 20, 19, 18]


data_random_tree = sorted(data_random_tree)
data_partition_tree = sorted(data_partition_tree)
data_random_fattree = sorted(data_random_fattree)
data_partition_fattree = sorted(data_partition_fattree)
data_random_dcell = sorted(data_random_dcell)
data_partition_dcell = sorted(data_partition_dcell)
print data_random_tree
print data_partition_tree

print data_random_fattree
print data_partition_fattree
print data_random_dcell
print data_partition_dcell
#plot_two_cdfs("test_cdf.eps", data_random_tree, data_partition_tree)
#plot_two_cdfs("test_cdf.eps", data_random_fattree, data_partition_fattree)
#plot_two_cdfs("test_cdf.eps", data_random_dcell, data_partition_dcell)
#plot_two_cdfs("test_cdf.eps", [1,2,3,4,6], [1,2,3,4,5])

