# S7 PTXAS Compile-Time Parser Worker Log

## Purpose

Resolve or precisely bound the local smoke blocker in CUDA 13.1 `ptxas`
informational-output parsing:

```text
GPGPU-Sim: ERROR while parsing output of ptxas (used to capture resource usage information)
ptxas info    : Compile time = 2.998 ms
```

This worker must not run the full simulator on `dsp5060`, must not modify
accepted configs, calibration `latest.yaml`, generated bulk outputs, or real
metrics artifacts, and must not fake or promote metrics.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Host: `dsp-ubuntu`
- Base HEAD: `f151f8100379`
- Base subject: `fix: parse CUDA 13 ptxas barrier usage`
- Timestamp: `2026-06-09T03:36:52+08:00`
- Run id: `s7-ptxas-compile-time-20260609-033652`
- Artifact root: `artifacts/s7/s7-ptxas-compile-time-20260609-033652/`
- Initial working tree: pre-existing unrelated modification observed in
  `docs/sm120-calibration/supervisor-log.md`.

## Inputs Reviewed

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- Prior worker log:
  `docs/sm120-calibration/worker-logs/worker-20260609-031826-s7-ptxas-parser.md`
- PTXAS resource parser:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/ptxinfo.l`
  and `ptxinfo.y`
- Smoke evidence from the prior worker under
  `artifacts/s7/s7-ptxas-parser-20260609-031826/`

## Actions

- Confirmed the current parser accepted CUDA 13.1 barrier/resource lines but
  did not recognize `ptxas info : Compile time = <float> ms`.
- Added a lexer rule that recognizes the whole CUDA 13.x compile-time payload
  as a `COMPILE_TIME` token:

```text
Compile time = <integer-or-decimal> ms
```

- Added a no-op `line_info` grammar arm for `COMPILE_TIME`.
- Kept resource parsing strict: the rule only applies after the existing
  `HEADER INFO COLON` prefix and does not bypass parsing of register, barrier,
  memory, or cmem-bank resource forms.

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

- `rebuild-gpgpusim.log`, exit `0`.
- `rebuild-gpgpusim-final.log`, exit `0`, after final source whitespace
  cleanup.
- `rebuild-final-key-lines.log` shows `bison` regenerated `ptxinfo`, compiled
  `ptxinfo.tab.o` and `lex.ptxinfo_.o`, and retained the pre-existing
  `ptxinfo.y` two reduce/reduce conflicts.

### Generator And Whitespace Checks

Commands:

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
git diff --check
```

Evidence:

- `generate-check-only.log`, exit `0`.
- `generate-check-only-final.log`, exit `0`.
- `git-diff-check.log`, exit `0`.
- `git-diff-check-final2.log`, exit `0`.
- `protected-config-scoped-status-final.log` is empty; no accepted configs,
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
  -N s7-ptxas-compile-time-20260609-033652-smoke-plan \
  -r artifacts/s7/s7-ptxas-compile-time-20260609-033652/sim-smoke-plan \
  -l local \
  -n
```

Evidence:

- `procman-status-before-plan-corrected.log`: `Nothing Active`.
- `local-smoke-plan.log`, exit `0`.
- `sim-smoke-plan-files.log` records the dry-run files and copied runtime.
- `procman-status-after-plan.log`: `Nothing Active`.
- `process-scan-before-plan.log` found unrelated `accel-sim.out` processes
  outside this workspace; local procman state for this workspace was idle.

Process note:

- An earlier status probe used `procman.py status`, which is not the local
  procman status CLI and failed by trying to stat an executable named
  `status`. The corrected status command is `procman.py -p`; only the
  corrected status was used as the smoke gate.

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
  -N s7-ptxas-compile-time-20260609-033652-smoke \
  -r artifacts/s7/s7-ptxas-compile-time-20260609-033652/sim-smoke \
  -l local \
  -c 1
```

Evidence:

