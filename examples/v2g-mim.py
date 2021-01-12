#!/usr/bin/python

""" 
    Really simple and minimal testing module for v2g

    To install RiseV2G on your local machine run: util/install.sh -g.
    It will:
    - Create the directory /usr/share/.miniV2G/RiseV2G and copy in it all the RiseV2G files (latest jar releases and two config files);
    - Make sure java, xterm, curl is installed and install it otherwise.
"""

from mininet.net import Mininet
from mininet.node import NullController
from mininet.cli import CLI
from mininet.log import setLogLevel, info

from v2g import EV, SE, MiMOVSSwitch, MiMNode # TODO: replace with mininet.v2g
from time import sleep

def v2gNet():

    "Create a network without an EV and SE connected via a switch."

    start_on_load = False

    net = Mininet(  )

    info( '*** Adding controller\n' )
    net.addController( 'c0', NullController )

    # no controller, the switch will take care

    info( '*** Adding hosts: SE, EV and mim\n' )
    se1 = net.addHost("se1", SE )
    ev1 = net.addHost("ev1", EV )
    mim = net.addHost("mim", MiMNode)

    info( '*** Adding MiM switch\n' )

    s1 = net.addSwitch( 's1', MiMOVSSwitch )

    info( '*** Creating links\n' )
    net.addLink( se1, s1 )
    net.addLink( ev1, s1 )
    net.addLink( mim, s1 ) # ev and se don't know about mim

    sleep(1)  # IMPORTANT! Give a second to the net to complete the setup (otherwise crashes are possible)

    info( '*** Starting network\n')
    net.start()

    info( '*** Running CLI\n' )
    info( '*** BASIC USAGE:\n' )
    info( '     - With `py se1.startCharge()` the SE will wait for charging EVs.\n' )
    info( '     - With `py ev1.charge(in_xterm=True)` the EV will start charging in the linked SE.\n' )

    info('%s %s\n'%(se1.IP(), se1.MAC()))
    info('%s %s\n'%(ev1.IP(), ev1.MAC()))
    info('%s %s\n'%(mim.IP(), mim.MAC()))

    s1.add_mim_flows(se1, ev1, mim)
    mim.start_arpspoof(se1, ev1)
    ## CAREFUL: MAC addrs in table of source are matching, however communication works anyway
    # sleep(1)
    # se1.cmd("arp", "-d", "%s" % mim.IP()) # problem: arpspoof wants to know the macaddr of source
    # ev1.cmd("arp", "-d", "%s" % mim.IP()) # problem: arpspoof wants to know the macaddr of source
    # this generates an entry in the table of source with macaddr of mim

    # tested connection with 
    # # mim: nc -l -p 20000
    # # se1: nc 10.0.0.2 20000
    # mim.receive_thread()
    # sleep(1)
    # se1.test_send(ev1)

    if start_on_load == True:
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
