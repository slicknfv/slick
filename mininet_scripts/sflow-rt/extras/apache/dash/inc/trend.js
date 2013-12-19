$(document).ready(function() {
  var interval = 1000;
  var timeout = 60000;
  var maxPoints = 120;
  var options = {type:'line',chartRangeMin:0};

  function updateFunction(chart) {
    return function(response) {
      if(!response) return;
      var name = response[0].metricName;
      var value = response[0].metricValue;
      var trend = chart.data(name);
      if(!trend) {
        trend = [];
        for(var i = 0; i < maxPoints; i++) trend[i] = 0;
          chart.data(name,trend);
	}
	trend.push(value);
	trend.shift();

	chart.sparkline(trend,options);
      }
    }

    $('a.trend').each(function(i) {
      var chart = $(this);
      var url = chart.attr('href');
      if(url) {
        var callback = updateFunction(chart);
        (function poll() {
          $.ajax({
              url: url,
              success: function(data) {
              callback(data);
              setTimeout(poll,interval);
            },
            dataType: 'json',
            timeout: timeout
          });
        })(); 
      }
   });
});
