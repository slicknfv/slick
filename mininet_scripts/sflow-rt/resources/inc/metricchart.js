$(document).ready(function() {
  var path = window.location.pathname;
  var n = path.lastIndexOf('/');
  var url = path.substring(0,n) + "/json" + window.location.search;

  $.jqplot.sprintf.thousandsSeparator = ',';

  var lines;
  var labels;
  var start;
  var end;
  var maxPoints = 5 * 60;
  var step = 1000;

  var suffixes = ["μ","m",,"K","M","G","T","P","E"];
  function formatValue(format,value,includeMillis) {
      if(value == 0) return $.jqplot.sprintf(format,value);

      var i = 2;
      var divisor = 1;

      if(includeMillis) {
         i = 0;
         divisor = 0.000001;
      }

      var absval = Math.abs(value);
      while(i < suffixes.length) {
         if((absval /divisor) < 1000) break;
         divisor *= 1000;
         i++;
      }
      var scaled = Math.round(absval * 1000 / divisor) / 1000;
      return $.jqplot.sprintf(format,scaled) + (suffixes[i] ? suffixes[i] : "");
   }

   function getValueFormatter(suppressMillis) {
     return function(format,value) {
       return formatValue(format,value,suppressMillis);
     }
   }
  
  function updateChart(data) {
      if(!data || data.length == 0) return;

      var now = new Date(); 

      var endMs = now.getTime();   
      endMs -= endMs % step;
      end = new Date(endMs);

      var startMs = now.getTime() - (maxPoints * step);
      startMs -= startMs % step;
      start = new Date(startMs);
     
      if(!lines) {
	  lines = [];
	  for(var l = 0; l < data.length; l++) {
	     var points = [];
	     lines.push(points);
	  }
      }

      labels = [];
      for(var l = 0; l < data.length; l++) {
	  labels.push(data[l].metricName);
	  var points = lines[l];
	  points.push([end, data[l].metricValue]);
	  while(points[0][0].getTime() < startMs) points.shift();
      }

      var options = {
          axesDefaults: {
	      labelRenderer: $.jqplot.CanvasAxisLabelRenderer
	  },
          seriesDefaults: {
	      showMarker: false,
              fill: false,
	      rendererOptions: {
		  highlightMouseOver: false,
		  highlightMouseDown: false,
		  highlightColor: null
	      }
          },
          axes:{
	      xaxis:{
		  min: start,
		  max: end,
		  renderer: $.jqplot.DateAxisRenderer,
		  tickOptions: {
		      formatString: '%H:%M:%S'
		  }
	      }, 
	      yaxis:{
		  min: 0,
                  tickOptions: {
                      formatString: "%g",
                      formatter: getValueFormatter(false)
                  },
		  labelOptions: {
		      fontSize: '10pt',
		      fontFamily: 'Arial, Helvetica, sans-serif'
		  }
	      }
	  },
	  legend: {
	      renderer: $.jqplot.EnhancedLegendRenderer,
	      rendererOptions: {
		  numberRows: 1,
		  seriesToggle: false
	      },
              show: true,
	      placement: 'outsideGrid',
	      location: 's',
	      labels: labels
	 }
      };
     
      var plot = $("#stripchart").data('jqplot');
      if(plot) plot.destroy();
      $("#stripchart").empty().jqplot(lines,options);

      // update info 
      $("#info").empty();
      var info = [];
      for(var i = 0; i < data.length; i++) {
        if(data[i].topKeys) {
           var row = [];
           row.push(data[i].metricName);
           row.push(data[i].topKeys[0].key);
           row.push(data[i].agent);
           row.push(data[i].metricValue); 
           info.push(row);
        }
      }
      if(info.length > 0) {
         var table = '<div id="content" style="min-height:0px">'; 
         table += "<table><thead>";
         table += "<tr><th>Metric</th><th>Top Key</th><th>Agent</th><th>Value</th></tr>";
         table += "</thead><tbody>";
         for(var r = 0; r < info.length; r++) {
           table += '<tr class="' + (r % 2 ? 'odd' : 'even') + '"><td>' + info[r][0] + "</td><td>" + info[r][1] + "</td><td>" + info[r][2] + '</td><td class="alignr">' + formatValue("%.2f", info[r][3], false) + "</td></tr>";
         }
         table += "</tbody></table>";
         table += "</div>";
         $("#info").append(table);
      }
  }

  $(window).resize(function() {
     var plot = $('#stripchart').data('jqplot');
     if(plot) plot.replot();
  });

  (function poll() {
      $.ajax({
	      url: url,
	      success: function(data) {
		  updateChart(data);
		  setTimeout(poll, step);
	      },
	      error: function(result,status,errorThrown) {
                  $('#info').empty();
		  $('#stripchart').empty().append('<span class="warn">' + status + (errorThrown ? '&nbsp;&nbsp;' + errorThrown : '') + '</span>');
	      },
	      dataType: "json",
	      timeout: 60000
           });
   })();
})
   
