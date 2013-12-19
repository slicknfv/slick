// author: Peter
// version: 1.0
// date: 10/2/2013
// description: JSON-RPC 2.0 client

include('extras/json2.js');

function RpcServer(url,usr,passwd) {
  this.url = url;
  this.usr = usr;
  this.passwd = passwd;
  this.id = 0;
  this.call = function(method,params) {
    var msgid = this.id++;
    var req = { jsonrpc:'2.0', id:msgid, method:method };
    if(params) req.params = params;
    var resp = http(this.url,'post','application/json',JSON.stringify(req),this.usr,this.passwd);
    if(resp) {
      resp = JSON.parse(resp);
      if(resp.error) throw error;
      if(msgid != resp.id) throw "bad response id";
      return resp.result;
    }
    return resp;
  }
}

