"""
Additional Nodes for Vehicle to Grid (V2G) communication
"""

import atexit  # clean the mess on exit
import fileinput
# to generate the random prefix for folders
import random
import string
import sys
from os import popen

from mininet.term import makeTerm
from mininet.node import OVSSwitch
from mininet.moduledeps import pathCheck
from mininet.node import Node
from mininet.util import quietRun


class Electric(Node):
    """A basic Node class with the support for V2G communication"""

    def __init__(self, name, path=None, **kwargs):
        # check if java is available (it is needed for RiseV2G)
        # maybe TODO add this in the installer
        pathCheck('java')
        # set the path of RiseV2G
        # TODO: add on the installer a copy to this folder
        if path is not None:
            self.RISE_PATH = path
        else:
            self.RISE_PATH = "/usr/share/.miniV2G/RiseV2G"

        # check if it exists
        if "No such file or directory" in popen('ls {}'.format(self.RISE_PATH)).read():
            exit(
                "*** Fatal error: directory %s not found. Select the right folder which contains the needed jar files.")
        # TODO: check for the specific jar files

        # initialize the subprocess object
        self.proc = None

        Node.__init__(self, name, **kwargs)

        # setup a random prefix for folders (to better cleanup everything in the end)
        prefix_len = 4
        self.FOLDER_PREFIX = ''.join(random.choice(string.ascii_lowercase) for i in range(prefix_len))

        # cleanup of the generated folder
        def cleaner():
            print('*** Cleaning up the mess')
            popen("rm -rd {}*".format(self.FOLDER_PREFIX))

        atexit.register(cleaner)

    def intfSetup(self, folder, intfName=None):
        """Sets the intfName on the .properties file.
        :param folder: the subfolder containing the designated RiseV2G jar file
        :param intfName: """
        # to decide if it is an ev or se it check the path;
        # if you change the default folder it is better to change this stuff
        if "ev" in folder:
            prefix = "EVCC"
        else:
            prefix = "SECC"

        for line in fileinput.input([folder + "/" + prefix + "Config.properties"], inplace=True):
            if line.strip().startswith('network.interface'):
                line = 'network.interface = {}\n'.format(intfName)
            sys.stdout.write(line)


class EV(Electric):
    """An Electric Vehicle (EV) is a Node containing all the
    necessary to be able to start the communication from its
    EV Communication Controller (EVCC) with a SECC to require charging service """

    def __init__(self, name, path=None, **kwargs):
        self.name = str(name)
        Electric.__init__(self, self.name, path, **kwargs)

        self.folder = "{}_ev_{}".format(self.FOLDER_PREFIX, self.name)
        self.cmd("mkdir {}".format(self.folder))
        self.cmd("cp {}/EVCCConfig.properties {}/".format(self.RISE_PATH, self.folder))
        # this cp can resist to update of risev2g but you must have onyl one version
        self.cmd("cp {}/rise-v2g-evcc-*.jar {}/".format(self.RISE_PATH, self.folder))
        # cd into the right folder
        self.cmd("cd ./{}".format(self.folder))

    def charge(self, in_xterm=False, intf=None):
        """Starting the charging process.
        :param in_xterm: True to run the charge inside an xterm instance. Default: False.
        :param intf: the interface to which search for EVSE. Default: None, use the default interface."""

        print("*** Looking for EVSE and start charging...")
        # setting the interface (default: default interface)
        if intf is None:
            intf = self.intf().name
        self.intfSetup(self.folder, intf)

        if in_xterm:
            # run inside an xterm. You must append the return value to net.terms to terminal on exit.
            command = "cd ./{}; java -jar rise-v2g-evcc-*.jar; bash -i".format(self.folder)
            # this return a list of just one xterm, so [0] is needed
            self.proc = makeTerm(self, cmd="bash -i -c '{}'".format(command))[0]
            return self.proc
        else:
            self.proc = self.popen("cd ./{}; java -jar rise-v2g-evcc-*.jar".format(self.folder), shell=True)
            # print the stdout to the CLI at the end of the charging process
            proc_stdout = self.proc.communicate()[0].strip()
            print(proc_stdout)


