#!/usr/bin/env python3

"""
This is a NodeServer for Polyglot v2 written in Python3
It will contain many different custom objects that will connect random technology.
-----------------------------------------------------------------------------------
Import the polyglot interface module.
Also using the broadlink module from: https://github.com/mjg59/python-broadlink
        The MIT License (MIT)
        Copyright (c) 2014 Mike Ryan
        Copyright (c) 2016 Matthew Garrett 
"""
try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
import broadlink

import sys
import json
# Import the Dictionary that contains all nodes and RFCodes for each. (RFCodes.py)
from RFCodes import RFCodes
#import logging
#import urllib3

"""
polyinterface has a LOGGER that is created by default and logs to:
logs/debug.log
You can use LOGGER.info, LOGGER.warning, LOGGER.debug, LOGGER.error levels as needed.
"""
LOGGER = polyinterface.LOGGER
# IF you want a different log format than the current default
#polyinterface.LOG_HANDLER.set_log_format('%(asctime)s %(threadName)-10s %(name)-18s %(levelname)-8s %(module)s:%(funcName)s: %(message)s')


"""
Open the server.json file and collect the data within it. 
"""
with open('server.json') as data:
    SERVERDATA = json.load(data)
    data.close()
try:
    VERSION = SERVERDATA['credits'][0]['version']
    LOGGER.info('Broadlink Poly Version {} found.'.format(VERSION))
except (KeyError, ValueError):
    LOGGER.info('Broadlink Poly Version not found in server.json.')
    VERSION = '0.0.0'

