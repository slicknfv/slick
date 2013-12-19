<#include "resources/filters/header.ftl"/>
<div id="content">
<table>
<thead>
<tr><th>URI</th><th>Operations</th><th>Description</th><th>Arguments</th></tr>
</thead>
<tbody>
<tr class="even">
    <td><a href="${root}version">/version</a></td>
    <td>GET</td><td>Software version number</td>
    <td></td>
</tr>
<tr class="odd">
    <td><a href="${root}analyzer/html">/analyzer/html</a></td>
    <td>GET</td><td>Statistics describing analyzer performance</td>
    <td></td>
</tr>
<tr class="even">
    <td><a href="${root}analyzer/json">/analyzer/json</a></td>
    <td>GET</td><td>Statistics describing analyzer performance</td>
    <td></td>
</tr>
<tr class="odd">
    <td><a href="${root}agents/html">/agents/html</a></td>
    <td>GET</td><td>List agents</td>
    <td>accepts same arguments as json query below</td>
</tr>
<tr class="even">
    <td><a href="${root}agents/json">/agents/json</a></td>
    <td>GET</td>
    <td>List agents</td>
    <td><b>query</b> Used to filter agents, e.g. agent=10.0.0.1&amp;agent=test1 returns information on selected agents</td>
</tr>
<tr class="odd">
    <td><a href="${root}metrics/html">/metrics/html</a></td>
    <td>GET</td><td>List currently active metrics and elapsed time (in mS) since last seen</td>
    <td></td>
</tr>
<tr class="even">
    <td><a href="${root}metrics/json">/metrics/json</a></td>
    <td>GET</td><td>List currently active metrics and elapsed time (in mS) since last seen</td>
    <td></td>
</tr>
<tr class="odd">
    <td>/metric/{agent}/html</td>
    <td>GET</td><td>Retrieve metrics for agent</td>
    <td>accepts same arguments as json query below</td>
</tr>
<tr class="even">
    <td>/metric/{agent}/json</td>
    <td>GET</td>
    <td>Retrieve metrics for agent</td>
    <td><b>agent:</b> ip address or hostname of agent</td>
</tr>
<tr class="odd">
    <td>/metric/{agent}/{metric}/html</td>
    <td>GET</td>
    <td>Plot metric</td>
    <td>accepts same arguments as json query below</td>
</tr>
<tr class="even">
    <td>/metric/{agent}/{metric}/json</td>
    <td>GET</td>
    <td>Retrieve metric</td>
    <td><b>agent:</b> list of agent addresses/hostnames e.g. 10.0.0.1;switch1 - the token <i>ALL</i> represents all agents<br /><b>metric:</b> ordered list of metric names, e.g. load_one,load_five - prefix metric with <i>max:</i>, <i>min:</i>, <i>sum:</i>, <i>avg:</i>, <i>var:</i>, <i>sdev:</i>, <i>med:</i>, <i>q1:</i>, <i>q2:</i>, <i>q3:</i>, <i>iqr:</i> or <i>any:</i> to specify aggregation operation, e.g. max:load_one,min:load_one.
Default aggregation <i>max</i> is used if no prefix specified<br />
<b>query:</b> query parameters applied as filter to select agents based on metrics, e.g. os_name=linux&amp;os_name=windows&amp;cpu_num=2&amp;host_name=*web.*</b></td>
</tr>
<tr class="odd">
    <td>/dump/{agent}/{metric}/html</td>
    <td>GET</td>
    <td>Dump metric values</td>
    <td>accepts same arguments as json query below</td>
</tr>
<tr class="even">
    <td>/dump/{agent}/{metric}/json</td>
    <td>GET</td>
    <td>Dump metric values</td>
    <td><b>agent:</b> list of agent addresses/hostnames e.g. 10.0.0.1;switch1 - the token <i>ALL</i> represents all agents<br /><b>metric:</b>list of metric names, e.g. load_one;load_five - the token <i>ALL</i> represents all metrics<br /><b>query:</b> query parameters applied as filter to select agents based on metrics, e.g. os_name=linux&amp;os_name=windows&amp;cpu_num=2&amp;host_name=*web.*</b></td>
</tr>
<tr class="odd">
    <td><a href="${root}flowkeys/html">/flowkeys/html</a></td>
    <td>GET</td>
    <td>List currently active flow keys and elapsed time (in mS) since last seen</td>
    <td></td>
