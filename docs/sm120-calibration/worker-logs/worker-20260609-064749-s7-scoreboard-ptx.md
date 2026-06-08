# S7 Scoreboard PTX Worker Log

## Purpose

Resolve or precisely bound the PTX-mode scoreboard trace-metadata crash:

```text
traced_instruction::get_num_operands(this=0x0)
Scoreboard::checkCollision_remodeling()
Subcore::issue()
Subcore::cycle()
```

The fix must preserve trace-mode MICRO25/remodeled behavior, keep
scoreboarding enabled, avoid hard-coded SM120/RTX5060 values, and avoid
accepted config, calibration `latest`, generated bulk-output, or fake metric
changes.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Host: `dsp-ubuntu`
- Base HEAD: `fc68f6fa3ec89d326ecc5d6584c0e2b9daff3dc9`
- Base subject: `fix: handle PTX-mode remodeled memory latencies`
- Timestamp: `2026-06-09T06:47:49+08:00`
- Run id: `s7-scoreboard-ptx-20260609-064749`
- Artifact root: `artifacts/s7/s7-scoreboard-ptx-20260609-064749/`
- Initial working tree: inherited source edits for this task in the files
  listed below; no accepted configs, calibration `latest`, or generated bulk
  outputs were dirty.

## Actions

- Read the supervisor log, overall plan, and previous memory-latency worker
  log.
- Inspected the prior coredump evidence that showed PTX performance
  simulation entering `Scoreboard::checkCollision_remodeling()` with a
  `warp_inst_t` lacking `extra_trace_instruction_info`.
- Updated the remodeled issue/scoreboard path so PTX instructions without
  enhanced trace metadata use classic RAW/WAW and WAR scoreboard checks,
  reserves, and releases.
- Preserved trace-mode remodeled scoreboard behavior for instructions with
  enhanced trace metadata.
- Made missing enhanced trace metadata a hard trace-mode contract violation
  in metadata-dependent issue, scoreboard, register-file, barrier, retirement,
  predicate-latency, and memory-latency helper paths, instead of silently
  falling back in assertion-disabled builds.
- Made PTX no-metadata remodeled register-file read checks return ready and
  read allocation no-op, matching the lack of enhanced operand-use metadata.
- Did not disable scoreboarding globally.
- Did not edit accepted configs, calibration `latest`, generated bulk outputs,
  or calibration metrics.
- Did not run any simulator workload on `dsp5060`.

## Evidence

### Final Rebuild

Command:

```bash
export CUDA_INSTALL_PATH=/usr/local/cuda-13.1
export PATH="$CUDA_INSTALL_PATH/bin:$PATH"
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
make -C simulator-remodeled/gpu-simulator/gpgpu-sim -j"$(nproc)"
```

Evidence:

- `artifacts/s7/s7-scoreboard-ptx-20260609-064749/rebuild-gpgpusim-final-after-rf-allocation.log`
- `artifacts/s7/s7-scoreboard-ptx-20260609-064749/rebuild-gpgpusim-final-after-rf-allocation.exitcode`: `0`

Earlier rebuilds in the same artifact directory also passed before the final
RF-allocation guard tightening.

### Generator And Whitespace Checks

Commands:

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
git diff --check
```

Evidence:

- `artifacts/s7/s7-scoreboard-ptx-20260609-064749/generate-check-only-final-after-rf-allocation.log`
- `artifacts/s7/s7-scoreboard-ptx-20260609-064749/generate-check-only-final-after-rf-allocation.exitcode`: `0`
- `artifacts/s7/s7-scoreboard-ptx-20260609-064749/git-diff-check-final-after-rf-allocation.log`
- `artifacts/s7/s7-scoreboard-ptx-20260609-064749/git-diff-check-final-after-rf-allocation.exitcode`: `0`

### Setup-Only Smoke Planning

Command:

```bash
export CUDA_INSTALL_PATH=/usr/local/cuda-13.1
export PATH="$CUDA_INSTALL_PATH/bin:$PATH"
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment
python3 simulator-remodeled/util/job_launching/procman.py -p
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-scoreboard-ptx-20260609-064749-smoke-plan-final-after-rf-allocation \
  -r artifacts/s7/s7-scoreboard-ptx-20260609-064749/sim-smoke-plan-final-after-rf-allocation \
  -l local \
  -n
```

Evidence:

- `artifacts/s7/s7-scoreboard-ptx-20260609-064749/local-smoke-plan-final-after-rf-allocation.log`
- `artifacts/s7/s7-scoreboard-ptx-20260609-064749/local-smoke-plan-final-after-rf-allocation.exitcode`: `0`
- The plan log records `Nothing Active` before setup-only planning.

Note: one earlier final setup-only command repeated the known invalid
`procman.py print` form before the plan. It was guarded, produced
`FileNotFoundError: 'print'`, and did not affect the setup-only plan exit.
The correct final ProcMan status command is recorded in
`procman-print-final.log` with `Nothing Active`.

### One Local Smoke

Exactly one local smoke was run for this task before later non-smoke guard
tightening. No second smoke was run because the assignment required exactly
one local smoke after a passing build/checks.

Command:

```bash
export CUDA_INSTALL_PATH=/usr/local/cuda-13.1
export PATH="$CUDA_INSTALL_PATH/bin:$PATH"
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-scoreboard-ptx-20260609-064749-smoke \
  -r artifacts/s7/s7-scoreboard-ptx-20260609-064749/sim-smoke \
  -l local \
  -c 1
