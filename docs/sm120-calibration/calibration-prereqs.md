# SM120 Calibration Prerequisites

## Purpose

Record the S3 MVP prerequisites for CUDA 13.2 / SM120 calibration work without
claiming that any RTX 5060 or RTX 5070 Ti parameter is already calibrated.

## Python Environment

Use a local virtual environment and the existing simulator requirements file:

```bash
cd /home/xiewx/accel-0608/modern-gpu-simulator/simulator-remodeled
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`simulator-remodeled/.venv/` and a root `.venv/` are ignored by git. Do not
commit the virtual environment.

## Tuner Microbenchmark Build

The tuner makefile now has an explicit SM120 build path while preserving the
historical default build:

```bash
cd /home/xiewx/accel-0608/modern-gpu-simulator/simulator-remodeled/util/tuner/GPU_Microbenchmark

# Dry-run one target with CUDA 13.2-style settings.
make -C ubench/system/system_config \
  CUDA_PATH=/usr/local/cuda-13.2 \
  CUDA_ARCH=sm_120 \
  HW_DEF=SM120_RTX5060 \
  -n

# Actual microbenchmark builds should be done only when CUDA 13.2/nvcc is
# available on the selected machine.
make -C ubench/system/system_config \
  CUDA_PATH=/usr/local/cuda-13.2 \
  CUDA_ARCH=sm_120 \
  HW_DEF=SM120_RTX5060
```

`CUDA_ARCH=sm_120` restricts `nvcc` code generation to
`compute_120/sm_120`, which avoids mixing old default `sm_50` through `sm_86`
targets into a CUDA 13.2 SM120 build. Omitting `CUDA_ARCH` keeps the existing
multi-architecture default for older flows.

`CUDA_PATH` selects the toolkit root used for `bin/nvcc` and CUDA sample include
paths, even if the shell exports a generic `CC`. If a nonstandard compiler
wrapper is required, pass `CC=/path/to/nvcc` on the make command line or define
it in the target Makefile.

`HW_DEF=SM120_RTX5060` or `HW_DEF=SM120_RTX5070_TI` selects draft SM120
hardware-definition headers. Omitting `HW_DEF` keeps the historical
`volta_TITANV_hw_def.h` default. The SM120 headers are bootstrap inputs only;
they contain placeholder/common assumptions and must not be reported as
calibrated facts.

The S3 build cleanup also removed direct tuner dependencies on legacy
`cudaDeviceProp.clockRate`, `cudaDeviceProp.memoryClockRate`, and the CUDA
sample-only `helper_cuda.h` path for the touched tuner device-query/config
benchmarks. Modern CUDA headers expose these clock and memory values through
`cudaDeviceGetAttribute`; the tuner compatibility layer now centralizes those
reads in `hw_def/common/deviceQuery.h`. The tuner `system/deviceQuery` target
does not invent CUDA-cores-per-SM values for architectures missing from its
legacy lookup table; unlisted architectures print `unknown for sm_XY`.

## Lightweight Device Collection

Use the official-tool collector from the local workspace. It runs commands over
ssh and writes all results back to the local output directory:

```bash
cd /home/xiewx/accel-0608/modern-gpu-simulator/simulator-remodeled/util/hw_stats

# Layout check only.
python3 collect_sm120_device_info.py --dry-run

# RTX 5060 host collection. This runs only lightweight tool queries remotely.
python3 collect_sm120_device_info.py --remote dsp5060 --device 0
```

Default output is `simulator-remodeled/util/hw_stats/device_info/<timestamp>-.../`
and is ignored by git. Each run records `manifest.json`, stdout, stderr, and
return code for:

- `nvidia-smi`, `nvidia-smi -L`, `nvidia-smi -q -x`
- conservative `nvidia-smi --query-gpu=...` queries, including compute
  capability when the driver exposes `compute_cap`
- `nvcc --version`, `nvcc --list-gpu-code`
- `ncu --version`
- `nsys --version`

Optional metric discovery for later Nsight mapping work:

```bash
python3 collect_sm120_device_info.py --remote dsp5060 --device 0 --include-metric-discovery
```

This adds `ncu --query-metrics --devices 0`; it is still not a benchmark run,
but it can produce verbose output.

## Compatibility Risks And Next Steps

- CUDA 13.2 was not available in the local S3 environment. Local `nvcc` was
  CUDA 13.1, and the RTX 5060 host `dsp5060` reported CUDA 12.8. The new build
  path was compile-checked with CUDA 13.1 and `sm_120`, but CUDA 13.2 remains
  explicitly unverified until that toolkit is installed or selected.
- CUDA 13.2 may not accept every legacy `sm_50` through `sm_86` target in the
  old default tuner build. Use `CUDA_ARCH=sm_120` for SM120 work and verify with
  `nvcc --list-gpu-code` on the target toolchain.
- Current `util/hw_stats/run_hw.py` still contains nvprof-era paths and fixed
  Nsight Compute metric names. S4/S5 must validate metric availability on SM120
  with `ncu --query-metrics` before using those counters for correlation.
- `nvidia-smi` does not expose every CUDA runtime attribute needed for layered
  overlays. S4/S5 still need a small CUDA runtime/device-property collector for
  SM count, memory bus width when not available through official query fields,
  registers, shared memory modes, and occupancy-related fields.
- The SM120 `hw_def` entries seed the old tuner equations. They do not resolve
  unresolved Blackwell questions such as GDDR7 timing, L2 partition mapping,
  tensor issue ratios, or RTX 5060/RTX 5070 Ti timing differences.
- Clock fields collected from official tools are observed or nominal state, not
  controlled calibration clocks. Calibration results must record clock-locking
  policy or observed clocks per run.
