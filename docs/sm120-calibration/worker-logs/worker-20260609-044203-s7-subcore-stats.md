# S7 Subcore Stats Worker Log

## Purpose

Resolve or precisely bound the local smoke segmentation fault in remodeled
issue-stage stats:

```text
Subcore::issue(SM*)
simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc:514
shared_sm->m_sm_stats.m_stats_map["total_num_cycles_issue_stage_stall_no_valid_instruction"] is an empty/null shared_ptr
```

The task scope excludes accepted config edits, generated bulk-output edits,
calibration `latest` promotion, fake metrics, and full simulator execution on
`dsp5060`.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Host: `dsp-ubuntu`
- Base HEAD: `494dfd7e25957431c486757315668e13610a82f0`
- Base subject: `fix: preserve runtime opcode latency options`
- Timestamp: `2026-06-09T04:42:03+08:00`
- Run id: `s7-subcore-stats-20260609-044203`
- Artifact root: `artifacts/s7/s7-subcore-stats-20260609-044203/`
- Initial working tree: pre-existing supervisor edit in
  `docs/sm120-calibration/supervisor-log.md`; not modified by this worker.

## Actions

- Confirmed the crashing stat name is already registered by
  `gpgpu_sim::create_gpu_per_sm_stats()` in
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-sim.cc`.
- Confirmed remodeled `SM::create_gpu_per_sm_stats(Element_stats&)` copies the
  registered aggregate stat definitions into each `SM::m_sm_stats`.
- Root cause: remodeled `SM` objects were constructed and initialized without
  calling that existing stats-copy hook, so `Subcore::issue()` accesses through
  `m_stats_map["..."]` inserted empty `shared_ptr` entries with `operator[]`.
- Wired the remodeled-SM construction path in
  `exec_simt_core_cluster::create_shader_core_ctx()` to call
  `m_core[i]->create_gpu_per_sm_stats(m_gpu->m_gpu_per_sm_stats);` before
  `m_core[i]->init()`.
- Preserved existing stat names and avoided a local null check that would drop
  stats.
- Did not edit accepted configs, calibration `latest`, or generated bulk
  outputs.
- Command hygiene note: an incorrect ProcMan status probe used `procman.py -s`,
  which runs ProcMan selfTest. The self-test process group was stopped, its
  local self-test artifacts were removed, and follow-up ProcMan/process checks
  showed no active local jobs.

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

- `artifacts/s7/s7-subcore-stats-20260609-044203/rebuild-gpgpusim.log`,
  exit `0`.

### Generator And Whitespace Checks

Commands:

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
git diff --check
```

Evidence:

- `artifacts/s7/s7-subcore-stats-20260609-044203/generate-check-only.log`,
  exit `0`.
- `artifacts/s7/s7-subcore-stats-20260609-044203/generate-check-only-final.log`,
  exit `0`.
- `artifacts/s7/s7-subcore-stats-20260609-044203/git-diff-check.log`,
  exit `0`.
- `artifacts/s7/s7-subcore-stats-20260609-044203/git-diff-check-final.log`,
  exit `0` before this worker log was added.

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
  -N s7-subcore-stats-20260609-044203-smoke-plan \
  -r artifacts/s7/s7-subcore-stats-20260609-044203/sim-smoke-plan \
  -l local \
  -n
```

Evidence:

- `artifacts/s7/s7-subcore-stats-20260609-044203/procman-print-before-plan.log`:
  `Nothing Active`.
- `artifacts/s7/s7-subcore-stats-20260609-044203/local-smoke-plan.log`,
  exit `0`.
- `artifacts/s7/s7-subcore-stats-20260609-044203/sim-smoke-plan-files.log`
  records copied config/runtime files.
- `artifacts/s7/s7-subcore-stats-20260609-044203/procman-print-before-smoke.log`:
  `Nothing Active`.

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
  -N s7-subcore-stats-20260609-044203-smoke \
  -r artifacts/s7/s7-subcore-stats-20260609-044203/sim-smoke \
  -l local \
  -c 1
```

Evidence:

- `artifacts/s7/s7-subcore-stats-20260609-044203/local-smoke-run.log`,
  launcher exit `0`.
