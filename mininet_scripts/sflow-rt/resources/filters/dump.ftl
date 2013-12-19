<#include "resources/filters/header.ftl"/>
<div id="content">
<table id="metrics">
<thead>
<tr><th>Agent</th><th>Data Source</th><th>Metric</th><th>Value</th></tr>
</thead>
<tbody>
<#list metrics as metric>
<#assign trCss = (metric_index % 2 == 0)?string("even","odd")>
<tr class="${trCss}"><td>${metric.agent}</td><td>${metric.dsIndex}</td><td>${metric.metricName}</td><td>${metric.metricValue}</td></tr></#list>
</tbody>
</table>
</div>
<#include "resources/filters/footer.ftl">
