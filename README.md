# UDI Polyglot v2 Temperature Sensors 

[![license](https://img.shields.io/github/license/mashape/apistatus.svg)](https://github.com/Panda88CO/UDI-RPITempSensors/LICENSE)

This Poly provides an interface between [Raspberry Pi ](https://www.raspberrypi.org/documentation/usage/gpio-plus-and-raspi2/) DS18B20 temperature sensors and [Polyglot v2](https://github.com/UniversalDevicesInc/polyglot-v2) server.
Supports a 4x20 LCD I2C display 

### Installation instructions
Install from node server store 
Use customer config to set default temp unit and names of probes
Supports for offset for each probe - offset is specified in unit chosen 
Support for I2C 4x20 LCD display on RPi
Display is somewhat configurable (using displayCol and displayRow)
Setting in Configuration  
Check POLYGLOT_CONFIG.md file 

If using display - one must enableDisplay in configuration (set t0 1 and then save config)
Restart
Configure display Parameter (save Config)
Restart 


### Notes
shortPoll updates temperature, min/max, and display
LongPoll sends a heartbeat back to ISY
There is a bug (polyglot v2?) preventing node name update.  To update erase node (click delete) in polyglot interface and restart.   

Thanks and good luck.

