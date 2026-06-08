# S7 Function Stack Worker Log

## Purpose

Resolve or precisely bound the local smoke assertion in the remodeled fetch
path:

```text
../shader.h:229: unsigned int shd_warp_t::get_current_unique_function_id_call(): Assertion `!m_function_call_stack.empty()' failed
Subcore::fetch() at simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc:981
```

The task scope excludes accepted config edits, generated bulk-output edits,
calibration `latest` promotion, fake metrics, and full simulator execution on
`dsp5060`.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Host: `dsp-ubuntu`
- Base HEAD: `4fa4577ad06fdbb21e00c305356a515925b826ad`
- Base subject: `fix: initialize remodeled SM stats`
- Timestamp: `2026-06-09T05:11:36+08:00`
- Run id: `s7-function-stack-20260609-051136`
- Artifact root: `artifacts/s7/s7-function-stack-20260609-051136/`
- Initial working tree: pre-existing supervisor edit in
  `docs/sm120-calibration/supervisor-log.md`; not modified by this worker.

## Actions

- Compared baseline fetch (`shader_core_ctx::fetch()`) with remodeled
  `Subcore::fetch()` and trace-mode warp initialization.
- Confirmed trace-mode remodeled launch pushes the kernel
  `unique_function_id` onto each active warp's function-call stack in
  `SM::init_warps()`.
- Confirmed the local smoke config is PTX/performance simulation, not
  trace replay: `-gpgpu_ptx_sim_mode 0`, `-is_SM_remodeling_enabled 1`, and
  `-is_ibuffer_remodeled_enabled 1`.
- Root cause for the assigned assertion: remodeled fetch always used the
  trace-mode function-call stack to derive function-relative instruction-cache
  addresses, but PTX mode uses baseline `PROGRAM_MEM_START` instruction
  addresses and does not seed the trace function-call stack.
- Updated `Subcore::fetch()` so only trace mode calls
  `get_current_unique_function_id_call()`; PTX mode uses function id `0`.
- Updated remodeled `SM::from_local_pc_to_global_pc_address()` and
  `SM::from_global_pc_address_to_local_pc()` so PTX mode round-trips through
  `PROGRAM_MEM_START`, while trace mode preserves existing function-relative
  address translation.
- Did not weaken the stack assertion. Trace mode still asserts if the function
  stack is missing.
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

- `artifacts/s7/s7-function-stack-20260609-051136/rebuild-gpgpusim.log`,
  exit `0`.

### Generator And Whitespace Checks

Commands:

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
git diff --check
```

Evidence:

- `artifacts/s7/s7-function-stack-20260609-051136/generate-check-only.log`,
  exit `0`.
- `artifacts/s7/s7-function-stack-20260609-051136/git-diff-check.log`,
  exit `0`.

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
  -N s7-function-stack-20260609-051136-smoke-plan \
  -r artifacts/s7/s7-function-stack-20260609-051136/sim-smoke-plan \
  -l local \
  -n
```

Evidence:

- `artifacts/s7/s7-function-stack-20260609-051136/procman-print-before-plan.log`:
  `Nothing Active`.
- `artifacts/s7/s7-function-stack-20260609-051136/local-smoke-plan.log`,
  exit `0`.
- `artifacts/s7/s7-function-stack-20260609-051136/sim-smoke-plan-files.log`
  records copied config/runtime files.
- `artifacts/s7/s7-function-stack-20260609-051136/procman-print-before-smoke.log`:
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
  -N s7-function-stack-20260609-051136-smoke \
  -r artifacts/s7/s7-function-stack-20260609-051136/sim-smoke \
  -l local \
  -c 1
```

Evidence:

- `artifacts/s7/s7-function-stack-20260609-051136/local-smoke-run.log`,
  launcher exit `0`.
- Exactly one ProcMan job was queued: `Job 464`.
- `artifacts/s7/s7-function-stack-20260609-051136/procman-poll-smoke-001.log`
  records the single local job while active.
- `artifacts/s7/s7-function-stack-20260609-051136/procman-print-after-smoke.log`:
  `Nothing Active`.

Smoke result:

- The assigned `shd_warp_t::get_current_unique_function_id_call()` assertion
  did not recur.
- The smoke advanced past PTX parsing/predecode, kernel stream push, and the
  previous immediate remodeled fetch assertion. The simulator stdout under
  `artifacts/s7/s7-function-stack-20260609-051136/sim-smoke/backprop-rodinia-2.0-ft/4096___data_result_4096_txt/RTX5060_SM120_GEN/`
  includes:

```text
GPGPU-Sim PTX: ... done pre-decoding instructions for '_Z22bpnn_layerforward_CUDAPfS_S_S_ii'.
GPGPU-Sim PTX: pushing kernel '_Z22bpnn_layerforward_CUDAPfS_S_S_ii' to stream 0, gridDim= (1,256,1) blockDim = (16,16,1)
```

- The smoke advanced to a new blocker:

```text
Segmentation fault (core dumped)
traced_instruction::get_contains_setp(this=0x0) at src/traced_instruction.cc:279
warp_inst_t::assign_predicate_latencies_if_needed()
Subcore::single_decode() at subcore.cc:851
Subcore::decode() at subcore.cc:920
Subcore::cycle() at subcore.cc:107
SM::cycle() at sm.cc:263
simt_core_cluster::core_cycle() at shader.cc:4498
```

- Evidence:
  - `artifacts/s7/s7-function-stack-20260609-051136/coredump-info-2704092.log`
  - `artifacts/s7/s7-function-stack-20260609-051136/coredump-gdb-backtrace-2704092.log`
  - `artifacts/s7/s7-function-stack-20260609-051136/smoke-stdout-tail-final.log`
  - `artifacts/s7/s7-function-stack-20260609-051136/smoke-stderr-tail-final.log`
- No real simulator metrics appeared before the new segmentation fault. No
  configs or calibration `latest` files were promoted.

## Changed Files

Code:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/sm.cc`

Documentation:

- `docs/sm120-calibration/worker-logs/worker-20260609-051136-s7-function-stack.md`

Pre-existing unrelated working-tree change observed and not modified by this
worker:

- `docs/sm120-calibration/supervisor-log.md`

Ignored/local artifacts:

- `artifacts/s7/s7-function-stack-20260609-051136/`

## Reviewer Rounds

- Round 1 blank-context reviewer: `ACCEPT`.
  - Prompt: `reviewer-round1.prompt.txt`.
  - Final message: `reviewer-round1-final-message.txt`.
  - Stdout/verdict: `reviewer-round1-codex.stdout.txt`.
  - Stderr/tool transcript: `reviewer-round1-codex.stderr.txt`.
  - Exit code: `reviewer-round1-codex.exitcode`, value `0`.
  - Reviewer residual risk: no trace-mode smoke was run, but the trace-mode
    branch is unchanged.

## Final Status

Accepted by the worker's blank-context reviewer. The assigned remodeled fetch
function-call-stack assertion is resolved for the one local smoke. The smoke is
now precisely bounded at a distinct null `traced_instruction` segmentation
fault in `warp_inst_t::assign_predicate_latencies_if_needed()` called from
`Subcore::single_decode()`. Real simulator metrics remain blocked by that new
segmentation fault, so no calibration outputs were promoted.
