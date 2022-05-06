#!/usr/bin/env python3

import polyinterface
import sys
import os
import RPi.GPIO as GPIO
import json
import glob
import time
import datetime
import os,subprocess
from subprocess import call
from w1thermsensor import W1ThermSensor


LOGGER = polyinterface.LOGGER

BRCM_PORTS = {'port2':2, 'port3':3,'port17':17,'port27':27,'port22':22,'port10':10,'port9':9,
              'port11':11,'port5':5,'port6':6,'port13':13,'port19':19,'port26':26,'port14':14,
              'port15':15,'port18':18,'port23':23,'port24':24,'port25':25,'port8':8, 'port7':7,
              'port12':12,'port16':16,'port20':20,'port20':21} # port4 removed as used for temp sensor
PORT_MODE = {0:'GPIO.OUT', 1:'GPIO.IN', -1:'GPIO.UNKNOWN'}


class Controller(polyinterface.Controller):
    def __init__(self, polyglot):
        super().__init__(polyglot)
        LOGGER.info('_init_')
        self.name = 'RPi Temp_IO_Control'
        self.address = 'rpitempIO'
        self.primary = self.address
        self.hb = 0
        self.internal= []
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False) 
        self.INPUT_PINS = {}
        self.OUTPUT_PINS = {}
                
    def start(self):
        LOGGER.info('Start  TempSensors')
        self.removeNoticesAll()
        try:
            os.system('modprobe w1-gpio')
            os.system('modprobe w1-therm')
            self.setDriver('ST', 1)
        except:
            LOGGER.debug('modprobe OS calls not successful')
            self.addNotice('TempSensor detection not successful')
            self.setDriver('ST', 0)
        LOGGER.debug('start - Temp Sensor controller')

        try:
            self.mySensors = W1ThermSensor()
            self.nbrSensors = len(self.mySensors.get_available_sensors())
            LOGGER.info( str(self.nbrSensors) + ' Sensors detected')
            self.discover()
            self.setDriver('ST', 1)
        except:
            LOGGER.info('ERROR initializing w1thermSensors ')
            self.setDriver('ST', 0)
            self.stop()  

        self.check_params(self)
        self.discover()         
        self.updateInfo()
        self.reportDrivers()
 

    def stop(self):
        LOGGER.debug('stop - Cleaning up Temp Sensors & GPIO')

    def heartbeat(self):
        LOGGER.debug('heartbeat: hb={}'.format(self.hb))
        if self.hb == 0:
            self.reportCmd("DON",2)
            self.hb = 1
        else:
            self.reportCmd("DOF",2)
            self.hb = 0

    def shortPoll(self):
        LOGGER.debug('Controller shortPoll')
        for node in self.nodes:
             if node != self.address:
                self.nodes[node].updateInfo()
                   
    def longPoll(self):
        LOGGER.debug('Controller longPoll')
        self.heartbeat()
        for node in self.nodes:
            if node != self.address:
                self.nodes[node].updateInfo()
        
    def updateInfo(self):
        LOGGER.debug('Update Info CTRL')
        pass

    def query(self, command=None):
        LOGGER.debug('TOP querry')

        for node in self.nodes:
            self.nodes[node].updateInfo()
            #self.nodes[node].update24Hqueue()

    def discover(self, command=None):
        LOGGER.debug('discover')
 
        count = 0
        for mySensor in self.mySensors.get_available_sensors():
            count = count+1
            currentSensor = mySensor.id.lower() 
            LOGGER.info(currentSensor+ 'Sensor Serial Number Detected - use Custom Params to rename')
            address = 'rpitemp'+str(count)
            # check if sensor serial number exist in custom parapms and then replace name
            if currentSensor in self.polyConfig['customParams']:
               LOGGER.debug('A customParams name for sensor detected')
               name = self.polyConfig['customParams'][currentSensor]
            else:
               LOGGER.debug('Default Naming')
               name = 'Sensor'+str(count)
            LOGGER.debug( address + ' '+ name + ' ' + currentSensor)
            if not address in self.nodes:
               self.addNode(TEMPsensor(self, self.address, address, name, currentSensor), update=False)
               LOGGER.debug('Sensor Node Created')
            else:
                self.addNode(TEMPsensor(self, self.address, address, name, currentSensor), update=True)
                LOGGER.debug('Sensor Node Updated')
        # GPIO Pins
        LOGGER.debug('OUT_PINS: '+str(self.OUTPUT_PINS))
  
        for out_pin in self.OUTPUT_PINS :
            LOGGER.info( ' gpio output :' + str(out_pin))
            address = 'outpin'+  str(out_pin)
            name = str(self.OUTPUT_PINS[out_pin]) 
            LOGGER.debug( address + ' ' + name + ' ' + str(out_pin))
            if not address in self.nodes:
               LOGGER.debug('GPIO out'+ self.address +' ' + address + ' ' + name  )
               self.addNode(GPOUTcontrol(self, self.address, address, name, out_pin), update=False)
               GPIO.setup(int(out_pin), GPIO.OUT) 
            else:
               self.addNode(GPOUTcontrol(self, self.address, address, name, out_pin), update=True)
               GPIO.setup(int(out_pin), GPIO.OUT) 

        LOGGER.debug('IN_PINS: '+str(self.INPUT_PINS))
        for in_pin in self.INPUT_PINS :
            LOGGER.info( ' gpio input :' + str(in_pin))
            address = 'inpin'+  str(in_pin)
            name = str(self.INPUT_PINS[in_pin]) 
            LOGGER.debug( address + ' ' + name + ' ' + str(in_pin))
            if not address in self.nodes:
               LOGGER.debug('GPIO in'+ self.address +' ' + address + ' ' + name  )
               self.addNode(GPINcontrol(self, self.address, address, name, in_pin), update=False)
               GPIO.setup(int(in_pin), GPIO.IN)   
            else:
               self.addNode(GPINcontrol(self, self.address, address, name, in_pin), update=True)
               GPIO.setup(int(in_pin), GPIO.IN)  


    def check_params(self, command=None):
        LOGGER.debug('Check Params')
        LOGGER.debug(str(self.polyConfig['customParams'])) 
        params = {}
        count = 0
        self.removeNoticesAll()
        self.addNotice('To add IOpin use portN as Key and IN:name or OUT:name as value to define ports')
        self.addNotice('N is BRCM port number (4 use for temp semnsor)')     
        for mySensor in self.mySensors.get_available_sensors():
            count = count+1
            currentSensor = mySensor.id.lower() 
            if not(currentSensor in self.polyConfig['customParams']):
                params[currentSensor]=['NoName'+str(count)]
        if not(params == {}):
            self.addCustomParam(params)
        LOGGER.debug(str(params))
    
        for customP in self.polyConfig['customParams']:
            LOGGER.debug(str(customP))
            if customP.lower() in BRCM_PORTS:
                PortNumber = BRCM_PORTS[customP.lower()]
                PortDef = self.polyConfig['customParams'][customP]
                PortInfo = PortDef.split(':',1)
                LOGGER.debug(str(PortNumber) + ' ' + str(PortInfo))
                if PortInfo[0].lower() == 'in':
                    self.INPUT_PINS.update({PortNumber:PortInfo[1]})
                    LOGGER.debug('Input Pin: '+str(PortNumber) + ' ' + str(PortInfo[1]))
                elif PortInfo[0].lower() == 'out':
                    self.OUTPUT_PINS.update({PortNumber:PortInfo[1]})
                    LOGGER.debug('Output Pin: '+str(PortNumber) + ' ' + str(PortInfo[1]))

                else:
                    self.addNotice('Must use IN or OUT:name(port 4 is used for temp sensors)')                    
        self.saveCustomData(self.polyConfig['customParams'])
        


    id = 'RPISPA'
    commands = {'DISCOVER': discover}
    drivers = [{'driver': 'ST', 'value': 1, 'uom': 2}]


