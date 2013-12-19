$(document).ready(function() {
  var timeout = 60;
  var maxEvents = 20;
  var url = "../events/json?maxEvents=" + maxEvents + "&timeout=" + timeout;
  var lastID = null;

  var events;

  function mergeData(data) {
    if(!events) events = data;
    else {
      events = data.concat(events);
      if(events.length > maxEvents) events.length = maxEvents;
    }
  }

  function updateEvents(data) {
    if(!data || data.length == 0) return;

    lastID = data[0].eventID;
    mergeData(data);
 
    var content = '';
    for(var i = 0; i < events.length; i++) {
      var id = events[i].eventID;
      
      content += '<tr class="' + (id % 2 == 0 ? "even" : "odd") + '">';
      content += '<td class="alignl">' + id + '</td>';
      content += '<td class="alignl">' + (new Date(events[i].timestamp)) + '</td>';
      content += '<td class="alignl">' + events[i].thresholdID + '</td>';
      content += '<td class="alignl">' + events[i].metric + '</td>';
      content += '<td class="alignr">' + events[i].threshold + '</td>';
      content += '<td class="alignr">' + events[i].value.toFixed(2) + '</td>';
      content += '<td class="alignl">' + events[i].agent + '</td>';
      content += '<td class="alignl">' + events[i].dataSource + '</td>';
      content += '</tr>';
    }
    $('#events tbody').html(content); 
    $("#events tbody tr")
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
            url: url + (lastID != null ? "&eventID=" + lastID : ""),
            success: function(data) {
               updateEvents(data);
            },
            dataType: "json",
            complete: poll,
            timeout: timeout * 2 * 1000
       });
  })();
})