</tr>
<tr class="even">
    <td><a href="${root}flowkeys/json">/flowkeys/json</a></td>
    <td>GET</td>
    <td>List currently active flow keys and elapsed time (in mS) since last seen</td>
    <td></td>
</tr>
<tr class="odd">
    <td><a href="${root}flow/html">/flow/html</a></td>
    <td>GET, POST</td><td>Manage flow definitions</td>
    <td>
<b>name:</b> name used to identify flow specification<br/>
<b>keys:</b> list of flowkey attributes, e.g. ipsource,ipdestination<br />
<b>value:</b> Numeric flowkey attribute, e.g. <i>frames</i>, <i>bytes</i>, <i>requests</i>, <i>duration</i><br />
<b>filter:</b> boolean expression filtering flowkeys, e.g. sourcegroup=local&amp;destinationgroup=external<br />
<b>n:</b> number of largest flows to maintain (i.e. the n in &quot;top n&quot;)<br/>
<b>t:</b> smoothing factor (in seconds)<br />
<b>fs:</b> string used to separate flow record fields, default is comma &quot;,&quot;<br />
<b>log:</b> if <i>true</i>, record flows for access through REST API<br />
<b>flowStart:</b> if <i>true</i>, record start of flow, otherwise record end of flow<br />
<b>activeTimeout:</b> number seconds before flushing active flow<br />
<b>ipfixCollectors:</b> send flows as IPFIX messages to specified list of collectors (e.g. <i>10.0.0.1,localhost</i>).<br />
Functions of the form &lt;funcname&gt;:&lt;arg1&gt;:&ltarg2&gt;... can be applied used to define a flowkey or a filter:<br />
prefix:&lt;flowkey&gt;:&lt;delim&gt;:&lt;num_tokens&gt;, e.g. prefix:uripath:/:1<br />
suffix:&lt;flowkey&gt;:&lt;delim&gt;:&lt;num_tokens&gt;, e.g. suffix:uripath:/:1<br />
mask:&lt;flowkey&gt;:&lt;mask_bits&gt;, e.g. mask:ipsource:24<br />
null:&lt;flowkey&gt;:&lt;null_value&gt;, e.g. null:vlan:undefined<br />
or:&lt;flowkey1&gt;:&ltflowkey2&gt;, e.g. or:ipsource:ip6source<br />
The following prefixes can be used to modify the way that the value field is computed:<br />
rate:&lt;flowkey&gt;, e.g. rate:requests<br />
avg:&lt;flowkey&gt;, e.g. avg:duration<br />
count:&lt;flowkey&gt;, e.g. count:ipsource<br />
When ipfixCollectors is set, only the following subset of keys is allowed, <i>macsource, macdestination, ethernetprotocol, vlan, priority, ipprotocol, ipsource, ipdestination, ip6source, ip6destination, ip6nexthdr, tcpsourceport, tcpdestinationport, udpsourceport, udpdestinationport, inputifindex, outputifindex</i> and the following values, <i>bytes, frames</i>. </td>
</tr>
<tr class="even">
    <td><a href="${root}flow/json">/flow/json</a></td>
    <td>GET</td>
    <td>List flow definitions</td>
    <td></td>
</tr>
<tr class="odd">
    <td>/flow/{name}/json</td>
    <td>GET, PUT, DELETE</td>
    <td>Manage flow definition</td>
    <td><b>name:</b> name used to identify flow specification<br />Flow parameters are expressed as JSON object, e.g. {keys:'ipsource,ipdestination', value:'bytes', filter:'ipprotocol=1'}</td>
</tr>
<tr class="even">
     <td>/activeflows/{agent}/{name}/html</td>
     <td>GET</td>
     <td>List top active flows, removing duplicates for flows reported by multiple data sources</td>
     <td>accepts same arguments as json query below</td>
</tr>
<tr class="odd">
     <td>/activeflows/{agent}/{name}/json</td>
     <td>GET</td>
     <td>List top active flows, removing duplicates for flows reported by multiple data sources</td>
     <td><b>agent:</b> list of agent addresses/hostnames e.g. 10.0.0.1;switch1 - the token <i>ALL</i> represents all agents<br /><b>name:</b> name used to identify flow specification<br /><b>query:</b> set <i>maxFlows</i> to change limit number of flow record returned (default is 100), <i>minValue</i> to only report flows exceeding specified value, <i>aggMode</i> to <i>sum</i> or <i>max</i> to specify how flows are combined (max is default) e.g. maxFlows=200&amp;minValue=1000&amp;aggMode=sum returns up to 200 active flows with value &gt;= 1000 and summing values for each flow</td>
