"""
Additional Nodes for Vehicle to Grid (V2G) communication
"""

from os import popen
from subprocess import Popen
import signal
import shlex
from mininet.node import Node
from mininet.moduledeps import pathCheck
from mininet.link import Intf
import sys
import fileinput
import atexit # clean the mess on exit
# to generate the random prefix for folders
import random, string
from mininet.net import Mininet

class Electric( Node ):
    """A basic Node class with the support for V2G communication"""


    def __init__( self, name, path=None, **kwargs ):
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
        if "No such file or directory" in popen('ls ' + self.RISE_PATH).read():
            exit("**** Fatal error: directory %s not found. Select the right folder which contains the needed jar files.")
        #TODO: check for the specific jar files

        Node.__init__(self, name, **kwargs)

        # setup a random prefix for folders (to better cleanup everything in the end)
        self.FOLDER_PREFIX = ''.join(random.choice(string.ascii_lowercase) for i in range(4))

        # cleanup of the generated folder
        def cleaner():
            print('*** Cleaning up the mess')
            popen("rm -rd "+self.FOLDER_PREFIX+"*")

        atexit.register(cleaner)


    def intfSetup(self, folder, intfName=None):
        "Set the intfName on the .properties file"
        # to decide if it is an ev or se it check the path;
        # if you change the default folder it is better to change this stuff
        if "ev" in folder:
            prefix="EVCC"
        else:
            prefix="SECC"

        for line in fileinput.input([folder+"/"+prefix+"Config.properties"], inplace=True):
            if line.strip().startswith('network.interface'):
                line = 'network.interface = '+intfName+'\n'
            sys.stdout.write(line)



class EV( Electric ):
    """An Electric Vehicle (EV) is a Node containing all the
    necessary to be able to start the communication from its
    EV Communication Controller (EVCC) with a SECC to require charging service """

    def __init__(self, name, path=None, **kwargs):
        self.name=str(name)
        Electric.__init__( self, self.name, path, **kwargs)

        self.folder = self.FOLDER_PREFIX + "_ev_" + self.name
        self.cmd("mkdir "+self.folder)
        self.cmd("cp "+self.RISE_PATH+"/EVCCConfig.properties "+self.folder+"/")
        # this cp can resist to update of risev2g but you must have only one version
        self.cmd("cp "+self.RISE_PATH+"/rise-v2g-evcc-*.jar "+self.folder+"/")
        # cd into the right folder
        self.cmd("cd ./"+self.folder)


    def charge(self, background=False, intf=None):
        """Starting the charging process"""
        print("*** Looking for EVSE and start charging...")

        # setting the interface (default: default interface)
        if intf is None:
            intf = self.intf().name
        self.intfSetup(self.folder, intf)

        p = self.popen("cd ./"+self.folder+"; java -jar rise-v2g-evcc-*.jar", shell=True)
        if not background:
            proc_stdout = p.communicate()[0].strip()
            print(proc_stdout)



class SE( Electric ):
    """An EV Supply Equipment (EVSE) is a Node containing which can
    provide charging services to an EV by communication using the
    Supply Equipment Communication Controller (SECC) """

    def __init__(self, name, path=None, **kwargs):
        self.name=str(name)
        Electric.__init__( self, self.name, path, **kwargs)

        self.folder = self.FOLDER_PREFIX + "_se_" + self.name
        self.cmd("mkdir "+self.folder)
        self.cmd("cp "+self.RISE_PATH+"/SECCConfig.properties "+self.folder+"/")
        # this cp can resist to update of risev2g but you must have onyl one version
        self.cmd("cp "+self.RISE_PATH+"/rise-v2g-secc-*.jar "+self.folder+"/")
        # cd into the right folder
        self.cmd("cd ./"+self.folder)


    def start(self, background=False, intf=None):
        """ Start the listening phase.
            backgroud: True if you want to do other things from the CLI"""

        # setting the interface (default: default interface)
        if intf is None:
            intf = self.intf().name
        self.intfSetup(self.folder, intf)

        # better promising approach, not yet perfet (TODO)
        print("*** Starting waiting for EVs...")
        self.p = self.popen("cd ./"+self.folder+"; java -jar rise-v2g-secc-*.jar", shell=True)
        if not background:
            proc_stdout = self.p.communicate()[0].strip()
            print(proc_stdout)

    def state(self):
        """ Print and return the state of a backgrounded process"""
        if hasattr(self, 'p'):
            state = self.p.poll()
            if state is None:
                print("* Running!")
            else:
                print("* Stopped (State: {}).".format(state))
            return state
        else:
            print("* The process does not exist. Call .start() first.")
            return None


    def stop(self):
        # TODO: maybe can be usefull to print stdout
        if hasattr(self, 'p'):
            state = self.p.terminate() #send_signal(signal.SIGINT)
            print("* Stopped successfully.")
        else:
            print("* The process does not exist. Call .start() first.")
            return None
