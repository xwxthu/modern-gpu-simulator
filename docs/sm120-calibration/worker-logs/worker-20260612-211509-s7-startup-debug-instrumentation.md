# S7 Startup Debug Instrumentation Worker Log

## Purpose

Add minimal default-off early startup / first-output instrumentation to localize
S7 runs where ProcMan shows a CPU-heavy simulator process but stdout remains
`0` bytes before any existing `GPGPUSIM_KERNEL_DISPATCH_DEBUG` or
`GPGPUSIM_KERNEL_PROGRESS_DEBUG` line appears.

This work does not promote configs, does not generate candidate metrics, does
not modify accepted/generated/latest configs, and does not change job aliases.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base checkpoint: `4bc66b5` (`docs: record SM120 candidate0002 silent diagnostic`)
- Timestamp: `2026-06-12T21:15:09+08:00`
- Host: `dsp-ubuntu`
- Assigned scope: narrow startup/first-output diagnostics in simulator runtime
  and launch handoff paths.

Pre-existing tracked modification observed and not edited by this worker:

- `docs/sm120-calibration/supervisor-log.md`

## Mandatory Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-204302-s7-candidate0002-bounded-diagnostic.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-194351-s7-dispatch-bind-instrumentation.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-201232-s7-candidate0001-final-dispatch-diagnostic.md`

## Code Paths Inspected

- Runtime/device initialization and simulator thread startup:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/libcuda/cuda_runtime_api.cc`
  and `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpusim_entrypoint.cc`
- GPGPU-Sim option/config parsing, trace option/config parse, GPU and stream
  manager creation:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpusim_entrypoint.cc`
- CUDA fat-binary registration, function registration, launch setup, grid
  initialization, PDOM/launch handoff, and stream enqueue:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/libcuda/cuda_runtime_api.cc`
  and `simulator-remodeled/gpu-simulator/gpgpu-sim/src/stream_manager.cc`
- Existing dispatch/progress debug gates:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-sim.cc`

## Changed Files

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpusim_entrypoint.h`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpusim_entrypoint.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/libcuda/cuda_runtime_api.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/stream_manager.cc`
- `docs/sm120-calibration/worker-logs/worker-20260612-211509-s7-startup-debug-instrumentation.md`

## Source Changes

Added a shared startup diagnostic helper:

```text
GPGPUSIM_STARTUP_DEBUG=1
```

When disabled, the helper caches the env check and returns without output.
When enabled, it emits immediately flushed stderr lines with a consistent
prefix:

```text
GPGPUSIM-STARTUP enabled (env:GPGPUSIM_STARTUP_DEBUG)
GPGPUSIM-STARTUP stage=<stage> ...
```

Instrumentation boundaries now include:

- runtime init enter/device creation/device ready,
- simulator init enter, splash printed, simulator/parser env read,
- option parser creation, GPU and trace option registration,
- option parse done, locale set, GPU config init, trace config parse,
- custom options set, GPU created, stream manager created,
- simulator thread start and first work detected,
- fat binary registration,
- CUDA function registration,
- CUDA launch enter/context ready/config ready,
- grid init begin/kernel lookup/finalize,
- launch grid init done,
- stream manager push begin/done,
- launch stream push done and launch done.

The new diagnostics intentionally use stderr so they are useful when ProcMan
stdout remains empty or fully buffered.

Supervisor-review rework changed the env gate from unsynchronized mutable
function statics to C++11 thread-safe local-static initialization:

```text
static const bool enabled = []() { ... }();
```

The rework also casts newly added startup diagnostic `%p` arguments explicitly
to `void *`.

Second reviewer rework tightened the env contract: only the exact string `0`
disables the diagnostic. Non-empty values such as `01` and `0debug` now enable
the diagnostic as requested.

## Evidence

Relevant source anchors after implementation:

