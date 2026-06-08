# S7 Trace Runtime Link Worker Log

## Purpose

Resolve or precisely bound the local smoke blocker where the CUDA 13.1
GPGPU-Sim runtime loaded as `libcudart.so.13` failed with unresolved
`_ZTV16trace_shd_warp_t`. This worker did not run a full simulator on
`dsp5060`, did not write `accepted configs/latest.yaml`, did not write any
calibration `latest.yaml`, and did not fake metrics.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Host: `dsp-ubuntu`
- Base HEAD: `4a32e4c9486ce807978bec5f46017d80aee3ff79`
- Base subject: `fix: add CUDA 13 cudart ABI support`
- Timestamp: `2026-06-09T02:33:11+08:00`
- Run id: `s7-trace-link-20260609-023311`
- Artifact root: `artifacts/s7/s7-trace-link-20260609-023311/`

## Inputs Reviewed

- Prior worker log:
  `docs/sm120-calibration/worker-logs/worker-20260609-020840-s7-cuda13-abi.md`
- Prior blocker artifacts:
  `artifacts/s7/s7-cuda13-abi-20260609-015602/new-blocker-symbols.log`
  `new-blocker-object-search.log`, `new-blocker-source-search.log`,
  `new-blocker-link-evidence.log`, and `moved-output-inspection.log`
- Runtime build files:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/Makefile` and sub-Makefiles
- Trace support build/source files:
  `simulator-remodeled/gpu-simulator/trace-driven/Makefile`,
  `trace_driven.cc`, `trace_driven.h`,
  `simulator-remodeled/gpu-simulator/trace-parser/Makefile`,
  and `simulator-remodeled/util/traces_enhanced/Makefile`
- Runtime trace option paths:
  `simulator-remodeled/gpu-simulator/main.cc` and
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpusim_entrypoint.cc`

## Root Cause Addressed

The rebuilt GPGPU-Sim `libcudart.so.13` linked GPGPU-Sim core and remodeling
objects that reference trace-driven and enhanced-trace classes, but did not link
the objects that define them. The immediate loader blocker was the
`trace_shd_warp_t` vtable, defined by `trace-driven/trace_driven.cc`.

The minimal existing object set required to close the local unresolved set is:

- `simulator-remodeled/gpu-simulator/build/<config>/trace_driven.o`
- `simulator-remodeled/gpu-simulator/build/<config>/trace_parser.o`
- `simulator-remodeled/util/traces_enhanced/obj/*.o`
- `simulator-remodeled/util/traces_enhanced/pb_trace/obj/*.o`
- system libraries after object inputs: `-lz` and `-lprotobuf`

This set is the same trace support family already used by the standalone
`accel-sim.out` link. It avoids linking unrelated tools. A temporary link probe
confirmed that this object set does not create a large dependency cascade or
duplicate-definition failure.

## Changes

- `simulator-remodeled/gpu-simulator/gpgpu-sim/Makefile`
  - Adds `ACCELSIM_ROOT`, `ACCELSIM_CONFIG`, trace-driven, trace-parser, and
    traces_enhanced object variables.
  - Adds a `trace_runtime_support` target when `TRACE=1`, reusing existing
    trace-driven/trace-parser/traces_enhanced Makefile targets.
  - Adds trace support objects to the Linux `libcudart.so` link.
  - Moves runtime system libraries after objects and adds `-lprotobuf`, so
    zlib/protobuf dynamic dependencies are emitted as `DT_NEEDED`.

No accepted/generated config or `latest.yaml` path was modified.

## Rebuild And Link Inspection

Commands:

```bash
export CUDA_INSTALL_PATH=/usr/local/cuda-13.1
export PATH="$CUDA_INSTALL_PATH/bin:$PATH"
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
make -C simulator-remodeled/gpu-simulator/gpgpu-sim -j"$(nproc)"
```

Evidence:

- `link-probe-actual.log`, exit `0`
- `rebuild-gpgpusim-trace-link.log`, exit `0`
- `rebuilt-lib-trace-link-inspection.log`
- `rebuilt-lib-ldd-r.log`, exit `0`
- `rebuilt-lib-non-system-undefined.log`
- `app-ldd-r-against-rebuilt-runtime.log`, exit `0`

Final rebuilt runtime evidence:

- `libcudart.so.13 -> libcudart.so` exists.
- `readelf -d` reports `SONAME libcudart.so.13`.
- `readelf -d` reports `DT_NEEDED` for `libz.so.1` and `libprotobuf.so.32`.
- `ldd -r` on the rebuilt runtime exits `0`.
- App-side `ldd -r` binds `libcudart.so.13` to the rebuilt GPGPU-Sim runtime.
- No non-system unresolved trace/remodeling/traces_enhanced candidates remain.

## Setup-Only

Command:

```bash
export CUDA_INSTALL_PATH=/usr/local/cuda-13.1
export PATH="$CUDA_INSTALL_PATH/bin:$PATH"
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-trace-link-20260609-023311-smoke-plan \
  -r artifacts/s7/s7-trace-link-20260609-023311/sim-smoke-plan \
  -l local \
  -n
```

