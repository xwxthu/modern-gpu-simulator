# S7 Memory Latency Worker Log

## Purpose

Resolve or precisely bound the local smoke assertion in PTX-mode remodeled
memory latency handling:

```text
abstract_hardware_model.cc:514: virtual void warp_inst_t::generate_mem_latencies(gpgpu_sim*): Assertion `shader_config.is_trace_mode' failed
warp_inst_t::generate_mem_latencies()
Subcore::single_decode() at remodeling/subcore.cc:871
```

The task scope excludes accepted config edits, calibration `latest`
promotion, generated bulk-output edits, fake metrics, and full simulator
execution on `dsp5060`.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Host: `dsp-ubuntu`
- Base HEAD: `65b3f4d6f74a25423a0b9df4c09d0a985d8301a4`
- Base subject: `fix: guard trace predicate latency in PTX mode`
- Timestamp: `2026-06-09T05:56:23+08:00`
- Run id: `s7-memory-latency-20260609-055623`
- Artifact root: `artifacts/s7/s7-memory-latency-20260609-055623/`
- Initial working tree: pre-existing supervisor edit in
  `docs/sm120-calibration/supervisor-log.md`; not modified by this worker.

## Actions

- Compared the recent PTX-mode predicate-latency guard with
  `warp_inst_t::generate_mem_latencies()` and the remodeled memory subcore
  queue.
- Confirmed the assigned assertion came from an unconditional
  `shader_config.is_trace_mode` assertion before trace-only memory-reference
  operand metadata access.
- Confirmed plain PTX `ptx_instruction::pre_decode()` / `set_opcode_and_latency()`
  already assigns normal instruction latency and initiation interval.
- Updated `warp_inst_t::generate_mem_latencies()` so PTX mode initializes the
  remodeled memory queue from the predecoded latency/initiation values and
  config-backed shared/global-local/constant SM-side memory latency.
- Preserved the trace-mode detailed memory latency path and added an explicit
  trace metadata assertion before dereferencing enhanced trace operands.
- Did not skip memory instructions, disable remodeled decode, or disable
  trace-mode memory latency modeling.
- Did not edit accepted configs, calibration `latest`, or generated bulk
  outputs.

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

- `artifacts/s7/s7-memory-latency-20260609-055623/rebuild-gpgpusim.log`,
  exit `0`.

### Generator And Whitespace Checks

Commands:

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
git diff --check
```

Evidence:

- `artifacts/s7/s7-memory-latency-20260609-055623/generate-check-only.log`,
  exit `0`.
- `artifacts/s7/s7-memory-latency-20260609-055623/git-diff-check.log`,
  exit `0`.
- `artifacts/s7/s7-memory-latency-20260609-055623/git-diff-check-final-before-review.log`,
  exit `0` after the worker log update.
- `artifacts/s7/s7-memory-latency-20260609-055623/git-diff-check-final.log`,
  exit `0` after recording the reviewer verdict.

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
  -N s7-memory-latency-20260609-055623-smoke-plan \
  -r artifacts/s7/s7-memory-latency-20260609-055623/sim-smoke-plan \
  -l local \
  -n
```

Evidence:

- `artifacts/s7/s7-memory-latency-20260609-055623/procman-print-before-plan-corrected.log`:
  `Nothing Active`.
- `artifacts/s7/s7-memory-latency-20260609-055623/local-smoke-plan.log`,
  exit `0`.
- `artifacts/s7/s7-memory-latency-20260609-055623/sim-smoke-plan-files.log`
  records copied config/runtime files.
- `artifacts/s7/s7-memory-latency-20260609-055623/procman-print-before-smoke.log`:
  `Nothing Active`.

Note: an earlier attempted ProcMan check passed `print` positionally and
failed with `FileNotFoundError: 'print'`; this was an invalid command
invocation, not evidence of an active job.

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
  -N s7-memory-latency-20260609-055623-smoke \
  -r artifacts/s7/s7-memory-latency-20260609-055623/sim-smoke \
  -l local \
  -c 1
```

Evidence:

- `artifacts/s7/s7-memory-latency-20260609-055623/local-smoke-run.log`,
  launcher exit `0`.
- Exactly one ProcMan job was queued: `Job 466`.
- `artifacts/s7/s7-memory-latency-20260609-055623/procman-poll-smoke-*.log`
  records the single local job while active, then complete, then inactive.
- `artifacts/s7/s7-memory-latency-20260609-055623/procman-print-after-smoke.log`:
  `Nothing Active`.