class GPOUTcontrol(polyinterface.Node):
    def __init__(self, controller, primary, address, name, opin):
        super().__init__(controller, primary, address, name)
        self.opin = opin
        LOGGER.info('init GPIOControl')


    def start(self):
        LOGGER.info('start GPIOControl')
        self.setDriver('GV0', GPIO.input(self.opin))
        
    
    def stop(self):
        LOGGER.info('stop GPIOControl')
        GPIO.cleanup()

    def shortPoll(self):
        LOGGER.info('shortpoll GPIOControl')
        self.updateInfo()


    def longPoll(self):
        LOGGER.info('longpoll GPIOControl')
        self.updateInfo()
        

    def ctrlOutput(self, command):
        LOGGER.info('ctrlRelay GPIOControl')
        cmd = command.get('cmd')
        LOGGER.debug(str(cmd))
        if cmd in ['OUT_ON', 'OUT_OFF']:
           if cmd == 'OUT_ON':
              GPIO.output(self.opin, GPIO.HIGH)
              self.setDriver('GV0', 1)
           else:
              GPIO.output(self.opin, GPIO.LOW)  
              self.setDriver('GV0', 0)
        else:
              self.setDriver('GV0', 2)
        self.reportDrivers()

              
    def query(self, command=None):
        LOGGER.debug('GPIO querry')
        self.updateInfo()

    def updateInfo(self, command=None):
        LOGGER.debug('GPOUT UpdateInfo')
        self.setDriver('GV0', GPIO.input(self.opin))
        self.reportDrivers()

    drivers = [{'driver': 'GV0', 'value': 2, 'uom': 25}
              ] 

    commands = { 'OUT_ON'  : ctrlOutput,
                 'OUT_OFF' : ctrlOutput,
                 'UPDATE'  : updateInfo}

    id = 'PINOUT'

