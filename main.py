from pyModbusTCP.client import ModbusClient
import json
import time
from multiprocessing import Process, Queue
import process_funk



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
	c = ModbusClient(host=settings['modbus_settings']['server_adress'], port=settings['modbus_settings']['server_port'], unit_id=settings['modbus_settings']['unit_id'], auto_open=True)

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
		for query in holding_registers: #Holding registers are read
			try:
				regs = c.read_holding_registers(int(query), int(holding_registers[query])) #Making the query for data
				if regs:
					reg_counter = 0 #Resetting counter for data in each package, separate counter is used as 32bit datas are read from two registers at the same time
					skip_next = False
					for reg in regs: #Looping through the registers in the received package
						curr_reg = int(query) + reg_counter
						#print(curr_reg)
						#print(settings['holding_registers'][str(curr_reg)])
						if skip_next == False: #If data is 16bit or first package of 32bit
							if settings['holding_registers'][str(curr_reg)]['size'] == "32":
								skip_next = True #Set to true if data is 32bit to skip reading the next package in the loop as it is being read in this run
								high_byte = int(regs[reg_counter]) + 65535
								low_byte = regs[int(reg_counter) + 1]
								final_value = high_byte + low_byte #Adding high and low byte in 32bit data
							else:
								final_value = regs[reg_counter]

							if "scaling" in settings['holding_registers'][str(curr_reg)]: #If scaling value is included in setup file
								final_outdata['holding_registers'][curr_reg] = str(final_value / int(settings['holding_registers'][str(curr_reg)]['scaling'])) #Received value is divided with scaling factor
							else:
								final_outdata['holding_registers'][curr_reg] = str(final_value)

						else:
							skip_next = False #In this instance the current register is being skipped as it is the last part of a 32bit data and has already been processed

						reg_counter = reg_counter + 1 #Adding 1 to the counter
			except Exception as e:
				print("Holding regs read error: ", curr_reg, e)

		time.sleep(5/10) #Sleeping between holding and input registers as some units need this


		for query in input_registers:
			#print(query)
			#print(input_registers[query])
			try:
				regs = c.read_input_registers(int(query), int(input_registers[query]))
				if regs:
					reg_counter = 0
					skip_next = False
					for reg in regs:
						curr_reg = int(query) + reg_counter
						#print(curr_reg)
						#print(settings['input_registers'][str(curr_reg)])
						if skip_next == False:
							if settings['input_registers'][str(curr_reg)]['size'] == "32":
								skip_next = True
								high_byte = int(regs[reg_counter]) + 65535
								low_byte = regs[int(reg_counter) + 1]
								final_value = int(high_byte + low_byte)
							else:
								final_value = int(regs[reg_counter])

							if "scaling" in settings['input_registers'][str(curr_reg)]:
								final_outdata['input_registers'][curr_reg] = str(final_value / int(settings['input_registers'][str(curr_reg)]['scaling']))
							else:
								final_outdata['input_registers'][curr_reg] = str(final_value)

						else:
							skip_next = False

						reg_counter = reg_counter + 1
			except Exception as e:
				print("input regs read error: ", curr_reg, e)

		#print(final_outdata)
		mqtt_sender_queue.put(final_outdata)
		time.sleep(int(settings['modbus_settings']['read_delay'])/100)
