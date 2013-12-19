$(document).ready(function() {
    $("#metrics tbody tr")
       .hover(
         function() { $(this).addClass("dynhoveron"); },
         function() { $(this).removeClass("dynhoveron"); }
       )
       .click(
         function() { 
           var cells = $(this).find("th");
           var metric = cells[0];
           document.location = "../metric/ALL/" + metric.innerHTML + "/html"; }
       )
})
