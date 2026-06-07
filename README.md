# Modern GPU Simulator for RTX5060

This repository contains a remodeled Accel-Sim/GPGPU-Sim based simulator for
modern NVIDIA GPUs.  It starts from the MICRO 2025 modern GPU simulator work and
adds local RTX5060/SM120 support and validation utilities for this server.

The previous README is preserved as `README-original.md`.

## What This Repository Improves

Compared with the original Accel-Sim framework, the remodeled simulator includes
the main MICRO 2025 architecture changes:

- A redesigned modern SM model, including sub-core pipeline and memory pipeline.
- SASS trace support with static instruction metadata and control-bit handling.
- Configurable dependence handling using scoreboards or compiler control bits.
- Enhanced dependency tracking for uniform, predicate, and uniform-predicate
  registers.
- WAR-hazard protection, corrected instruction addresses, improved fetch/decode
  timing, L0 instruction cache, and instruction prefetching.
- Parallel simulator execution support and AccelWattch integration.
- Google Protocol Buffers based dynamic traces and JSON static metadata.

This `dev-5060` branch additionally adapts the repository to the local RTX5060
environment:

- Adds a smoke-ready `SM120_RTX5060` configuration.
- Fixes CUDA 12.8 / GCC 13 build and trace-generation issues.
- Adds a reproducible RTX5060 native trace smoke script.
- Repairs the Rodinia/gpu-app trace path for CUDA 12.8.
- Guards zero-denominator derived stat printing to avoid `nan/-nan` in reports.

The RTX5060 configuration is validated for functional and stability use. It is
not yet a paper-level performance or power calibration.

## Tested Local Toolchain

Use CUDA 12.8 for this repository.

- GPU: NVIDIA RTX 5060
- CUDA toolkit: `/usr/local/cuda-12.8`
- `nvcc`: CUDA 12.8, `V12.8.93`
- NVBit: 1.7.5
- Driver: `595.71.05`
- `nvidia-smi` may report CUDA 13.2 because that is the driver-supported maximum
  CUDA version. That is not the toolkit used here.

Recommended environment:

```bash
export CUDA_INSTALL_PATH=/usr/local/cuda-12.8
export CUDA_HOME=/usr/local/cuda-12.8
export PATH=$CUDA_INSTALL_PATH/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_INSTALL_PATH/lib64:$LD_LIBRARY_PATH
```

## Repository Layout

- `simulator-remodeled/`: simulator, tracer, apps, and launch utilities.
- `simulator-remodeled/gpu-simulator/`: GPGPU-Sim/Accel-Sim simulator.
- `simulator-remodeled/util/tracer_nvbit/`: NVBit tracer and trace helpers.
- `simulator-remodeled/gpu-app-collection/`: benchmark applications.
- `simulator-remodeled/util/job_launching/`: simulation launch and stats tools.
- `APEs/`: error data from the upstream remodeled simulator work.
- `checkpoint_files/`: simulator checkpoint-related files.

From this point, most commands assume:

```bash
cd /home/xiewx/accel-0605/modern-gpu-simulator/simulator-remodeled
```

## Build the Simulator

```bash
export CUDA_INSTALL_PATH=/usr/local/cuda-12.8
export PATH=$CUDA_INSTALL_PATH/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_INSTALL_PATH/lib64:$LD_LIBRARY_PATH

source ./gpu-simulator/setup_environment_no_git.sh
make -j -C ./gpu-simulator
```

The simulator binary is:

```bash
./gpu-simulator/bin/release/accel-sim.out
```

## Build the NVBit Tracer

```bash
export CUDA_INSTALL_PATH=/usr/local/cuda-12.8
export PATH=$CUDA_INSTALL_PATH/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_INSTALL_PATH/lib64:$LD_LIBRARY_PATH

./util/tracer_nvbit/install_nvbit.sh
make -C ./util/tracer_nvbit ARCH=sm_120
```

## Quick RTX5060 Smoke Test

Run the reusable native trace smoke script from the repository root:

```bash
cd /home/xiewx/accel-0605/modern-gpu-simulator

WORK_DIR=/tmp/accelsim-sm120-smoke \
CUDA_INSTALL_PATH=/usr/local/cuda-12.8 \
ARCH=sm_120 \
GPGPUSIM_CONFIG=SM120_RTX5060 \
simulator-remodeled/util/tracer_nvbit/run_sm120_rtx5060_native_smoke.sh
```

Expected result:

