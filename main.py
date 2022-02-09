from pyModbusTCP.client import ModbusClient
import json
import time
from multiprocessing import Process, Queue
import process_funk
import functions



if __name__ == '__main__':

	config_file = "flexit_config_2.json" ## Change this to the config file you would like to use
	with open(config_file, "r") as in_file:
	    settings = json.loads(in_file.read())
					
#Creating queues to transfer data between the three processes
	mqtt_receiver_queue = Queue()
	mqtt_sender_queue = Queue()

#Declaring the variables and datas to store holding register and input register data
	holding_registers = {}
	holding_start = True
	holding_start_int = 0

	input_registers = {}
	input_start = True
	input_start_int = 0

#Declaring the final output variable holders
	final_outdata = {}
	final_outdata['holding_registers'] = {}
	final_outdata['input_registers'] = {}

#Creating the modbus instance
	c = ModbusClient(host=settings['modbus_settings']['server_adress'], port=settings['modbus_settings']['server_port'], unit_id=settings['modbus_settings']['unit_id'], auto_open=True, timeout=1)

	#Making packets for holding registers
	for adress in settings['holding_registers']: #Looping through holding registers 
		if holding_start == True: #If first register in file
			holding_start = False #Sets first register in file to false
			holding_start_int = int(adress)
			if settings['holding_registers'][adress]['size'] == "16": #If data is 16 bits only one register is added to package
				holding_registers[holding_start_int] = 1
			elif settings['holding_registers'][adress]['size'] == "32": # If data is 32 bits two registers is added to package
				holding_registers[holding_start_int] = 2

		else:
			if int(adress) == int(holding_start_int) + int(holding_registers[holding_start_int]):
				if settings['holding_registers'][adress]['size'] == "16": #If data is 16 bits only one register is added to package
					holding_registers[holding_start_int] = int(holding_registers[holding_start_int] + 1)
				elif settings['holding_registers'][adress]['size'] == "32": # If data is 32 bits two registers is added to package
					holding_registers[holding_start_int] = int(holding_registers[holding_start_int] + 2)
			else:
				holding_start_int = adress
				if settings['holding_registers'][adress]['size'] == "16": #If data is 16 bits only one register is added to package
					holding_registers[adress] = 1
				elif settings['holding_registers'][adress]['size'] == "32": # If data is 32 bits two registers is added to package
					holding_registers[adress] = 2


	#Samler alle input registers
	for adress in settings['input_registers']:
		if input_start == True:
			input_start = False
			input_start_int = int(adress)
			if settings['input_registers'][adress]['size'] == "16": #If data is 16 bits only one register is added to package
				input_registers[input_start_int] = 1
			elif settings['input_registers'][adress]['size'] == "32": # If data is 32 bits two registers is added to package
				input_registers[input_start_int] = 2

		else:
			if int(adress) == int(input_start_int) + int(input_registers[input_start_int]):
				if settings['input_registers'][adress]['size'] == "16": #If data is 16 bits only one register is added to package
					input_registers[input_start_int] = int(input_registers[input_start_int] + 1)
				elif settings['input_registers'][adress]['size'] == "32": # If data is 32 bits two registers is added to package
					input_registers[input_start_int] = int(input_registers[input_start_int] + 2)
			else:
				input_start_int = adress
				if settings['input_registers'][adress]['size'] == "16": #If data is 16 bits only one register is added to package
					input_registers[adress] = 1
				elif settings['input_registers'][adress]['size'] == "32": # If data is 32 bits two registers is added to package
					input_registers[adress] = 2

#Starting processes for sending and receiving MQTT data
	mqtt_receiver_process = Process(target=process_funk.mqtt_receiver, args=(mqtt_receiver_queue, settings)) 
	mqtt_receiver_process.start()
	time.sleep(1)
	mqtt_sender_process = Process(target=process_funk.mqtt_sender, args=(mqtt_sender_queue, settings))
	mqtt_sender_process.start()



	while True: #Main loop starts here
	#try:
		try:
			data_from_mqtt = mqtt_receiver_queue.get_nowait()
			try:
				if data_from_mqtt:
					if data_from_mqtt['data_type'] == "holding_registers":
						if "scaling" in settings['holding_registers'][data_from_mqtt['register']]:
							value_to_write = int(float(data_from_mqtt['payload']) * int(settings['holding_registers'][str(data_from_mqtt['register'])]['scaling']))
						else:
							value_to_write = int(data_from_mqtt['payload'])
						c.write_single_register(int(data_from_mqtt['register']), value_to_write)
			except Exception as e:
				print("Kunne ikke skrive til modbus pga: ", e)
		except Exception as e:
			None

		final_outdata['holding_registers'] = functions.register_loop(settings['holding_registers'], c, "holding", holding_registers) #Reading holding registers

		time.sleep(1/10) #Sleeping between holding and input registers as some units need this


		final_outdata['input_registers'] = functions.register_loop(settings['input_registers'], c, "input", input_registers) #Reading input registers
		
		#print(final_outdata)
		mqtt_sender_queue.put(final_outdata)
		time.sleep(int(settings['modbus_settings']['read_delay'])/100)
#		except Exception as e:
#			print("Main loop failed due to: ", e)