""" Define My MultiPass! Controller Node Class"""
class Controller(polyinterface.Controller):
    """
    The Controller Class is the primary node from an ISY perspective. It is a Superclass
    of polyinterface.Node so all methods from polyinterface.Node are available to this
    class as well.

    Class Variables:
    self.nodes: Dictionary of nodes. Includes the Controller node. Keys are the node addresses
    self.name: String name of the node
    self.address: String Address of Node, must be less than 14 characters (ISY limitation)
    self.polyConfig: Full JSON config dictionary received from Polyglot for the controller Node
    self.added: Boolean Confirmed added to ISY as primary node
    self.config: Dictionary, this node's Config

    Class Methods (not including the Node methods):
    start(): Once the NodeServer config is received from Polyglot this method is automatically called.
    addNode(polyinterface.Node, update = False): Adds Node to self.nodes and polyglot/ISY. This is called
        for you on the controller itself. Update = True overwrites the existing Node data.
    updateNode(polyinterface.Node): Overwrites the existing node data here and on Polyglot.
    delNode(address): Deletes a Node from the self.nodes/polyglot and ISY. Address is the Node's Address
    longPoll(): Runs every longPoll seconds (set initially in the server.json or default 10 seconds)
    shortPoll(): Runs every shortPoll seconds (set initially in the server.json or default 30 seconds)
    query(): Queries and reports ALL drivers for ALL nodes to the ISY.
    getDriver('ST'): gets the current value from Polyglot for driver 'ST' returns a STRING, cast as needed
    runForever(): Easy way to run forever without maxing your CPU or doing some silly 'time.sleep' nonsense
                  this joins the underlying queue query thread and just waits for it to terminate
                  which never happens.
    """
    mybroadlink = None

    def __init__(self, polyglot):
        """
        Optional.
        Super runs all the parent class necessities. You do NOT have
        to override the __init__ method, but if you do, you MUST call super.
        """
        super().__init__(polyglot)
        self.name = 'MultiPass Controller'
        # This can be used to call your function everytime the config changes
        # But currently it is called many times, so not using.
        # self.poly.onConfig(self.process_config)

    def start(self):
        """
        Optional.
        Polyglot v2 Interface startup done. Here is where you start your integration.
        This will run, once the NodeServer connects to Polyglot and gets it's config.
        In this example I am calling a connect method. While this is optional,
        this is where you should start. No need to Super this method, the parent
        version does nothing.
        """
        LOGGER.info('Starting MultiPass NodeServer version {}'.format(VERSION))
        
        # Show values on startup if desired.
        self.setDriver('ST', 1)
        LOGGER.debug('MultiPass. ST=%s', self.getDriver('ST'))
        #self.heartbeat(0)
        #self.check_params()
        #self.set_debug_level(self.getDriver('GV1'))
        #self.poly.add_custom_config_docs("<b>This is some custom config docs data</b>")
        self.connectbl()
        LOGGER.info('MultiPass Start complete')
    '''
    def shortPoll(self):
        """
        Optional.
        This runs every 10 seconds. You would probably update your nodes either here
        or longPoll. No need to Super this method the parent version does nothing.
        The timer can be overriden in the server.json.
        """
        LOGGER.debug('shortPoll')
        for node in self.nodes:
            if node != self.address:
                self.nodes[node].shortPoll()
    '''
    '''
    def longPoll(self):
        """
        Optional.
        This runs every 30 seconds. You would probably update your nodes either here
        or shortPoll. No need to Super this method the parent version does nothing.
        The timer can be overriden in the server.json.
        """
        LOGGER.debug('longPoll')
    '''
    def connectbl(self, command=None):
        
        # First Try to Auth and see if connection is already established.
        if self.mybroadlink != None:
            result = self.mybroadlink.auth()
            if result: 
                self.setDriver('GV0', 1)
                LOGGER.info('Previous Connection Authenticated to Broadlink @ 192.168.2.16.')
                return
            else:
                self.setDriver('GV0', 0)
        
        # There will be many objects used in the MultiPass! Node Server this is the first. 
        # Attempt to connect to the known Broadlink RM Pro+
        self.mybroadlink = self.connect_broadlink()

        # Once connected create the nodes defined in RFCodes.py.
        if self.mybroadlink != None: self.populate_broadlink()      

    def connect_broadlink(self):
        """
        Connect to the known Broadlink device and Authenticate.
        device = gendevice(devtype, host, mac, name=name, cloud=cloud)
        devtype = 0x27a9 = (rm, "RM pro+", "Broadlink") <-- from broadlink.__init__.py 
        host = 192.168.2.15 (DHCP reservation), port 80
        mac = 78:0f:77:63:5a:25 Convert to bytes = b'x\x0fwcZ%'
        """
        d = broadlink.gendevice(0x27a9,('192.168.2.16', 80), b'x\x0fwcZ%', name='Apt', cloud=False)

        try:
            result = d.auth()
            self.setDriver('GV0', 1)
            LOGGER.info('Successful Connection and Authentication to Broadlink @ 192.168.2.16.') 
        except:
            self.setDriver('GV0', 0)
            LOGGER.info('Unable to connect to Broadlink @ 192.168.2.16.') 
        return d if result else None
    
    def populate_broadlink(self):
        """
        Once connected and authenticated to broadlink verify nodes match dictionary.
        """
        for node in RFCodes.keys():
            # Create Mac address from Device Name
            address = node.encode('utf-8').hex()
            if len(address) < 12: 
                address = address.zfill(12) # Pad to 12 Hex Characters
            else:
                address = address[:12] # Trim to 12 Hex Characters
            if not address in self.nodes:
                self.addNode(omniamotor(self, self.address, address, node, self.mybroadlink),update=True)        
                self.setDriver('GV1', int(self.getDriver('GV1')) + 1 )

    def stop(self):
        try:
            del self.broadlink
        except:
            pass
        self.setDriver('GV0', 0)
        LOGGER.debug('Broadlink Link stopped. GV0=%s', self.getDriver('GV0'))
        self.setDriver('ST', 0)        
        LOGGER.debug('MultiPass NodeServer stopped. ST=%s', self.getDriver('ST'))

    id = 'controller'

    commands = { 'CONNECTBL': connectbl }

    drivers = [
        {'driver': 'ST', 'value': 1, 'uom': 2},
        {'driver': 'GV0', 'value': 0, 'uom': 2},
        {'driver': 'GV1', 'value': 0, 'uom': 56} ] 

