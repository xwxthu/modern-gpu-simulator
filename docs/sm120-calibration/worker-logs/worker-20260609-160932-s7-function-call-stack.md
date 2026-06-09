# S7 Function-Call-Stack Worker Log

## Purpose

Take over the dirty worktree left by two replacement workers for the current S7
PTX smoke blocker:

```text
shd_warp_t::pop_function_call(active_mask_t):
Assertion `!m_function_call_stack.empty()' failed.
```

The assigned root-cause question was whether remodeled PTX-mode warp reclaim
should mark a warp done without popping the trace/SASS function-call stack, while
preserving trace-mode stack handling and the `pop_function_call()` assertion.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base HEAD at takeover:
  `f741c9001e29f8be495a7543ac2b115951d81c32`
- Timestamp:
  `2026-06-09T16:09:32+08:00`
- Takeover state:
  dirty tracked worktree with only:
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/sm.cc`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader.h`
- Inherited partial code:
  - trace mode still called `warp->set_done_exit()`
  - PTX mode called new `warp->set_done_exit_for_ptx_reclaim()`
  - the new helper asserted `m_function_call_stack.empty()` and only set
    `m_done_exit = true`
- New artifact root for this takeover:
  `artifacts/s7/s7-function-call-stack-20260609-160932/`
- Reused partial smoke artifact:
  `artifacts/s7/s7-function-call-stack-20260609-154658/`

## Inputs Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/worker-logs/worker-20260609-144109-s7-ptx-stats-concurrency.md`
- Original blocker evidence:
  `artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/coredump-gdb-focused-new-blocker-1032513.log`
- Partial worker artifacts:
  - `artifacts/s7/s7-function-call-stack-20260609-151805/`
  - `artifacts/s7/s7-function-call-stack-20260609-154658/`

## Root Cause

The assertion was real and should remain in `pop_function_call()`. The bug was
that remodeled PTX-mode warp reclaim was calling the trace/SASS done-exit path.

The remodeled function-call stack is maintained from trace metadata:

- trace-mode warp init pushes the kernel unique function id in
  `SM::init_warps()`
- trace-mode issue checks `unique_function_id` against
  `get_current_unique_function_id_call()`
- trace-mode `CALL_OPS` and `RET_OPS` push/pop the same stack

PTX mode does not populate that stack:

- `SM::create_shd_warp()` creates plain `shd_warp_t` in PTX mode
- the trace stack push in `SM::init_warps()` is inside
  `m_config->is_trace_mode`
- CALL/RET stack maintenance in `SM::issue_warp()` is also inside
  `m_config->is_trace_mode`

The original core confirms the mismatch. GDB shows
`m_config->is_trace_mode == false`, `warp->m_function_call_stack.size() == 0`,
and the abort path is:

```text
shd_warp_t::pop_function_call()
shd_warp_t::set_done_exit()
SM::check_if_warp_has_finished_executing_and_can_be_reclaim()
Subcore::fetch()
```

Therefore PTX reclaim should only mark the warp done, but should assert that
the trace/SASS function-call stack is empty. This preserves the invariant that
non-empty stacks must be consumed through the trace path and keeps empty pop as
a hard failure.

## Actions

- Audited the inherited diff and surrounding code.
- Confirmed `pop_function_call()` and `get_current_unique_function_id_call()`
  assertions were not removed or weakened.
- Confirmed trace mode still calls the original `set_done_exit()` path and
  therefore still pops the trace/SASS function-call stack at reclaim.
- Confirmed PTX mode now calls `set_done_exit_for_ptx_reclaim()`, which asserts
  the trace/SASS stack is empty and sets `m_done_exit`.
- Added one call-site comment documenting why PTX reclaim does not pop the
  trace/SASS stack.
- Did not:
  - turn empty-stack pop into a no-op
  - delete or weaken `pop_function_call()` assertions
  - skip warp reclaim
  - alter config generation, latest aliases, calibration results, or metrics
  - run simulator workloads on `dsp5060`

## Changed Files

Code:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/sm.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader.h`

Documentation:

- `docs/sm120-calibration/worker-logs/worker-20260609-160932-s7-function-call-stack.md`

Ignored/local artifacts:

- `artifacts/s7/s7-function-call-stack-20260609-160932/`
- Additional focused core evidence copied/generated in
  `artifacts/s7/s7-function-call-stack-20260609-154658/`

## Validation Commands And Results

Whitespace check passed:

```bash
git diff --check
```

- Evidence:
  `artifacts/s7/s7-function-call-stack-20260609-160932/git-diff-check.log`
- Exit code:
  `artifacts/s7/s7-function-call-stack-20260609-160932/git-diff-check.exitcode`,
  value `0`

SM120 generated-config reproducibility check passed:

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
```

