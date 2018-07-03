# Measuring Packet loss inside an IP CLos 

Juniper devices running Junos OS with Enhanced Automation are equipped with a version of python interpreter that is accessible to users under the shell. 

In an IP Clos topology it is important to ensure that no packet loss exists between the spines and the leafs. Provided the existence of a plethora of links interconnecting the latter entities, this python script performs sanity checks using ping between the point to point links and measures packet loss. Inspired by the telemetry concept and open-nti[1], the results are send as UDP datagrams to a Fluentd receiver and consequently to an Influx instance for further processing.

The IP addresses of the point-to-point links are collected with a regex expression applied to the ifconfig results, hence it is tailored to the specific ifconfig's output and may not considered portable.

Only interfaces named with prefixes that are enlisted in the polling_ifces tuple are considered (i.e. not interested to measure fxp, em, irb, vtep and other similar interfaces). The IPv4 and IPv6 addresses are matched with the regex and a nametuple is created with all of them. A ping is performed to either all IPv4 or IPv6 addresses and the results are sent to an Fluentd endpoint.

The script needs to run periodically either within a crontab entry or using an event-option depending on the Junos version.

[1] https://github.com/Juniper/open-nti
