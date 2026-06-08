# S7 PTXAS Parser Worker Log

## Purpose

Resolve or precisely bound the local smoke blocker in CUDA 13.1 `ptxas`
resource-output parsing:

```text
GPGPU-Sim: ERROR while parsing output of ptxas (used to capture resource usage information)
ptxas info    : Used 28 registers, used 1 barriers, 400 bytes cmem[0], 8 bytes cmem[2]
```

This worker must not run the full simulator on `dsp5060`, must not modify
accepted configs, calibration `latest.yaml`, generated bulk outputs, or real
metrics artifacts, and must not fake or promote metrics.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Host: `dsp-ubuntu`
- Base HEAD: `06fd88c2220c`
- Base subject: `fix: register trace config on cudart path`
- Timestamp: `2026-06-09T03:18:26+08:00`
- Run id: `s7-ptxas-parser-20260609-031826`
- Artifact root: `artifacts/s7/s7-ptxas-parser-20260609-031826/`
- Initial working tree: only pre-existing unrelated modification observed in
  `docs/sm120-calibration/supervisor-log.md`.

## Inputs Reviewed

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- Prior worker log:
  `docs/sm120-calibration/worker-logs/worker-20260609-025836-s7-trace-config.md`
- PTXAS resource parser:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/ptxinfo.l`
  and `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/ptxinfo.y`
- Parser resource callbacks:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/cuda-sim.cc`
- Kernel resource data model:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/abstract_hardware_model.h`
- Parser build rules:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/Makefile`

## Actions

- Confirmed the parser had an existing `ptxinfo_barriers(unsigned)` callback
  and `gpgpu_ptx_sim_info::barriers` field, but the lexer/grammar did not
  recognize CUDA 13.1 `ptxas -v` resource text `used 1 barriers`.
- Added lexer tokens for lowercase `used` and singular/plural
  `barrier(s)`.
- Added grammar productions for `USED INT_OPERAND BARRIERS` and legacy-style
  `INT_OPERAND BARRIERS`, both routed to `ptxinfo_barriers($N)`.
- Reset `g_ptxinfo.barriers` in `clear_ptxinfo()` with the other resource
  counters to avoid stale barrier counts between parsed kernels.

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

- `artifacts/s7/s7-ptxas-parser-20260609-031826/rebuild-gpgpusim.log`,
  exit `0`.
- The rebuild regenerated and compiled the modified `ptxinfo` parser:
  `bison --name-prefix=ptxinfo_ ... ptxinfo.y` and
  `flex --outfile=.../lex.ptxinfo_.c ptxinfo.l`.
- The rebuilt runtime linked as `libcudart.so` with `SONAME
  libcudart.so.13`.
- `artifacts/s7/s7-ptxas-parser-20260609-031826/rebuilt-runtime-inspection.log`
  shows `ldd -r` completed without unresolved-symbol output.

The rebuild reported the existing `ptxinfo.y` two reduce/reduce conflicts.
`parser-conflicts/orig-bison.log` and `parser-conflicts/current-bison.log`
show the same conflict count and the same `INT_OPERAND BYTES GMEM` example for
base `06fd88c2220c` and the modified grammar, so the conflict warning was not
introduced by this worker.

### Generator And Whitespace Checks

Commands:

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
git diff --check
```

Evidence:

- `generate-check-only.log`, exit `0`.
- `git-diff-check.log`, exit `0`.
- `protected-config-scoped-status.log` is empty; no accepted configs,
  calibration latest, or generated bulk config outputs were modified.

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
  -N s7-ptxas-parser-20260609-031826-smoke-plan \
  -r artifacts/s7/s7-ptxas-parser-20260609-031826/sim-smoke-plan \
  -l local \
  -n
```

Evidence:

- `local-smoke-plan.log`, exit `0`.
- `sim-smoke-plan-files.log` records the dry-run files and copied runtime.
- `procman-status-before-plan.log` and `procman-status-after-plan.log` both
  report `Nothing Active`.

Process note:

- `process-scan-before-plan.log` found unrelated `accel-sim.out` processes
  outside this workspace. The local procman state for this workspace was idle,
  which was the gating condition for the local smoke.

### One Local Smoke

Command:

```bash
export CUDA_INSTALL_PATH=/usr/local/cuda-13.1
export PATH="$CUDA_INSTALL_PATH/bin:$PATH"
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-ptxas-parser-20260609-031826-smoke \
  -r artifacts/s7/s7-ptxas-parser-20260609-031826/sim-smoke \
  -l local \
  -c 1
```

Evidence:

- `local-smoke-run.log`, launcher exit `0`.
- Exactly one procman job was queued: `Job 4`.
- `procman-status-poll-1.log`: one active job.
- `procman-status-poll-2.log`: one complete job.
- `procman-status-final.log`: `Nothing Active`.
- `ptxas-file-numbered.log` records the exact CUDA 13.1 `ptxas -v` output.
- `smoke-final-marker-grep.log` records the resolved blocker and the next
  blocker.

Smoke result:

- The assigned blocker is resolved. The smoke no longer fails on:

```text
ptxas info    : Used 28 registers, used 1 barriers, 400 bytes cmem[0], 8 bytes cmem[2]
```

- The parser consumed that line and produced:

```text
GPGPU-Sim PTX: Kernel '_Z24bpnn_adjust_weights_cudaPfiS_iS_S_' : regs=28, lmem=0, smem=0, cmem=408
```

- The smoke advanced to a new CUDA 13.1 `ptxas` output blocker:

```text
GPGPU-Sim: ERROR while parsing output of ptxas (used to capture resource usage information)
GPGPU-Sim:     backprop-rodinia-2.7.sm_120.ptx (backprop-rodinia-2.1.sm_75.ptxas:6) Syntax error:

   ptxas info    : Compile time = 2.998 ms
                         ^
```

- Stderr still contains:

```text
libgomp: Invalid value for environment variable OMP_NUM_THREADS:
```

- No real simulator metrics appeared in `smoke-final-marker-grep.log`.

No second smoke was run after the new blocker appeared.

## Changed Files

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/ptxinfo.l`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/ptxinfo.y`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/cuda-sim.cc`
- `docs/sm120-calibration/worker-logs/worker-20260609-031826-s7-ptxas-parser.md`

Ignored/local artifacts:

- `artifacts/s7/s7-ptxas-parser-20260609-031826/`

Pre-existing unrelated working-tree change observed and not modified by this
worker:

- `docs/sm120-calibration/supervisor-log.md`

## Reviewer Rounds

- Round 1 blank-context reviewer: ACCEPT.
  - Reviewer runner: `codex exec -s read-only`
  - Exit code: `0`
  - Evidence:
    `artifacts/s7/s7-ptxas-parser-20260609-031826/reviewer-round1.prompt.txt`,
    `reviewer-round1-codex.stdout.txt`,
    `reviewer-round1-codex.stderr.txt`, and
    `reviewer-round1-codex.exitcode`.
  - Reviewer summary: the parser change is scoped, preserves existing
    resource forms, routes CUDA 13.1 `used 1 barriers` to the existing barrier
    model, clears barrier state with other kernel resources, validates with a
    rebuild and one smoke, and precisely bounds the next `Compile time = ...
    ms` parser blocker. No findings.

## Final Status

Accepted. The assigned CUDA 13.1 `used 1 barriers` parser blocker is resolved,
and the next blocker is precisely bounded as parsing of:

```text
ptxas info    : Compile time = 2.998 ms
```
