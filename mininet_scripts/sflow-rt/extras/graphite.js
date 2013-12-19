// author: Peter
// version: 1.0
// date: 11/23/2013
// description: Log metrics to Graphite

// based on article:
// http://blog.sflow.com/2013/11/metric-export-to-graphite.html

include('extras/json2.js');

var graphiteServer = "10.0.0.151";
var graphitePort = null;

var errors = 0;
var sent = 0;
var lastError;

setIntervalHandler(function() {
  var keys = ['sum:load_one'];
  var prefix = 'linux.';
  var vals = metric('ALL',keys,{os_name:['linux']});
  var metrics = {};
  for(var i = 0; i < keys.length; i++) {
    metrics[prefix + keys[i]] = vals[i].metricValue;
  }
  try { 
    logInfo(JSON.stringify(metrics));
    graphite(graphiteServer,graphitePort,metrics);
    sent++;
  } catch(e) {
    errors++;
    lastError = e.message;
  }
} , 15);

setHttpHandler(function() {
  var message = { 'errors':errors,'sent':sent };
  if(lastError) message.lastError = lastError;
  return JSON.stringify(message);
});
