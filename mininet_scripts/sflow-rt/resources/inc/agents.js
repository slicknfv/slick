$(document).ready(function() {
    $("#agents tbody tr")
       .hover(
         function() { $(this).addClass("dynhoveron"); },
         function() { $(this).removeClass("dynhoveron"); }
       )
       .click(
         function() { 
           var cells = $(this).find("th");
           var agent = cells[0];
           document.location = "../metric/" + agent.innerHTML + "/html"; }
       )
})