- `local-smoke-run.log`, launcher exit `0`.
- Exactly one procman job was queued: `Job 5`.
- `procman-status-poll-1.log`: one active job.
- `procman-status-poll-2.log`: `Nothing Active`.
- `ptxas-file-numbered.log` records the exact CUDA 13.1 `ptxas -v` output,
  including `Compile time = 3.823 ms` and `Compile time = 2.857 ms` for the
  `sm_120` PTX.
- `compile-time-parser-evidence.log` records compile-time lines across all
  generated ptxas files and no parser syntax error on those lines.
- `smoke-final-marker-grep.log` and `smoke-key-lines.log` record the resolved
  blocker and the next blocker.

Smoke result:

- The assigned compile-time parser blocker is resolved. The smoke no longer
  fails on `ptxas info    : Compile time = ... ms`.
- The parser consumed the `sm_120` ptxas file and produced:

```text
GPGPU-Sim PTX: Kernel '_Z24bpnn_adjust_weights_cudaPfiS_iS_S_' : regs=31, lmem=0, smem=0, cmem=0
GPGPU-Sim PTX: Kernel '_Z22bpnn_layerforward_CUDAPfS_S_S_ii' : regs=18, lmem=0, smem=1088, cmem=0
```

- The smoke advanced to performance-simulation launch:

```text
GPGPU-Sim PTX: cudaLaunch for 0x0x5ee83255d940 (mode=performance simulation) on stream 0
GPGPU-Sim PTX: Finding immediate postdominators for '_Z22bpnn_layerforward_CUDAPfS_S_S_ii'...
```

- The next blocker is a segmentation fault before real simulator metrics:

```text
slurm.sim: line 59: 2348067 Segmentation fault (core dumped) .../backprop-rodinia-2.0-ft 4096 ./data/result-4096.txt
```

- `coredumpctl-info-2348067.log` records `Signal: 11 (SEGV)` for PID
  `2348067`.
- `coredump-offset-symbolization.log` maps the top simulator-library frame
  `libcudart.so + 0x196ab6` to:

```text
ptx_instruction::set_opcode_and_latency()
simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/cuda-sim.cc:768
```

- `cuda-sim-set-opcode-context.log` shows line 768 is the `sscanf` of
  `gpgpu_ctx->func_sim->opcode_latency_fp`.
- Stderr still contains:

```text
libgomp: Invalid value for environment variable OMP_NUM_THREADS:
```

- No real simulator metrics appeared; `smoke-error-metrics-scan.log` found no
  `gpu_tot_sim_cycle`, `gpu_sim_cycle`, or simulation-exit metrics.
- No second smoke was run after the new blocker appeared.

## Changed Files

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/ptxinfo.l`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/ptxinfo.y`
- `docs/sm120-calibration/worker-logs/worker-20260609-033652-s7-ptxas-compile-time.md`

Ignored/local artifacts:

- `artifacts/s7/s7-ptxas-compile-time-20260609-033652/`

Pre-existing unrelated working-tree change observed and not modified by this
worker:

- `docs/sm120-calibration/supervisor-log.md`

## Reviewer Rounds

- Round 1 blank-context reviewer: ACCEPT.
  - Reviewer runner: `codex exec -s read-only`
  - Exit code: `0`
  - Evidence:
    `artifacts/s7/s7-ptxas-compile-time-20260609-033652/reviewer-round1.prompt.txt`,
    `reviewer-round1-codex.stdout.txt`,
    `reviewer-round1-codex.stderr.txt`, and
    `reviewer-round1-codex.exitcode`.
  - Reviewer summary: the lexer/grammar change is minimal and scoped, existing
    register/barrier/memory/cmem parsing paths are unchanged, rebuild and smoke
    evidence demonstrate compile-time lines were consumed, protected config
    scope is clean, no metrics were fabricated, and the remaining
    `overall-plan.md` current-blocker text is supervisor follow-up rather than
    a worker defect.

## Final Status

Accepted. The assigned CUDA 13.1 `Compile time = ... ms` parser blocker is
resolved, and the next blocker is precisely bounded as a local smoke
segmentation fault before simulator metrics in:

```text
ptx_instruction::set_opcode_and_latency()
simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/cuda-sim.cc:768
```
