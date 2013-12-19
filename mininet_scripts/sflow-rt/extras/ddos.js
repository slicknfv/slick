// author: Peter
// version: 1.0
// date: 9/30/2013
// description: DDoS controller script

// based on article:
// http://blog.sflow.com/2013/10/embedding-sdn-applications.html

include('extras/json2.js');

var flowkeys = 'ipsource';
var value = 'frames';
var filter = 'outputifindex!=discard&direction=ingress&sourcegroup=external';
var threshold = 1000; // 1000 packets per second
var groups = {'external':['0.0.0.0/0'],'internal':['10.0.0.2/32']};

var metricName = 'ddos';
var controls = {};
var enabled = true;

function sendy(address,type,state) {
  var result = runCmd(['../pyretic/pyretic/pyresonance/sendy_json.py',
                       '-i',address,'-e',type,'-V',state]);
}

function block(address) {
  if(!controls[address]) {
     sendy(address,'auth','clear');
     controls[address] = 'blocked';
  }
}
function allow(address) {
  if(controls[address]) {
     sendy(address,'auth','authenticated');
     delete controls[address];
  }
}

setGroups(groups);
setFlow(metricName, {keys:flowkeys, value:value, filter:filter, n:10, t:2});
setThreshold(metricName,{metric:metricName,value:threshold,byFlow:true});

setEventHandler(function(evt) {
  if(!enabled) return;

  var address = evt.flowKey;
  block(address);
},[metricName]);

setHttpHandler(function(request) {
  var result = {};
  try {
    var action = '' + request.query.action;
    switch(action) {
    case 'block':
       var address = request.query.address[0];
       if(address) block(address);
        break;
    case 'allow':
       var address = request.query.address[0];
       if(address) allow(address);
       break;
    case 'enable':
      enabled = true;
      break;
    case 'disable':
      enabled = false;
      break;
    }
  }
  catch(e) { result.error = e.message }
  result.controls = controls;
  result.enabled = enabled;
  return JSON.stringify(result);
});