- `gpgpusim_startup_debug_enabled()` and flushed stderr output:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpusim_entrypoint.cc:51`
- simulator config/trace/GPU/stream-manager creation markers:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpusim_entrypoint.cc:260`
- runtime device initialization:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/libcuda/cuda_runtime_api.cc:193`
- fat binary and function registration:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/libcuda/cuda_runtime_api.cc:598`
  and `simulator-remodeled/gpu-simulator/gpgpu-sim/libcuda/cuda_runtime_api.cc:787`
- CUDA launch and stream handoff:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/libcuda/cuda_runtime_api.cc:940`
  and `simulator-remodeled/gpu-simulator/gpgpu-sim/src/stream_manager.cc:445`
- grid initialization:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/libcuda/cuda_runtime_api.cc:4142`

## Commands Run

```bash
sed -n '1,240p' docs/sm120-calibration/supervisor-log.md
sed -n '1,240p' docs/sm120-calibration/overall-plan.md
sed -n '1,240p' docs/sm120-calibration/worker-logs/worker-20260612-204302-s7-candidate0002-bounded-diagnostic.md
sed -n '1,240p' docs/sm120-calibration/worker-logs/worker-20260612-194351-s7-dispatch-bind-instrumentation.md
sed -n '1,240p' docs/sm120-calibration/worker-logs/worker-20260612-201232-s7-candidate0001-final-dispatch-diagnostic.md
rg -n "GPGPUSIM_KERNEL_(PROGRESS|DISPATCH)_DEBUG|GPGPUSIM-DISPATCH|GPGPUSIM-K.*PROGRESS|main\\(|gpgpu_ptx_sim_init|OptionParser|read_config|stream_manager|gpgpu_sim" simulator-remodeled/gpu-simulator/gpgpu-sim/src simulator-remodeled/gpu-simulator/libcuda -g '*.{cc,cpp,c,h}'
rg -n "gpgpu_ptx_sim_init_perf|start_sim_thread|gpgpu_ptx_sim|cudaLaunch|cuLaunch|__cudaRegister|register_function|gpgpu_cuda_ptx_sim_init_grid|stream_operation" simulator-remodeled/gpu-simulator/gpgpu-sim/libcuda simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim -g '*.{cc,cpp,c,h}'
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release && make -C simulator-remodeled/gpu-simulator/gpgpu-sim -j"$(nproc)"
git diff --check
python3 simulator-remodeled/util/job_launching/procman.py -p
find simulator-remodeled/util/job_launching/configs -maxdepth 1 -name 'define-s7-bounded-sweep-temp.yml' -print
git status --short
```

Command results:

- Initial simulator rebuild passed, exit code `0`. Warnings were existing
  deprecation/hidden-virtual warning classes.
- `git diff --check`: passed, exit code `0`.
- ProcMan final check: `Nothing Active`.
- Temporary alias check: no `define-s7-bounded-sweep-temp.yml` found.
- No ProcMan diagnostic job was run for this worker.

Additional supervisor-review rework commands:

```bash
rg -n "gpgpusim_startup_debug\\(|%p|gpgpusim_startup_debug_enabled" simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpusim_entrypoint.cc simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpusim_entrypoint.h simulator-remodeled/gpu-simulator/gpgpu-sim/libcuda/cuda_runtime_api.cc simulator-remodeled/gpu-simulator/gpgpu-sim/src/stream_manager.cc
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release && make -C simulator-remodeled/gpu-simulator/gpgpu-sim -j"$(nproc)"
git diff --check
python3 simulator-remodeled/util/job_launching/procman.py -p
find simulator-remodeled/util/job_launching/configs -maxdepth 1 -name 'define-s7-bounded-sweep-temp.yml' -print
git status --short
```

Additional command results:

- Rebuild after supervisor-review rework passed, exit code `0`. Warnings were
  existing deprecation/hidden-virtual/maybe-uninitialized warning classes.
- `git diff --check`: passed, exit code `0`.
- ProcMan final check: `Nothing Active`.
- Temporary alias check: no `define-s7-bounded-sweep-temp.yml` found.
- No ProcMan diagnostic job was run for the rework.