class SE(Electric):
    """An EV Supply Equipment (EVSE) is a Node containing which can
    provide charging services to an EV by communication using the
    Supply Equipment Communication Controller (SECC)
    """

    def __init__(self, name, path=None, **kwargs):
        self.name = str(name)
        Electric.__init__(self, self.name, path, **kwargs)

        self.folder = "{}_se_{}".format(self.FOLDER_PREFIX, self.name)
        self.cmd("mkdir {}".format(self.folder))
        self.cmd("cp {}/SECCConfig.properties {}/".format(self.RISE_PATH, self.folder))
        # this cp can resist to update of risev2g but you must have onyl one version
        self.cmd("cp {}/rise-v2g-secc-*.jar {}/".format(self.RISE_PATH, self.folder))
        # cd into the right folder
        self.cmd("cd ./{}".format(self.folder))

    def startCharge(self, intf=None):
        """
        Spawn an xterm and start the listening phase in it.
        It is not possible to launch it without xterm because otherwise it sometime randomly crashes.
        :param intf: Interface in which listen for charging requests. If None, default is used.
        :returns A popen xterm instance. To be appended to "net.terms" to assure a correct close on exit."""

        # setting the interface (default: default interface)
        if intf is None:
            intf = self.intf().name
        self.intfSetup(self.folder, intf)

        print("*** Starting waiting for EVs...")
        command = "cd ./{}; java -jar rise-v2g-secc-*.jar; bash -i".format(self.folder)
        # this return a list of just one xterm, so [0] is needed
        self.proc = makeTerm(self, cmd="bash -i -c '{}'".format(command))[0]
        return self.proc

    def state(self):
        """ Print and return the state of a process
        :return the state of the process or False if the process does not exists."""
        if self.proc is not None:
            state = self.proc.poll()
            if state is None:
                print("* Running!")
            else:
                print("* Stopped (State: {}).".format(state))
            return state
        else:
            print("* The process does not exist. Call .startCharge() first.")
            return False

    def stopCharge(self):
        """Stops the charging process.
        :return True if stopped successfully, False if the process does not exists"""
        # TODO: maybe can be useful to print stdout
        if self.proc is not None:
            self.proc.kill()
            self.proc = None
            print("* Stopped successfully.")
            return True
        else:
            print("* The process does not exist. Call .startCharge() first.")
            return False

        
class MiMOVSSwitch( OVSSwitch ):
    "Open vSwitch switch acting as Man-in-the-middle. Depends on ovs-vsctl."

    def __init__( self, name, failMode='secure', datapath='kernel',
                  inband=False, protocols=None,
                  reconnectms=1000, stp=False, batch=False, **params ):
        """name: name for switch
           failMode: controller loss behavior (secure|standalone)
           datapath: userspace or kernel mode (kernel|user)
           inband: use in-band control (False)
           protocols: use specific OpenFlow version(s) (e.g. OpenFlow13)
                      Unspecified (or old OVS version) uses OVS default
           reconnectms: max reconnect timeout in ms (0/None for default)
           stp: enable STP (False, requires failMode=standalone)
           batch: enable batch startup (False)"""
        OVSSwitch.__init__( self, name, **params )

    def dpctl( self, *args ):
        "Run ovs-ofctl command"
        return self.cmd( 'ovs-ofctl', *args )

    def add_mim( self, source, target, mim ):
        # BEWARE THIS IS IPV4

        # get ip, mac

        # arp request is sent to broadcast (flood rule)
        # arp reply is sent to who requested

        # sh ovs-ofctl add-flow s1 dl_type=0x806,nw_proto=1,dl_src=00:00:00:00:00:03,actions=drop

        # sh ovs-ofctl add-flow s1 dl_src=00:00:00:00:00:01,dl_dst=00:00:00:00:00:03,actions=mod_nw_dst:10.0.0.3,output:3
        # sh ovs-ofctl add-flow s1 dl_src=00:00:00:00:00:03,dl_dst=00:00:00:00:00:01,actions=mod_nw_src:10.0.0.2,output:1
        # sh ovs-ofctl add-flow s1 dl_type=0x806,nw_proto=1,actions=flood
        # arpspoof -i h3-eth0 -c own -t 10.0.0.1 10.0.0.2

        # drop arp replies from mim (3)
        # print(self.cmd("ovs-ofctl", "add-flow", "s1", "dl_type=0x806,nw_proto=1,nw_src=10.0.0.3,actions=drop"))
        
        # mac 10.0.0.2 is already linked to (3) by mim arpspoof
        # malicious node changes the ip
        # source -> mim, mim
        self.cmd("ovs-ofctl", "add-flow", "s1", "dl_src=%s,dl_dst=%s,actions=mod_nw_dst:%s,output:3" % (source.MAC(), mim.MAC(), mim.IP()))
        # mim -> target, source
        self.cmd("ovs-ofctl", "add-flow", "s1", "dl_src=%s,dl_dst=%s,actions=mod_nw_src:%s,output:1" % (mim.MAC(), source.MAC(), target.IP()))
        # drop the arp relys coming from mim
        # self.cmd("ovs-ofctl", "add-flow", "s1", "dl_type=0x806,nw_proto=1,dl_src=%s,actions=drop" % (mim.MAC()))
        # flood the arp relys to all nodes who requested them
        self.cmd("ovs-ofctl", "add-flow", "s1", "dl_type=0x806,nw_proto=1,actions=flood")
        print(self.cmd("ovs-ofctl", "dump-flows", "s1"))

class MiMNode( Node ):
    def __init__( self, name, source=None, inNamespace=True, **params ):
        Node.__init__(  self, name, inNamespace=True, **params  )

    def start_arpspoof( self, source, target ):
        # "2>/dev/null 1>/dev/null &"
        self.cmd("arpspoof", "-i mim-eth0", "-c own", "-t %s" % source.IP(), "%s" % target.IP(), " &")
        # on mim
        # arpspoof -i h3-eth0 -c own -t 10.0.0.1 10.0.0.2 # send arp reply
