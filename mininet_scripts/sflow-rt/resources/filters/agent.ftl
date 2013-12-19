<#include "resources/filters/header.ftl"/>
<div id="content">
<#assign names = metrics?keys?sort>
<table class="overview" id="agent">
<tbody>
<#list names as name>
<#assign trCss = (name_index % 2 == 0)?string("even","odd")>
<tr class="${trCss}"><th>${name}</th><td>${metrics[name]}</td></tr></#list>
</tbody>
</table>
</div>
<#include "resources/filters/footer.ftl">
