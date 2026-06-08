# S7 Predicate Latency Worker Log

## Purpose

Resolve or precisely bound the local smoke segmentation fault in remodeled
decode/predicate latency handling:

```text
traced_instruction::get_contains_setp(this=0x0) at util/traces_enhanced/src/traced_instruction.cc:279
warp_inst_t::assign_predicate_latencies_if_needed()
Subcore::single_decode() at simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc:851
```

The task scope excludes accepted config edits, calibration `latest` promotion,
generated bulk-output edits, fake metrics, and full simulator execution on
`dsp5060`.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Host: `dsp-ubuntu`
- Base HEAD: `e8dd5bca47e08ad6d8a4750e90466a7159b6acbd`
- Base subject: `fix: handle PTX-mode remodeled fetch PCs`
- Timestamp: `2026-06-09T05:32:13+08:00`
- Run id: `s7-predicate-latency-20260609-053213`
- Artifact root: `artifacts/s7/s7-predicate-latency-20260609-053213/`
- Initial working tree: pre-existing supervisor edit in
  `docs/sm120-calibration/supervisor-log.md`; not modified by this worker.

## Actions

- Compared baseline PTX decode/fetch behavior with remodeled
  `Subcore::single_decode()` and the trace-driven latency helpers.
- Confirmed the assigned crash came from unconditional trace-only metadata
  access in `warp_inst_t::assign_predicate_latencies_if_needed()` while the
  smoke is PTX/performance simulation mode (`-gpgpu_ptx_sim_mode 0`), not trace
  replay.
- Confirmed PTX parsing already assigns normal instruction latency and
  initiation interval in `ptx_instruction::pre_decode()`, including predicate
  instruction handling from the PTX/gpgpusim config path.
- Updated `warp_inst_t::assign_predicate_latencies_if_needed()` so PTX mode
  returns without touching enhanced trace metadata.
- Kept the trace-enhanced contract explicit: trace mode still requires
  `traced_instruction` metadata and a trace config before decomposing
  `PREDICATE_OP` latency into INT latency plus extra predicate stages, or before
  checking SASS opcodes containing `SETP`.
- Did not skip `Subcore::single_decode()` and did not disable remodeled decode
  globally.
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

- `artifacts/s7/s7-predicate-latency-20260609-053213/rebuild-gpgpusim.log`,
  exit `0`.

### Generator And Whitespace Checks

Commands:

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
git diff --check
```

Evidence:

- `artifacts/s7/s7-predicate-latency-20260609-053213/generate-check-only.log`,
  exit `0`.
- `artifacts/s7/s7-predicate-latency-20260609-053213/git-diff-check.log`,
  exit `0`.
- `artifacts/s7/s7-predicate-latency-20260609-053213/git-diff-check-final.log`,
  exit `0` after the worker log update.

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
  -N s7-predicate-latency-20260609-053213-smoke-plan \
  -r artifacts/s7/s7-predicate-latency-20260609-053213/sim-smoke-plan \
  -l local \
  -n
```

Evidence:

- `artifacts/s7/s7-predicate-latency-20260609-053213/procman-print-before-plan.log`:
  `Nothing Active`.
- `artifacts/s7/s7-predicate-latency-20260609-053213/local-smoke-plan.log`,
  exit `0`.
- `artifacts/s7/s7-predicate-latency-20260609-053213/sim-smoke-plan-files.log`
  records copied config/runtime files.
- `artifacts/s7/s7-predicate-latency-20260609-053213/procman-print-before-smoke.log`:
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
  -N s7-predicate-latency-20260609-053213-smoke \
  -r artifacts/s7/s7-predicate-latency-20260609-053213/sim-smoke \
  -l local \
  -c 1
```

Evidence:

- `artifacts/s7/s7-predicate-latency-20260609-053213/local-smoke-run.log`,
  launcher exit `0`.
- Exactly one ProcMan job was queued: `Job 465`.
- `artifacts/s7/s7-predicate-latency-20260609-053213/procman-poll-smoke-*.log`
  records the single local job while active and then inactive.
- `artifacts/s7/s7-predicate-latency-20260609-053213/procman-print-final.log`:
  `Nothing Active`.

Smoke result:

- The assigned `traced_instruction::get_contains_setp(this=0x0)` segmentation
  fault did not recur.
- The smoke advanced past PTX parsing/predecode, kernel stream push, remodeled
  fetch, and decode predicate-latency assignment. The simulator stdout under
  `artifacts/s7/s7-predicate-latency-20260609-053213/sim-smoke/backprop-rodinia-2.0-ft/4096___data_result_4096_txt/RTX5060_SM120_GEN/`
  includes:

```text
GPGPU-Sim PTX: ... done pre-decoding instructions for '_Z22bpnn_layerforward_CUDAPfS_S_S_ii'.
GPGPU-Sim PTX: pushing kernel '_Z22bpnn_layerforward_CUDAPfS_S_S_ii' to stream 0, gridDim= (1,256,1) blockDim = (16,16,1)
```

- The smoke advanced to a new PTX-mode blocker:

```text
backprop-rodinia-2.0-ft: abstract_hardware_model.cc:514: virtual void warp_inst_t::generate_mem_latencies(gpgpu_sim*): Assertion `shader_config.is_trace_mode' failed.
warp_inst_t::generate_mem_latencies()
Subcore::single_decode() at subcore.cc:871
Subcore::decode() at subcore.cc:920
Subcore::cycle() at subcore.cc:107
```

- Evidence:
  - `artifacts/s7/s7-predicate-latency-20260609-053213/coredump-info-2780696.log`
  - `artifacts/s7/s7-predicate-latency-20260609-053213/coredump-gdb-current-bt-2780696.log`
  - `artifacts/s7/s7-predicate-latency-20260609-053213/coredump-gdb-backtrace-2780696.log`
  - `artifacts/s7/s7-predicate-latency-20260609-053213/smoke-stdout-tail-final.log`
  - `artifacts/s7/s7-predicate-latency-20260609-053213/smoke-stderr-tail-final.log`
- No real simulator metrics appeared before the new assertion. No configs or
  calibration `latest` files were promoted.

## Changed Files

Code:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/abstract_hardware_model.cc`

Documentation:

- `docs/sm120-calibration/worker-logs/worker-20260609-053213-s7-predicate-latency.md`

Pre-existing unrelated working-tree change observed and not modified by this
worker:

- `docs/sm120-calibration/supervisor-log.md`

Ignored/local artifacts:

- `artifacts/s7/s7-predicate-latency-20260609-053213/`

## Reviewer Rounds

- Round 1 blank-context reviewer: `ACCEPT`.
  - Prompt: `reviewer-round1.prompt.txt`.
  - Final message: `reviewer-round1-final-message.txt`.
  - Stdout/verdict: `reviewer-round1-codex.stdout.txt`.
  - Stderr/tool transcript: `reviewer-round1-codex.stderr.txt`.
  - Exit code: `reviewer-round1-codex.exitcode`, value `0`.
  - Reviewer residual risk: no trace-mode smoke was run, but the trace-mode
    predicate-latency branch is unchanged except for explicit assertions when
    required trace metadata/config are missing.

## Final Status

Accepted by the worker's blank-context reviewer. The assigned null
`traced_instruction` segmentation fault is resolved for the one local smoke.
The smoke is now precisely bounded at a distinct PTX-mode assertion in
`warp_inst_t::generate_mem_latencies()` because that trace-enhanced memory
latency helper still asserts `shader_config.is_trace_mode`. Real simulator
metrics remain blocked by that new assertion, so no calibration outputs were
promoted.
