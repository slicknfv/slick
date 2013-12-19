// author: Peter
// version: 1.0
// date: 10/6/2013
// description: Arista eAPI runCmds
// var s = new RpcServer('http://192.168.56.201/command-api','usr','passwd');
// var result = s.runCmds(["show version"]);

include('extras/jsonrpc.js');

RpcServer.runCmds = function(cmds) {
  return this.call('runCmds',{version:1,format:'json',cmds:cmds});
}
