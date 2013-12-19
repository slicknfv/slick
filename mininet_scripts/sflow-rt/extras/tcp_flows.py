#!/usr/bin/env python
# based on article:
# http://blog.sflow.com/2013/08/restflow.html

import requests
import json
import signal

rt = 'http://localhost:8008'
name = 'tcp'

def sig_handler(signal,frame):
  requests.delete(rt + '/flow/' + name + '/json');
  exit(0)
signal.signal(signal.SIGINT, sig_handler)

flow = {'keys':'ipsource,ipdestination,tcpsourceport,tcpdestinationport',
        'value':'frames',
        'log':True}
r = requests.put(rt + '/flow/' + name + '/json',data=json.dumps(flow))

flowurl = rt + '/flows/json?name=' + name + '&maxFlows=100&timeout=60'
flowID = -1
while 1 == 1:
  r = requests.get(flowurl + "&flowID=" + str(flowID))
  if r.status_code != 200: break
  flows = r.json()
  if len(flows) == 0: continue

  flowID = flows[0]["flowID"]
  flows.reverse()
  for f in flows:
    print str(f['flowKeys']) + ',' + str(int(f['value'])) + ',' + str(f['end'] - f['start']) + ',' + f['agent'] + ',' + str(f['dataSource'])

