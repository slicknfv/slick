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

def plot_two_cdfs(filename, data_list1, data_list2, x_label="No Label", y_label="No Label",title="No Graph Title" ):
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
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)
    plt.show()
    plt.savefig(filename)


def plot_bar_graphs(dict1, dict2):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    assert len(dict1) == len(dict2)

    list1 =  [ ]
    list2 =  [ ]
    # Ordering the lists, since we want to compare smae links.
    for k,val in dict1:
        print k
        if k in dict2:
            list1.append(val)
            list2.append(dict2[k])
    assert len(list1) == len(list2)
    print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",list1, list2
    #assert len(dict1) == len(list1)
    #N = len(dict1)
    N = len(list1)
    ind = np.arange(N)  
    width = 0.35
    ## the bars
    rects1 = ax.bar(ind, list1, width, color='black')#,
                #yerr=menStd,
                #error_kw=dict(elinewidth=2,ecolor='red'))

    rects2 = ax.bar(ind+width, list2, width, color='red')#,
                    #yerr=womenStd,
                    #error_kw=dict(elinewidth=2,ecolor='black'))

    ax.set_xlim(-width,len(ind)+width)
    ax.set_ylim(0,450)
    ax.set_ylabel('Link Utilization(Kbps)')
    ax.set_title('Links')
    xTickMarks = ['Link'+str(i) for i in range(1,N)]
    ax.set_xticks(ind+width)
    xtickNames = ax.set_xticklabels(xTickMarks)
    plt.setp(xtickNames, rotation=45, fontsize=10)
    
    ## add a legend
    #ax.legend( (rects1[0], rects2[0]), ('Men', 'Women') )
    ax.legend( (rects1[0], rects2[0]), ('No Partition', 'Partition') )
    
    plt.show()


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

###############################################
# Plot CDF for bandwidth utilization
##############################################
tree_bandwidth_utilization_partition = [8.865691166261707 , 4.512516142513163 , 4.418344869706838 , 4.3735320915132005 , 8.475877874564452, 4.186960662186347, 17.055164934795894 , 34.415270132567926 , 25.783898782529917, 34.277859881692336, 25.82073153409096, 8.838394925807004,25.47832225663953 ,4.312872652607679, 29.472445951531554 ,25.287101609333682, 8.472877733013927, 17.03800745267796, 4.43741633606486,38.49784636915705, 34.25024088496469]
tree_bandwidth_utilization_no_part = [33.50629561478795, 15.747600076687112 , 7.981258909469961, 7.847101170714658, 7.969946614129485, 256.28582314790305, 249.41149165690186, 202.99749591230665 , 133.90683356944487, 69.67055996531506 , 8.10064417403327 , 16.136472439996496, 7.589828613538556 , 69.31706079353457 , 7.706644702161306, 15.526799126082732 , 7.606513961124824 , 34.22294171299514 , 233.81769732974672 , 15.541295145947498, 248.3814043155284 , 234.4661183312998, 32.28039181669031, 203.52102453728443 , 32.172053836688534, 15.603249164658193, 16.1952910252058]

tree_bw_util_no_part = [24.787110019080913, 185.52512601492566, 6.299102723872155, 191.5443277531684, 6.141810505791069, 6.061191398623585, 11.626773532339115, 151.90139399911513, 51.71285415847437, 6.126468431533797, 12.267358307956455, 6.062235119627321, 51.61741708243231, 6.138418927805924, 12.279824840569542, 5.676498860677083,  26.126118916570096, 23.81703695374852, 12.283711217791907, 11.605836419853796, 24.08339985321536, 175.5690603236167, 152.6207695609592, 175.0645792939117, 185.78168987221216, 12.335786929425291]


tree_bw_util_part = [123.00963054458441, 21.114422345762417, 10.147123230120137, 10.659140964985115, 9.695155430070727, 149.2825083769978, 140.37359233086917, 80.1180866160506, 85.21282547806216, 10.490108470338498, 20.508609191852447, 9.680033070213382, 85.36550073689024, 10.040737508654514, 19.713904958827975, 9.750468713780714, 40.93057596334051, 120.87991370805126, 20.099581351111492, 139.88269953350644, 120.61371788032085, 41.950060437353976, 80.38729584800485, 42.04631821334697, 21.035368111056798, 20.752238799270273]


#plot_two_cdfs("test_cdf.eps", tree_bw_util_no_part, tree_bw_util_part)
