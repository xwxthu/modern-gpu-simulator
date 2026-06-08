// Draft SM120 common hardware definitions for tuner microbenchmarks.
//
// These values are bootstrap inputs for S3 only. They are not calibrated
// hardware facts. Values that are copied from current flat SM120 configs or
// inherited from older tuner assumptions must be replaced or tagged with
// provenance by the S4/S5 calibration flow.

#ifndef BLACKWELL_SM120_COMMON_HW_DEF_H
#define BLACKWELL_SM120_COMMON_HW_DEF_H

#include "./common/common.h"
#include "./common/deviceQuery.h"

#define L1_SIZE (128 * 1024)

#define ISSUE_MODEL issue_model::single
#define CORE_MODEL core_model::subcore

// Placeholder: current tuner memory enums do not model GDDR7. The existing
// SM120 flat configs use a 16-bit channel style, burst length 16, and command
// ratio 4, matching this GDDR6 enum shape closely enough for bootstrap builds.
#define DRAM_MODEL dram_model::GDDR6

#define WARP_SCHEDS_PER_SM 4

// Bootstrap ratio from current SM120 flat configs: PTX tensor latency 64 and
// trace tensor latency 8. Revisit with SM120 tensor microbenchmarks in S5.
#define SASS_hmma_per_PTX_wmma 8

// Bootstrap topology from current SM120 configs:
// -gpgpu_n_sub_partition_per_mchannel 8 and -icnt_flit_size 40.
#define L2_BANKS_PER_MEM_CHANNEL 8
#define L2_BANK_WIDTH_in_BYTE 32

#endif
