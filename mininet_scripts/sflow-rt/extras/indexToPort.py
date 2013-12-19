#!/usr/bin/env python
import os
import re
import json

ifindexToPort = {}
path = '/sys/devices/virtual/net/'
for child in os.listdir(path):
  parts = re.match('(.*)-(.*)', child)
  if parts == None: continue
  ifindex = open(path+child+'/ifindex').read().split('\n',1)[0]
  ifindexToPort[ifindex] = {'switch':parts.group(1),'port':child}
print json.dumps(ifindexToPort) 
print len(ifindexToPort)
