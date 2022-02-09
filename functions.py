# -*- coding: utf-8 -*-
import time

def uintjoiner16bto32bit(high_byte, low_byte): #simple function that joins two 16 bit values to a uint32
	final_value = int("{:016b}".format(int(high_byte)) + "{:016b}".format(int(low_byte)), 2)
	return(final_value)


def intjoiner16bto32bit(high_byte, low_byte): #simple function that joins two 16 bit values to a int32
	high_byte_bits = "{:016b}".format(int(high_byte))
	sign = high_byte_bits[0]
	print(sign)
	uint_value = int("{:015b}".format(int(high_byte)) + "{:016b}".format(int(low_byte)), 2)

	if sign == "1":
		final_value = float(0 - uint_value)
	else:
		final_value = uint_value

	return(final_value)

def uinttoint16bit(byte): #This function converts a raw 16bit value from uint to int
	byte_bits = "{:016b}".format(int(byte))
	byte_value = "{:015b}".format(int(byte))
	sign = str(byte_bits[0])
	if sign == "0":
		final_value = int(byte_value, 2)
	else:
		final_value = float(0 - int(byte_value, 2))

	return(final_value)


def register_loop(settings, request, data_type, registers):

	result_holder = {}
	for query in registers:
		try:
			if data_type == "input":
				regs = request.read_input_registers(int(query), int(registers[query]))
			elif data_type == "holding":
				regs = request.read_holding_registers(int(query), int(registers[query]))
				
			if regs:
				reg_counter = 0 #Resetting counter for data in each package, separate counter is used as 32bit datas are read from two registers at the same time
				skip_next = False
				for reg in regs: #Looping through the registers in the received package
					curr_reg = int(query) + reg_counter
					#print(curr_reg)
					#print(settings[str(curr_reg)])
					if skip_next == False: #If data is 16bit or first package of 32bit
						if settings[str(curr_reg)]['size'] == "32":
							skip_next = True #Set to true if data is 32bit to skip reading the next package in the loop as it is being read in this run
							high_byte = regs[reg_counter]
							low_byte = regs[int(reg_counter) + 1]
							if settings[str(curr_reg)]['signed'] == "True":
								final_value = intjoiner16bto32bit(high_byte, low_byte) #Adding high and low byte in 32bit data
							elif settings[str(curr_reg)]['signed'] == "False":
								final_value = uintjoiner16bto32bit(high_byte, low_byte) #Adding high and low byte in 32bit data

						else:
							if settings[str(curr_reg)]['signed'] == "True":
								final_value = uinttoint16bit(regs[reg_counter]) #Adding high and low byte in 32bit data
							elif settings[str(curr_reg)]['signed'] == "False":
								final_value = regs[reg_counter]

						if "scaling" in settings[str(curr_reg)]: #If scaling value is included in setup file
							result_holder[curr_reg] = str(float(final_value) / int(settings[str(curr_reg)]['scaling'])) #Received value is divided with scaling factor
						else:
							result_holder[curr_reg] = str(final_value)

					else:
						skip_next = False #In this instance the current register is being skipped as it is the last part of a 32bit data and has already been processed

					reg_counter = reg_counter + 1 #Adding 1 to the counter
		except Exception as e:
			print("Modbus regs read error: ", e)
	return(result_holder) #Return the final data


def package_maker(settings):
	start = True
	registers = {}
	for adress in settings: #Looping through  registers 
		if start == True: #If first register in file
			start = False #Sets first register in file to false
			start_int = int(adress)
			if settings[adress]['size'] == "16": #If data is 16 bits only one register is added to package
				registers[start_int] = 1
			elif settings[adress]['size'] == "32": # If data is 32 bits two registers is added to package
				registers[start_int] = 2

		else:
			if int(adress) == int(start_int) + int(registers[start_int]):
				if settings[adress]['size'] == "16": #If data is 16 bits only one register is added to package
					registers[start_int] = int(registers[start_int] + 1)
				elif settings[adress]['size'] == "32": # If data is 32 bits two registers is added to package
					registers[start_int] = int(registers[start_int] + 2)
			else:
				start_int = adress
				if settings[adress]['size'] == "16": #If data is 16 bits only one register is added to package
					registers[adress] = 1
				elif settings[adress]['size'] == "32": # If data is 32 bits two registers is added to package
					registers[adress] = 2
	return(registers)

