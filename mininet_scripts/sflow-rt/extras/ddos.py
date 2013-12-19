#!/usr/bin/env python
# based on article:
# http://blog.sflow.com/2013/01/performance-aware-software-defined.html

import requests
import json
import signal

rt = 'http://localhost:8008'

def sig_handler(signal,frame):
  requests.delete(rt + '/flow/ddos/json')
  requests.delete(rt + '/threshold/ddos/json')
  exit(0)
signal.signal(signal.SIGINT, sig_handler)

groups = {'external':['0.0.0.0/0'],'internal':['10.0.0.0/8']}
flows = {'keys':'ipsource,ipdestination','value':'frames','filter':'sourcegroup=external&destinationgroup=internal'}
threshold = {'metric':'ddos','value':400}

r = requests.put(rt + '/group/json',data=json.dumps(groups))
r = requests.put(rt + '/flow/ddos/json',data=json.dumps(flows))
r = requests.put(rt + '/threshold/ddos/json',data=json.dumps(threshold))

eventurl = rt + '/events/json?maxEvents=10&timeout=60'
eventID = -1
while 1 == 1:
  r = requests.get(eventurl + "&eventID=" + str(eventID))
  if r.status_code != 200: break
  events = r.json()
  if len(events) == 0: continue
  eventID = events[0]["eventID"]
  events.reverse()
  for e in events:
    thresholdID = e['thresholdID']
    if "ddos" == thresholdID:
      r = requests.get(rt + '/metric/' + e['agent'] + '/' + e['dataSource'] + '.' + e['metric'] + '/json')
      metrics = r.json()
      if len(metrics) > 0:
        evtMetric = metrics[0]
        evtKeys = evtMetric.get('topKeys',None)
        if(evtKeys and len(evtKeys) > 0):
          topKey = evtKeys[0]
          key = topKey.get('key', None)
          value = topKey.get('value',None)
          print e['metric'] + "," + e['agent'] + ',' + key + ',' + str(value)
