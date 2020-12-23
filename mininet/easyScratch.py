""" Really simple and minimal testing module for v2g

    Since the project is on an alpha version:
    - Install in your machine the usual mininet;
    - Create the directory /usr/share/.miniV2G/RiseV2G and copy in it all the RiseV2G files (two jar and two config);
    - Run this script from the folder that containing also v2g.py.

    TODO: In future all this stuff will be automatically done by the installer
"""


from mininet.net import Mininet
from v2g import EV, SE
from mininet.cli import CLI
from time import sleep

net = Mininet()

se1 = net.addHost("se1", SE)
ev1 = net.addHost("ev1", EV)

net.addLink(se1, ev1)

sleep(1)  # IMPORTANT! Give a second to the net to complete the setup (otherwise crashes are possible)
net.terms += [se1.startCharge()]  # append to net.terms to enable "exit" command to close it
sleep(1)
net.terms += [ev1.charge(in_xterm=True)]

CLI(net)

net.stop()
