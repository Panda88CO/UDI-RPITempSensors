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
        LOGGER.setLevel(logging.INFO)
        LOGGER.debug('_init_')
        self.name = 'Rpi Temp Sensors'
        self.address = 'controller'
        self.primary = self.address
        self.sensorList = []
        self.sensorListIndx = 0
        self.displayTypes = ['TEMP', 'TEMPMAX', 'TEMPMIN', 'TIME']
        self.LCDdisplayConfig= {0: 'displayText1:Txt/VAL', 1:'displayText2:Txt/VAL', 2:'displayText3:Txt/VAL',3:'displayText4:Txt/VAL'}
        self.displayContents = {0: 'displayText1:Txt/VAL', 1:'displayText2:Txt/VAL', 2:'displayText3:Txt/VAL',3:'displayText4:Txt/VAL'}
        self.dateTimeConfig = '%m/%d/%y %H:%M'
        self.hb = 0
        self.displayRow = 4
        self.displayCol = 20
        self.LCDdisplayEn = False

        try:
            os.system('modprobe w1-gpio')
            os.system('modprobe w1-therm')
            self.setDriver('GV0', 1)
        except:
            LOGGER.error('modprobe OS calls not successful')
            self.setDriver('GV0', 0)


    def start(self):
        LOGGER.info('start - Temp Sensor controller')
        self.removeNoticesAll()
        try:
            self.discover()
            self.displayInit = True
            self.setDriver('GV0', 1)

            self.updateInfo()
            self.reportDrivers()
            time.sleep(3)
            self.shortPoll()
            self.displayInit = False 
        except Exception as e:
            LOGGER.error('ERROR initializing: {}'.format(e))
            self.setDriver('GV0', 0)
            self.stop()


    def stop(self):
        LOGGER.info('stop - Cleaning up Temp Sensors')
        if self.lcd:
            self.lcd.close(clear=True)

    def shortPoll(self):
        LOGGER.debug('shortPoll')   
        try:                        
            for node in self.nodes:
                self.nodes[node].updateInfo()
                self.nodes[node].update24Hqueue()
            #LOGGER.debug('DisplayEnabled: {} - {}'.format(self.LCDdisplayEn, self.DisplaySensor))
            if self.LCDdisplayEn:   
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

        except Exception as e:
            LOGGER.error('shortPoll failed: {}'.format(e))

    def longPoll(self):
        LOGGER.debug('longPoll')
        self.heartbeat()
        #LOGGER.debug(self.nodes)
        #self.nodes = self.poly.getNodes()
        pass

    def lcdUpdate(self, node):
        #self.lcd.clear()
        try:
            tempStr = str('{}: {}{}'.format( self.nodes[node].name[:(self.displayCol - 7)], str(self.nodes[node].tempDisplay), self.tempUnitStr())[:self.displayCol])
            tempMinStr = str('Min Temp: {}{}'.format(self.nodes[node].tempDisplayMin,self.tempUnitStr())[:self.displayCol])
            tempMaxStr = str('Max Temp: {}{}'.format(self.nodes[node].tempDisplayMax,self.tempUnitStr())[:self.displayCol])
            tempMinMaxStr = str('Min {} Max {}{}'.format(self.nodes[node].tempDisplayMin,self.nodes[node].tempDisplayMax,self.tempUnitStr())[:self.displayCol])
            timeStr = str(self.nodes[node].currentTime.strftime(self.dateTimeConfig).center(self.displayCol)[:self.displayCol])


            for dispLine in range(0,self.displayRow):
                self.lcd.cursor_pos = (dispLine,0) 
                if self.LCDdisplayConfig[dispLine].upper() == 'TEMP':
                    if self.displayContents[dispLine] != tempStr or self.displayInit:
                        self.lcd.write_string(tempStr.center(self.displayCol))
                        self.displayContents[dispLine] = tempStr
                elif self.LCDdisplayConfig[dispLine].upper() == 'TEMPMAX':
                    if self.displayContents[dispLine] != tempMaxStr or self.displayInit:
                        self.lcd.write_string(tempMaxStr.center(self.displayCol))
                        self.displayContents[dispLine] = tempMaxStr
                elif self.LCDdisplayConfig[dispLine].upper() == 'TEMPMIN':
                    if self.displayContents[dispLine] != tempMinStr or self.displayInit:
                        self.lcd.write_string(tempMinStr.center(self.displayCol))
                        self.displayContents[dispLine] = tempMinStr
                elif self.LCDdisplayConfig[dispLine].upper() == 'TEMPMINMAX':
                    if self.displayContents[dispLine] != tempMinMaxStr or self.displayInit:
                        self.lcd.write_string(tempMinMaxStr.center(self.displayCol))
                        self.displayContents[dispLine] = tempMinMaxStr                        
                elif self.LCDdisplayConfig[dispLine].upper() == 'DATETIME':
                    if self.displayContents[dispLine] != timeStr or self.displayInit:
                        self.lcd.write_string(timeStr.center(self.displayCol))
                        self.displayContents[dispLine] = timeStr
                elif self.LCDdisplayConfig[dispLine]== '':
                    self.lcd.cr()                       
                else:
                    dispTEXT = self.LCDdisplayConfig[dispLine][:self.displayCol].center(self.displayCol)
                    if self.displayContents[dispLine] != dispTEXT or self.displayInit:
                        self.lcd.write_string(dispTEXT.center(self.displayCol))
                        self.displayContents[dispLine] = dispTEXT
        except Exception as e:
            LOGGER.error('lcdUpdate failed :{}'.format(e))


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
        try:
            if self.hb == 0:
                self.reportCmd('DON',2)
                self.hb = 1
            else:
                self.reportCmd('DOF',2)
                self.hb = 0
        except Exception as e:
            LOGGER.error('heartbeat failed to execute: {}'.format(e)
            )
    def discover(self, command = None):
        LOGGER.info('Discover')
        #LOGGER.info('cutsomParams {}'.format(self.polyConfig['customParams']))
        try:
            count = 0
            self.mySensors = W1ThermSensor.get_available_sensors()
            LOGGER.debug(self.mySensors)
            self.nbrSensors = len(self.mySensors)
            LOGGER.info( str(self.nbrSensors) + ' Sensors detected')
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
                    LOGGER.debug('Default Naming')
                    name = None
                    self.polyConfig['customParams'][currentSensor] = name
                    self.addCustomParam({currentSensor: None})
                    name = None
                    self.addNotice('Please name sensor {} in configuration and restart:'.format(currentSensor))
                    self.stop()
                if ('offset_'+currentSensor) in self.polyConfig['customParams']:
                    
                    tComp = float(self.polyConfig['customParams']['offset_'+currentSensor])
                    if tComp != 0.0:
                        LOGGER.info('A customParams offset exist')
                else:
                    LOGGER.debug('Creating Temp Offset param')
                    tComp = 0.0
                    self.polyConfig['customParams']['offset_'+currentSensor] = tComp        
                    self.addCustomParam({'offset_'+currentSensor: 0.0})
                if name :
                    LOGGER.info('Addning node {}, {}, {}'.format(address, name, currentSensor))
                    self.addNode(TEMPsensor(self, self.address, address, name, currentSensor, tComp), True)
                    self.sensorList.append(address)
            if 'displayEnabled' in self.polyConfig['customParams']:
                temp = int(str(self.polyConfig['customParams']['displayEnabled']))
                self.LCDdisplayEn = (temp == 1) 
            else:
                self.polyConfig['customParams']['displayEnabled'] = 0
                self.LCDdisplayEn = False
                self.addNotice('To enable display set displayEnabled = 1 -  restart - then configure display parameters')
                self.addCustomParam({'displayEnabled': self.polyConfig['customParams']['displayEnabled'] })

            if self.LCDdisplayEn:
                
                self.LCDdisplay = {}
                self.lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=self.displayCol, rows=self.displayRow, dotsize=8, charmap='A02', auto_linebreaks=True)
                self.lcd.clear()
                self.lcd.cursor_pos = (0,0)    
                self.lcd.write_string( 'UDI-RPiTempSensors'.center(self.displayCol))
                LOGGER.info('LCD display added')
                
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
                            #LOGGER.debug('{} == {}'.format(self.nodes[node].name.upper(), tempNode.upper()) )
                        if not found:
                            self.addNotice('Unknown sensor specified: {}'.format(tempNode))
                            self.DisplaySensor = 'MULTISENSORS' 
                else:           
                    self.DisplaySensor = 'MULTISENSORS'
                    self.polyConfig['customParams']['DisplaySensor'] = self.DisplaySensor
                    self.addCustomParam({'DisplaySensor': self.DisplaySensor })
                    
                if 'displayRow' in self.polyConfig['customParams']:
                    self.displayRow = int(self.polyConfig['customParams']['displayRow'])

                if 'displayCol' in self.polyConfig['customParams']:
                    self.displayCol = int(self.polyConfig['customParams']['displayCol'])
                LOGGER.info ('Checking for TIME format to : {}'.format(self.dateTimeConfig))
                LOGGER.info('CustomParams: {}'.format(self.polyConfig['customParams']))
                if 'dateTimeConfig' in self.polyConfig['customParams']:
                    self.dateTimeConfig = self.polyConfig['customParams']['dateTimeConfig']
                    LOGGER.info ('Updating TIME format to : {}'.format(self.dateTimeConfig))

                for line in range(0,self.displayRow):
                    indexStr = 'displayText'+str(line+1)
                    if indexStr in self.polyConfig['customParams']:
                        self.LCDdisplayConfig[line] = self.polyConfig['customParams'][indexStr]
                    else:
                        if line in self.LCDdisplayConfig:
                            self.polyConfig['customParams'][indexStr] =  self.LCDdisplayConfig[line]
                        else:
                            self.LCDdisplayConfig[line] ='Input Text or Param'
                        self.addCustomParam({indexStr: self.LCDdisplayConfig[line]})
                        LOGGER.debug('Add text lines {} - {}'.format(indexStr,self.LCDdisplayConfig[line] ))

            else:
                LOGGER.debug('No Display')
        
            self.reportDrivers()
        except Exception as e:
            LOGGER.error('Discover failed: {}'.format(e))

    def setTempUnit(self, command ):
        LOGGER.info('setTempUnit')
        try:
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
            self.shortPoll()
        except Exception as e:
            LOGGER.error('setTemp Unit failed: {}'.format(e))


    id = 'controller'
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
        LOGGER.info('TempSensor start')
        try:    
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
        except Exception as e:
            LOGGER.error('TEMPsensor start failed: {}'.format(e))


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
        try:
            self.tempC = self.sensor.get_temperature(Unit.DEGREES_C)
            LOGGER.debug('TempSensor: {} updateInfo: temp(C) - uncompensated: {}'.format(self.sensorID, self.tempC))
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

            self.setDriver('GV6', int(self.currentTime.strftime("%m")), True, True, 47 )
            self.setDriver('GV7', int(self.currentTime.strftime("%d")), True, True, 9)
            self.setDriver('GV8', int(self.currentTime.strftime("%Y")), True, True, 77)
            self.setDriver('GV9', int(self.currentTime.strftime("%H")), True, True, 20)
            self.setDriver('GV10',int(self.currentTime.strftime("%M")), True, True, 44)
            #self.reportDrivers()
        except Exception as e:
            logging.error ('Error obtaining temperature :{}'.format(e))

                                             


    def updateTemp(self, command = None):
        LOGGER.debug('updateTemp {}'.format(self.sensorID))
        self.updateInfo()
        self.parent.shortPoll()


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