- Exactly one ProcMan job was queued: `Job 463`.
- `artifacts/s7/s7-subcore-stats-20260609-044203/procman-polls-smoke.log`
  records the single local job while active.
- `artifacts/s7/s7-subcore-stats-20260609-044203/procman-print-after-smoke.log`
  and `procman-print-final-before-review.log`: `Nothing Active`.

Smoke result:

- The assigned issue-stage stats null-pointer segmentation fault did not recur.
- The smoke advanced through PTX parsing/predecode and kernel stream push. The
  simulator stdout under
  `artifacts/s7/s7-subcore-stats-20260609-044203/sim-smoke/backprop-rodinia-2.0-ft/4096___data_result_4096_txt/RTX5060_SM120_GEN/`
  includes:

```text
GPGPU-Sim PTX: ... done pre-decoding instructions for '_Z22bpnn_layerforward_CUDAPfS_S_S_ii'.
GPGPU-Sim PTX: pushing kernel '_Z22bpnn_layerforward_CUDAPfS_S_S_ii' to stream 0, gridDim= (1,256,1) blockDim = (16,16,1)
```

- The smoke advanced to a new blocker:

```text
backprop-rodinia-2.0-ft: ../shader.h:229: unsigned int shd_warp_t::get_current_unique_function_id_call(): Assertion `!m_function_call_stack.empty()' failed.
```

- `artifacts/s7/s7-subcore-stats-20260609-044203/coredump-gdb-backtrace-2601218.log`
  maps the new blocker to:

```text
shd_warp_t::get_current_unique_function_id_call() at ../shader.h:229
Subcore::fetch() at subcore.cc:981
Subcore::cycle() at subcore.cc:108
SM::cycle() at sm.cc:263
simt_core_cluster::core_cycle() at shader.cc:4498
```

- No real simulator metrics appeared before the new assertion. No configs or
  calibration `latest` files were promoted.
- Non-blocking evidence note: `smoke-key-lines.exitcode` is `2` because the grep
  also referenced missing convenience log names, but the copied `.o463`/`.e463`
  logs and GDB backtrace contain the required smoke evidence.

### ProcMan Cleanup

Evidence:

- `artifacts/s7/s7-subcore-stats-20260609-044203/procman-kill-selftest.log`
- `artifacts/s7/s7-subcore-stats-20260609-044203/procman-selftest-processgroup-cleanup.log`
- `artifacts/s7/s7-subcore-stats-20260609-044203/procman-print-after-selftest-cleanup.log`:
  no lingering active jobs.
- `artifacts/s7/s7-subcore-stats-20260609-044203/process-scan-after-selftest-cleanup.log`:
  no local workspace simulator jobs from the self-test cleanup.

## Changed Files

Code:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader.cc`

Documentation:

- `docs/sm120-calibration/worker-logs/worker-20260609-044203-s7-subcore-stats.md`

Pre-existing unrelated working-tree change observed and not modified by this
worker:

- `docs/sm120-calibration/supervisor-log.md`

Ignored/local artifacts:

- `artifacts/s7/s7-subcore-stats-20260609-044203/`

## Reviewer Rounds

- Round 1 blank-context reviewer: `ACCEPT`.
  - Prompt: `reviewer-round1.prompt.txt`.
  - Final message: `reviewer-round1-final-message.txt`.
  - Stdout/verdict: `reviewer-round1-codex.stdout.txt`.
  - Stderr/tool transcript: `reviewer-round1-codex.stderr.txt`.
  - Exit code: `reviewer-round1-codex.exitcode`, value `0`.
  - Non-blocking note: `smoke-key-lines.exitcode` is `2` due to missing
    convenience log names, but the copied job logs and GDB backtrace contain the
    required evidence.

## Final Status

Accepted by the worker's blank-context reviewer. The assigned remodeled
issue-stage stats crash is resolved for the one local smoke. The smoke is now
precisely bounded at a distinct `shd_warp_t::get_current_unique_function_id_call`
assertion in `Subcore::fetch()`. Real simulator metrics remain blocked by that
new assertion, so no calibration outputs were promoted.
