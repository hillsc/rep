from numpy import ascontiguousarray
from numpy import split, frombuffer, expand_dims
from numpy import *
import cv2
import sys
import os
from ctypes import *
from ctypes.util import find_library

imageds_dll = CDLL("/home/vagrant/imageds/build/src/libimageds.so", mode=1)
sys.settrace

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
	print (buffers[0])
	print (buffers[1])
	print (buffers[2])
	print (buffers[0].buffer)
	print (buffers[1].buffer)
	print (buffers[2].buffer)
	buf1 = (c_uint8 * 50).from_address(buffers[0].buffer)
	print (ctypeslib.as_array(buf1))
	print (buffers[0].buffer)


	return imageds_dll.imageds_load_array(imageds_handle, imageds_region, imageds_attr_array, buffers[0], buffers[1], buffers[2])



def read_image(handle, region, attr_array):
	#transform data into expected imageds strcuts
	imageds_handle = handle
	imageds_region = region
	imageds_attr_array_ = attr_array
	array = attr_array
	ret_buffer = POINTER(c_void_p)()
	print (imageds_dll)
	print (handle)
	print (region)
	print (array)
	print (ret_buffer)
	rc = imageds_dll.imageds_read_array(handle, region, array, byref(ret_buffer))
	print (rc)
	#sys.exit()
	#return imageds_array_to_np_array(ret_buffer, attr_array.contents.num_attributes)

def create_attr_array(name, num_attributes, attribute_names, attribute_types, compression):
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
	c_num_dimensions = c_int(num_dimensions)
	c_dimension_name = (c_char_p * len(dimension_name))(*dimension_name)
	c_dimension_name = cast(c_dimension_name, POINTER(c_char_p))
	c_start = (c_ulonglong * len(start))(*start)
	c_start = cast(c_start, POINTER(c_ulonglong))
	c_end = (c_ulonglong * len(start))(*end)
	c_end = cast(c_end, POINTER(c_ulonglong))
	return pointer(imageds_region_t(c_num_dimensions, c_dimension_name, c_start, c_end))
	

def create_imageds_buffer(data, size):
	ret_buffer = data
	c_size = c_size_t(size)
	return imageds_buffer_t(ret_buffer, size)
	
	
def np_array_to_imageds_buffers(np_array):
	# NOT TESTED AT ALL - COMPLETELY SCRATCH
	buffers = []
	ptr = np_array.ctypes.data_as(c_void_p)
	dims = split(np_array, np_array.ndim)
	print ("shape: ", np_array.shape)
	print ("size: ", np_array.size)
	print ("itemsize: ", np_array.itemsize)
	print ("strides: ", np_array.strides)
	colors=dsplit(np_array, np_array.shape[-1])
	#print (colors[0])
	print (colors)
	print ("dims\n\n", dims)
	print ("\n\n\n")
	for i in colors:
		i = i.ravel()
		size = i.ctypes.strides_as(c_int)
		#print (i.ctypes.shape)
		#print (i.ctypes.shape[1])
		#print (i.ctypes.shape[2])
		print (size[0])
		#print (size[1])
		#print (size[2])
		#i = i.ravel()
		print ("i:  ", i)
		print (i.strides)
		#data_array = ascontiguousarray(i, dtype=uint8)
		data_ptr = i.ctypes.data_as(c_void_p)
		buffers.append(create_imageds_buffer(data_ptr, np_array.ctypes.shape[0]*np_array.ctypes.shape[1]))
	return buffers

