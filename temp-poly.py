#!/usr/bin/env python3

import polyinterface
import sys
import RPi.GPIO as GPIO
import os
import glob
import time
import datetime
import queue
import os,subprocess
from subprocess import call
from w1thermsensor import W1ThermSensor


LOGGER = polyinterface.LOGGER

try:
    infile = open(fileName, 'r')
    sensorList = json.load(infile)
    infile.close()
except:
    sensorList = {}
    sensorList['sensors']=[]
    
sensorList['sensors'].append({
                                "serialNumber": "0000ffff",
                                "ISYname":      "test123"      
                            })
sensorList['sensors'].append({
                                "serialNumber": "0000aaaa",
                                "ISYname":      "test321"      
                            })
print(sensorList)
with open(fileName, 'w') as outfile:
    json.dump(sensorList, outfile)
outfile.close()



class Controller(polyinterface.Controller):
    def __init__(self, polyglot):
        super().__init__(polyglot)
        LOGGER.info('_init_')
        self.name = 'Rpi Temp Sensors'
        self.address = 'rpitemp'
        self.primary = self.address
        try:
            os.system('modprobe w1-gpio')
            os.system('modprobe w1-therm')
            self.setDriver('ST', 1)
        except:
            LOGGER.debug('modprobe OS calls not successful')
            self.setDriver('ST', 0)


    def start(self):
        LOGGER.info('start - Temp Sensor controller')
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
        self.updateInfo()
        self.reportDrivers()

    def stop(self):
        LOGGER.debug('stop - Cleaning up Temp Sensors')


    def shortPoll(self):
        LOGGER.debug('shortPoll')
        for node in self.nodes:
            self.nodes[node].updateInfo()
            
    def longPoll(self):
        LOGGER.debug('longPoll')
        for node in self.nodes:
            self.nodes[node].updateInfo()
            self.nodes[node].update24Hqueue()

    def update24Hqueue (self):
         LOGGER.debug('Update24H queue')
         pass

    def updateInfo(self):
        LOGGER.info('Update Info')
        pass

    def query(self, command=None):
        LOGGER.info('querry Info')
        for node in self.nodes:
            self.nodes[node].updateInfo()
            self.nodes[node].update24Hqueue()



    def discover(self, command=None):
        LOGGER.info('discover')
        count = 0
        for mySensor in self.mySensors.get_available_sensors():
            count = count+1
            currentSensor = mySensor.id.lower()
            LOGGER.info(currentSensor + 'Sensor Serial Number Detected - use custom params to rename')
            address = 'rpitemp'+str(count)
            if currentSensor in self.polyConfig['customParams']:
               LOGGER.debug('A customParams name for sensor detected')
               name = self.polyConfig['customParams'][currentSensor]
            else:
               LOGGER.debug('Default Naming')
               name = 'Sensor'+str(count)
            
            LOGGER.debug( address + ' '+ name + ' ' + currentSensor)
            if not address in self.nodes:
               self.addNode(TEMPsensor(self, self.address, address, name, currentSensor))


    def check_params(self, command=None):
        # Looking for custom defined names - allowing sensor detection order to change and not affect ISY
        LOGGER.info('Check Params' )
       
    id = 'RPITEMP'
    commands = {'DISCOVER': discover}
    drivers = [{'driver': 'ST', 'value': 1, 'uom': 2}]


class TEMPsensor(polyinterface.Node):
    def __init__(self, controller, primary, address, name, sensorID):
        super().__init__(controller, primary, address, name)
        self.startTime = datetime.datetime.now()
        self.queue24H = []
        self.sensorID = str(sensorID)


    def start(self):
        LOGGER.info('TempSensor start')
        self.sensor = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, self.sensorID )
        self.tempC = self.sensor.get_temperature(W1ThermSensor.DEGREES_C)
        self.tempMinC24H = self.tempC
        self.tempMaxC24H = self.tempC
        self.tempMinC24HUpdated = False
        self.tempMaxC24HUpdated = False
        self.currentTime = datetime.datetime.now()
        self.updateInfo()
        LOGGER.debug(str(self.tempC) + ' TempSensor Reading')
        #return True

    def stop(self):
        LOGGER.info('STOP - Cleaning up Temp Sensors')
        #self.sensor = None


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
        #pass

    def updateInfo(self):
        LOGGER.info('TempSensor updateInfo')
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
        self.setDriver('GV3', round(self.tempC*9/5+32.0, 1))
        self.setDriver('GV4', round(self.tempMinC24H*9.0/5+32.0, 1))
        self.setDriver('GV5', round(self.tempMaxC24H*9.0/5+32.0, 1))
        self.setDriver('GV6', int(self.currentTime.strftime("%m")))
        self.setDriver('GV7', int(self.currentTime.strftime("%d")))
        self.setDriver('GV8', int(self.currentTime.strftime("%Y")))
        self.setDriver('GV9', int(self.currentTime.strftime("%H")))
        self.setDriver('GV10',int(self.currentTime.strftime("%M")))
        self.setDriver('ST', 1)
        self.reportDrivers()

        #return True                                                    
        
    
    def query(self, command=None):
        LOGGER.info('TempSensor querry')
        self.updateInfo()


    drivers = [{'driver': 'GV0', 'value': 0, 'uom': 4},
               {'driver': 'GV1', 'value': 0, 'uom': 4},
               {'driver': 'GV2', 'value': 0, 'uom': 4},
               {'driver': 'GV3', 'value': 0, 'uom': 17},
               {'driver': 'GV4', 'value': 0, 'uom': 17},
               {'driver': 'GV5', 'value': 0, 'uom': 17},              
               {'driver': 'GV6', 'value': 0, 'uom': 47},               
               {'driver': 'GV7', 'value': 0, 'uom': 9},
               {'driver': 'GV8', 'value': 0, 'uom': 77},              
               {'driver': 'GV9', 'value': 0, 'uom': 20},              
               {'driver': 'GV10', 'value': 0, 'uom': 44},
               {'driver': 'ST', 'value': 0, 'uom': 2}              
              ]
    id = 'TEMPSENSOR'
    
    commands = { 'UPDATE': updateInfo }



if __name__ == "__main__":
#    signal.signal(signal.SIGTERM, signal_term_handler)
    try:
        LOGGER.info('Starting Temperaure Server')
        polyglot = polyinterface.Interface('Temp_Sensors')
        
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
