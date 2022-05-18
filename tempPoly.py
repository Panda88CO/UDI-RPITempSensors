#!/usr/bin/env python3

from site import addusersitepackages
import polyinterface
import sys
import os
import datetime
import time
import os
import logging
from subprocess import call
from w1thermsensor import W1ThermSensor, Sensor, Unit
from RPLCD.i2c import CharLCD

LOGGER = polyinterface.LOGGER

class Controller(polyinterface.Controller):
    def __init__(self, polyglot):
        super().__init__(polyglot)
        LOGGER.setLevel(logging.DEBUG)
        LOGGER.info('_init_')
        self.name = 'Rpi Temp Sensors'
        self.address = 'controller'
        self.primary = self.address
        self.sensorList = []
        self.sensorListIndx = 0
        self.LCDdisplay = {0:'TEMP', 1:'TEMPMIN', 2:'TEMPMAX', 3:'TIME'}
        self.hb = 0
        try:
            os.system('modprobe w1-gpio')
            os.system('modprobe w1-therm')
            self.setDriver('GV0', 1)
        except:
            LOGGER.debug('modprobe OS calls not successful')
            self.setDriver('GV0', 0)


    def start(self):
        LOGGER.debug('start - Temp Sensor controller')
        self.removeNoticesAll()
        try:
            self.discover()
            self.setDriver('GV0', 1)
        except Exception as e:
            LOGGER.info('ERROR initializing w1thermSensors: {}'.format(e))
            self.setDriver('GV0', 0)
            self.stop()

        self.updateInfo()
        self.reportDrivers()

    def stop(self):
        LOGGER.debug('stop - Cleaning up Temp Sensors')


    def shortPoll(self):
        LOGGER.debug('shortPoll')
        self.heartbeat()
        for node in self.nodes:
            self.nodes[node].updateInfo()

        if self.LCDdisplayEn:
            #LOGGER.debug(self.sensorList)
            #LOGGER.debug(self.sensorListIndx)          
            if self.DisplaySensor == 'MULTISENSORS':
                adr = self.sensorList[self.sensorListIndx]
                for node in self.nodes:
                    if adr == self.nodes[node].address:
                       self.lcdUpdate (node) 
                self.sensorListIndx = self.sensorListIndx + 1
                if self.sensorListIndx >= len(self.sensorList):
                    self.sensorListIndx = 0
                
            else:
                name = self.DisplaySensor
                for node in self.nodes:
                    if name == self.nodes[node].name:
                        self.lcdUpdate (node)


            
    def longPoll(self):
        LOGGER.debug('longPoll')
        #LOGGER.debug(self.nodes)
        #self.nodes = self.poly.getNodes()
        for node in self.nodes:
            self.nodes[node].updateInfo()
            self.nodes[node].update24Hqueue()

    def lcdUpdate(self, node):
            self.lcd.clear()
            tempStr = '{}{} - {}'.format(str(self.nodes[node].tempDisplay), self.tempUnitStr(),  self.nodes[node].name)
            tempMinStr = 'Min Temp: {}{}'.format(self.nodes[node].tempDisplayMin,self.tempUnitStr())
            tempMaxStr = 'Max Temp: {}{}'.format(self.nodes[node].tempDisplayMax,self.tempUnitStr()) 
            timeStr = self.nodes[node].currentTime.strftime("%m/%d/%y %H:%M").center(20)
            for dispLine in range(0,4):
                self.lcd.cursor_pos = (dispLine,0)   
                if self.LCDdisplay[dispLine] == 'TEXT':
                    self.lcd.write_string(self.LCDdisplayText[:20].center(20))
                elif self.LCDdisplay[dispLine] == 'TEMP':
                    self.lcd.write_string(tempStr[:20].center(20))
                elif self.LCDdisplay[dispLine] == 'TEMPMAX':
                    self.lcd.write_string(tempMaxStr[:20].center(20))
                elif self.LCDdisplay[dispLine] == 'TEMPMIN':
                    self.lcd.write_string(tempMinStr[:20].center(20))
                elif self.LCDdisplay[dispLine] == 'TIME':
                    self.lcd.write_string(timeStr[:20].center(20))
                else:
                    strTemp = '{} -Unknown type'.format(self.LCDdisplay[dispLine])
                    self.lcd.write_string(strTemp[:20])

    def tempUnitStr (self):
        if self.tempUnit == 2:
            unit = 'K'
        elif self.tempUnit == 1:
            unit = 'F'
        else:
            unit = 'C'
        return(unit)

    def update24Hqueue (self):
         LOGGER.debug('Update24H queue')
         pass

    def updateInfo(self):
        LOGGER.debug('Update Info')
        pass

    def heartbeat(self):
        LOGGER.debug('heartbeat: ' + str(self.hb))
        if self.hb == 0:
            self.reportCmd('DON',2)
            self.hb = 1
        else:
            self.reportCmd('DOF',2)
            self.hb = 0

    def discover(self, command = None):
        LOGGER.info('Discover')
        #LOGGER.info('cutsomParams {}'.format(self.polyConfig['customParams']))
        count = 0
        self.mySensors = W1ThermSensor.get_available_sensors()
        #LOGGER.debug(self.mySensors)
        self.nbrSensors = len(self.mySensors)
        #LOGGER.info( str(self.nbrSensors) + ' Sensors detected')
        if 'tempUnit' in self.polyConfig['customParams']:
            temp = self.polyConfig['customParams']['tempUnit'][:1].upper()
            logging.debug('tempUnit: {}'.format(temp))
            if temp == 'K':
                self.tempUnit  = 2
            elif temp == 'F':
                self.tempUnit  = 1
            else:
                self.tempUnit = 0
        else:
            self.tempUnit = 0 #default to C
            self.addCustomParam({'tempUnit': 'Celcius'})
        self.setDriver('GV3', self.tempUnit, True, True)  
        for mySensor in self.mySensors:
            count = count+1
            currentSensor = mySensor.id.lower() 
            LOGGER.info(currentSensor+ 'Sensor Serial Number Detected - use Custom Params to rename')
            address = 'rpitemp'+str(count)
            # check if sensor serial number exist in custom parapms and then replace name
            if currentSensor in self.polyConfig['customParams']:
               LOGGER.info('A customParams name for sensor detected')
               name = self.polyConfig['customParams'][currentSensor]
            else:
                LOGGER.info('Default Naming')
                name = 'Sensor'+str(count)
                self.polyConfig['customParams'][currentSensor] = name
                self.addCustomParam({currentSensor: name})

            if ('tComp_'+currentSensor) in self.polyConfig['customParams']:
                LOGGER.info('A customParams offset exist')
                tComp = float(self.polyConfig['customParams']['tComp_'+currentSensor])
            else:
                LOGGER.info('Creating Temp Offset param')
                tComp = 0.0
                self.polyConfig['customParams']['tComp_'+currentSensor] = tComp        
                self.addCustomParam({'tComp_'+currentSensor: 0.0})

            LOGGER.debug('Addning node {}, {}, {}'.format(address, name, currentSensor))
            self.addNode(TEMPsensor(self, self.address, address, name, currentSensor, tComp), True)
            self.sensorList.append(address)
        if 'displayEnabled' in self.polyConfig['customParams']:
            temp = int(str(self.polyConfig['customParams']['displayEnabled']))
            self.LCDdisplayEn = (temp == 1) 
        else:
            self.polyConfig['customParams']['displayEnabled'] = 0
            self.LCDdisplayEn = False
            self.addCustomParam({'displayEnabled': self.polyConfig['customParams']['displayEnabled'] })

        if self.LCDdisplayEn:
            displayTypes = ['TEXT', 'TEMP', 'TEMPMAX', 'TEMPMIN', 'TIME']
            self.LCDdisplay = {}
            self.lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=20, rows=4, dotsize=8, charmap='A02', auto_linebreaks=True)
            self.lcd.clear()
            self.lcd.cursor_pos = (1,0)    
            self.lcd.write_string( 'UDI-RPiTempSensors'.center(20))
            LOGGER.debug('LCD display added')
            
            if 'DisplaySensor' in self.polyConfig['customParams']:
                tempNode = self.polyConfig['customParams']['DisplaySensor']
                if tempNode.upper() == 'MULTISENSORS':
                    self.multiSensors = True
                    self.DisplaySensor = 'MULTISENSORS'

                else:
                    found = False
                    for node in self.nodes:
                        if self.nodes[node].name.upper() == tempNode.upper():
                            self.multSensors = False
                            found = True
                            self.DisplaySensor = tempNode
                        LOGGER.debug('{} == {}'.format(self.nodes[node].name.upper(), tempNode.upper()) )
                    if not found:
                        self.addNotice('Unknown sensor specified: {}'.format(tempNode))
                        self.DisplaySensor = 'MULTISENSORS' 
            else:           
                self.DisplaySensor = 'MULTISENSORS'
                self.polyConfig['customParams']['DisplaySensor'] = self.DisplaySensor
                self.addCustomParam({'DisplaySensor': self.DisplaySensor })
                

            if 'displayText' in self.polyConfig['customParams']:
                self.LCDdisplayText = self.polyConfig['customParams']['displayText']
            else:
                self.LCDdisplayText = 'Specify Text'
                self.polyConfig['customParams']['displayText'] =  self.LCDdisplayText
                self.addCustomParam({'displayText': self.LCDdisplayText})

            if 'displayLine0' in self.polyConfig['customParams']:
                tempLine = self.polyConfig['customParams']['displayLine0']
                if tempLine.upper() in displayTypes:
                    self.LCDdisplay[0] = tempLine.upper()
            else:
                self.LCDdisplay[0] = 'TEXT'
                self.polyConfig['customParams']['displayLine0'] =  self.LCDdisplay[0]
                self.addCustomParam({'displayLine0': self.LCDdisplay[0]})
          
            if 'displayLine1' in self.polyConfig['customParams']:
                tempLine = self.polyConfig['customParams']['displayLine1']
                if tempLine.upper() in displayTypes:
                    self.LCDdisplay[1] = tempLine.upper()
            else:
                self.LCDdisplay[1] = 'tempLine'
                self.polyConfig['customParams']['displayLine1'] =  self.LCDdisplay[1]
                self.addCustomParam({'displayLine1': self.LCDdisplay[1]})     

            if 'displayLine2' in self.polyConfig['customParams']:
                tempLine = self.polyConfig['customParams']['displayLine2']
                if tempLine.upper() in displayTypes:
                    self.LCDdisplay[2] = tempLine.upper()
            else:
                self.LCDdisplay[2] = 'TEMPMIN'
                self.polyConfig['customParams']['displayLine2'] =  self.LCDdisplay[2]
                self.addCustomParam({'displayLine2': self.LCDdisplay[2]})

            if 'displayLine3' in self.polyConfig['customParams']:
                tempLine = self.polyConfig['customParams']['displayLine3']
                if tempLine.upper() in displayTypes:
                    self.LCDdisplay[3] = tempLine.upper()
            else:
                self.LCDdisplay[3] = 'TIME'
                self.polyConfig['customParams']['displayLine3'] =  self.LCDdisplay[3]
                self.addCustomParam({'displayLine3': self.LCDdisplay[3]})

            


        else:
            LOGGER.debug('No Display')
    
        self.reportDrivers()

    def setTempUnit(self, command ):
        LOGGER.info('setTempUnit')
        self.tempUnit  = int(command.get('value'))
        
        if 'tempUnit' in self.polyConfig['customParams']:
            if self.tempUnit  == 2:
                self.polyConfig['customParams']['tempUnit'] = 'Kelvin'
            elif self.tempUnit  == 1:
                self.polyConfig['customParams']['tempUnit'] = 'Fahrenheit'
            else:
                self.polyConfig['customParams']['tempUnit'] = 'Celcius'
        else:
            self.tempUnit = 0 #default to C
            self.addCustomParam({'tempUnit': 'Celcius'})
        self.setDriver('GV3', self.tempUnit, True, True)  
        self.longPoll()


    id = 'RPITEMP'
    commands =  {'DISCOVER' : discover, 'TUNIT'    : setTempUnit} 


    drivers = [ {'driver': 'GV0', 'value': 0, 'uom' : 25},
                {'driver': 'GV3', 'value': 0, 'uom' : 25},] 


