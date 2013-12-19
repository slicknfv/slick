<#include "resources/filters/header.ftl"/>
<div id="content">
<#assign names = flowkeys?keys?sort>
<table class="overview">
<tbody>
<#list names as name>
<#assign trCss = (name_index % 2 == 0)?string("even","odd")>
<tr class="${trCss}"><th>${name}</a></th><td>${flowkeys[name]}</td></tr></#list>
</tbody>
</table>
</div>
<#include "resources/filters/footer.ftl">
