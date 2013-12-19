<html>
<head>
<title>sFlow-RT</title>
<link rel="stylesheet" type="text/css" href="${root}inc/inmsf/main.css" media="all" />
<#if styleSheets??>
<#list styleSheets as styleSheet><link rel="stylesheet" type="text/css" href="${root}inc/${styleSheet}" />
</#list>
</#if>
<#if scripts??>
<#list scripts as script><script type="text/javascript" src="${root}inc/${script}"></script>
</#list>
</#if>
</head>
<body>

<div id="main">
<div id="titleBar"><a name="top"></a><div id="product"><span id="logo"></span>sFlow-RT</div></div>
<div id="menuBar">
<ul>
  <li><a href="${root}html/api.html">RESTflow API</a></li>
  <li><a href="${root}agents/html">Agents</a></li>
  <li><a href="${root}metrics/html">Metrics</a></li>
  <li><a href="${root}flow/html">Flows</a></li>
  <li><a href="${root}threshold/html">Thresholds</a></li>
  <li><a href="${root}events/html">Events</a></li>
  <li><a href="${root}html/index.html">About</a></li>
</ul>
</div>