class TEMPsensor(polyinterface.Node):
    def __init__(self, controller, primary, address, name, sensorID, tempComp):
        super().__init__(controller, primary, address, name)
        self.startTime = datetime.datetime.now()
        self.queue24H = []
        self.sensorID = str(sensorID)
        self.tempComp = float(tempComp)

    def start(self):
        LOGGER.debug('TempSensor start')
        self.sensor = W1ThermSensor(sensor_id=self.sensorID )
        self.tempC = self.sensor.get_temperature(Unit.DEGREES_C)
        self.tempMinC24H = self.tempC
        self.tempMaxC24H = self.tempC
        self.tempDisplay = self.tempC
        self.tempDisplayMin = self.tempC
        self.tempDisplayMax = self.tempC
        self.tempMinC24HUpdated = False
        self.tempMaxC24HUpdated = False
        self.currentTime = datetime.datetime.now()
        self.updateInfo()
        
        LOGGER.debug('TempSensor Reading (uncompensateed): {}'.format(self.tempC))

    def stop(self):
        LOGGER.debug('STOP - Cleaning up Temp Sensors')
    

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
 

    def updateInfo(self):
        LOGGER.debug('TempSensor updateInfo')
        self.tempC = self.sensor.get_temperature(Unit.DEGREES_C)
        LOGGER.info('TempSensor: {} updateInfo: temp(C) - uncompensated: {}'.format(self.sensorID, self.tempC))
        if self.tempC < self.tempMinC24H:
            self.tempMinC24H = self.tempC
            self.tempMin24HUpdated = True
        elif self.tempC > self.tempMaxC24H:
            self.tempMaxC24H = self.tempC
            self.tempMax24HUpdated = True
        self.currentTime = datetime.datetime.now()
        
        if  self.parent.tempUnit == 2:
            self.tempDisplay = self.tempC+273.15+self.tempComp
            self.tempDisplayMin = self.tempMinC24H+273.15+self.tempComp
            self.tempDisplayMax = self.tempMaxC24H+273.15+self.tempComp
            self.setDriver('GV0', round(self.tempDisplay,1), True, True, 26)
            self.setDriver('GV1', round(self.tempDisplayMin,1), True, True, 26)
            self.setDriver('GV2', round( self.tempDisplayMax ,1), True, True, 26)
        elif self.parent.tempUnit == 1:
            self.tempDisplay = round(self.tempC*9/5+32+self.tempComp,1)
            self.tempDisplayMin = round(self.tempMinC24H*9/5+32+self.tempComp,1)
            self.tempDisplayMax = round(self.tempMaxC24H*9/5+32+self.tempComp,1)
            self.setDriver('GV0', round(self.tempDisplay,1), True, True, 17)
            self.setDriver('GV1', round(self.tempDisplayMin,1), True, True, 17)
            self.setDriver('GV2', round( self.tempDisplayMax ,1), True, True, 17)
  
        else:
            self.tempDisplay = round(self.tempC+self.tempComp,1)
            self.tempDisplayMin = round(self.tempMinC24H+self.tempComp,1)
            self.tempDisplayMax = round(self.tempMaxC24H+self.tempComp,1)     
            self.setDriver('GV0', round(self.tempDisplay,1), True, True, 4)
            self.setDriver('GV1', round(self.tempDisplayMin,1), True, True, 4)
            self.setDriver('GV2', round( self.tempDisplayMax ,1), True, True, 4)

        self.setDriver('GV6', int(self.currentTime.strftime("%m")))
        self.setDriver('GV7', int(self.currentTime.strftime("%d")))
        self.setDriver('GV8', int(self.currentTime.strftime("%Y")))
        self.setDriver('GV9', int(self.currentTime.strftime("%H")))
        self.setDriver('GV10',int(self.currentTime.strftime("%M")))
        self.reportDrivers()

                                             


    def updateTemp(self, command = None):
        LOGGER.info('updateTemp {}'.format(self.sensorID))
        self.updateInfo()


    drivers = [{'driver': 'GV0', 'value': 0, 'uom': 4},
               {'driver': 'GV1', 'value': 0, 'uom': 4},
               {'driver': 'GV2', 'value': 0, 'uom': 4},   
               #   
               {'driver': 'GV9', 'value': 0, 'uom': 20},              
               {'driver': 'GV10', 'value': 0, 'uom': 44},                        
               {'driver': 'GV6', 'value': 0, 'uom': 47},               
               {'driver': 'GV7', 'value': 0, 'uom': 9},
               {'driver': 'GV8', 'value': 0, 'uom': 77},
                ]
    id = 'TEMPSENSOR'
    
    commands = { 'UPDATE'   : updateTemp,
                } 



if __name__ == "__main__":

    try:
        LOGGER.info('Starting Temperaure Server')
        polyglot = polyinterface.Interface('Temp_Sensors')
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
