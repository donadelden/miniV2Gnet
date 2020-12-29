""" Really simple and minimal testing module for v2g

    To install RiseV2G on your local machine run: util/install.sh -g.
    It will:
    - Create the directory /usr/share/.miniV2G/RiseV2G and copy in it all the RiseV2G files (two jar and two config);
    - Make sure java is installed and install it otherwise.
    - Install or make sure you have: xorg-xhost, xterm
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
net.terms += [se1.startCharge(in_xterm=True)]  # append to net.terms to enable "exit" command to close it
sleep(1)
net.terms += [ev1.charge(in_xterm=True)]

CLI(net)

net.stop()
