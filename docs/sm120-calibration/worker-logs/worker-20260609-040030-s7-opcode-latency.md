# S7 Opcode Latency Segfault Worker Log

## Purpose

Resolve or precisely bound the local smoke segmentation fault previously mapped
to:

```text
ptx_instruction::set_opcode_and_latency()
simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/cuda-sim.cc:768
```

The task scope excludes accepted config edits, generated bulk-output edits,
calibration `latest` promotion, fake metrics, and full simulator execution on
`dsp5060`.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Host: `dsp-ubuntu`
- Base HEAD: `9822684a8595c53a4f690a30bd6a76a5501f43af`
- Base subject: `fix: parse CUDA 13 ptxas compile time lines`
- Timestamp: `2026-06-09T04:00:30+08:00`
- Run id: `s7-opcode-latency-20260609-040030`
- Artifact root: `artifacts/s7/s7-opcode-latency-20260609-040030/`
- Initial working tree: pre-existing supervisor edit in
  `docs/sm120-calibration/supervisor-log.md`; not modified by this worker.

## Actions

- Confirmed the generated SM120 config provides opcode latency options, but the
  CUDA runtime path destroyed its temporary `option_parser_t` at the end of
  `gpgpu_context::gpgpu_ptx_sim_init_perf()`.
- Root cause: `OPT_CSTR` parsed values are owned by `OptionRegistry<char *>`.
  Destroying the parser deleted the parsed opcode latency strings and reset the
  registered `cuda_sim` pointers to `NULL`; later PTX setup called `sscanf` on
  those pointers.
- Added `GPGPUsim_ctx::g_runtime_config_opp` so the runtime parser survives for
  the simulator context lifetime. The standalone trace-simulator path already
  keeps its parser alive until simulation teardown.
- Added shared `cuda_sim` helpers to parse opcode latency, opcode initiation,
  and CDP latency strings with clear validation instead of unchecked `sscanf`.
- Reused the same helpers from `ptx_instruction::set_opcode_and_latency()` and
  `shader_core_config::set_pipeline_latency()`.
- Preserved older five-field integer opcode latency/initiation configs by
  filling the optional `SHFL` slot from the registered defaults:
  latency `32`, initiation `4`.

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
- `rebuild-gpgpusim-final.log`, exit `0`, after formatting-only cleanup.
- `rebuild-gpgpusim-strict-parser-final.log`, exit `0`, after replacing the
  CSV helper with stricter unsigned-token parsing.

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
- `git-diff-check-final.log`, exit `0`.
- `git-diff-check-final2.log`, exit `0`.

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
  -N s7-opcode-latency-20260609-040030-smoke-plan \
  -r artifacts/s7/s7-opcode-latency-20260609-040030/sim-smoke-plan \
  -l local \
  -n
```

Evidence:

- `procman-status-before-plan-corrected.log`: `Nothing Active`.
- `process-scan-before-plan-final.log`: no local workspace simulator jobs.
- `local-smoke-plan.log`, exit `0`.
- `sim-smoke-plan-files.log` records copied config and runtime.
- `procman-status-after-plan-before-smoke.log`: `Nothing Active`.

Note: an initial `procman.py -p` probe failed because `procman.py` was not on
`PATH`; the corrected helper path was
`simulator-remodeled/util/job_launching/procman.py`.

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
  -N s7-opcode-latency-20260609-040030-smoke \
  -r artifacts/s7/s7-opcode-latency-20260609-040030/sim-smoke \
  -l local \
  -c 1
```

Evidence:

- `local-smoke-run.log`, launcher exit `0`.
- Exactly one procman job was queued: `Job 6`.
- `procman-status-poll-1.log` and `procman-status-poll-2.log`: one active job.
- `procman-status-poll-3.log` and `procman-status-after-smoke.log`:
  `Nothing Active`.
- `smoke-parsed-opcode-options.log` records non-null parsed opcode latency and
  initiation strings in the simulator output.
- `smoke-key-lines.log` shows the smoke advanced past the former
  `set_opcode_and_latency()` point to:

```text
GPGPU-Sim PTX: cudaLaunch for ... (mode=performance simulation) on stream 0
GPGPU-Sim PTX: ... done pre-decoding instructions for '_Z22bpnn_layerforward_CUDAPfS_S_S_ii'.
GPGPU-Sim PTX: pushing kernel '_Z22bpnn_layerforward_CUDAPfS_S_S_ii' to stream 0, gridDim= (1,256,1) blockDim = (16,16,1)
```

Smoke result:

- The assigned opcode-latency null/lifetime crash is resolved for this smoke.
- No real simulator metrics appeared:
  `smoke-metrics-scan.log`, no `gpu_tot_sim_cycle`, `gpu_sim_cycle`, or
  simulation exit markers.
- The smoke advanced to a new segmentation fault in the remodeled subcore issue
  stage. `coredump-offset-symbolization.log` maps the top frames to:

```text
Subcore::issue(SM*)
simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc:514

Subcore::cycle()
simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc:107
```

- `gdb-core-backtrace.log` further bounds the new blocker:

```text
shared_sm->m_sm_stats.m_stats_map["total_num_cycles_issue_stage_stall_no_valid_instruction"]->increment_with_integer(1);
$2 = std::map with 1 element = {
  ["total_num_cycles_issue_stage_stall_no_valid_instruction"] =
    std::shared_ptr<Single_stat_abstract> (empty) = {get() = 0x0}
}
```

- Stderr still contains the pre-existing environment warning:

```text
libgomp: Invalid value for environment variable OMP_NUM_THREADS:
```

No second local smoke was run after the new blocker appeared.

## Changed Files

Code:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/cuda-sim.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/cuda-sim.h`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpusim_entrypoint.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpusim_entrypoint.h`

Documentation:

- `docs/sm120-calibration/worker-logs/worker-20260609-040030-s7-opcode-latency.md`

Pre-existing unrelated working-tree change observed and not modified by this
worker:

- `docs/sm120-calibration/supervisor-log.md`

Ignored/local artifacts:

- `artifacts/s7/s7-opcode-latency-20260609-040030/`

## Reviewer Rounds

- Round 1 blank-context reviewer: `ACCEPT`, no blocking findings.
  - Prompt: `reviewer-round1.prompt.txt`.
  - Stdout/verdict: `reviewer-round1-codex.stdout.txt`.
  - Stderr/tool transcript: `reviewer-round1-codex.stderr.txt`.
  - Exit code: `reviewer-round1-codex.exitcode`, value `0`.
  - Non-blocking note: update this worker log from pending to accepted after the
    verdict.

## Final Status

Accepted by the worker-spawned blank-context reviewer. The assigned
`ptx_instruction::set_opcode_and_latency()` segmentation fault is fixed for the
local smoke. The smoke now reaches kernel stream push and stops at a new
remodeled issue-stage stats registration/null counter blocker in
`Subcore::issue(SM*)`.
