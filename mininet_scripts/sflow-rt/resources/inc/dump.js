$(document).ready(function() {
    $("#metrics tbody tr")
       .hover(
         function() { $(this).addClass("dynhoveron"); },
         function() { $(this).removeClass("dynhoveron"); }
       )
       .click(
         function() { 
           var cells = $(this).find("td");
           var agent = cells[0];
           var dataSource = cells[1];
           var metric = cells[2];
           document.location = "../../../metric/" + agent.innerHTML + "/" + dataSource.innerHTML + "." + metric.innerHTML + "/html"; }
       )
})
