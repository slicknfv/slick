#!/usr/bin/env python
import requests
import signal

def sig_handler(signal,frame):
  exit(0)
signal.signal(signal.SIGINT, sig_handler)

eventurl = 'http://localhost:8008/events/json?maxEvents=10&timeout=60'
eventID = -1
while 1 == 1:
  r = requests.get(eventurl + "&eventID=" + str(eventID))
  if r.status_code != 200: break
  events = r.json()
  if len(events) == 0: continue

  eventID = events[0]["eventID"]
  events.reverse()
  for e in events:
    print str(e['eventID']) + ',' + str(e['timestamp']) + ',' + e['thresholdID'] + ',' + e['metric'] + ',' + str(e['threshold']) + ',' + str(e['value']) + ',' + e['agent'] + ',' + e['dataSource']
