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
from mininet.moduledeps import pathCheck
from mininet.node import Node


class Electric(Node):
    """A basic Node class with the support for V2G communication"""

    def __init__(self, name, path=None, **kwargs):
        # double check if java is available (it is needed for RiseV2G)
        pathCheck('java')
        # set the path of RiseV2G
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

        # initialize the folder for the RiseV2G copy
        self.folder = ""

        # cleanup of the generated folder
        def cleaner():
            print('*** Cleaning up the mess')
            popen("rm -rd {}*".format(self.FOLDER_PREFIX))

        atexit.register(cleaner)

        # set the available charging modes
        self.modes_available = ["AC_single_phase_core", "AC_three_phase_core", "DC_core", "DC_extended",
                                "DC_combo_core", "DC_unique"]
        # available payment systems
        self.payment_available = ["Contract", "ExternalPayment"]

    def intfSetup(self, intfName=None):
        """Sets the intfName on the .properties file.
        :param intfName: the intfName to be setted. """

        return self.setProperty('network.interface', intfName)

    def setProperty(self, prop_name, prop_value):
        """
        Set a specified property.
        :param prop_name: the name of the property
        :param prop_value: the new value of the property
        :return True if all ok, False if exceptions occurs """

        # check and set the prefix values
        if "ev" in self.folder:
            prefix = "EVCC"
        else:
            prefix = "SECC"

        try:
            f = fileinput.input([self.folder + "/" + prefix + "Config.properties"], inplace=True)
            for line in f:
                if line.strip().startswith(prop_name):
                    line = '{} = {}\n'.format(prop_name, prop_value)
                sys.stdout.write(line)
            f.close()
            return True
        except Exception as e:
            print("*** Problem in writing properties ({}).".format(e))
            return False

    def printProperties(self):

        # to decide if it is an ev or se it check the path;
        # if you change the default folder it is better to change this stuff
        if "ev" in self.folder:
            prefix = "EVCC"
        else:
            prefix = "SECC"

        f = fileinput.input([self.folder + "/" + prefix + "Config.properties"], mode='r')
        for line in f:
            if not line.strip().startswith('#'):
                print(line)
        f.close()




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
        self.intfSetup(intf)

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

    def setEnergyTransferRequested(self, req):
        """ Set the energy transfer modes
        :param req: the requested energy transfer mode
        """

        if isinstance(req, str):
            # check if the mode is available
            if req in self.modes_available:
                return self.setProperty('energy.transfermode.requested', req)
            else:
                print("*** Modes available: {}".format(self.modes_available))
                return False
        else:
            print("*** You must provide a sting, a list or a set.")
            return False


class SE(Electric):
    """An EV Supply Equipment (EVSE) is a Node which can
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

    def startCharge(self, in_xterm=True, intf=None):
        """
        Spawn an xterm and start the listening phase in it.
        It is not possible to launch it without xterm because otherwise sometimes it randomly crashes.
        :param intf: Interface to listen for charging requests. If None, default is used.
        :returns A popen xterm instance. To be appended to "net.terms" to assure a correct close on exit."""

        # setting the interface (default: default interface)
        if intf is None:
            intf = self.intf().name
        self.intfSetup(intf)

        print("*** Starting waiting for EVs...")
        if in_xterm:
            # run inside an xterm. You must append the return value to net.terms to terminal on exit.
            command = "cd ./{}; java -jar rise-v2g-secc-*.jar; bash -i".format(self.folder)
            # this return a list of just one xterm, so [0] is needed
            self.proc = makeTerm(self, cmd="bash -i -c '{}'".format(command))[0]
        else:
            # TODO: test this
            self.proc = self.popen("cd ./{}; java -jar rise-v2g-secc-*.jar".format(self.folder), shell=True)
            # print the stdout to the CLI at the start of the charging process
            proc_stdout = self.proc.communicate(timeout=15)[0].strip()
            print(proc_stdout)
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

    def setEnergyTransferModes(self, modes):
        """ Set the energy transfer modes
        :param modes: the modes available
        """

        if isinstance(modes, list) or isinstance(modes, set):
            # check if the modes are available
            if all(m in self.modes_available for m in modes):
                return self.setProperty('energy.transfermodes.supported', ', '.join(modes))
            else:
                print("*** Modes available: {}".format(self.modes_available))
        elif isinstance(modes, str):
            # check if the mode is available
            if modes in self.modes_available:
                return self.setProperty('energy.transfermodes.supported', modes)
            else:
                print("*** Modes available: {}".format(self.modes_available))
                return False
        else:
            print("*** You must provide a sting, a list or a set.")
            return False

    def setChargingFree(self, free=True):
        """ Set if the nergy transfer is free or not
        :param free: charging type (True for free charging, False otherwise)
        """

        if free:
            return self.setProperty('energy.transfermodes.supported', 'true')
        else:
            return self.setProperty('energy.transfermodes.supported', 'false')

    def setPaymentOption(self, payments):
        """ Set if the nergy transfer is free or not
        :param payments: payment modes to be supported
        """

        if isinstance(payments, list) or isinstance(payments, set):
            # check if the payments are available
            if all(m in self.payment_available for m in payments):
                return self.setProperty('authentication.modes.supported', ', '.join(payments))
            else:
                print("*** Payments available: {}".format(self.payment_available))
        elif isinstance(payments, str):
            # check if the mode is available
            if payments in self.payment_available:
                return self.setProperty('authentication.modes.supported', payments)
            else:
                print("*** Payments available: {}".format(self.payment_available))
                return False
        else:
            print("*** You must provide a sting, a list or a set.")
            return False
