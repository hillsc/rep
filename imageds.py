from numpy import ascontiguousarray
from numpy import split, frombuffer, expand_dims
from numpy import *
import cv2
import sys
import os
from ctypes import *
from ctypes.util import find_library
#tiledb_dll = cdll.LoadLibrary(os.path.join(os.path.dirname(os.path.abspath("libtiledb.so")), "libtiledb.so"))
#imageds_dll = cdll.LoadLibrary(os.path.join(os.path.dirname(os.path.abspath("libimageds.so")), "libimageds.so"))

imageds_dll = CDLL("/home/vagrant/imageds/build/src/libimageds.so", mode=1)
print (imageds_dll)
#print imageds_dll['connect']
sys.settrace

#test = CFUNCTYPE(None)
#test1 = test(("read_array", imageds_dll))
#print test1
#read_array_func = getattr(imageds_dll, 'read_array')
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
	imageds_handle = POINTER(c_void_p)()
	#imageds_handle = imageds_dll._handle
	print (imageds_handle)
	rc = imageds_dll.imageds_connect(c_char_p(b"test"), byref(imageds_handle))
	print ("Connect() RC: (%i)\n", rc)
	return imageds_handle

def load_image(handle, region, attr_array, np_array):
	# Data expected to be in form of imageds structs
	imageds_handle = handle
	imageds_region = region
	imageds_attr_array = attr_array

	# transform np_array into imageds buffer structs
	buffers = np_array_to_imageds_buffers(np_array)

	return imageds_dll.imageds_load_array(imageds_handle, imageds_region, imageds_attr_array, buffers[0], buffers[1], buffers[2])



def read_image(handle, region, attr_array):
	#transform data into expected imageds strcuts
	imageds_handle = handle
	imageds_region = region
	imageds_attr_array_ = attr_array
	array = attr_array
	ret_buffer = (POINTER(c_void_p))()
	print (imageds_dll)
	print (handle)
	print (region)
	print (array)
	print (ret_buffer)
	rc = imageds_dll.imageds_read_array(handle, region, array, byref(ret_buffer))
	print (rc)
	#sys.exit()
	return imageds_array_to_np_array(ret_buffer, attr_array.contents.num_attributes)

def create_attr_array(name, num_attributes, attribute_names, attribute_types, compression):
	
	# build struct from converted input
	
	c_name = c_char_p(name)
	c_num_attributes = c_int(num_attributes)
	c_attribute_names = (c_char_p * len(attribute_names))(*attribute_names)
	c_attribute_names = cast(c_attribute_names, POINTER(c_char_p))

	c_attribute_types = (c_int * num_attributes)(*attribute_types)
	c_attribute_types = cast(c_attribute_types, POINTER(c_int))
	if compression is not None:
		c_compression = (c_int * num_attributes)(*compression)
		c_compression = cast(c_compression, POINTER(c_int))
	else:
		c_compression = c_void_p()


	return pointer(imageds_attr_array_t(c_name, c_num_attributes, c_attribute_names, c_attribute_types, c_compression))

def create_imageds_region(num_dimensions, dimension_name, start, end):
	# TODO check input 
	c_num_dimensions = c_int(num_dimensions)
	#c_dimension_name = c_void_p((c_char_p * len(dimension_name))(*dimension_name))
	c_dimension_name = (c_char_p * len(dimension_name))(*dimension_name)
	c_dimension_name = cast(c_dimension_name, POINTER(c_char_p))
	print (c_dimension_name)
	#c_start = POINTER(c_ulonglong(start))
	c_start = (c_ulonglong * len(start))(*start)
	c_start = cast(c_start, POINTER(c_ulonglong))
	print (c_start)
	#c_end = POINTER(c_ulonglong(end))
	c_end = (c_ulonglong * len(start))(*end)
	c_end = cast(c_end, POINTER(c_ulonglong))
	return pointer(imageds_region_t(c_num_dimensions, c_dimension_name, c_start, c_end))
	

def create_imageds_buffer(data, size):
	ret_buffer = data
	c_size = c_size_t(size)
	return imageds_buffer_t(ret_buffer, size)
	
	
def np_array_to_imageds_buffers(np_array):
	buffers = []
	ptr = np_array.ctypes.data_as(c_void_p)
	dims = split(np_array, np_array.ndim)
	for i in dims:
		size = i.ctypes.strides_as(c_int)
		print (size[0])
		print (size[1])
		print (size[2])
		data_array = ascontiguousarray(i, dtype=int)
		data_ptr = data_array.ctypes.data_as(c_void_p)
		buffers.append(create_imageds_buffer(data_ptr, size[0]))
	return buffers

def imageds_array_to_np_array(ret_buffer, num_attributes):
	#print (ret_buffer.contents)
	y = []
	#print (type(ret_buffer.contents))
	tmp = array(y)

	#y.ctypes.data = ret_buffer.contents.value
	#x = frombuffer((c_ubyte * 300*300).from_address(ret_buffer.contents.value), dtype=uint8).copy()
	#print (POINTER(c_uint8).from_address(ret_buffer.contents.value).contents)
	#print (x.size)
	#print (x)
	#print ((POINTER(c_int).from_address(ret_buffer.contents.value)).contents)
	#ret_buffer.contents = cast(ret_buffer.contents, POINTER(c_int))
	print ("hey")
	print (ret_buffer)	
	#print (type(ret_buffer.contents))
	for i in range(0, num_attributes):
		#x = frombuffer(ret_buffer[i], dtype=int)
		#x = ctypeslib.as_array(ret_buffer, shape=(1000,))
		#pi =  pointer((ret_buffer.contents))
		#print (ret_buffer.contents.value[i])
		print (addressof(ret_buffer.contents))
		print (c_void_p.from_address(addressof(ret_buffer.contents)).value)
		np = ctypeslib.as_array(cast(addressof(ret_buffer.contents), POINTER(c_void_p)), shape=(1000,))
		#np = ctypeslib.as_array(POINTER(ret_buffer.contents)(), shape=(1000,))
		print(np)

		#append(np_array, x, axis=1)
		#y.append(x)
	return array(y)

if len(sys.argv) != 2:
	print ('Usage: test_python.py <filename>')
	sys.exit()

filename = sys.argv[1]
#print filename
im = cv2.imread(filename)
#print (im)
print (type(im))
cv2.imshow("tmp", im)
#np_array 
sys.stderr = sys.stdout
x = connect()
region = create_imageds_region(2, [b"Row", b"Column"], [0, 0], [299, 299])
print (region)
attr_array = create_attr_array(b"TestImage", 3, [b"R", b"G", b"B"], [4, 4, 4], [0, 0, 0])
print (attr_array)
print (attr_array.contents.name)
#load_rc = load_image(x, region, attr_array, im)
read_rc = read_image(x, region, attr_array)
print (read_rc)

#filename = 
#scipy.ndimage.imread(filename)