def imageds_array_to_np_array(ret_buffer, num_attributes):
	y = []
	tmp = array(y)

	#y.ctypes.data = ret_buffer.contents.value
	#x = frombuffer((c_ubyte * 300*300).from_address(ret_buffer.contents.value), dtype=uint8).copy()
	#print (POINTER(c_uint8).from_address(ret_buffer.contents.value).contents)
	#print ((POINTER(c_int).from_address(ret_buffer.contents.value)).contents)
	#ret_buffer.contents = cast(ret_buffer.contents, POINTER(c_int))
	print (ret_buffer)	
	arr = (300+1)*c_uint8
	#arr = (300*300+1)*c_byte
	ptrarr = (c_void_p * num_attributes)
	print (ret_buffer.contents)
	ptr1 = c_void_p.from_address(addressof(ret_buffer.contents))
	#ptr2 = c_void_p.from_address(addressof(ret_buffer.contents.value)+1)
	#ptr3 = c_void_p.from_address(addressof(ret_buffer.contents.value)+2)
	print ("ptr1: ", ptr1.value)
	print ("ptr1: ", addressof(ptr1))
	print (addressof(ret_buffer.contents))
	print (ret_buffer.contents.value)
	#print ("ptr2: ", ptr2.value)
	#print ("ptr3: ", ptr3.value)
	byte_arr = bytearray(string_at(ret_buffer[0], 50))
	print (frombuffer(byte_arr, dtype=uint8))
	byte_arr = bytearray(string_at(ret_buffer[1], 50))
	print (frombuffer(byte_arr, dtype=uint8))

	#sys.exit()
	print (ret_buffer[0])
	print (ret_buffer[1])
	print (ret_buffer[2])
	print (ret_buffer[3])
	print (ret_buffer[4])
	print (ctypeslib.as_array(arr.from_address(addressof(ret_buffer.contents))))	
	for i in range(0, num_attributes):
		print (addressof(ret_buffer.contents))
		#print (c_void_p.from_address(addressof(ret_buffer.contents)).value)
		#np = ctypeslib.as_array(cast(addressof(ret_buffer.contents), POINTER(c_void_p)), shape=(1000,))
		print ("buffer conetns for itr: ", i)
		#print (frombuffer(int_asbuffer(addressof(ret_buffer.contents), 300*300*3*dtype(uint8).itemsize)))
		#print (ctypeslib.as_array(pointer(cast(c_void_p(ptrarr[i]), POINTER(c_char))), shape=(100,)))
		#append(np_array, x, axis=1)
		#y.append(x)
	return array(y)

# for testing load image
if len(sys.argv) != 2:
	print ('Usage: test_python.py <filename>')
	sys.exit()
filename = sys.argv[1]
#print filename
im = cv2.imread(filename)
#cv2.imshow("tmp", im)
print (im)
sys.stderr = sys.stdout
x = connect()
region = create_imageds_region(2, [b"Row", b"Column"], [0, 0], [4, 4])
attr_array = create_attr_array(b"TestImage2", 3, [b"B", b"G", b"R"], [4, 4, 4], [0, 0, 0])
load_rc = load_image(x, region, attr_array, im)
print ("load rc:", load_rc)
#retrieved_image = read_image(x, region, attr_array)

class MyWrapper(object):
	def __init__(self, rows, cols, x, region, attr_array):
		self.size = rows.value * cols.value
		#self.size = 100 * 100
		self.ret_buffer = POINTER(c_void_p)()
		self.handle = connect()
		self.region = region
		#self.region = create_imageds_region(2, [b"Row", b"Column"], [0, 0], [5, 5])
		self.attr_array = attr_array

	
	@property
	def buffer(self):
		imageds_dll.imageds_read_array(self.handle, self.region, self.attr_array, byref(self.ret_buffer))
		#imageds_dll.test_1(byref(self.ret_buffer), 50, 3)
		print (self.ret_buffer[0])
		print (self.ret_buffer[1])

		buf1 = (c_uint8 * (self.size)).from_address(self.ret_buffer[0])
		buf2 = (c_uint8 * (self.size)).from_address(self.ret_buffer[1])
		buf3 = (c_uint8 * (self.size)).from_address(self.ret_buffer[2])
		buf1._wrapper = self
		buf2._wrapper = self
		buf3._wrapper = self
		print (self.ret_buffer[0])
		arr1 = ctypeslib.as_array(buf1)
		arr2 = ctypeslib.as_array(buf2)
		arr3 = ctypeslib.as_array(buf3)
		return vstack((arr1,arr2,arr3))
	

ret_buffer = POINTER(c_void_p)()
#rc = imageds_dll.test_1(pointer(ret_buffer), 50, 3);
imageds_dll.imageds_read_array(x, region, attr_array, byref(ret_buffer))
print (ret_buffer[0])
print (ret_buffer[1])
print (ret_buffer[2])
print (ret_buffer[0])
print (addressof(ret_buffer.contents))
y = ret_buffer[1]
print (ctypeslib.as_array((c_uint8 * 400).from_address(y)))
x = ret_buffer[0]
print (ctypeslib.as_array((c_uint8 * 25).from_address(x)))
z = ret_buffer[2]
print (ctypeslib.as_array((c_uint8 * 100).from_address(z)))

#imageds_dll.free_array_buffer(ret_buffer)
rows = c_int(5)
#rows = 50
#cols = 50
cols = c_int(20)
wrap = MyWrapper(rows, cols, x, region, attr_array)
buf = wrap.buffer
#for i in buf[0]:
#	print (i)
#print (buf[0])
print (buf)
#byte_arr = bytearray(string_at((ret_buffer[0]), size=50))
#print (frombuffer(byte_arr, dtype=uint8))
#print (ret_buffer[0])
#print (ret_buffer)
#print (ret_buffer.contents.value)

#byte_arr2 = bytearray(string_at((ret_buffer[1]), size=50))
#print (frombuffer(byte_arr2, dtype=uint8))
#print (ret_buffer[1])