Smoke result:

- The assigned `generate_mem_latencies()` trace-mode assertion did not recur:
  `smoke-old-blocker-search.log` contains no matching lines.
- The smoke advanced past PTX predecode and kernel stream push:

```text
GPGPU-Sim PTX: ... done pre-decoding instructions for '_Z22bpnn_layerforward_CUDAPfS_S_S_ii'.
GPGPU-Sim PTX: pushing kernel '_Z22bpnn_layerforward_CUDAPfS_S_S_ii' to stream 0, gridDim= (1,256,1) blockDim = (16,16,1)
```

- The smoke advanced to a new PTX-mode blocker:

```text
traced_instruction::get_num_operands(this=0x0)
Scoreboard::checkCollision_remodeling()
Subcore::issue()
Subcore::cycle()
```

- Evidence:
  - `artifacts/s7/s7-memory-latency-20260609-055623/coredump-info-2867244.log`
  - `artifacts/s7/s7-memory-latency-20260609-055623/coredump-gdb-current-bt-2867244.log`
  - `artifacts/s7/s7-memory-latency-20260609-055623/coredump-gdb-backtrace-2867244.log`
  - `artifacts/s7/s7-memory-latency-20260609-055623/coredump-gdb-bt-full-2867244.log`
  - `artifacts/s7/s7-memory-latency-20260609-055623/smoke-stdout-tail-final.log`
  - `artifacts/s7/s7-memory-latency-20260609-055623/smoke-stderr-tail-final.log`
- No real simulator metrics appeared before the new segmentation fault:
  `smoke-metrics-search.log` is empty.
- No configs or calibration `latest` files were promoted.

## Changed Files

Code:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/abstract_hardware_model.cc`

Documentation:

- `docs/sm120-calibration/worker-logs/worker-20260609-055623-s7-memory-latency.md`

Pre-existing unrelated working-tree change observed and not modified by this
worker:

- `docs/sm120-calibration/supervisor-log.md`

Ignored/local artifacts:

- `artifacts/s7/s7-memory-latency-20260609-055623/`

## Reviewer Rounds

- Round 1 blank-context reviewer attempt: failed before review due unsupported
  `codex exec` CLI argument usage.
  - Prompt: `reviewer-round1.prompt.txt`.
  - Stdout: `reviewer-round1-codex.stdout.txt`.
  - Stderr: `reviewer-round1-codex.stderr.txt`.
  - Exit code: `reviewer-round1-codex.exitcode`, value `2`.
- Round 2 blank-context reviewer attempt: timed out before verdict.
  - Prompt: `reviewer-round2.prompt.txt`.
  - Stdout: `reviewer-round2-codex.stdout.txt`.
  - Stderr/tool transcript: `reviewer-round2-codex.stderr.txt`.
  - Exit code: `reviewer-round2-codex.exitcode`, value `124`.
- Round 3 and Round 4 reviewer attempts: failed or timed out while trying the
  CLI review subcommand forms.
  - Prompts/transcripts: `reviewer-round3.*`, `reviewer-round4.*`.
- Round 5 prompt-only blank-context reviewer: `ACCEPT`.
  - Prompt: `reviewer-round5.prompt.txt`.
  - Final message: `reviewer-round5-final-message.txt`.
  - Stdout/verdict: `reviewer-round5-codex.stdout.txt`.
  - Stderr/tool transcript: `reviewer-round5-codex.stderr.txt`.
  - Exit code: `reviewer-round5-codex.exitcode`, value `0`.
  - Reviewer residual risk: the trace-mode missing-metadata guard uses
    `assert(false)` followed by `return`, matching the nearby predicate-latency
    guard style. In builds with assertions disabled this would return with the
    resized zero-filled stage vector if trace metadata were unexpectedly absent.
    The reviewer did not consider this a blocking regression for the PTX smoke
    blocker.

## Final Status

Accepted by the worker's blank-context reviewer. The assigned PTX-mode
`generate_mem_latencies()` trace assertion is resolved for the one local smoke.
The smoke is now precisely bounded at a distinct PTX-mode trace-metadata access
in `Scoreboard::checkCollision_remodeling()`:

```text
traced_instruction::get_num_operands(this=0x0)
Scoreboard::checkCollision_remodeling()
Subcore::issue()
Subcore::cycle()
```

Real simulator metrics remain blocked by that new segmentation fault, so no
calibration outputs were promoted.
