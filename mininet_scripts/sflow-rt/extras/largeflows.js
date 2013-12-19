// based on article:
// http://blog.sflow.com/2013/06/large-flow-detection-script.html

var fs = require('fs');
var http = require('http');

var rt = { hostname: 'localhost', port: 8008 };
var flowkeys = 'ipsource,ipdestination,udpsourceport,udpdestinationport';
var threshold = 125000; // 1 Mbit/s   = 10% of link bandwidth

var links = {};

// mininet mapping between sFlow ifIndex numbers and switch/port names
var ifindexToPort = {};
var path = '/sys/devices/virtual/net/';
var devs = fs.readdirSync(path);
for(var i = 0; i < devs.length; i++) {
 var dev = devs[i];
 var parts = dev.match(/(.*)-(.*)/);
 if(!parts) continue;

 var ifindex = fs.readFileSync(path + dev + '/ifindex');
 ifindex = parseInt(ifindex).toString();
 var port = {'switch':parts[1],'port':dev};
 ifindexToPort[ifindex] = port;
}

function extend(destination, source) {
 for (var property in source) {
  if (source.hasOwnProperty(property)) {
   destination[property] = source[property];
  }
 }
 return destination;
}

function jsonGet(target,path,callback) {
 var options = extend({method:'GET',path:path},target);
 var req = http.request(options,function(resp) {
  var chunks = [];
  resp.on('data', function(chunk) { chunks.push(chunk); });
  resp.on('end', function() { callback(JSON.parse(chunks.join(''))); });
  });
  req.end();
};

function jsonPut(target,path,value,callback) {
 var options = extend({method:'PUT',headers:{'content-type':'application/json'},path:path},target);
 var req = http.request(options,function(resp) {
  var chunks = [];
  resp.on('data', function(chunk) { chunks.push(chunk); });
  resp.on('end', function() { callback(chunks.join('')); });
 });
 req.write(JSON.stringify(value));
 req.end();
};

function getLinkRecord(agent,ifindex) {
 var linkkey = agent + ">" + ifindex;
 var rec = links[linkkey];
 if(!rec) {
  rec = {agent:agent, ifindex:ifindex, port:ifindexToPort[ifindex]};
  links[linkkey] = rec;
 }
 return rec;
}

function updateLinkLoads(metrics) {  
 for(var i = 0; i < metrics.length; i++) {
  var metric = metrics[i];
  var rec = getLinkRecord(metric.agent,metric.dsIndex);
  rec.total = metric.metricValue;
 }
}

function largeFlow(link,flowKey,now,dt) {
 console.log(now + " " + " " + dt + " " + link.port.port + " " + flowKey);
}

function getEvents(id) {
 jsonGet(rt,'/events/json?maxEvents=10&timeout=60&eventID='+ id,
  function(events) {
   var nextID = id;
   if(events.length > 0) {
    nextID = events[0].eventID;
    events.reverse();
    var now = (new Date()).getTime();
    for(var i = 0; i < events.length; i++) {
     var evt = events[i];
     var dt = now - evt.timestamp;
     if('detail' == evt.thresholdID
        && Math.abs(dt) < 5000) {
      var flowKey = evt.flowKey;
      var rec = getLinkRecord(evt.agent,evt.dataSource);
      largeFlow(rec,flowKey,now,dt);
     }
    }
   }
   getEvents(nextID);
  }
 );
}

function startMonitor() {
 getEvents(-1);
 setInterval(function() {
  jsonGet(rt,'/dump/ALL/total/json', updateLinkLoads)
 }, 1000);
}

function setTotalFlows() {
 jsonPut(rt,'/flow/total/json',
  {value:'bytes',filter:'outputifindex!=discard&direction=ingress', t:2},
  function() { setDetailedFlows(); }
 );
}

function setDetailedFlows() {
 jsonPut(rt,'/flow/detail/json',
  {
   keys:flowkeys,
   value:'bytes',filter:'outputifindex!=discard&direction=ingress',
   n:10,
   t:2
  },
  function() { setThreshold(); }
 );
}

function setThreshold() {
 jsonPut(rt,'/threshold/detail/json',
  {
   metric:'detail',
   value: threshold,
   byFlow: true
  },
  function() { startMonitor(); }
 );
}

function initialize() {
 setTotalFlows();
}

initialize();
