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

    def test_send(self, rec):
        """Test send to MiM via TCP """
        TCP_IP = rec.IP()
        TCP_PORT = 2000
        BUFFER_SIZE = 1024
        MESSAGE = 'Test'

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((TCP_IP, TCP_PORT))
            s.send(MESSAGE)
            data = s.recv(BUFFER_SIZE)
            s.close()
            print("received: ", data)
        except:
            print("cant connect")


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

    def add_mim_flows( self, source, target, mim, use_ipv6=True ):
        """Sets the flows for a MiM switch.
        :param source: the source (e.g. se1)
        :param target: the target (e.g. ev1)
        :param mim: the MiM node (e.g. mim)
        :param use_ipv6: choose ipv6 or ipv4 (default: true)"""

        if use_ipv6:
            # TODO: should be addded to mininet node itself in the future
            get_ipv6 = "ifconfig %s | grep inet6 | grep -o -P '(?<=inet6 ).*(?= prefixlen)'"
            sourceIPV6 = source.cmd(get_ipv6 % (source.intf().name)).rstrip()
            targetIPV6 = target.cmd(get_ipv6 % (target.intf().name)).rstrip()
            mimIPV6 = mim.cmd(get_ipv6 % (mim.intf().name)).rstrip()

            # write ips to a common file in home folder
            f = open(".common_ips.txt", "w+")
            f.write(sourceIPV6 + "\n" + targetIPV6)
            f.close()

        # TODO: DOES NOT WORK, alternative? environment vars?
        # save ipv6 of source and target in /etc/hosts for easy access to terminal
        # source.cmd("echo '%s" % targetIPV6 +"%"+"%s     ev1' > ~/.hosts" % source.intf().name)
        # source.cmd("export HOSTALIASES=~/.hosts")
        
        ### IPV4
        if not use_ipv6:
            # CLI EXAMPLE
            # sh ovs-ofctl add-flow s1 dl_src=00:00:00:00:00:01,dl_dst=00:00:00:00:00:03,actions=mod_nw_dst:10.0.0.3,output:3
            # sh ovs-ofctl add-flow s1 dl_src=00:00:00:00:00:03,dl_dst=00:00:00:00:00:01,actions=mod_nw_src:10.0.0.2,output:1
            # sh ovs-ofctl add-flow s1 dl_type=0x806,nw_proto=1,actions=flood

            #  PART 1 fake communication with source : IPV4 ONLY
            # mac 10.0.0.2 is already linked to (3) by mim arpspoof
            # malicious node changes the ip
            # source -> mim, mim
            self.cmd("ovs-ofctl", "add-flow", "s1", "dl_src=%s,dl_dst=%s,actions=mod_nw_dst:%s,output:3" % (source.MAC(), mim.MAC(), mim.IP()))
            # mim -> target, source
            self.cmd("ovs-ofctl", "add-flow", "s1", "dl_src=%s,dl_dst=%s,actions=mod_nw_src:%s,output:1" % (mim.MAC(), source.MAC(), target.IP()))

            # PART 2 fake communication with target : IPV4 ONLY
            # source -> mim, mim
            self.cmd("ovs-ofctl", "add-flow", "s1", "dl_src=%s,dl_dst=%s,actions=mod_nw_dst:%s,output:3" % (target.MAC(), mim.MAC(), mim.IP()))
            # mim -> target, source
            self.cmd("ovs-ofctl", "add-flow", "s1", "dl_src=%s,dl_dst=%s,actions=mod_nw_src:%s,output:2" % (mim.MAC(), target.MAC(), source.IP()))
            
            # flood the arp relys to all nodes who requested them
            self.cmd("ovs-ofctl", "add-flow", "s1", "dl_type=0x806,nw_proto=1,actions=flood")
        ### IPV6
        else:
            # ICMPv6 messages are sent in the network to understand the mac addresses of the others

            # INCLUDE UDP MESSAGES

            # PART 1 fake communication with source : IPV6 ONLY (0x86dd)
            # direction: source -> any
            # action: change ip to mim and send flow to mim
            self.cmd("ovs-ofctl", "add-flow", "s1", "dl_type=0x86dd,ipv6_src=%s,in_port=1,actions=set_field:%s-\>ipv6_dst,output:3" % (sourceIPV6, mimIPV6))
            # messages generated by parasite6 need redirection to source
            # direction: target (generated by mim) -> source
            # action: send flow to source
            self.cmd("ovs-ofctl", "add-flow", "s1", "dl_type=0x86dd,ipv6_dst=%s,in_port=3,actions=set_field:%s-\>ipv6_src,output:1" % (sourceIPV6, targetIPV6))

            # PART 2 fake communication with target : IPV6 ONLY (0x86dd)
            # direction: target -> any
            # action: change ip to mim and send flow to mim

            # udp = nw_proto 17, fix: 
            self.cmd("ovs-ofctl", "add-flow", "s1", "--strict", "priority=1,dl_type=0x86dd,ipv6_src=%s,in_port=2,actions=set_field:%s-\>ipv6_dst,output:3" % (targetIPV6, mimIPV6))
            # TODO: INSTEAD OF THIS FLOW, THE MESSAGE ITSELF MAY BE CHANGED
            # self.cmd("ovs-ofctl", "add-flow", "s1", "--strict", "priority=2,dl_type=0x86dd,ipv6_src=%s,in_port=2,nw_proto=6,actions=mod_tp_dst:%d,output:3" % (targetIPV6, 20000)) # so that we know the destination port
            self.cmd("ovs-ofctl", "add-flow", "s1", "--strict", "priority=3,dl_type=0x86dd,ipv6_src=%s,in_port=2,nw_proto=17,tp_dst=%d,actions=mod_tp_dst:%d,output:3" % (targetIPV6, 15118, 15119))
            # self.cmd("ovs-ofctl", "add-flow", "s1", "dl_type=0x86dd,ipv6_src=%s,in_port=3,nw_proto=17,tp_src=%d,actions=output:1" % (mimIPV6, 15120))
            # # messages generated by parasite6 need redirection to source
            # # direction: source (generated by mim) -> target
            # # action: send flow to target
            self.cmd("ovs-ofctl", "add-flow", "s1", "dl_type=0x86dd,ipv6_dst=%s,in_port=3,actions=set_field:%s-\>ipv6_src,output:2" % (targetIPV6, sourceIPV6))

            
        print(self.cmd("ovs-ofctl", "dump-flows", "s1"))

