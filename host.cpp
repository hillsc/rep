/**********
Copyright (c) 2017, Xilinx, Inc.
All rights reserved.
Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:
1. Redistributions of source code must retain the above copyright notice,
this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors
may be used to endorse or promote products derived from this software
without specific prior written permission.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
**********/

#include "CL/cl.h"
#include "xcl.h"

#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>
#include <fstream>
#include <ctime>
#include <iostream>
//#include <boost/timer/timer.hpp>

using std::vector;
using std::find;

using namespace std;

//timer_t start_time;
//clock_t end_time;
double run_time;

clock_t start_time = clock();
//boost::timer::auto_cpu_timer t;

static const int elements = 1e8;

void check(cl_int err) {
  if (err) {
    printf("ERROR: Operation Failed: %d\n", err);
    exit(EXIT_FAILURE);
  }
}

// This example illustrates how to transfer data back and forth
// between host and device
int main(int argc, char **argv) {
    
  // Read in first fastq file

  ifstream ifs("/nfs/home/hillsc/CCAoGD/SRR2113606_2.fastq.1");
  auto const start_pos = ifs.tellg();
  ifs.ignore(std::numeric_limits<std::streamsize>::max());
  auto const char_count = ifs.gcount();
  ifs.seekg(start_pos);
  auto fastq = vector<char>(char_count);
  ifs.read(&fastq[0], fastq.size());


  // Read in second fastq file

  ifstream ifs2("/nfs/home/hillsc/CCAoGD/SRR2113606_2.fastq.2");
  auto const start_pos_2 = ifs2.tellg();
  ifs2.ignore(std::numeric_limits<std::streamsize>::max());
  auto const char_count_2 = ifs2.gcount();
  ifs2.seekg(start_pos_2);
  auto fastq_2 = vector<char>(char_count_2);
  ifs2.read(&fastq_2[0], fastq_2.size());


  // Record size of files
  size_t size_in_bytes = fastq.size() * sizeof(char);
  size_t size_in_bytes_2 = fastq_2.size() * sizeof(char);
  printf("size of fastq file 1 (bytes): %zu\n", size_in_bytes); 
  printf("size of fastq file 2 (bytes): %zu\n", size_in_bytes_2); 

  // Create vectors for returned data for lossless comparison
  auto fastq_returned = vector<char>(char_count);
  auto fastq_2_returned = vector<char>(char_count_2);

  cl_int err;
  cl_int err_2;

  xcl_world world = xcl_world_single();

  printf("Allocating and transferring data to %s\n", world.device_name);
  cl_mem buffer = xcl_malloc(world, CL_MEM_READ_ONLY, size_in_bytes);
  cl_mem buffer_2 = xcl_malloc(world, CL_MEM_READ_ONLY, size_in_bytes_2);
  
  cl_event async_event = 0;
  cl_event async_event_2 = 0;
  cl_int eventStatus;
  cl_int eventStatus_2;
  cl_int status;
  

  cl_command_queue ooo_queue = clCreateCommandQueue(
	  world.context, world.device_id, CL_QUEUE_PROFILING_ENABLE | CL_QUEUE_OUT_OF_ORDER_EXEC_MODE_ENABLE, &err);
  check(err);
  // Data can also be copied asynchronously with respect to the main thread by
  // sending CL_FALSE as the second parameter
  err = clEnqueueWriteBuffer(
      ooo_queue, buffer,
      CL_FALSE, // false indicates this is asynchronous call
      0, size_in_bytes, fastq.data(), 0, nullptr, &async_event);

  printf("Writing fastq file 1 to FPGA \n");

  err_2 = clEnqueueWriteBuffer(
      ooo_queue, buffer_2,
      CL_FALSE, // false indicates this is asynchronous call
      0, size_in_bytes_2, fastq_2.data(), 0, nullptr, &async_event_2);


  printf("Writing fastq file 2 to FPGA \n");
 
  // Wait for whichever write finsihes first
  // Fastq file 2 should finish first because queue is asynchronous
  // and file 2 is 1/4 the size of file 1

  while(1) {

      status = clGetEventInfo(async_event, CL_EVENT_COMMAND_EXECUTION_STATUS, 1*sizeof(cl_int), &eventStatus, NULL);

      if (eventStatus == 0)
      {
	  cout << "Fastq file 1 finished writing" << endl;
	  break;
      }
      
      status = clGetEventInfo(async_event_2, CL_EVENT_COMMAND_EXECUTION_STATUS, 1*sizeof(cl_int), &eventStatus_2, NULL);

      if (eventStatus_2 == 0)
      {
	  cout << "Fastq file 2 finished writing" << endl;
	  break;
      }
      


  }

  // Proved fastq file 2 completed first, so now
  // wait for file 1 to finish
  clWaitForEvents(1, &async_event);
  clWaitForEvents(1, &async_event_2);



  // Reading fastq files back from FPGA

  cl_event read_event = 0;
  cl_event read_event_2 = 0;


  // Data can be transferred back to the host using the read buffer operation
  clEnqueueReadBuffer(ooo_queue,
                      buffer,  // This buffers data will be read
                      CL_TRUE, // blocking call
                      0,       // offset
                      size_in_bytes,
                      fastq_returned.data(), // Data will be stored here
                      0, nullptr, &read_event);

  printf("Reading fastq file 1 back to host \n");

  clEnqueueReadBuffer(ooo_queue,
                      buffer_2,  // This buffers data will be read
                      CL_TRUE, // blocking call
                      0,       // offset
                      size_in_bytes_2,
                      fastq_2_returned.data(), // Data will be stored here
                      0, nullptr, &read_event_2);

  printf("Reading fastq file 2 back to host \n");


  check(clReleaseMemObject(buffer));
  check(clReleaseMemObject(buffer_2));

  check(clReleaseEvent(async_event));
  check(clReleaseEvent(async_event_2));
  check(clReleaseEvent(read_event));
  check(clReleaseEvent(read_event_2));
  xcl_release_world(world);

  clock_t end_time = clock();
  run_time = (end_time - start_time) / (double) CLOCKS_PER_SEC;
  printf("Runtime (seconds): %f\n", run_time);
  
  double throughput;
  throughput = (((double) size_in_bytes + (double) size_in_bytes_2) / run_time) / (double) 1000000.0;
  
  printf("Throughput (MB/s): %f\n", throughput);
  
  
  printf("Comparing received fastq data to original: \n");

  if (equal(fastq.begin(), fastq.end(), fastq_returned.begin()))
      printf("Fastq file 1 returned is same as original\n");

  if (equal(fastq_2.begin(), fastq_2.end(), fastq_2_returned.begin()))
      printf("Fastq file 2 returned is same as original\n");

  printf("TEST PASSED\n");

  return EXIT_SUCCESS;
}
