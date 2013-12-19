$(document).ready(function() {
  var timeout = 60;
  var maxFlows = 20;
  var url = "../flows/json?maxFlows=" + maxFlows + "&timeout=" + timeout;
  var lastID = null;

  var flows;

  function mergeData(data) {
    if(!flows) flows = data;
    else {
      flows = data.concat(flows);
      if(flows.length > maxFlows) flows.length = maxFlows;
    }
  }

  function updateFlows(data) {
    if(!data || data.length == 0) return;

    lastID = data[0].flowID;
    mergeData(data);
 
    var content = '';
    for(var i = 0; i < flows.length; i++) {
      var id = flows[i].flowID;
      
      content += '<tr class="' + (id % 2 == 0 ? "even" : "odd") + '">';
      content += '<td class="alignl">' + id + '</td>';
      content += '<td class="alignl">' + (new Date(flows[i].start)).toLocaleTimeString() + '</td>';
      content += '<td class="alignl">' + (new Date(flows[i].end)).toLocaleTimeString() + '</td>';
      content += '<td class="alignl">' + flows[i].name + '</td>';
      content += '<td class="alignl">' + flows[i].flowKeys + '</td>';
      content += '<td class="alignr">' + flows[i].value.toFixed(0) + '</td>';
      content += '<td class="alignl">' + flows[i].agent + '</td>';
      content += '<td class="alignl">' + flows[i].dataSource + '</td>';
      content += '</tr>';
    }
    $('#flows tbody').html(content); 
    $("#flows tbody tr")
       .hover(
         function() { $(this).addClass("dynhoveron"); },
         function() { $(this).removeClass("dynhoveron"); }
       )
       .click(
         function() { 
           var cells = $(this).find("td");
           var metric = cells[3];
           var agent = cells[6];
           var dataSource = cells[7];
           document.location = "../metric/" + agent.innerHTML + "/" + dataSource.innerHTML + "." + metric.innerHTML + "/html"; }
       )
  }

  (function poll() {
      $.ajax({
            url: url + (lastID != null ? "&flowID=" + lastID : ""),
            success: function(data) {
               updateFlows(data);
            },
            dataType: "json",
            complete: poll,
            timeout: timeout * 2 * 1000
       });
  })();
})
