#ifndef HW_DEF_H
#define HW_DEF_H

// Default selection remains the historical Volta definition. Build with
// HW_DEF=SM120_RTX5060 or HW_DEF=SM120_RTX5070_TI to select the draft SM120
// entries through common/common.mk.
#if defined(ACCELSIM_HW_DEF_SM120_RTX5060)
#include "sm120_RTX5060_hw_def.h"
#elif defined(ACCELSIM_HW_DEF_SM120_RTX5070_TI)
#include "sm120_RTX5070_TI_hw_def.h"
#else
//#include "kepler_TITAN_hw_def.h"

//#include "pascal_TITANX_hw_def.h"

//#include "volta_QV100_hw_def.h"

//#include "turing_RTX2060_hw_def.h"

//#include "ampere_RTX3070_hw_def.h"

#include "volta_TITANV_hw_def.h"
#endif

#endif