class MiMNode( Node ):
    """Basic node class for man in the middle."""
    def __init__( self, name, source=None, inNamespace=True, **params ):
        Node.__init__(  self, name, inNamespace=True, **params  )

    def start_spoof( self, source=None, target=None, use_ipv6=True ):
        # IPV4
        # cli example
        # arpspoof -i h3-eth0 -c own -t 10.0.0.1 10.0.0.2 2>/dev/null 1>/dev/null & # send arp reply
        if not use_ipv6:
            if source != None and target != None:
                # fake MAC in arp table of source
                self.cmd("arpspoof", "-i %s" % self.intf().name, "-t %s" % source.IP(), "%s" % target.IP(), " 2>/dev/null 1>/dev/null &")
                # fake MAC in arp table of target
                self.cmd("arpspoof", "-i %s" % self.intf().name, "-t %s" % target.IP(), "%s" % source.IP(), " 2>/dev/null 1>/dev/null &")
        # IPV6
        else:
            self.cmd('echo 1 > /proc/sys/net/ipv6/conf/all/forwarding')
            self.cmd('ip6tables -I OUTPUT -p icmpv6 --icmpv6-type redirect -j DROP')
            self.cmd('parasite6 %s' % self.intf().name, "2>/dev/null 1>/dev/null &")
