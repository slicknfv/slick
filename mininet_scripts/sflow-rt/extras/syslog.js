// author: Peter
// version: 1.0
// date: 11/24/2013
// description: Syslog export script

// based on article:
// http://blog.sflow.com/2013/11/exporting-events-using-syslog.html

var server = '10.0.0.153';
var port = 514;
var facility = 16; // local0
var severity = 5;  // notice

var flowkeys = ['ipsource','ipdestination','icmpunreachableport'];

setFlow('uport', {
  keys:flowkeys,
  value:'frames',
  log:true,
  flowStart:true
});

setFlowHandler(function(rec) {
  var keys = rec.flowKeys.split(',');
  var msg = {};
  for(var i = 0; i < flowkeys.length; i++) msg[flowkeys[i]] = keys[i];
  
  syslog(server,port,facility,severity,msg);
},['uport']);
