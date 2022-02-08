# -*- coding: utf-8 -*-
from multiprocessing import Process, Queue
import paho.mqtt.client as mqtt #import the client1
import json
import time

def mqtt_receiver(to_main, settings):
	print("Mottaker startet")

	topic_holder = {}
	topic_holder['holding_registers'] = {}
	for register in settings['holding_registers']:
		topic_name = settings['holding_registers'][str(register)]['name']
		topic = "{}{}/{}/{}/c".format(settings['mqtt_settings']['basetopic'], "holding_registers", register,topic_name)
		if settings['holding_registers'][register]['writeable'] == "True":
			topic_holder['holding_registers'][register] = topic

	mqtt_client = mqtt.Client("io")
	mqtt_client.username_pw_set(username=settings['mqtt_settings']['server_user'],password=settings['mqtt_settings']['server_password'])
	mqtt_client.connect(settings['mqtt_settings']['server_adress'], int(settings['mqtt_settings']['server_port'])) #connect to broker

	mqtt_client.on_message=mqtt_handler(to_main, settings).process_message
	mqtt_client.loop_start()

	mqtt_client.subscribe("82/ventilasjon/holding_registers/1/Supply_Air_Speed_2/c")
	for data_type in topic_holder:
		for top in topic_holder[data_type]:
			mqtt_client.subscribe(str(topic_holder[data_type][top]))
			print(topic_holder[data_type][top])
	while(True):
		None



def mqtt_sender(from_main, settings):
	print("Sender startet")
	payload_log = {}
	while(True):
		mqtt_client = mqtt.Client("None")
		mqtt_client.username_pw_set(username=settings['mqtt_settings']['server_user'],password=settings['mqtt_settings']['server_password'])
		mqtt_client.connect(settings['mqtt_settings']['server_adress'], int(settings['mqtt_settings']['server_port'])) #connect to broker

		data = from_main.get()
		for data_type in data:
			for register in data[data_type]:

				topic_name = settings[data_type][str(register)]['name']
				topic = "{}{}/{}/{}/s".format(settings['mqtt_settings']['basetopic'], data_type, register,topic_name)
				payload = str(data[data_type][register])
				if topic not in payload_log:
					payload_log[topic] = "null"

				if payload_log[topic] != payload:
					mqtt_client.publish(topic, payload)
					payload_log[topic] = payload
					#print("Sendte {}, med data {}".format(topic, payload))
				time.sleep(10/1000)
		#print(data)

def mqtt_proxy(to_proxy, to_main, settings):
	while True:
		data = to_proxy.get()
		print(data)

class mqtt_handler:
	def __init__(self, to_main, settings):
		self.to_main = to_main
		print("tester")

	def process_message(self, client, userdata, message):
		data_holder = {}
		data_holder['payload'] = message.payload
		split_topic = message.topic.split("/")
		data_holder['data_type'] = split_topic[2]
		data_holder['register'] = split_topic[3]
		self.to_main.put(data_holder)