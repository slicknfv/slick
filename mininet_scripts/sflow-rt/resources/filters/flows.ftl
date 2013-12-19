<#include "resources/filters/header.ftl"/>
<div id="content">
<form method="post">
<#assign names = flows?keys?sort>
<div class="constrain">
<table class="constrain" id="flows">
<thead>
<tr><th>Name</th><th>Keys</th><th>Value</th><th>Filter</th></tr>
</thead>
<tbody>
<#list names as name>
<#assign trCss = (name_index % 2 == 0)?string("even","odd")>
<tr class="${trCss}"><td class="alignl">${name}</td><td class="alignl">${flows[name].keys!""}</td><td class="alignl">${flows[name].value!""}</td><td class="alignl">${flows[name].filter!""}</td></tr></#list>
<tr><td class="sep" colspan="4">&nbsp;</td></tr>
<tr><td><input type="text" name="name" size="20"></td><td><input type="text" name="keys" size="40"></td><td><input type="text" name="value" size="20"></td><td><input type="text" name="filter" size="40"></td></tr>
<tr><td colspan="4" class="formbuttons"><button type="submit">Submit</button></td></tr>
</tbody>
</table>
</div>
</form>

</div>
<#include "resources/filters/footer.ftl">