Additional second-reviewer rework commands:

```bash
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release && make -C simulator-remodeled/gpu-simulator/gpgpu-sim -j"$(nproc)"
git diff --check
python3 simulator-remodeled/util/job_launching/procman.py -p
find simulator-remodeled/util/job_launching/configs -maxdepth 1 -name 'define-s7-bounded-sweep-temp.yml' -print
git status --short
```

Additional second-reviewer command results:

- Rebuild after exact-`0` env fix passed, exit code `0`. Warnings were existing
  deprecation/hidden-virtual/maybe-uninitialized warning classes.
- `git diff --check`: passed, exit code `0`.
- ProcMan final check: `Nothing Active`.
- Temporary alias check: no `define-s7-bounded-sweep-temp.yml` found.
- No ProcMan diagnostic job was run for this rework.

## Reviewer Rounds

### Round 1

- Reviewer: blank-context subagent `019ebbf8-9fb3-7711-8772-5a52a5cb8242`
- Verdict: `ACCEPT`
- Findings: no blocking findings.
- Reviewer summary:
  - Instrumentation is default-off via `GPGPUSIM_STARTUP_DEBUG`.
  - Output goes to flushed stderr with consistent `GPGPUSIM-STARTUP` prefix.
  - Coverage is adequate for runtime/device creation, config/env/trace parse,
    GPU/stream-manager creation, registration, launch, grid init, and stream
    handoff.
  - Disabled overhead is limited to cheap function calls and nearby argument
    evaluation.
  - No config, stdout, simulator state, result behavior, or compile-risk issue
    was apparent beyond existing local style patterns.

### Supervisor Review

- Verdict: `CHANGES_NEEDED`
- Findings:
  1. `gpgpusim_startup_debug_enabled()` used unsynchronized mutable static
     `checked/enabled`, which could race on first call from concurrent
     CUDA/runtime paths.
  2. Newly added diagnostics using `%p` should pass `void *` arguments
     explicitly.
- Fixes:
  - Replaced the env gate with C++11 thread-safe local-static lambda
    initialization while preserving the same enable policy and one-time flushed
    banner.
  - Cast newly added startup diagnostic pointer arguments to `void *`,
    including `hostFun` and `fatCubin`.

### Round 2

- Reviewer: fresh blank-context subagent `019ebc01-646c-7970-b74f-99b4ae0f6903`
- Verdict: `CHANGES_NEEDED`
- Finding:
  - The env gate disabled any value whose first character was `0`. The requested
    behavior disables only the exact string `0`.
- Fix:
  - Changed the env gate to `env && env[0] != '\0' && strcmp(env, "0") != 0`
    and added `<string.h>`.

### Round 3

- Reviewer: fresh blank-context subagent `019ebc04-a3c4-73e0-80eb-31a2f38849e5`
- Verdict: `ACCEPT`
- Findings: no blocking findings.
- Reviewer summary:
  - `gpgpusim_startup_debug_enabled()` uses C++ function-local static
    initialization and enables only when `GPGPUSIM_STARTUP_DEBUG` is non-empty
    and not exactly `0`.
  - Enabled banner is emitted once and flushes `stderr`.
  - Startup diagnostics use `GPGPUSIM-STARTUP` and flush each line.
  - New startup `%p` diagnostics explicitly pass `void *`, including
    device/GPU, `hostFun`, `context`, and kernel lookup pointers.
  - Diff scope is instrumentation/docs only; no config, results, or promotion
    paths were touched.

## No-Promotion Confirmation

- No candidate metrics were generated.
- No S6 report was generated.
- No accepted/generated/latest configs were edited.
- No calibration result was promoted.
- No job aliases were added or changed.
- No local ProcMan diagnostic job was launched.

## Final Status

Complete. The simulator now has default-off stderr startup diagnostics suitable
for a follow-up bounded `candidate_0002` silent-path diagnostic using
`GPGPUSIM_STARTUP_DEBUG=1` alongside the existing dispatch/progress debug
variables.