class GPINcontrol(polyinterface.Node):
    def __init__(self, controller, primary, address, name, inpin):
        super().__init__(controller, primary, address, name)
        self.inpin = inpin
        LOGGER.info('init GPIOControl')
        self.waterLevel  = 2 # Unknown
        self.measAverage = 10
        self.lastNMeas = []

    def start(self):
        LOGGER.info('start GPIOControl')
        self.setDriver('GV0', self.waterLevel )
        self.lastNMeas.append(GPIO.input(self.inpin))
        if len(self.lastNMeas) >= self.measAverage: # should only reach equal but to be safe
            self.avgLow = sum(self.lastNMeas)/len(self.lastNMeas)
            
    def stop(self):
        LOGGER.info('stop GPIOControl')
        GPIO.cleanup()

    def shortPoll(self):
        LOGGER.info('shortpoll GPIOControl')      
        self.updateInfo()


    def longPoll(self):
        LOGGER.info('longpoll GPIOControl')
        #self.updateInfo()
        

              
    def query(self, command=None):
        LOGGER.debug('GPIO querry')
        self.updateInfo()
    

    def updateInfo(self, command=None):
        LOGGER.debug('GPIN UpdateInfo: ' + str(self.waterLevel))
        self.lastNMeas.append(GPIO.input(self.inpin))
        LOGGER.debug('INPUT ' + str(self.inpin)+ ' = ' + str(self.lastNMeas[-1]) + ' len ' + str(len(self.lastNMeas))  )
        if len(self.lastNMeas) >= self.measAverage: # should only reach equal but to be safe
            self.avgLow = sum(self.lastNMeas)/len(self.lastNMeas)
            self.lastNMeas.pop() 
            if self.avgLow < 2/len(self.lastNMeas):
               self.waterLevel = 1
            else:
               self.waterLevel = 0
        else:
            self.waterLevel = 2
        self.setDriver('GV0', self.waterLevel)
        self.reportDrivers()

    drivers = [{'driver': 'GV0', 'value': 2, 'uom': 25}
              ] 

    commands = { 'UPDATE'  : updateInfo}

    id = 'PININ'

