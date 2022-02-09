# -*- coding: utf-8 -*-

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
	byte_bits = "{:016}".format(int(byte))
	byte_value = "{:015}".format(int(byte))
	sign = byte_bits[0]
	if sign == "0":
		final_value = byte_value
	else:
		final_value = float(0 - int(byte_value))

	return(final_value)