## Configuration and setup

 >Multiple Temperature Sensors DS18B20 can be placed placed on the same 2 wire bus on RPi - Vcc Pin1, GND Pin6, Data Pin7 - 4.7K Ohm resistor from pin7 to pin 1 - only one resistor is needed if multiple sensors are used 
(Only tested with 2 sensors this far)
> Sensors can be bought on Amazon or similar - search for DS18B20 - remember 4.7K resistor is usually not included, but some kit do - also one need to connect to the RPI header 

> shortPoll updates temperature
> longPoll logs values for 24Hour Min/Max

>Use custom config parameters to name sensors in node server/ISY.  
Sensors shows up with NoName when found - Name them to desired disply in ISY

Input Ports can be defined by specifying portN (Brcm numbering) as KEY and VALUE as IN:name (name is shown in ISY)
Output Ports can be defined by specifying portN (Brcm numbering) as KEY and VALUE as OUT:name (name shown in ISY)

> Uses W1ThemSensor library - more info can be found there 

Added a heat beat function toggling with SHORT POll - ISY can be used to detect this and know if connection is lost 

#### For more information:
- <https://www.raspberrypi.org/documentation/usage/gpio/>
- <https://pinout.xyz/pinout/wiringpi>
- <https://github.com/timofurrer/w1thermsensor>
