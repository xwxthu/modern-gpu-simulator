// Draft RTX 5060 SM120 tuner definition.
//
// This is a bootstrap entry for building SM120 microbenchmarks. It mirrors
// current smoke-ready flat config assumptions where needed and must not be
// treated as a calibrated RTX 5060 parameter set.

#ifndef SM120_RTX5060_HW_DEF_H
#define SM120_RTX5060_HW_DEF_H

#include "blackwell_SM120_common_hw_def.h"

// Smoke-config clock domain seed from
// gpu-simulator/gpgpu-sim/configs/tested-cfgs/SM120_RTX5060/gpgpusim.config.
// Calibration runs must record controlled or observed clocks separately.
#define CLK_FREQUENCY 2640

#endif
