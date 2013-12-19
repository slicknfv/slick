#!/usr/bin/env python
# based on article:
# http://blog.sflow.com/2013/08/restful-control-of-switches.html

import requests
import json
import signal
from jsonrpclib import Server

switch_ips = ["192.168.56.201","192.168.56.202"]
username = "user"
password = "password"

sflow_ip = "192.168.56.1"
sflow_port = "6343"
sflow_polling = "20"
sflow_sampling = "10000"

metric = "largeflow"
metric_threshold = 125000000

flows = { "keys":"ipsource,ipdestination",
          "value":"bytes",
          "n":10,
          "t":2 }
threshold = {"metric":metric,"value":metric_threshold,"byFlow":True}

for switch_ip in switch_ips:
  switch = Server("http://%s:%s@%s/command-api" %
                (username, password, switch_ip))
  response = switch.runCmds(1,
   ["enable",
    "configure",
    "sflow source %s" % switch_ip,
    "sflow destination %s %s" % (sflow_ip, sflow_port),
    "sflow polling-interval %s" % sflow_polling,
    "sflow sample output interface",
    "sflow sample dangerous %s" % sflow_sampling,
    "sflow run"])

r = requests.put("http://%s:8008/flow/%s/json" % (sflow_ip, metric),
                 data=json.dumps(flows))
r = requests.put("http://%s:8008/threshold/%s/json" % (sflow_ip, metric),
                 data=json.dumps(threshold))

def sig_handler(signal,frame):
  requests.delete("http://%s:8008/flow/%s/json" % (sflow_ip, metric))
  requests.delete("http://%s:8008/threshold/%s/json" % (sflow_ip, metric))
  exit(0)
signal.signal(signal.SIGINT, sig_handler)

eventID = -1
while 1 == 1:
  r = requests.get("http://%s:8008/events/json?maxEvents=10&timeout=60&eventID=%s"
                   % (sflow_ip,eventID))
  if r.status_code != 200: break
  events = r.json()
  if len(events) == 0: continue

  eventID = events[0]["eventID"]
  for e in events:
    if metric == e["metric"]:
      print e["flowKey"]