- Exit code: `0`
- Copied runtime dir:
  `artifacts/s7/s7-trace-link-20260609-023311/sim-smoke-plan/gpgpu-sim-builds/gpgpu-sim_git-commit-4a32e4c9486ce807978bec5f46017d80aee3ff79_modified_1.0/`
- `setup-only-copied-runtime-inspection.log` shows the copied runtime keeps
  `SONAME libcudart.so.13`, `DT_NEEDED libz.so.1`, `DT_NEEDED libprotobuf.so.32`,
  and passes `ldd -r`.

## One Local Smoke

Command:

```bash
export CUDA_INSTALL_PATH=/usr/local/cuda-13.1
export PATH="$CUDA_INSTALL_PATH/bin:$PATH"
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-trace-link-20260609-023311-smoke \
  -r artifacts/s7/s7-trace-link-20260609-023311/sim-smoke \
  -l local \
  -c 1
```

- Launcher exit code: `0`
- Exactly one local procman job was queued.
- Poll 1 and 2: procman `RUNNING`.
- Final poll: procman `Nothing Active`.
- `job-status-final.log` reports `COMPLETE_ERR_FILE_HAS_CONTENTS`.
- Moved `.o2/.e2` outputs exist in the run dir.

Smoke result:

```text
GPGPU-Sim ** ERROR: Unknown Option: '-is_extra_traces_enabled'
```

The previous runtime loader blocker is resolved: the app starts GPGPU-Sim and
prints the simulator splash and PTX simulation mode before failing during config
option parsing. No simulator metrics were produced. `metrics-grep.log` contains
no `gpu_tot_sim_cycle`, `gpu_tot_sim_insn`, `gpu_tot_ipc`,
`gpgpu_simulation_time`, or `gpgpu_simulation_rate`.

## New Blocker

The current local smoke blocker is now configuration/initialization, not shared
library linking:

- The generated run config contains `-is_extra_traces_enabled 1`.
- `trace_config::reg_options()` in `trace-driven/trace_driven.cc` registers
  `-is_extra_traces_enabled`.
- The standalone trace-driven path in `gpu-simulator/main.cc` calls
  `trace_config::reg_options(opp)` via `gpgpu_trace_sim_init_perf_model`.
- The runtime cudart path in `gpgpu-sim/src/gpgpusim_entrypoint.cc` registers
  PTX, interconnect, and `gpgpu_sim_config` options, but does not register
  `trace_config` options before parsing `gpgpusim.config`.

Recommendation: handle this as the next, separate design point. The runtime now
links trace support, but its initialization path still does not instantiate and
register trace-driven `trace_config` options. A narrow follow-up would need to
decide where the runtime-owned `trace_config` should live and how it should
interact with `g_trace_config`; this worker stopped after the single allowed
local smoke.

## Artifact Summary

- Link/rebuild:
  `link-probe-actual.log`, `rebuild-gpgpusim-trace-link.log`,
  `rebuilt-lib-trace-link-inspection.log`, `rebuilt-lib-ldd-r.log`,
  `rebuilt-lib-non-system-undefined.log`
- App/runtime loader:
  `app-ldd-r-against-rebuilt-runtime.log`,
  `setup-only-copied-runtime-inspection.log`
- Setup/smoke:
  `local-smoke-plan.log`, `sim-smoke-plan-files.log`,
  `local-smoke-run.log`, `procman-status-poll-1.log`,
  `procman-status-poll-2.log`, `procman-status-poll-3.log`,
  `job-status-final.log`, `moved-output-inspection.log`, `metrics-grep.log`
- Source/change evidence:
  `source-diff.patch`, `artifact-files.list`, `artifact-files.sha256`

## Final Checks

- `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`
  - Exit code: `0`
  - Evidence: `final-generate-check-only.log`
  - Output generated `SM120_RTX5070_TI` and `SM120_RTX5060` bootstrap
    profiles with `gpgpu_keys=217` and `trace_keys=13`.
- `git diff --check`
  - Exit code: `0`
  - Evidence: `final-git-diff-check.log`
- Accepted/generated config scoped status:
  - Exit code: `0`
  - Evidence: `final-accepted-generated-config-scoped-status.log`
  - Output was empty. No accepted config, generated tested config,
    calibration result, or `latest.yaml` path was modified.

## Reviewer Rounds

- Round 1 blank-context reviewer: ACCEPT.
  - Reviewer runner: `codex exec -s read-only`
  - Exit code: `0`
  - Evidence: `reviewer-round1-codex.txt`
  - Reviewer summary: Makefile change is scoped to runtime linking and reuses
    existing trace-driven/trace-parser/traces_enhanced outputs; rebuilt CUDA
    13.1 `libcudart.so.13` passes `ldd -r` with no non-system unresolved
    trace symbols; the single smoke reached GPGPU-Sim startup and stopped on
    the new `-is_extra_traces_enabled` config parsing blocker; final checks and
    protected config/latest constraints pass.

## Status

`_ZTV16trace_shd_warp_t` and the associated trace-driven/remodeling/enhanced
trace runtime link blocker are resolved at build, loader, setup-only, and one
local smoke attempt. The next precise blocker is unknown runtime config option
`-is_extra_traces_enabled`; no simulator metrics were produced.
