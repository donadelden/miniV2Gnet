#!/usr/bin/python

""" 
    Really simple and minimal testing module for v2g

    To install RiseV2G on your local machine run: util/install.sh -g.
    It will:
    - Create the directory /usr/share/.miniV2G/RiseV2G and copy in it all the RiseV2G files (latest jar releases and two config files);
    - Make sure java, xterm, curl is installed and install it otherwise.
"""

from mininet.net import Mininet
from v2g import EV, SE
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from time import sleep

def v2gNet():

    "Create a network with an EV and SE connected via a link."

    net = Mininet(  )

    info( '*** Adding SE and EV\n' )
    se1 = net.addHost("se1", SE)
    ev1 = net.addHost("ev1", EV)

    info( '*** Creating link\n' )
    net.addLink( se1, ev1 )

    sleep(1)  # IMPORTANT! Give a second to the net to complete the setup (otherwise crashes are possible)

    info( '*** Starting network\n')
    net.start()

    info( '*** Running CLI\n' )
    info( '*** BASIC USAGE:\n' )
    info( '     - With `py se1.startCharge(in_xterm=True)` the SE will wait for charging EVs.\n' )
    info( '     - With `py ev1.charge(in_xterm=True)` the EV will start charging in the linked SE.\n' )

    info( '*** Starting charge on the SE.\n' )
    # TODO: move the sleep command to the SE and EV charge.
    sleep( 1 ) # IMPORTANT! Give a second to the net to complete the setup (otherwise crashes are possible)
    net.terms += [ se1.startCharge() ]
    info( '*** EV is charging.\n' )
    sleep( 1 )
    net.terms += [ ev1.charge( in_xterm=True ) ]
    CLI( net )

    info( '*** Stopping network' )
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    v2gNet()
