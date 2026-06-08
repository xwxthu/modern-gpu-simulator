# S7 Trace Config Runtime Worker Log

## Purpose

Resolve or precisely bound the local smoke blocker:

```text
GPGPU-Sim ** ERROR: Unknown Option: '-is_extra_traces_enabled'
```

This worker did not run the full simulator on `dsp5060`, did not modify
accepted configs, calibration `latest.yaml`, generated bulk outputs, or real
metrics artifacts, and did not promote configs.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Host: `dsp-ubuntu`
- Base HEAD: `e9206098354c0e04f276e251360c8f103ff71b96`
- Base subject: `fix: link trace runtime into cudart`
- Timestamp: `2026-06-09T02:58:36+08:00`
- Run id: `s7-trace-config-20260609-025836`
- Artifact root: `artifacts/s7/s7-trace-config-20260609-025836/`

## Inputs Reviewed

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- Prior worker log:
  `docs/sm120-calibration/worker-logs/worker-20260609-023311-s7-trace-link.md`
- Runtime entry path:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpusim_entrypoint.cc`
- Runtime context:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpusim_entrypoint.h`
- Standalone trace-driven initialization:
  `simulator-remodeled/gpu-simulator/main.cc`
- Trace option owner:
  `simulator-remodeled/gpu-simulator/trace-driven/trace_driven.{cc,h}`
- Downstream trace-config use:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/abstract_hardware_model.cc`

## Root Cause

The CUDA runtime initialization path registered PTX, opcode latency,
interconnect, and `gpgpu_sim_config` options before parsing `gpgpusim.config`,
but did not register `trace_config` options. The generated SM120 config includes
trace-driven option keys such as `-is_extra_traces_enabled 1`, so runtime config
parsing rejected the option before simulation could proceed.

The standalone trace-driven path already calls `trace_config::reg_options()` and
stores `g_trace_config`. The runtime path also needs a `trace_config` object
because remodeled runtime code can later dereference `g_trace_config` for
latency data.

## Changes

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpusim_entrypoint.cc`
  - Includes `trace_driven.h` only when `TRACING_ON` is enabled.
  - Allocates a runtime-owned `trace_config` in `gpgpu_ptx_sim_init_perf()`.
  - Registers trace options before `option_parser_cmdline()`.
  - Parses trace latency strings after config parsing and GPU config init.
  - Deletes the runtime-owned trace config in `GPGPUsim_ctx::~GPGPUsim_ctx()`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpusim_entrypoint.h`
  - Initializes `g_trace_config`.
  - Adds `g_trace_config_owned` so the shared simulator context can distinguish
    runtime-owned from externally owned trace configs.
- `simulator-remodeled/gpu-simulator/main.cc`
  - Marks the standalone trace-driven stack `trace_config` as non-owned after
    assigning `g_trace_config`.

No generated or accepted config files were modified.

## Evidence

### Rebuild

Command:

```bash
export CUDA_INSTALL_PATH=/usr/local/cuda-13.1
export PATH="$CUDA_INSTALL_PATH/bin:$PATH"
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
make -C simulator-remodeled/gpu-simulator/gpgpu-sim -j"$(nproc)"
```

Evidence:

- Initial build after root-cause fix:
  `artifacts/s7/s7-trace-config-20260609-025836/rebuild-gpgpusim.log`,
  exit `0`.
- Final build after guarding the direct trace include with `TRACING_ON`:
  `artifacts/s7/s7-trace-config-20260609-025836/rebuild-gpgpusim-final.log`,
  exit `0`.
- Rebuilt runtime inspection:
  `artifacts/s7/s7-trace-config-20260609-025836/rebuilt-lib-final-inspection.log`,
  exit `0`.

Runtime inspection shows:

- `SONAME libcudart.so.13`
- `DT_NEEDED` includes `libz.so.1` and `libprotobuf.so.32`
- `ldd -r` exits cleanly
- `trace_config::reg_options`, `trace_config::parse_config`, and
  `trace_config::trace_config` are defined in the rebuilt runtime.

### Generator And Whitespace Checks

Commands:

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
git diff --check
```

Evidence:

- `final2-generate-check-only.log`, exit `0`
  - Generated `SM120_RTX5070_TI profile=bootstrap gpgpu_keys=217 trace_keys=13`
  - Generated `SM120_RTX5060 profile=bootstrap gpgpu_keys=217 trace_keys=13`
- `final2-git-diff-check.log`, exit `0`

