from numpy import ascontiguousarray
from numpy import split, frombuffer, expand_dims
from numpy import *

from ctypes import *
imageds_dll = CDLL("libimageds.so", mode=1)

class imageds_attr_array_t(Structure):
	_fields_ = [("name", c_char_p),("num_attributes", c_int),("attribute_names", POINTER(c_char_p)),("atrribute_types", POINTER(c_int)),("compression", POINTER(c_int))]

class imageds_region_t(Structure):
	_fields_ = [("num_dimensions", c_int),("dimension_name", POINTER(c_char_p)),("start", POINTER(c_ulonglong)),("end", POINTER(c_ulonglong))]

class imageds_buffer_t(Structure):
	_fields_ = [("buffer", c_void_p),("size", c_size_t)]

# attempt to represent attr_types_t, compression_t types (typedef enum in c)
# approach taken from: https://stackoverflow.com/questions/36932/how-can-i-represent-an-enum-in-python
#def enum(**enums):
#	return type('Enum', (), enums)


#class attr_types_t(Structure):
#	_fields_ = [("type", c_int)]
	
#class compression_t(Structure):
#	_fields_ = [("type", c_int)]
	
def connect(): 
	handle = POINTER(c_void_p)()
	imageds_dll.connect(c_char_p("ws"), byref(handle))
	return handle

def load_image(handle, region, attr_array, np_array):
	# Data expected to be in form of imageds structs
	imageds_region = region
	imageds_attr_array = attr_array

	# transform np_array into imageds buffer structs
	buffers = np_array_to_imageds_buffers(np_array)

	imageds_dll.load_array(handle, imageds_region, imageds_attr_array, buffers[0], buffers[1], buffers[2])

	return


def read_image(handle, region, attr_array):
	#transform data into expected imageds strcuts
	imageds_region = region
	imageds_attr_array_ = attr_array
	ret_buffer = POINTER(c_void_p)()
	imageds_dll.read_array(handle, imageds_region, imageds_attr_array, ret_buffer)
	return imageds_array_to_np_array(ret_buffer, attr_array.num_attributes)

def create_attr_array(name, num_attributes, attribute_names, attribute_types, compression):
	

	# build struct from converted input
	
	c_name = c_char_p(name)
	c_num_attributes = c_int(num_attributes)
	
	#c_attribute_names = POINTER(c_char_p)()
	#for i in attribute_names:
	#	tmp.append(c_char_p(i))
	c_attribute_names = POINTER((c_char_p * num_attributes)(*attribute_names))

	c_attribute_types = POINTER((c_int * num_attributes)(*attribute_types))

	if compression is not None:
		c_compression = POINTER((c_int * num_attributes)(*compression))
	else:
		c_compression = c_void_p()


	return imageds_attr_array_t(c_name, c_num_attributes, c_attribute_names, c_attribute_types, c_compression)
	


	# transform python object to c-string for input to api
	# imageds_dll.create_attr_array(attr_array)

def create_imageds_region(num_dimensions, dimension_name, start, end):
	# TODO check input 
	c_num_dimensions = c_int(num_dimensions)
	c_dimension_name = (c_void_p * len(dimension_name))(*dimension_name)
	c_start = POINTER(c_ulonglong(start))
	c_end = POINTER(c_ulonglong(end))
	return imageds_region_t(c_num_dimensions, c_dimension_name, c_start, c_end)
	

def create_imageds_buffer(data, size):
	ret_buffer = data
	c_size = c_size_t(size)
	return imageds_buffer_t(ret_buffer, size)
	
	
def np_array_to_imageds_buffers(np_array):
	buffers = []
	ptr = c_array.ctypes.data_as(c_void_p)
	dims = split(np_array, np_array.ndim)
	for i in dims:
		size = i.strides_as(c_int)
		data_array = ascontiguousarray(i, dtype=int)
		data_ptr = data_array.ctypes.data_as(c_void_p)
		buffers.append(create_imageds_buffer(data_ptr, size))
	return buffers

def imageds_array_to_np_array(ret_buffer, num_attributes):
	
	for i in range(0, num_attributes):
		x = frombuffer(*ret_buffer[i], dtype=int)
		(append(np_array, x, axis=1)
	return np_array


#filename = 
#scipy.ndimage.imread(filename)
