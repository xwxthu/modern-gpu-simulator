/*
Some of the code is adopted from device query benchmark
from CUDA SDK
*/

#include <cuda_runtime.h>

#include <iostream>
#include <memory>
#include <string>

#include "../../../hw_def/common/deviceQuery.h"

static int convertSMVer2Cores(int major, int minor) {
  struct SMToCores {
    int sm;
    int cores;
  };
  static const SMToCores table[] = {
      {0x30, 192}, {0x32, 192}, {0x35, 192}, {0x37, 192}, {0x50, 128},
      {0x52, 128}, {0x53, 128}, {0x60, 64},  {0x61, 128}, {0x62, 128},
      {0x70, 64},  {0x72, 64},  {0x75, 64},  {0x80, 64},  {0x86, 128},
      {0x87, 128}, {0x89, 128}, {0x90, 128},
  };

  int sm = ((major / 10) << 8) | ((major % 10) << 4) | minor;
  for (const auto &entry : table) {
    if (entry.sm == sm)
      return entry.cores;
  }
  return -1;
}

int main(int argc, char **argv) {
  int deviceCount = 0;
  cudaError_t error_id = cudaGetDeviceCount(&deviceCount);

  if (error_id != cudaSuccess) {
    printf("cudaGetDeviceCount returned %d\n-> %s\n",
           static_cast<int>(error_id), cudaGetErrorString(error_id));
    printf("Result = FAIL\n");
    exit(EXIT_FAILURE);
  }

  // This function call returns 0 if there are no CUDA capable devices.
  if (deviceCount == 0) {
    printf("There are no available device(s) that support CUDA\n");
  }

  int dev, driverVersion = 0, runtimeVersion = 0;

  for (dev = 0; dev < deviceCount; ++dev) {
    intilizeDeviceProp(dev);

    // device
    printf("  Device : \"%s\"\n\n", deviceProp.name);
    printf("  CUDA version number                         : %d.%d\n",
           deviceProp.major, deviceProp.minor);

    // core
    printf("  GPU Max Clock rate                             : %.0f MHz \n",
           static_cast<float>(GPU_CLK_FREQUENCY));
    printf("  Multiprocessors Count                       : %d\n",
           deviceProp.multiProcessorCount);
    printf("  Maximum number of threads per multiprocessor: %d\n",
           deviceProp.maxThreadsPerMultiProcessor);
    int cores_per_sm = convertSMVer2Cores(deviceProp.major, deviceProp.minor);
    if (cores_per_sm > 0) {
      printf("  CUDA Cores per multiprocessor               : %d \n",
             cores_per_sm);
    } else {
      printf("  CUDA Cores per multiprocessor               : unknown for sm_%d%d \n",
             deviceProp.major, deviceProp.minor);
    }
    printf("  Registers per multiprocessor                : %d\n",
           deviceProp.regsPerMultiprocessor);
    printf("  Shared memory per multiprocessor            : %lu bytes\n",
           deviceProp.sharedMemPerMultiprocessor);
    printf("  Warp size                                   : %d\n",
           deviceProp.warpSize);

    // threadblock config
    printf("  Maximum number of threads per block         : %d\n",
           deviceProp.maxThreadsPerBlock);
    printf("  Shared memory per block                     : %lu bytes\n",
           deviceProp.sharedMemPerBlock);
    printf("  Registers per block                         : %d\n",
           deviceProp.regsPerBlock);

    // L1 cache
    printf("  globalL1CacheSupported                      : %d\n",
           deviceProp.globalL1CacheSupported);
    printf("  localL1CacheSupported                       : %d\n",
           deviceProp.localL1CacheSupported);

    // L2 cache
    if (L2_SIZE) {
      printf("  L2 Cache Size                             : %.0f MB\n",
             static_cast<float>(L2_SIZE / 1048576.0f));
    }

    // memory
    char msg[256];
    snprintf(msg, sizeof(msg),
             "  Global memory size                        : %.0f GB\n",
             static_cast<float>(deviceProp.totalGlobalMem / 1073741824.0f));
    printf("%s", msg);
    printf("  Memory Clock rate                           : %.0f Mhz\n",
           static_cast<float>(MEM_CLK_FREQUENCY));
    printf("  Memory Bus Width                            : %d bit\n", MEM_BITWIDTH);

    printf(" ////////////////////////// \n");
  }
}
