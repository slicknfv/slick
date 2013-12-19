<#include "resources/filters/header.ftl"/>
<div id="content">
<h1>System Properties</h1>
<p>The following System properties can be set in the <b>start.sh</b> or <b>start.bat</b> script:</p>
<table>
<thead>
<tr><th>Property</th><th>Default</th><th>Description</th></tr></thead>
</thead>
<tbody>
<tr class="odd"><td>http.port</td><td>8008</td><td>TCP port to receive HTTP requests</td></tr>
<tr class="even"><td>http.log</td><td>no</td><td>Set to <i>yes</i> to enable http request logging</td></tr>
<tr class="odd"><td>http.html</td><td>yes</td><td>Set to <i>no</i> to exclude HTML pages</td></tr>
<tr class="even"><td>http.readonly</td><td>no</td><td>Set to <i>yes</i> to prevent POST/PUT operations from modifying thresholds, flows, and groups</td></tr>
<tr class="odd"><td>script.file</td><td></td><td>Comma separated list of JavaScript files to load at startup, see <a href="script.html">JavaScript Functions</a>. Use <i>http.readonly=yes</i> to prevent modification of settings installed by scripts</td></tr>
<tr class="even"><td>script.store</td><td>store</td><td>Directory for storing persistent objects for scripts</td></tr>
<tr class="odd"><td>sflow.port</td><td>6343</td><td>UDP port to receive sFlow</td></tr>
<tr class="even"><td>sflow.file</td><td></td><td>Playback sFlow from pcap file (disables <i>sflow.port</i>)</td></tr>
<tr class="odd"><td>events.max</td><td>1000</td><td>Maximum number of events to keep</td></tr>
<tr class="even"><td>flows.max</td><td>1000</td><td>Maximum number of completed flows to keep</td></tr>
<tr class="odd"><td>geo.country</td><td></td><td>GeoIP database location.
Set to resources/config/GeoIP.dat to use GeoLite database</td></tr>
<tr class="even"><td>geo.asn</td><td></td><td>GeoIP database location.
Set to resources/config/GeoIPASNum.dat to use GeoLite database</td></tr>
<tr class="odd"><td>geo.country6</td><td></td><td>GeoIP database location.
Set to resources/config/GeoIPv6.dat to use GeoLite database</td></tr>
<tr class="even"><td>geo.asn6</td><td></td><td>GeoIP database location.
Set to resources/config/GeoIPASNumv6.dat to use GeoLite database</td></tr>
<tr class="odd"><td>oui.names</td><td></td><td>OUI name file
Set to resources/config/oui.txt to lookup names</tr>
</tbody>
</table>
</div>
<#include "resources/filters/footer.ftl">