- Evidence:
  `artifacts/s7/s7-function-call-stack-20260609-160932/generate-check-only.log`
- Exit code:
  `artifacts/s7/s7-function-call-stack-20260609-160932/generate-check-only.exitcode`,
  value `0`
- Output:
  generated `SM120_RTX5070_TI` and `SM120_RTX5060` bootstrap profiles with
  `gpgpu_keys=217` and `trace_keys=13`.

Replacement worker reran the required read-only validation checks after taking
over the pending reviewer state:

```bash
git diff --check
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
```

- Evidence:
  - `artifacts/s7/s7-function-call-stack-20260609-160932/git-diff-check.replacement-final.log`
  - `artifacts/s7/s7-function-call-stack-20260609-160932/git-diff-check.replacement-final.exitcode`
  - `artifacts/s7/s7-function-call-stack-20260609-160932/generate-check-only.replacement-final.log`
  - `artifacts/s7/s7-function-call-stack-20260609-160932/generate-check-only.replacement-final.exitcode`
- Exit codes:
  - `git diff --check`: `0`
  - `generate_sm120_configs.py --check-only`: `0`

Reused the partial post-fix smoke rather than launching another full smoke. The
reason is that `s7-function-call-stack-20260609-154658` was already rebuilt and
run from the same code state except for one explanatory comment added by this
takeover, and it naturally reached the next blocker with `procman` showing
`Nothing Active`.

Reused build and smoke exit codes:

- `artifacts/s7/s7-function-call-stack-20260609-154658/rebuild-gpgpusim.exitcode`,
  value `0`
- `artifacts/s7/s7-function-call-stack-20260609-154658/local-smoke-run.exitcode`,
  value `0`
- copied into:
  `artifacts/s7/s7-function-call-stack-20260609-160932/reused-rebuild-gpgpusim.exitcode`
  and
  `artifacts/s7/s7-function-call-stack-20260609-160932/reused-local-smoke-run.exitcode`

Reused smoke result search:

- Evidence:
  `artifacts/s7/s7-function-call-stack-20260609-160932/reused-smoke-result-search.log`
- Exit code:
  `artifacts/s7/s7-function-call-stack-20260609-160932/reused-smoke-result-search.exitcode`,
  value `0`
- It shows:
  - first kernel launch:
    `_Z22bpnn_layerforward_CUDAPfS_S_S_ii`
  - first real kernel metrics:
    `gpu_tot_sim_cycle = 7729`
    and
    `gpu_tot_sim_insn = 4169728`
  - second kernel launch:
    `_Z24bpnn_adjust_weights_cudaPfiS_iS_S_`
  - final crash:
    PID `1366300` `Segmentation fault (core dumped)`
- It does not show the old `pop_function_call` assertion or
  `m_function_call_stack` assertion.

Final status capture:

- `artifacts/s7/s7-function-call-stack-20260609-160932/git-status-final.log`
- Only the two intended code files were dirty at the time of the final status
  capture.
- Replacement final status capture:
  `artifacts/s7/s7-function-call-stack-20260609-160932/git-status-replacement-final.log`,
  exit code `0`. Current tracked code changes remain the same two intended
  files, and this worker log is the only additional non-artifact path.

## Focused New Blocker Evidence

The new SIGSEGV was precisely bounded with `coredumpctl` and GDB from PID
`1366300`.

Core info:

- `artifacts/s7/s7-function-call-stack-20260609-160932/coredump-info-1366300.log`

Focused GDB stack:

- `artifacts/s7/s7-function-call-stack-20260609-160932/coredump-gdb-focused-new-blocker-1366300.log`

Focused GDB state:

- `artifacts/s7/s7-function-call-stack-20260609-160932/coredump-gdb-focused-new-blocker-state-1366300.log`

Fatal path:

```text
traced_instruction::get_num_destination_registers(this=0x0)
warp_inst_t::generate_dp_latencies()
Subcore::single_decode()
Subcore::decode()
Subcore::cycle()
SM::cycle()
simt_core_cluster::core_cycle()
gpgpu_sim::cycle() [OpenMP worker]
```

Key state:

- `shared_sm->m_config->is_trace_mode == false`
- `pI->pc == 10120`
- `pI->isize == 8`
- `pI->op == DP_OP`
- `pI->sp_op == DP___OP`
- `pI->m_decoded == true`
- `pI->m_extra_trace_instruction_info` is an empty
  `std::shared_ptr<traced_instruction>` with `get() == 0x0`
