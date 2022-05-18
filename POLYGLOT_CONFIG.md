## Configuration and setup

 >Multiple Temperature Sensors DS18B20 can be placed placed on the same 2 wire bus on RPi - Vcc Pin1, GND Pin6, Data Pin7 - 4.7K Ohm resistor from pin7 to pin 1 - only one resistor is needed if multiple sensors are used 
(Only tested with 2 sensors this far)
> Sensors can be bought on Amazon or similar - search for DS18B20 - remember 4.7K resistor is usually not included, but some kit do - also one need to connect to the RPI header 

> shortPoll updates temperature and - sends heartBeast and updated display
> longPoll logs values for 24Hour Min/Max 

# Use custom config parameters to name sensors in node server/ISY.  
Sensors <sensorId> shows up with NoName when found - Name them to desired disply in ISY *This in needed to cxreate th sensor node 

tempUnit: Specifies the temp unit (C,F,K) to be displayed (only uses first Char)
ofset_<sensorId>: Probe temperature offset/compensation - specified using tempUnit

displayEnabled: 1 - display enabled, 0 - display diabled
DisplpaySensor: MULTISENSORS specifies rolling display (updated every shortPoll) between multiple Sensors
                SensorName(seea above) specifies only that specific sensor to be displayed 
                It is ok to specify MULTISENSORS with only 1 sensor

displayType1-4 : Specifies what is displayed on each line: 
    Options are:
        TEMP : Sensors Temperature
        TEMPMIN: Min temp last 24Hours
        TEMPMAX: Max temp last 24Hours  
        TIME: Latest Time of measurement
        TEXT: Test in line correspondig to displayText 1-4
        NONE: Blank Line
displayText1-4: Max 20 character text strings to be displayed in text line 1-4







> Uses W1ThemSensor library - more info can be found there <https://github.com/timofurrer/w1thermsensor>

Added a heat beat function toggling with SHORT POll - ISY can be used to detect this and know if connection is lost 

#### For more information:
- <https://www.raspberrypi.org/documentation/usage/gpio/>
- <https://pinout.xyz/pinout/wiringpi>
- <https://github.com/timofurrer/w1thermsensor>
