#!/usr/bin/python

'''
Fat tree topology for data center networking

@author Milad Sharif (msharif@stanford.edu)

'''

from mininet.topo import Topo


class FatTreeNode(object):
    
    def __init__(self, pod = 0, sw = 0, host = 0, name = None, dpid = None):
        ''' Create FatTreeNode '''
        if dpid:
            self.pod = ( dpid & 0xff0000 ) >> 16
            self.sw = ( dpid & 0xff00 ) >> 8
            self.host = ( dpid & 0xff )
            self.dpid = dpid
        else:
            if name:
                pod, sw, host = [int(s) for s in name.split('h')]
            
            self.pod = pod
            self.sw = sw
            self.host = host
            self.dpid = (pod << 16) + (sw << 8) + host 

    def name_str(self):
        ''' Return name '''
        return "%ih%ih%i" % (self.pod, self.sw, self.host)

    def ip_str(self):
        ''' Return IP address '''
        return "10.%i.%i.%i" % (self.pod, self.sw, self.host)

    def mac_str(self):
        ''' Return MAC address '''
        return "00:00:00:%02x:%02x:%02x" % (self.pod, self.sw, self.host)

class NonBlockingTopo(Topo):
    
    LAYER_CORE = 0
    LAYER_HOST = 3

    def __init__(self, k=4):
        ''' Create a non-bloking switch '''
        super(NonBlockingTopo, self).__init__()
       
        self.k = k
        self.node_gen = FatTreeNode

        pods = range(0, k)
        edge_sw = range(0, k/2)
        agg_sw = range(k/2, k)
        hosts = range(2, k/2+2)
        
        core = self.node_gen(k, 1, 1)
        core_opts = self.def_opts(core.name_str())
        self.addSwitch(core.name_str(), **core_opts)

        for p in pods:
            for e in edge_sw:
                for h in hosts:
                    host = self.node_gen(p,e,h)
                    host_opts = self.def_opts(host.name_str())
                    self.addHost(host.name_str(), **host_opts)
                    self.addLink(host.name_str(), core.name_str())
        

    def layer(self, name):
        ''' Return the layer of a node '''
        node = self.node_gen(name = name)

        if (node.pod == self.k):
            layer = self.LAYER_CORE
        else:
            layer = self.LAYER_HOST
        
        return layer
    
    def def_opts(self, name):
        ''' return default dict for FatTree node '''
        node = self.node_gen(name = name)
        
        d = {'layer': self.layer(name)} 
        
        if d['layer'] == self.LAYER_HOST:
            d.update({'ip': node.ip_str()})
            d.update({'mac': node.mac_str()})
        d.update({'dpid': "%016x" % node.dpid})
        
        return d

class FatTreeTopo(Topo):    
    
    LAYER_CORE = 0
    LAYER_AGG  = 1
    LAYER_EDGE = 2
    LAYER_HOST = 3

    def __init__(self, k = 4):
        ''' Create FatTree topology 
            
            k : Number of pods (can support upto k^3/4 hosts)
        '''
        super(FatTreeTopo, self).__init__()

        self.k = k
        self.node_gen = FatTreeNode
        self.numPods = k
        self.aggPerPod = k / 2

        pods = range(0, k)
        edge_sw = range(0, k/2)
        agg_sw = range(k/2, k)
        core_sw = range(1, k/2+1)
        hosts = range(2, k/2+2)

        for p in pods:
            for e in edge_sw:
                edge = self.node_gen(p, e, 1)
                edge_opts = self.def_opts(edge.name_str())
                self.addSwitch(edge.name_str(), **edge_opts)

                for h in hosts:
                    host = self.node_gen(p, e, h)
                    host_opts = self.def_opts(host.name_str())
                    self.addHost(host.name_str(), **host_opts)
                    self.addLink(edge.name_str(),host.name_str())

                for a in agg_sw:
                    agg = self.node_gen(p, a, 1)
                    agg_opts = self.def_opts(agg.name_str())
                    self.addSwitch(agg.name_str(), **agg_opts)
                    self.addLink(agg.name_str(),edge.name_str())
            
            for a in agg_sw:
                agg = FatTreeNode(p, a, 1)
                
                for c in core_sw:
                    core = self.node_gen(k, a-k/2+1, c)
                    core_opts = self.def_opts(core.name_str())
                    self.addSwitch(core.name_str(), **core_opts)
                    self.addLink(agg.name_str(),core.name_str())

    def layer(self, name):
        ''' Return layer of node '''
        node = self.node_gen(name = name)

        if (node.pod == self.k):
            layer = self.LAYER_CORE
        elif (node.host == 1):
            if (node.sw < self.k/2):
                layer = self.LAYER_EDGE
            else:
                layer = self.LAYER_AGG
        else:
            layer = self.LAYER_HOST
        
        return layer
   
    def isPortUp(self, port):
        if port > (self.k/2):
            return True
        else:
            return False

    def layer_nodes(self, layer):
        ''' Return nodes at the given layer '''
        return [n for n in self.g.nodes() if self.layer(n) == layer]
   
    def upper_nodes(self, name):
        ''' Return nodes at one layer higher(closer to core) '''
        layer = self.layer(name) - 1
        return [n for n in self.g[name] if self.layer(n) == layer]

    def lower_nodes(self, name):
        '''Return edges one layer lower (closer to hosts) '''
        layer = self.layer(name) + 1
        return [n for n in self.g[name] if self.layer(n) == layer]

    def def_opts(self, name):
        ''' return default dict for FatTree node '''
        node = self.node_gen(name = name)
        
        d = {'layer': self.layer(name)}

        if d['layer'] == self.LAYER_HOST:
            d.update({'ip': node.ip_str()})
            d.update({'mac': node.mac_str()})
        d.update({'dpid': "%016x" % node.dpid})

        return d
    

