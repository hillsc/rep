import unittest
import numpy
import ctypes
import sys
import os
import time
import cv2
import pandas
import argparse

# insert python bindings into python's search path
# relative path to executing program, update as needed
sys.path.insert(0, '../../bindings/python/')
import imageds

##FLAGS
PLOT_RESULTS = False
EXPORT_CSV = False
NUM_RUNS = 100
PERSIST = True

inputs = []

input_arrays = []
input_regions = []

imageds_benchmark_suite = unittest.TestSuite()
opencv_benchmark_suite = unittest.TestSuite()

test_params = ["lib", "image", "filesize", "mode", "ids_size", "region", "attributes", "tile_extents", "compression", "time"]

imageds_benchmark_results = []
opencv_benchmark_results = []

def setUpModule():
	pass
def tearDownModule():
	if not PERSIST:
		os.system("rm -rf %s" % (b"BenchmarkImagedsWorkspace"))
	print(imageds_benchmark_results)

def set_flags():
	pass
	
def plot_results(results):
	pass

def export_csv(results):
	print("csv")

def finalize(test):
	#test_frame = pandas.DataFrame.from_records(test.results)
	imageds_benchmark_results.append(test.results)
	if PLOT_RESULTS:
		plot_results(test.results)
	if EXPORT_CSV:
		export_csv(test.results)
	
def load_inputs(load_compression_types, load_compression_levels):
	attribute_names = []
	compression = []
	compression_level = []
	attribute_types = []
	load_handle = imageds.connect(b"BenchmarkImagedsWorkspace")
	
	for i in range(0, len(inputs)):
		# set attribute names/types for each image to load
		attribute_names = []
		attribute_types = []
		for num in range(0, inputs[i].shape[-1]):
			attribute_names.append("ATTR" + str(num))
			attribute_types.append(4)
			
		load_region = imageds.create_imageds_region(2, ["X", "Y"], [0, 0], [inputs[i].shape[0]-1, inputs[i].shape[1]-1])
		input_regions.append(load_region)
		# load each image with the types of compression specified
		for j in range(0, len(load_compression_types)):
			# reset lists
			compression = []
			compression_level = []
			# set compression types/levels
			for _ in range(0, inputs[i].shape[-1]):
				compression.append(load_compression_types[j])
				if load_compression_levels[j] is not None:
					compression_level.append(load_compression_levels[j])
			if len(compression_level) != inputs[i].shape[-1]:
				compression_level = None
			
			# set name for array
			if compression_level is None:
				load_compression_levels[j] = "x"
			name = "benchmark_" + str(i) + "_" + str(load_compression_types[j]) + "_" + str(load_compression_levels[j])
			print(name)
			
			# load array with given compression
			load_array = imageds.create_imageds_array(name, inputs[i].shape[-1], attribute_names, attribute_types, compression, compression_level)
			input_arrays.append(load_array)
			
			rc = imageds.load_image(load_handle, load_region, load_array, inputs[i])
			if rc:
				print("Failed to load input image")
				sys.exit()
			del compression
			del compression_level
		del attribute_names
		del attribute_types

	imageds.disconnect(load_handle)


# set values for record
def set_data(test):

	if test.region is not None:
		test.data['region'] = str(int(test.region.end[0])-int(test.region.start[0]))+"x"+str(int(test.region.end[1])-int(test.region.start[1]))
		test.data['size'] = (int(test.region.end[0])-int(test.region.start[0]))*(int(test.region.end[1])-int(test.region.start[1]))
	else:
		test.data['region'] = 'whole'
		test.data['size'] = None
	
	if test.array is not None:
		test.data['attributes'] = str(test.array.num_attributes)
		test.data['compression'] = str(test.array.compression[0])
		if test.array.compression_level is not None:
			test.data['compression_level'] = str(test.array.compression_level)
		else:
			test.data['compression_level'] = "None"
	else:
		test.data['attributes'] = None
		test.data['compression'] = None
	
	test.data['tile_extents'] = "100x100"
	test.data['time'] = "0"


# set generic parameters for each test	
def initialize_default(test):
	test.workspace = b"BenchmarkImagedsWorkspace"
	test.handle = imageds.connect(test.workspace)
	test.array = None
	test.region = None
	test.data = dict()
	test.results = []
	set_data(test)


test_params = ["lib", "image", "file_size", "mode", "array_size", "region", "attributes", "tile_extents", "compression", "time"]

def execute_reads(test):
	runtimes = []
	test.data['mode'] = "read"
	set_data(test)
	for _ in range(0, NUM_RUNS):
		start = time.time()
		imageds.read_image(test.handle, test.region, test.array)
		end = time.time()
		runtimes.append(end - start)

	avg = (sum(runtimes) / NUM_RUNS)
	test.data['time'] = avg
	print(test.array)	
	test.results.append(test.data)
	
#################################################################
# IMAGEDS 
#################################################################


class BenchmarkImagedsNumAttributes(unittest.TestCase):
	def setUp(self):
		pass
	def tearDown(self):
		pass

class BenchmarkImagedsCompression(unittest.TestCase):
	@classmethod
	def setUpClass(self):
		self.handle = imageds.connect(b"BenchmarkImagedsWorkspace")
		load_inputs([imageds.NONE, imageds.GZIP], [None, 1])
	
	@classmethod
	def tearDownClass(self):
		imageds.disconnect(self.handle)
		#imageds_benchmark_results.append(self.results)

	def setUp(self):
		initialize_default(self)
		self.data['lib'] = "imageds"
		
	def tearDown(self):
		imageds.disconnect(self.handle)
		finalize(self)
		os.system("rm -rf %s" % (self.workspace.decode(sys.getdefaultencoding())))

	def test_no_compression(self):
		for i in input_arrays:
			self.array = i
			execute_reads(self)

		#self.array = imageds.create_imageds_array("benchmark", inputs[0].shape[-1], input_attr_names[0], [4, 4, 4], [0, 0, 0], None)

		#imageds_benchmark_results.append(self.results)
	
	#def test_gzip(self):
	#	del self.array

		
		


compression_benchmark_suite = unittest.TestLoader().loadTestsFromTestCase(BenchmarkImagedsCompression)
imageds_benchmark_suite.addTest(compression_benchmark_suite)


#################################################################
# OPENCV 
#################################################################



if __name__ == "__main__":
	print ("sfsf")
	if len(sys.argv) < 3:
		print ("Error")
		sys.exit()
	parser = argparse.ArgumentParser(description="desc")
	parser.add_argument(
		"-i",
		"--input",
		required=True,
		type=str,
		help="input help message")
	
	args = parser.parse_args()
	inputs.append(cv2.imread(args.input))
	#print(inputs[0])

print ("outside")
unittest.TextTestRunner(verbosity=2).run(imageds_benchmark_suite)