class TEMPsensor(polyinterface.Node):
    def __init__(self, controller, primary, address, name, sensorID):
        super().__init__(controller, primary, address, name)
        self.startTime = datetime.datetime.now()
        self.queue24H = []
        self.sensorID = str(sensorID)

    def start(self):
        LOGGER.debug('Spa Control start')
        self.sensor = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, self.sensorID )
        self.tempC = self.sensor.get_temperature(W1ThermSensor.DEGREES_C)
        self.tempMinC24H = self.tempC
        self.tempMaxC24H = self.tempC
        self.tempMinC24HUpdated = False
        self.tempMaxC24HUpdated = False
        self.currentTime = datetime.datetime.now()
        self.updateInfo()
        LOGGER.debug(str(self.tempC) + ' TempSensor Reading')

    def stop(self):
        LOGGER.debug('STOP - Cleaning up Temp Sensors')
        
    def shortPoll(self):
        LOGGER.info('shortpoll Sensor Control')
        self.updateInfo()


    def longPoll(self):
        LOGGER.info('longpoll Sensor Control')
        self.updateInfo()
        self.update24Hqueue()

    # keep a 24H log om measuremets and keep Min and Max 
    def update24Hqueue (self):
        timeDiff = self.currentTime - self.startTime
        if self.tempMinC24HUpdated:
            self.queue24H.append(self.tempMinC24H)
            LOGGER.debug('24H temp table updated Min')
        elif self.tempMaxC24HUpdated:
            self.queue24H.append(self.tempMaxC24H) 
            LOGGER.debug('24H temp table updated Max')
        else:
            self.queue24H.append(self.tempC)
        if timeDiff.days >= 1:         
            temp = self.queue24H.pop()
            if ((temp == self.tempMinC24H) or (temp == self.tempMaxC24H)):
                self.tempMaxC24H = max(self.queue24H)
                self.tempMinC24H = min(self.queue24H)
        LOGGER.debug('24H temp table updated')
        self.tempMinC24HUpdated = False
        self.tempMaxC24HUpdated = False
 

    def updateInfo(self, command=None):
        LOGGER.debug('TempSensor updateInfo')
        self.sensor = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, self.sensorID )
        self.tempC = self.sensor.get_temperature(W1ThermSensor.DEGREES_C)
        if self.tempC < self.tempMinC24H:
            self.tempMinC24H = self.tempC
            self.tempMin24HUpdated = True
        elif self.tempC > self.tempMaxC24H:
            self.tempMaxC24H = self.tempC
            self.tempMax24HUpdated = True
        self.currentTime = datetime.datetime.now()
        self.setDriver('GV0', round(float(self.tempC),1))
        self.setDriver('GV1', round(float(self.tempMinC24H),1))
        self.setDriver('GV2', round(float(self.tempMaxC24H),1))
        self.setDriver('GV3', int(self.currentTime.strftime("%m")))
        self.setDriver('GV4', int(self.currentTime.strftime("%d")))
        self.setDriver('GV5', int(self.currentTime.strftime("%Y")))
        self.setDriver('GV6', int(self.currentTime.strftime("%H")))
        self.setDriver('GV7',int(self.currentTime.strftime("%M")))
        self.reportDrivers()

        #return True                                                    
        
    
    def query(self, command=None):
        LOGGER.debug('TempSensor querry')
        self.updateInfo()


    drivers = [{'driver': 'GV0', 'value': 0, 'uom': 4},
               {'driver': 'GV1', 'value': 0, 'uom': 4},
               {'driver': 'GV2', 'value': 0, 'uom': 4},          
               {'driver': 'GV3', 'value': 0, 'uom': 47},               
               {'driver': 'GV4', 'value': 0, 'uom': 9},
               {'driver': 'GV5', 'value': 0, 'uom': 77},              
               {'driver': 'GV6', 'value': 0, 'uom': 20},              
               {'driver': 'GV7', 'value': 0, 'uom': 44}      
              ]
    id = 'TEMPSENSOR'
    
    commands = { 'UPDATE': updateInfo }



if __name__ == "__main__":

    try:
        LOGGER.info('Starting SPA Controller')
        polyglot = polyinterface.Interface('SPA_Temp_Control')
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
