# -*- coding: utf-8 -*-
import subprocess
import sys
import re
import json
import socket

from collections import namedtuple
from time import time

IFCONFIG = "/packages/mnt/junos-net/sbin/ifconfig"
PING = "/packages/mnt/junos-net/sbin/ping"
ifce = namedtuple('ifce', ['name', 'IP'])
polling_ifces = ("et", "xe")
OPENNTISRV = "x.y.z.w" #Fluentd endpoint IP address
OPENNTIPORT = 50050 #Fluentd endpoint port


def do_ping4(ip, size=56, count=3):
    """Pings a v4 address and returns the whole result for further processing;
    receives as input the local interface IP and calculates the other end's
    IP assuming /31 mask.
    """

    frags = ip.split('.')[:3]
    last_octet = int(ip.split('.')[-1])+1
    tmp_ip = frags.append(str(last_octet))
    target_ip = ".".join(frags)
    ping_result = subprocess.Popen([PING, '-J4', '-c', str(count), '-s', str(size),
                                   target_ip], stderr=subprocess.STDOUT, 
                                   stdout=subprocess.PIPE).communicate()
    return ping_result[0]

    
def do_ping6(ip, size=56, count=3):
    """Pings a v6 address and returns the whole result for further processing;
    receives as input the local interface IP and calculates the other end's
    IP assuming /128 mask.
    """

    frags = ip.split(':')[:-1]
    last_octet = int(ip.split(':')[-1])+1
    tmp_ip = frags.append(str(last_octet))
    target_ip = ":".join(frags)
    ping_result = subprocess.Popen([PING, '-J6', '-c', str(count), '-s', str(size),
                                   target_ip], stderr=subprocess.STDOUT, 
                                   stdout=subprocess.PIPE).communicate()
    return ping_result[0]
    
def send_data(ping_loss, portid):
    """Sends an UDP datagram to a fluentd receiver with a JSON message that is 
    constructed hereafter.
    """

    timestamp = int(time.time()* 1000000)
    data = {
        "record-type": "ping-loss",
        "time": timestamp,
        "router-id": socket.gethostname(),
        "port": str(portid),
        "ping-loss": ping_loss
    }
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(json.dumps(data), 0, (OPENNTISRV, OPENNTIPORT))

#run ifconfig from the provided path
try: 
    ifconfig = subprocess.check_output(IFCONFIG, stderr=subprocess.STDOUT).decode()
except subprocess.CalledProcessError as e:
    sys.stderr.write(e.ifconfig.decode())
    sys.exit(1)
except OSError:
    sys.stderr.write("ifconfig was not found in path\n")
    sys.exit(1)

#matches only the first IPv4 and IPv6 address of an interface based on Juniper's
#ifconfig result
rgx = r".*?[^inet,inet6](\S+).*?local=(\S+).*?" 
interfaces = []

#loops through the interfaces listed in polling_ifces and stores respective IPv4
#& IPv6 addresses in an array 
for k in ifconfig.split('\n\n'):
    if k.startswith(polling_ifces):
        interfaces.append(ifce((re.findall('^\S.*?(?=:)', k)), 
                        (re.findall('.*?[^inet,inet6](\S+).*?local=(\S+).*?',k))))

#regex to match the packet loss percentage in ping's output
regex = r'([0-9\\.]+)%\spacket\sloss' 

#loops through the array with the interfaces, pings the respective IPv4 & IPv6 
#and stores the packet_loss
for ifce in interfaces:
    if len(ifce.IP) > 0:
        if ifce.IP[0][1]:
            ping_res = do_ping4(ifce.IP[0][1]) #ping IPv4
            packet_loss = re.findall(regex, ping_res)[0]
            send_data(packet_loss, ifce.name)
        #if ifce.IP[1][1]:
        #    ping_res = do_ping6(ifce.IP[1][1]) #ping IPv6
        #    packet_loss = re.findall(regex, ping_res)[0]
        #    send_data(packet_loss, ifce.name)
