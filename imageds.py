#from numpy import ascontiguousarray
#from numpy import split, frombuffer, expand_dims
#from numpy import *
import numpy as np
import cv2
import sys
import os
import imageds_gen
from imageds_gen import *
from ctypes import *
from ctypes.util import find_library
from copy import deepcopy
#imageds_dll = CDLL("/home/vagrant/imageds/build/src/libimageds.so", mode=1)
sys.settrace

#class imageds_array_t(Structure):
#	_fields_ = [("name", c_char_p),("num_attributes", c_int),("attribute_names", POINTER(c_char_p)),("atrribute_types", POINTER(c_int)),("compression", POINTER(c_int))]

#class imageds_region_t(Structure):
#	_fields_ = [("num_dimensions", c_int),("dimension_name", POINTER(c_char_p)),("start", POINTER(c_ulonglong)),("end", POINTER(c_ulonglong))]

#class imageds_buffer_t(Structure):
#	_fields_ = [("buffer", c_void_p),("size", c_size_t)]

# attempt to represent attr_types_t, compression_t types (typedef enum in c)
# approach taken from: https://stackoverflow.com/questions/36932/how-can-i-represent-an-enum-in-python
#def enum(**enums):
#	return type('Enum', (), enums)


#class attr_types_t(Structure):
#	_fields_ = [("type", c_int)]
	
#class compression_t(Structure):
#	_fields_ = [("type", c_int)]
	
def connect(workspace): 
	imageds_handle = POINTER(POINTER(None))()
	#imageds_handle = imageds_dll._handle
	print (imageds_handle)
	rc = imageds_connect(c_char_p(workspace), byref(imageds_handle))
	print ("Connect() RC: (%i)\n", rc)
	return imageds_handle

def disconnect(handle):
	return imageds_disconnect(handle)

def load_image(handle, region, array, np_array):
	
	# transform np_array into imageds buffer structs
	buffers = []
	idx = 0
	channels = deepcopy(np.dsplit(np_array, np_array.shape[-1]))
	for i in range(len(channels)):
		data_array = np.ascontiguousarray(channels[i], dtype=np.uint8)
		data_ptr = data_array.ctypes.data_as(c_void_p)
		buffers.append(create_imageds_buffer(data_ptr, np_array.ctypes.shape[0]*np_array.ctypes.shape[1]))
	

	rc = imageds_load_array(handle, byref(region), byref(array), buffers[0], buffers[1], buffers[2])
	if rc:
		print ("Error loading image")
	else:
		print ("Image loaded successfully")
	return rc

def read_image(handle, region, array):
	
	ret_region_size = c_size_t()
	ret_buffer = POINTER(POINTER(None))()
	attrs = []

	rc = imageds_read_array(handle, byref(region), byref(array), byref(ret_buffer), byref(ret_region_size))
	
	if rc:
		print ("Error reading image")
		return rc
	
	# transform raw data to numpy ndarray (opencv format)
	for i in range(0, array.num_attributes):
		raw_data = np.ctypeslib.as_array((c_uint8 * ret_region_size.value).from_address(ret_buffer[i]))
		# assumes 2D region (2D pixel data)
		data = np.reshape(raw_data, ((region.end[0]+1)-region.start[0],(region.end[1]+1)-region.start[1]))
		attrs.append(data)
	attrs_tuple = tuple(attrs)
	ret_array = np.dstack(attrs_tuple)
	
	return ret_array

def create_imageds_array(name, num_attributes, attribute_names, attribute_types, compression):
	c_name = String(name)
	c_num_attributes = c_int(num_attributes)
	c_attribute_names = (c_char_p * len(attribute_names))(*attribute_names)
	c_attribute_names = cast(c_attribute_names, POINTER(POINTER(c_char)))
	c_attribute_types = (attr_types_t * num_attributes)(*attribute_types)
	c_attribute_types = cast(c_attribute_types, POINTER(attr_types_t))
	c_compression = (compression_t * num_attributes)(*compression)
	c_compression = cast(c_compression, POINTER(compression_t))

	return imageds_array_t(c_name, c_num_attributes, c_attribute_names, c_attribute_types, c_compression)

def create_imageds_region(num_dimensions, dimension_names, start, end):
	c_num_dimensions = c_int(num_dimensions)
	c_dimension_names = (c_char_p * len(dimension_names))(*dimension_names)
	c_dimension_names = cast(c_dimension_names, POINTER(POINTER(c_char)))
	c_start = (c_uint64 * len(start))(*start)
	c_start = cast(c_start, POINTER(c_uint64))
	c_end = (c_uint64 * len(start))(*end)
	c_end = cast(c_end, POINTER(c_uint64))
	return imageds_region_t(c_num_dimensions, c_dimension_names, c_start, c_end)
	

def create_imageds_buffer(data, size):
	buf = data
	c_size = c_size_t(size)
	return imageds_buffer_t(buf, size)
	

# for testing load image
test_image = 1;
if test_image == 1:
	if len(sys.argv) != 2:
		print ('Usage: test_python.py <filename>')
		sys.exit()
	filename = sys.argv[1]
#print filename
im = cv2.imread(filename)
#im = filename
#cv2.imshow("tmp", im)
#print (im)
sys.stderr = sys.stdout
x = connect("test")
print (x[0])
region = create_imageds_region(2, ["Row", "Column"], [0, 0], [299, 299])
attr_array = create_imageds_array("TestImage2", 3, ["B", "G", "R"], [4, 4, 4], [0, 0, 0])


load_rc = load_image(x, region, attr_array, im)
print ("load rc:", load_rc)
retrieved_image = read_image(x, region, attr_array)
disconnect(x)
cv2.imshow("final", retrieved_image)
if cv2.waitKey():
	cv2.destroyAllWindows()