</tr>
<tr class="even">
    <td><a href="${root}flows/html">/flows/html</a></td>
    <td>GET</td>
    <td>List completed flows. Flows will only be logged if <i>log:true</i> is specified in the flow specification.</td>
    <td></td>
</tr>
<tr class="odd">
    <td><a href="${root}flows/json">/flows/json</a></td>
    <td>GET</td>
    <td>List completed flows. Flows will only be logged if <i>log:true</i> is specified in the flow specification.</td>
    <td><b>query:</b> used to filter flows, e.g. name=udp&amp;maxFlows=100 returns most recent 100 flows with name=udp, or to block for flows, e.g. flowID=10&amp;maxFlows=100&amp;timeout=60, waits for up to 60 seconds for flows after flowID 10</td>
</tr>
<tr class="even">
    <td><a href="${root}group/json">/group/json</a></td>
    <td>PUT, GET</td>
    <td>Manage IP address groups</td><td>Groups define <i>sourcegroup</i>, <i>destinationgroup</i> attributes for flows, e.g. {external:['0.0.0.0/0'], internal:['10.0.0.0/8','172.16.0.0/12','192.168.0.0/16']}</td>
</tr>
<tr class="odd">
    <td><a href="${root}threshold/html">/threshold/html</a></td>
    <td>GET, POST</td>
    <td>Manage thresholds</td>
    <td><b>name:</b> name used to identify threshold specification<br/><b>metric:</b> metric to apply threshold to, e.g. load_one<br/><b>value:</b> threshold value, e.g. 1.0<br/><b>filter:</b> query encoded filter expression consistent with metric query, e.g. os_name=linux&amp;cpu_num=2<br/><b>byFlow:</b> set to <i>true</i> to generate a new event for each new flow exceeding threshold, otherwise only first flow generates event<br/><b>timeout:</b> seconds of hysteresis before re-arming threshold</td>
</tr>
<tr class="even">
    <td><a href="${root}threshold/json">/threshold/json</a></td>
    <td>GET</td>
    <td>Retrieve thresholds</td>
    <td></tr>
</tr>
<tr class="odd">
    <td>/threshold/{name}/json</td>
    <td>GET, PUT, DELETE</td>
    <td>Manage definition of threshold</td>
    <td><b>name:</b> name used to identify threshold specification<br />Threshold parameters are expressed as JSON object, e.g. {metric:"load_one", value:1, filter:{os_name:["linux"]}}</td>
</tr>
<tr class="even">
    <td><a href="${root}events/html">/events/html</a></td>
    <td>GET</td>
    <td>List events</td>
    <td></td>
</tr>
<tr class="odd">
    <td><a href="${root}events/json">/events/json</a></td>
    <td>GET</td>
    <td>List events</td>
    <td><b>query:</b> Used to filter events, e.g. thresholdID=load&amp;maxEvents=100 returns most recent 100 events generated by threshold &quot;load&quot;, or to block for events, e.g. ?eventID=10&amp;maxEvents=100&amp;timeout=60, waits for up to 60 seconds for events after eventID 10</td>
</tr>
<tr class="even">
    <td><a href="${root}scripts/json">/scripts/json</a></td>
    <td>GET</td>
    <td>Status of scripts loaded at startup. See <a href="properties.html">System Properties</a> and <a href="script.html">JavaScript Functions</a></td>
    <td></td>
</tr>
<tr class="odd">
    <td>/script/{script}/json</td>
    <td>GET, POST, PUT, DELETE</td>
    <td><i>script</i> specific</td>
    <td>Defined by <i>script</i></td>
</tr>
<tr class="even">
    <td>/forwarding/json</td>
    <td>GET</td>
    <td>List sFlow forwarding targets</td>
    <td></td>
<tr>
<tr class="odd">
    <td>/forwarding/{name}/json</td>
    <td>GET, PUT, DELETE</td>
    <td>Manage sFlow forwarding</td>
    <td><b>name:</b> name used to identify sFlow target<br/>
    Target is expressed as a JSON object, e.g. {address:'10.0.0.1',port:6343}</td>
</tr>
</tbody>
</table>
<p><b>Note:</b> RESTflow API is not final and is subject to change in future releases.</p>
</div>
<#include "resources/filters/footer.ftl">
