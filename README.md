# modbus2mqtt-bridge
A python project which itself reads data from a modbus server and publishes it to MQTT. Also possible to write data to modbus from MQTT.

# Why?

Used in my home automation system so that it can read and control my HVAC system independently of modbus support in main system. 

# How to use
The script reads data from modbus once it starts. The setup is done in a configuration file, please checkout flexit_config.json for how it works.
It will automatically make the MQTT topics based on "basetopic/datatype/register/name/s". The script will also subscribe to topics "basetopic/datatype/register/name/s" for the ones that are set as "writeable" = True in the config.