- `sm_warp_id == 40`
- `warp->m_kernel_id == 2`

This is a downstream PTX/remodeled decode-latency issue: a PTX-mode DP
instruction reaches `generate_dp_latencies()`, which unconditionally dereferences
trace-enhanced instruction metadata. It is not the old empty function-call-stack
assertion, and it is not evidence that warp reclaim was skipped.

## Reviewer Rounds

- Round 1 inherited reviewer attempt:
  - Prompt:
    `artifacts/s7/s7-function-call-stack-20260609-160932/reviewer/reviewer-round1-prompt.txt`
  - Runner:
    `codex exec -C /home/xiewx/accel-0608/modern-gpu-simulator -s read-only -a never --ephemeral`
  - Final message:
    none
  - Stderr:
    `error: unexpected argument '-a' found`
  - Exit code:
    `2`
  - Verdict:
    not counted; invocation arguments were invalid
- Round 2 inherited reviewer attempt:
  - Evidence:
    - `artifacts/s7/s7-function-call-stack-20260609-160932/reviewer/reviewer-round2-stdout.txt`
    - `artifacts/s7/s7-function-call-stack-20260609-160932/reviewer/reviewer-round2-stderr.txt`
  - Final message:
    none; stdout is empty and no exit-code file was present
  - Verdict:
    not counted; completion was not established
- Round 3 replacement reviewer attempt:
  - Evidence:
    - `artifacts/s7/s7-function-call-stack-20260609-160932/reviewer/reviewer-round3-stdout.txt`
    - `artifacts/s7/s7-function-call-stack-20260609-160932/reviewer/reviewer-round3-stderr.txt`
    - `artifacts/s7/s7-function-call-stack-20260609-160932/reviewer/reviewer-round3-final.txt`
    - `artifacts/s7/s7-function-call-stack-20260609-160932/reviewer/reviewer-round3.exitcode`
  - Final message:
    empty-prompt response asking what to work on
  - Exit code:
    `0`
  - Verdict:
    not counted; prompt file was accidentally written outside the repo and the
    reviewer received no task prompt
- Round 4 fresh blank-context read-only reviewer:
  - Prompt:
    `artifacts/s7/s7-function-call-stack-20260609-160932/reviewer/reviewer-round4-prompt.txt`
  - Runner:
    `codex exec -C /home/xiewx/accel-0608/modern-gpu-simulator --sandbox read-only -c approval_policy='"never"' --ephemeral --output-last-message artifacts/s7/s7-function-call-stack-20260609-160932/reviewer/reviewer-round4-final.txt - < artifacts/s7/s7-function-call-stack-20260609-160932/reviewer/reviewer-round4-prompt.txt`
  - Evidence:
    - `artifacts/s7/s7-function-call-stack-20260609-160932/reviewer/reviewer-round4-stdout.txt`
    - `artifacts/s7/s7-function-call-stack-20260609-160932/reviewer/reviewer-round4-stderr.txt`
    - `artifacts/s7/s7-function-call-stack-20260609-160932/reviewer/reviewer-round4-final.txt`
    - `artifacts/s7/s7-function-call-stack-20260609-160932/reviewer/reviewer-round4.exitcode`
  - Exit code:
    `0`
  - Verdict:
    `ACCEPT`
  - Reviewer summary:
    no blocking findings; root cause is supported by code and old core; fix is
    clean and scoped; trace mode remains on the original `set_done_exit()` pop
    path; PTX mode preserves the empty-stack invariant; validation and new
    SIGSEGV evidence are honest; no config/latest/generated/calibration/metrics
    promotion was found.

## Final Status

Complete for this worker scope. Replacement worker verified the inherited fix as
a clean root-cause repair for the assigned `pop_function_call()` empty-stack
blocker and did not make further code changes. A fresh blank-context read-only
reviewer returned `VERDICT: ACCEPT` in round 4.

The next precise blocker is the downstream PTX-mode remodeled decode-latency
SIGSEGV:

```text
traced_instruction::get_num_destination_registers(this=0x0)
warp_inst_t::generate_dp_latencies()
Subcore::single_decode()
```

The focused state shows `m_config->is_trace_mode == false` and an empty
`m_extra_trace_instruction_info` on a decoded PTX `DP_OP` instruction in kernel
2. This is separate from the resolved function-call-stack reclaim issue. No
supervisor rework is needed for this worker goal.