- summary reports `status=PASS`
- trace metadata contains `Binary Version=120`
- trace metadata contains `NVBIT Version=1.7.5`
- simulator uses `SM120_RTX5060`
- simulation exits successfully

All generated source, binaries, traces, logs, and validation files are written
under `WORK_DIR`.

## Trace Real Benchmarks

Build and run benchmark traces using the gpu-app collection and NVBit tracer.
For CUDA 12.8, this branch includes fixes for legacy Rodinia build issues.

```bash
cd /home/xiewx/accel-0605/modern-gpu-simulator/simulator-remodeled

export CUDA_INSTALL_PATH=/usr/local/cuda-12.8
export PATH=$CUDA_INSTALL_PATH/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_INSTALL_PATH/lib64:$LD_LIBRARY_PATH

source ./gpu-app-collection/src/setup_environment
make -j -C ./gpu-app-collection/src rodinia_2.0-ft
```

Example trace command:

```bash
./util/tracer_nvbit/run_hw_trace.py \
  -B rodinia_2.0-ft \
  -D 0
```

`run_hw_trace.py` also supports per-benchmark argument overrides via
`-A/--benchmark_args`, useful for short calibration runs.

Generated traces are placed under `./hw_run/traces/`.

## Run Simulation

Use the RTX5060 configuration:

```bash
./gpu-simulator/bin/release/accel-sim.out \
  -trace <path-to-traces>/dynamic_trace.pb \
  -config ./gpu-simulator/gpgpu-sim/configs/tested-cfgs/SM120_RTX5060/gpgpusim.config \
  -config ./gpu-simulator/configs/tested-cfgs/SM120_RTX5060/trace.config
```

Or use the launch manager:

```bash
./util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft \
  -C SM120_RTX5060 \
  -T ./hw_run/traces/device-0/12.8/ \
  -N rtx5060_eval

./util/job_launching/get_stats.py -N rtx5060_eval | tee stats.csv
```

## Validated RTX5060 Workloads

This branch has been validated on the local RTX5060 for:

- Native SM120 trace collection with NVBit 1.7.5.
- Existing Blackwell trace smoke tests.
- Real Rodinia native/trace/simulation closure for:
  - `backprop16`
  - `lud16`
  - `hotspot16`
  - `bfs8`
  - `srad16`
  - `nw128`
  - `pathfinder1000`
- Targeted SASS coverage workloads for:
  - texture-like reads
  - atomics and reductions
  - FP64, 64-bit integer, and special math
  - warp vote/shuffle and divergence
  - vector shared/global memory accesses

These tests validate functionality and stability. They do not establish
performance accuracy.

## Performance Evaluation Notes

For performance work, use CUDA 12.8 and `SM120_RTX5060`.

Collect hardware counters with Nsight Compute when possible. This server has
been checked with Nsight Compute CLI 2026.1.1.0 and profiling permission was
available during validation.

Do not directly compare the following as a single accuracy ratio:

- Nsight Compute instruction counters
- NVBit trace instruction counts
- simulator `gpu_tot_sim_insn`

They have different semantics. Similarly, L2 sectors, DRAM bytes, simulator
cache/DRAM stats, and timing/cycle fields need a unit bridge and controlled
clock methodology before calibration claims can be made.

The current RTX5060 config is a functional/stability draft. Follow-on calibration
work should focus on:

- memory partition and address mapping
- L2/cache unit mapping
- DRAM timing and bandwidth
- locked or recorded clocks
- remaining SASS/runtime gaps such as surface ops, tensor/MMA, `cp.async`,
  copy-engine behavior, LDSM, cooperative groups, and grid/cluster barriers
- AccelWattch/power calibration

## Citation

If you use the remodeled simulator, cite the MICRO 2025 simulator work:

```text
Rodrigo Huerta, Mojtaba Abaie Shoushtary, Jose-Lorenzo Cruz, Antonio Gonzalez,
Dissecting and Modeling the Architecture of Modern GPU Cores,
2025 IEEE/ACM International Symposium on Microarchitecture (MICRO)
```

If you use the parallelization components, cite:

```text
Rodrigo Huerta, Antonio Gonzalez,
GPU Simulation Acceleration via Parallelization,
2025 IEEE International Symposium on Performance Analysis of Systems and Software (ISPASS)
```

Also cite Accel-Sim:

```text
Mahmoud Khairy, Zhensheng Shen, Tor M. Aamodt, Timothy G. Rogers,
Accel-Sim: An Extensible Simulation Framework for Validated GPU Modeling,
2020 ACM/IEEE 47th Annual International Symposium on Computer Architecture (ISCA)
```
