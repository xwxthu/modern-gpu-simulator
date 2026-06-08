// Draft RTX 5070 Ti SM120 tuner definition.
//
// This is a bootstrap entry for building SM120 microbenchmarks. It mirrors
// current flat config assumptions where needed and must not be treated as a
// fully calibrated RTX 5070 Ti parameter set.

#ifndef SM120_RTX5070_TI_HW_DEF_H
#define SM120_RTX5070_TI_HW_DEF_H

#include "blackwell_SM120_common_hw_def.h"

// Config seed from
// gpu-simulator/gpgpu-sim/configs/tested-cfgs/SM120_RTX5070_TI/gpgpusim.config.
// Calibration runs must record controlled or observed clocks separately.
#define CLK_FREQUENCY 2580

#endif