```

Evidence:

- `artifacts/s7/s7-scoreboard-ptx-20260609-064749/local-smoke-run.log`,
  launcher exit `0`.
- Exactly one ProcMan job was queued: `Job 467`.
- `procman-poll-smoke-*.log` records the single local job active, then
  complete, then inactive.
- `procman-print-after-smoke.log`: `Nothing Active`.

Smoke result:

- The assigned scoreboard metadata crash did not recur:
  `smoke-old-scoreboard-blocker-search.log` is empty for
  `traced_instruction::get_num_operands`,
  `Scoreboard::checkCollision_remodeling`, and
  `Scoreboard_reads::checkCollision_remodeling`.
- The smoke advanced through PTX predecode and kernel push:

```text
GPGPU-Sim PTX: ... done pre-decoding instructions for '_Z22bpnn_layerforward_CUDAPfS_S_S_ii'.
GPGPU-Sim PTX: pushing kernel '_Z22bpnn_layerforward_CUDAPfS_S_S_ii' to stream 0, gridDim= (1,256,1) blockDim = (16,16,1)
```

- The smoke advanced to a new PTX-mode blocker:

```text
abstract_hardware_model.cc:676: void warp_inst_t::generate_mem_accesses(): Assertion `m_per_scalar_thread_valid' failed.
warp_inst_t::generate_mem_accesses()
SM::issue_warp() at sm.cc:366
Subcore::issue_warp() at subcore.cc:744
Subcore::issue() at subcore.cc:468
Subcore::cycle() at subcore.cc:106
SM::cycle() at sm.cc:263
simt_core_cluster::core_cycle() at shader.cc:4498
```

Evidence:

- `artifacts/s7/s7-scoreboard-ptx-20260609-064749/smoke-stdout-tail-final.log`
- `artifacts/s7/s7-scoreboard-ptx-20260609-064749/smoke-stderr-tail-final.log`
- `artifacts/s7/s7-scoreboard-ptx-20260609-064749/coredump-gdb-bt-3045625.log`
- `artifacts/s7/s7-scoreboard-ptx-20260609-064749/coredump-gdb-bt-full-3045625.log`
- `artifacts/s7/s7-scoreboard-ptx-20260609-064749/job-status-smoke.log`
  reports `ASSERT, ABORTED`.
- `artifacts/s7/s7-scoreboard-ptx-20260609-064749/smoke-metrics-search.log`
  is empty, so no real simulator metrics were produced.

## Changed Files

Code:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/abstract_hardware_model.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/functional_unit.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/register_file.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/register_file.h`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/sm.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/scoreboard.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/scoreboard_reads.cc`

Documentation:

- `docs/sm120-calibration/worker-logs/worker-20260609-064749-s7-scoreboard-ptx.md`

Ignored/local artifacts:

- `artifacts/s7/s7-scoreboard-ptx-20260609-064749/`

## Reviewer Rounds

- Round 1 blank-context reviewer attempt: failed before review due unsupported
  `codex exec` CLI argument usage.
  - Prompt: `reviewer-round1.prompt.txt`.
  - Stdout: `reviewer-round1-codex.stdout.txt`.
  - Stderr: `reviewer-round1-codex.stderr.txt`.
  - Exit code: `reviewer-round1-codex.exitcode`, value `2`.
- Round 2 blank-context reviewer attempt: timed out with no stdout after the
  CLI read-only reviewer stalled during repository inspection.
  - Stdout: `reviewer-round2-codex.stdout.txt`.
  - Stderr/tool transcript: `reviewer-round2-codex.stderr.txt`.
  - Exit code: `reviewer-round2-codex.exitcode`, value `124`.
- Round 3 through Round 5 reviewer attempts: failed before review due the
  local `codex review` / `codex exec review` CLI rejecting prompts combined
  with `--uncommitted`.
  - Artifacts: `reviewer-round3-*`, `reviewer-round4-*`,
    `reviewer-round5-*`.
- Round 6 prompt-only blank-context reviewer: `ACCEPT`.
  - Prompt: `reviewer-round6-prompt-only.prompt.txt`.
  - Final message: `reviewer-round6-final-message.txt`.
  - Stdout/verdict: `reviewer-round6-codex.stdout.txt`.
  - Stderr/tool transcript: `reviewer-round6-codex.stderr.txt`.
  - Exit code: `reviewer-round6-codex.exitcode`, value `0`.
  - Reviewer residual risk: the prompt-only review did not independently
    inspect files because it was explicitly instructed not to run tools, so the
    acceptance is limited to the supplied diff/evidence summary. It found no
    blocking issues in the goal achievement or validation evidence.

## Final Status

Accepted by the worker's blank-context reviewer. The assigned PTX-mode
scoreboard trace-metadata crash is resolved by the one local smoke and final
source validation passed. Real simulator metrics remain blocked by the new
`warp_inst_t::generate_mem_accesses()` / `m_per_scalar_thread_valid`
assertion, so no calibration outputs were promoted.
