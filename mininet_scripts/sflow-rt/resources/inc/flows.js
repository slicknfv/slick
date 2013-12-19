$(document).ready(function() {
    $("#flows tbody tr")
       .filter(function() {
         return $(this).hasClass("even") || $(this).hasClass("odd")
       })
       .hover(
         function() { $(this).addClass("dynhoveron"); },
         function() { $(this).removeClass("dynhoveron"); }
       )
       .click(
         function() { 
           var cells = $(this).find("td");
           var metric = cells[0];
           document.location = "../activeflows/ALL/" + metric.innerHTML + "/html?maxFlows=20&minValue=0&aggMode=max"; }
       )
})
