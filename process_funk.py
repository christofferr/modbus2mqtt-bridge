# -*- coding: utf-8 -*-
from multiprocessing import Process, Queue
import paho.mqtt.client as mqtt #import the client1
import json
import time

def mqtt_receiver(to_main, settings):

	topic_holder = {}
	topic_holder['holding_registers'] = {} # This list is to keep the topics for which to subscribe
	for register in settings['holding_registers']: #Looping through the settingsfile to retrieve the register
		topic_name = settings['holding_registers'][str(register)]['name'] #Find name of register
		topic = "{}{}/{}/{}/c".format(settings['mqtt_settings']['basetopic'], "holding_registers", register,topic_name) #Create the topic, the "c" indicates that it is for control
		if settings['holding_registers'][register]['writeable'] == "True": #Checking config file and checking if the holding register is writeable and only accepting of True
			topic_holder['holding_registers'][register] = topic #Adding the topic to the list of which we want to subscribe

	mqtt_client = mqtt.Client(None)
	mqtt_client.username_pw_set(username=settings['mqtt_settings']['server_user'],password=settings['mqtt_settings']['server_password'])
	mqtt_client.connect(settings['mqtt_settings']['server_adress'], int(settings['mqtt_settings']['server_port'])) #connect to broker

	mqtt_client.on_message=mqtt_handler(to_main, settings).process_message #Declares the class which receives the MQTT data and then sends them on to the main process
	mqtt_client.loop_start()

	for data_type in topic_holder: #Looping through the holding register of which we will subscribe to and be able to control
		for top in topic_holder[data_type]:
			mqtt_client.subscribe(str(topic_holder[data_type][top])) #Subscribing to topic

	while(True):
		None #Just keeping the thread alive



def mqtt_sender(from_main, settings):
	payload_log = {}
	while(True):
		#Starting the MQTT client
		mqtt_client = mqtt.Client(None)
		mqtt_client.username_pw_set(username=settings['mqtt_settings']['server_user'],password=settings['mqtt_settings']['server_password'])
		mqtt_client.connect(settings['mqtt_settings']['server_adress'], int(settings['mqtt_settings']['server_port'])) #connect to broker

		data = from_main.get() #Waiting for data to be received from the main thread
		for data_type in data: #Looping through the datatypes as input and holding registers
			for register in data[data_type]: #Looping through the registers in the data type

				topic_name = settings[data_type][str(register)]['name'] #Finding the name of the value
				topic = "{}{}/{}/{}/s".format(settings['mqtt_settings']['basetopic'], data_type, register,topic_name) #Creating the topic 
				payload = str(data[data_type][register]) #Formatting the payload
				if topic not in payload_log: #Adding the topic to the Payload log for later to be able to distinguish and only send new data
					payload_log[topic] = "null"

				if payload_log[topic] != payload: #Checking if the newly received data received is differen to the last value sent
					mqtt_client.publish(topic, payload) #Sending the data
					payload_log[topic] = payload #Adding the latest sent data to the log
					#print("Sendte {}, med data {}".format(topic, payload))
				time.sleep(10/1000) #Waiting just to not overload modbus server
		#print(data)



class mqtt_handler: #This is the class which receives the MQTT data
	def __init__(self, to_main, settings):
		self.to_main = to_main
		print("tester")

	def process_message(self, client, userdata, message):
		data_holder = {}
		data_holder['payload'] = message.payload #Extracting payload
		split_topic = message.topic.split("/") #Splitting the topic to use it later
		data_holder['data_type'] = split_topic[2] #Find the data type
		data_holder['register'] = split_topic[3] #Find the register
		self.to_main.put(data_holder) #Send the data back to the main thread to be written to the unit