Protected config status evidence:

- `final-protected-config-scoped-status.log` is empty.

### Setup-Only Smoke Planning

Command:

```bash
export CUDA_INSTALL_PATH=/usr/local/cuda-13.1
export PATH="$CUDA_INSTALL_PATH/bin:$PATH"
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-trace-config-20260609-025836-smoke-plan \
  -r artifacts/s7/s7-trace-config-20260609-025836/sim-smoke-plan \
  -l local \
  -n
```

Evidence:

- `local-smoke-plan.log`, exit `0`
- `sim-smoke-plan-files.log`
- `setup-only-copied-runtime-inspection.log`

The copied runtime preserved `SONAME libcudart.so.13` and clean `ldd -r`
dependency resolution.

### One Local Smoke

Note: this smoke ran after the root-cause fix. A later source cleanup guarded
the direct `trace_driven.h` include and runtime `trace_config` allocation with
`#if TRACING_ON`; the final CUDA 13.1 release rebuild passed after that cleanup.
The guarded final code preserves the same `TRACE=1` behavior used by this smoke,
and no second smoke was run after the new blocker appeared.

Pre-smoke procman evidence:

- `procman-status-before.log`: `Nothing Active`
- `procman-status-after-plan.log`: `Nothing Active`

Command:

```bash
export CUDA_INSTALL_PATH=/usr/local/cuda-13.1
export PATH="$CUDA_INSTALL_PATH/bin:$PATH"
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-trace-config-20260609-025836-smoke \
  -r artifacts/s7/s7-trace-config-20260609-025836/sim-smoke \
  -l local \
  -c 1
```

Evidence:

- `local-smoke-run.log`, launcher exit `0`
- Exactly one procman job was queued: `Job 3`.
- `procman-status-poll-1.log`: one active job.
- `procman-status-poll-2.log`: one complete job.
- `procman-status-final.log`: `Nothing Active`
- `moved-output-inspection.log`
- `smoke-marker-grep.log`

Smoke result:

- The prior blocker is resolved. The moved output does not contain:
  `Unknown Option: '-is_extra_traces_enabled'`.
- The smoke advanced through config parsing and PTX parsing to a new blocker:

```text
GPGPU-Sim: ERROR while parsing output of ptxas (used to capture resource usage information)
GPGPU-Sim:     backprop-rodinia-2.7.sm_120.ptx (backprop-rodinia-2.1.sm_75.ptxas:5) Syntax error:

   ptxas info    : Used 28 registers, used 1 barriers, 400 bytes cmem[0], 8 bytes cmem[2]
                                         ^
```

The stderr file also contains:

```text
libgomp: Invalid value for environment variable OMP_NUM_THREADS:
```

No real simulator metrics appeared in `smoke-marker-grep.log`.

No repeated smoke was run after this new blocker appeared.

## Changed Files

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpusim_entrypoint.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpusim_entrypoint.h`
- `simulator-remodeled/gpu-simulator/main.cc`
- `docs/sm120-calibration/worker-logs/worker-20260609-025836-s7-trace-config.md`

Ignored/local artifacts:

- `artifacts/s7/s7-trace-config-20260609-025836/`

Pre-existing unrelated working-tree change observed and not modified by this
worker:

- `docs/sm120-calibration/supervisor-log.md`

## Reviewer Rounds

- Round 1 blank-context reviewer: ACCEPT.
  - Reviewer runner: `codex exec -s read-only`
  - Exit code: `0`
  - Evidence:
    `artifacts/s7/s7-trace-config-20260609-025836/reviewer-round1.prompt.txt`,
    `reviewer-round1-codex.stdout.txt`,
    `reviewer-round1-codex.stderr.txt`, and
    `reviewer-round1-codex.exitcode`
  - Reviewer summary: runtime `trace_config` registration is scoped and ordered
    correctly, ownership is correct for runtime-owned versus standalone
    stack-owned configs, evidence shows the unknown-option blocker is resolved
    and the single smoke advanced to the PTX/ptxas parser blocker, smoke
    discipline was acceptable, and protected config status was clean.

## Final Status

Accepted. The `-is_extra_traces_enabled` unknown-option smoke blocker is
resolved for the CUDA runtime path. The current precisely bounded local smoke
blocker is CUDA 13.1 `ptxas` resource-output parsing of:

```text
ptxas info    : Used 28 registers, used 1 barriers, 400 bytes cmem[0], 8 bytes cmem[2]
```

No simulator metrics were produced.