class omniamotor(polyinterface.Node):
    """
    This is the class that all the Nodes will be represented by. You will add this to
    Polyglot/ISY with the controller.addNode method.

    Class Variables:
    self.primary: String address of the Controller node.
    self.parent: Easy access to the Controller Class from the node itself.
    self.address: String address of this Node 14 character limit. (ISY limitation)
    self.added: Boolean Confirmed added to ISY

    Class Methods:
    start(): This method is called once polyglot confirms the node is added to ISY.
    setDriver('ST', 1, report = True, force = False):
        This sets the driver 'ST' to 1. If report is False we do not report it to
        Polyglot/ISY. If force is True, we send a report even if the value hasn't changed.
    reportDrivers(): Forces a full update of all drivers to Polyglot/ISY.
    query(): Called when ISY sends a query request to Polyglot for this specific node
    """
    def __init__(self, controller, primary, address, name, dev):
        """
        Optional.
        Super runs all the parent class necessities. You do NOT have
        to override the __init__ method, but if you do, you MUST call super.

        :param controller: Reference to the Controller class
        :param primary: Controller address
        :param address: This nodes address
        :param name: This nodes name
        :param rfc: The Up / Down / Stop byte codes for RF Packets.
        """
        super().__init__(controller, primary, address, name)
        self.ctrl = controller
        self.pri = primary
        self.name = name
        self.dev = dev
        LOGGER.info('OmniaBlind Node Created {}.'.format(self.name))
        self.setDriver('ST', 1)

    def shortPoll(self):
        LOGGER.debug('shortPoll')
        """
        if int(self.getDriver('ST')) == 1:
            self.setDriver('ST',0)
        else:
            self.setDriver('ST',1)
        """
        LOGGER.debug('Omnia %s: ST=%s',self.name,self.getDriver('ST'))

    def longPoll(self):
        LOGGER.debug('longPoll')

    def start(self):
        """
        Optional.
        This method is run once the Node is successfully added to the ISY
        and we get a return result from Polyglot. Only happens once.
        """
        '''
        LOGGER.debug('%s: get ST=%s', self.lpfx, self.getDriver('ST'))
        self.setDriver('ST', 1)
        LOGGER.debug('%s: get ST=%s', self.lpfx, self.getDriver('ST'))
        self.setDriver('ST', 0)
        LOGGER.debug('%s: get ST=%s', self.lpfx, self.getDriver('ST'))
        self.setDriver('ST', 1)
        LOGGER.debug('%s: get ST=%s', self.lpfx, self.getDriver('ST'))
        self.setDriver('ST', 0)
        LOGGER.debug('%s: get ST=%s', self.lpfx, self.getDriver('ST'))
        self.http = urllib3.PoolManager()
        '''
        self.setDriver('ST', 1)

    def cmd_up(self,command):
        LOGGER.info('Broadlink RM device {}:{}.'.format("TEST-UP",command))
        #LOGGER.info('RFCode Lookup for {}:{}.'.format(self.name,RFCodes[self.name][1]))
        self.dev.send_data(RFCodes[self.name][1])

    def cmd_down(self,command):
        LOGGER.info('Broadlink RM device {}:{}.'.format("TEST-DOWN",command))
        #LOGGER.info('RFCode Lookup for {}:{}.'.format(self.name,RFCodes[self.name][-1]))
        self.dev.send_data(RFCodes[self.name][-1])

    def cmd_stop(self,command):
        LOGGER.info('Broadlink RM device {}:{}.'.format("TEST-STOP", command))
        #LOGGER.info('RFCode Lookup for {}:{}.'.format(self.name,RFCodes[self.name][0]))
        self.dev.send_data(RFCodes[self.name][0])

    '''
    def query(self,command=None):
        """
        Called by ISY to report all drivers for this node. This is done in
        the parent class, so you don't need to override this method unless
        there is a need.
        """
        self.reportDrivers()
    '''

    #Hints See: https://github.com/UniversalDevicesInc/hints
    #hint = [1,2,3,4]
    drivers = [{'driver': 'ST', 'value': 0, 'uom': 2}]
    """
    Optional.
    This is an array of dictionary items containing the variable names(drivers)
    values and uoms(units of measure) from ISY. This is how ISY knows what kind
    of variable to display. Check the UOM's in the WSDK for a complete list.
    UOM 2 is boolean so the ISY will display 'True/False'
    """
    id = 'omniamotor'
    """
    id of the node from the nodedefs.xml that is in the profile.zip. This tells
    the ISY what fields and commands this node has.
    """
    commands = {
                    'BUP': cmd_up,
                    'BDOWN': cmd_down,
                    'BSTOP': cmd_stop
                }
    """
    This is a dictionary of commands. If ISY sends a command to the NodeServer,
    this tells it which method to call. DON calls setOn, etc.
    """


if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('PythonTemplate')
        """
        Instantiates the Interface to Polyglot.
        The name doesn't really matter unless you are starting it from the
        command line then you need a line Template=N
        where N is the slot number.
        """
        polyglot.start()
        """
        Starts MQTT and connects to Polyglot.
        """
        control = Controller(polyglot)
        """
        Creates the Controller Node and passes in the Interface
        """
        control.runForever()
        """
        Sits around and does nothing forever, keeping your program running.
        """
    except (KeyboardInterrupt, SystemExit):
        LOGGER.warning("Received interrupt or exit...")
        """
        Catch SIGTERM or Control-C and exit cleanly.
        """
        polyglot.stop()
    except Exception as err:
        LOGGER.error('Excption: {0}'.format(err), exc_info=True)
    sys.exit(0)

