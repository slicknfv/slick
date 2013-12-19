#!/usr/bin/env python
# based on article:
# http://blog.sflow.com/2013/01/memcache-hot-keys-and-cluster-load.html

import requests
import json
import signal

rt='http://localhost:8008'

def sig_handler(signal,frame):
  requests.delete(rt + '/flow/hotkey/json')
  requests.delete(rt + '/flow/missedkey/json')
  requests.delete(rt + '/threshold/hotkey/json')
  requests.delete(rt + '/threshold/missedkey/json')
  exit(0)
signal.signal(signal.SIGINT, sig_handler)

hotkey = {'keys':'memcachekey', 'value':'bytes'}
missedkey = {'keys':'memcachekey', 'value':'requests', 'filter':'memcachestatus=NOT_FOUND'}
hotkeythreshold = {'metric':'hotkey', 'value':1500}
missedkeythreshold = {'metric':'missedkey', 'value':20}
r = requests.put(rt + '/flow/hotkey/json',data=json.dumps(hotkey))
r = requests.put(rt + '/flow/missedkey/json',data=json.dumps(missedkey))
r = requests.put(rt + '/threshold/hotkey/json',data=json.dumps(hotkeythreshold))
r = requests.put(rt + '/threshold/missedkey/json',data=json.dumps(missedkeythreshold))

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
    if "hotkey" == thresholdID or "missedkey" == thresholdID:
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
