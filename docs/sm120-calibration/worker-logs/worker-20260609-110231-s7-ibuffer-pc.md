# S7 IBuffer PC Worker Log

## Purpose

Fix or precisely bound the PTX-mode remodeled IBuffer PC mismatch assertion in
`Subcore::single_decode()`. The assigned blocker was:

```text
assert(ibuffer_entry.m_inst->pc == ibuffer_entry.m_pc)
```

at `subcore.cc:934`, with prior focused evidence showing `sm_warp_id = 32`,
`ibuffer_entry.m_pc = 48`, and `ibuffer_entry.m_valid = true`.

The fix must preserve instruction ownership and the PC invariant, avoid
weakening the assertion, preserve trace-mode MICRO25/remodeled behavior, avoid
SM120/RTX5060 hard-coded values, and avoid accepted config or generated-output
changes.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base HEAD: `d75fb941c33f60c9b26451fa12a19d7daf3fae96`
- Base subject: `fix: regenerate PTX memory latency after execution`
- Timestamp: `2026-06-09T11:02:31+08:00`
- Run id: `s7-ibuffer-pc-20260609-104918`
- Artifact root: `artifacts/s7/s7-ibuffer-pc-20260609-104918/`
- Initial tracked working tree: clean before this task's source edits.

## Actions

- Read the supervisor log, overall plan, immediate L1C latency worker log, and
  prior parameter-constant routing and scoreboard-reserve worker logs.
- Inspected remodeled PTX fetch/decode/issue paths:
  - `Subcore::fetch()` reserves an `IBuffer_Entry` before instruction decode.
  - `Subcore::decode()` fills entries by exact local PC match.
  - `Subcore::get_next_inst()` clones the canonical PTX instruction so the
    remodeled IBuffer owns the dynamic instruction instance.
  - `SM::issue_warp()` transfers the owned instruction out of the IBuffer and
    updates SIMT/warp PC in the existing PTX execution path.
- Identified the root cause: PTX-mode `IBuffer_Remodeled` used the trace/SASS
  fetch reservation model. It reserved `fetch_decode_width` entries and
  advanced `m_next_pc_to_fetch_request` by fixed 16-byte strides before PTX
  decode knew the instruction size. PTX instruction size comes from the decoded
  PTX instruction (`pI->isize`, commonly 8 or 4), so later fetches could reserve
  entries at PCs that did not match the decoded instruction PC.
- Changed PTX-mode reservation semantics:
  - PTX mode now refuses another fetch while any unresolved invalid IBuffer
    entry exists.
  - PTX mode reserves one unresolved entry per fetch request.
  - After successful PTX decode, the IBuffer cursor advances to
    `decoded_pc + inst_size`.
  - Trace mode still uses `fetch_decode_width` and fixed 16-byte trace/SASS
    reservation stride.
- Added decode-time invariants before mutating the cloned instruction:
  - `pI->valid()`
  - `pI->pc == ibuffer_entry.m_pc`
- Preserved the original assignment-time assertion
  `ibuffer_entry.m_inst->pc == ibuffer_entry.m_pc`.
- Did not change accepted configs, generated bulk outputs, calibration `latest`,
  fake metrics, or any SM120/RTX5060-specific constants.

## Evidence

### Prior Blocker Evidence

Focused prior coredump evidence:

- `artifacts/s7/s7-l1c-latency-20260609-100045/coredump-gdb-focused-ibuffer-pc-3795871.log`

Observed state at `Subcore::single_decode()`:

- assertion site: `subcore.cc:934`
- `sm_warp_id = 32`
- `ibuffer_entry.m_pc = 48`
- `ibuffer_entry.m_valid = true`
- `ibuffer_entry.m_inst = pI = 0x7e86f8070280`

### Rebuild

Release runtime rebuild with local CUDA 13.1 passed.

Evidence:

- `artifacts/s7/s7-ibuffer-pc-20260609-104918/rebuild-gpgpusim-final.log`
- `artifacts/s7/s7-ibuffer-pc-20260609-104918/rebuild-gpgpusim-final.exitcode`,
  value `0`

### Generator And Whitespace Checks

`python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`
passed.

Evidence:

- `artifacts/s7/s7-ibuffer-pc-20260609-104918/generate-check-only.log`
- `artifacts/s7/s7-ibuffer-pc-20260609-104918/generate-check-only.exitcode`,
  value `0`

`git diff --check` passed before and after the smoke.

Evidence:

- `artifacts/s7/s7-ibuffer-pc-20260609-104918/git-diff-check.log`
- `artifacts/s7/s7-ibuffer-pc-20260609-104918/git-diff-check.exitcode`,
  value `0`
- `artifacts/s7/s7-ibuffer-pc-20260609-104918/git-diff-check-post-smoke.log`
- `artifacts/s7/s7-ibuffer-pc-20260609-104918/git-diff-check-post-smoke.exitcode`,
  value `0`

### Setup-Only Smoke Planning

Setup-only planning for
`rodinia_2.0-ft:backprop-rodinia-2.0-ft:0` and `RTX5060_SM120_GEN` passed.

Evidence:

- `artifacts/s7/s7-ibuffer-pc-20260609-104918/local-smoke-plan.log`
- `artifacts/s7/s7-ibuffer-pc-20260609-104918/local-smoke-plan.exitcode`,
  value `0`

### One Local Smoke

Exactly one local smoke was run after the build and checks passed.

Evidence:

- Smoke launch:
  `artifacts/s7/s7-ibuffer-pc-20260609-104918/local-smoke-run.log`
- Job id: `473`
- Captured stdout:
  `artifacts/s7/s7-ibuffer-pc-20260609-104918/smoke-stdout.o473`
- Captured stderr:
  `artifacts/s7/s7-ibuffer-pc-20260609-104918/smoke-stderr.e473`
- Result search:
  `artifacts/s7/s7-ibuffer-pc-20260609-104918/smoke-result-search.log`

The assigned old assertion did not recur. The `== old assertion ==` section in
`smoke-result-search.log` is empty. No real simulator metrics were produced.

The smoke advanced to a new downstream abort:

```text
ERROR. EXECUTION PIPELINE FOR THIS INSTRUCTION NOT IMPLEMENTED
```

at `Subcore::get_fu()` / `subcore.cc:897`.

New blocker evidence:

- `artifacts/s7/s7-ibuffer-pc-20260609-104918/core.3995085`
- `artifacts/s7/s7-ibuffer-pc-20260609-104918/coredump-info-3995085.log`
- `artifacts/s7/s7-ibuffer-pc-20260609-104918/coredump-gdb-bt-3995085.log`
- `artifacts/s7/s7-ibuffer-pc-20260609-104918/coredump-gdb-focused-pipeline-thread1-3995085.log`

Focused GDB state for the new blocker:

- aborting thread: thread 1 / LWP `3995134`
- frame: `Subcore::get_fu(this=0x653346b73a10, pI=0x7d20d403f260)`
- `pI->pc = 0x2420`
- `pI->isize = 8`
- `pI->op = ALU_OP`
- `pI->sp_op = INT__OP`
- `pI->op_pipe = UNKOWN_OP`
- `pI->oprnd_type = INT_OP`
- `pI->memory_op = no_memory_op`
- `pI->m_decoded = true`
- `pI->m_warp_id = 12`
- `pI->m_dynamic_warp_id = 12`

This is a separate PTX pipeline-classification blocker; it is not the assigned
IBuffer PC assertion.

## Changed Files

Code:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/ibuffer_remodeled.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/ibuffer_remodeled.h`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc`

Documentation:

- `docs/sm120-calibration/worker-logs/worker-20260609-110231-s7-ibuffer-pc.md`

Ignored/local artifacts:

- `artifacts/s7/s7-ibuffer-pc-20260609-104918/`

## Reviewer Rounds

- Round 1 fresh read-only reviewer attempt: failed before review due to a CLI
  option ordering error.
  - Prompt:
    `artifacts/s7/s7-ibuffer-pc-20260609-104918/reviewer-round1.prompt.txt`
  - Stdout:
    `artifacts/s7/s7-ibuffer-pc-20260609-104918/reviewer-round1-codex.stdout.txt`
  - Stderr:
    `artifacts/s7/s7-ibuffer-pc-20260609-104918/reviewer-round1-codex.stderr.txt`
  - Exit code:
    `artifacts/s7/s7-ibuffer-pc-20260609-104918/reviewer-round1-codex.exitcode`,
    value `2`
- Round 2 fresh read-only reviewer attempt: timed out without a final verdict.
  The partial transcript showed the reviewer had scoped the question to the
  PC invariant and trace-mode fetch behavior, but it did not return `ACCEPT` or
  `CHANGES_NEEDED` before the timeout.
  - Prompt:
    `artifacts/s7/s7-ibuffer-pc-20260609-104918/reviewer-round2.prompt.txt`
  - Stdout:
    `artifacts/s7/s7-ibuffer-pc-20260609-104918/reviewer-round2-codex.stdout.txt`
  - Stderr:
    `artifacts/s7/s7-ibuffer-pc-20260609-104918/reviewer-round2-codex.stderr.txt`
  - Exit code:
    `artifacts/s7/s7-ibuffer-pc-20260609-104918/reviewer-round2-codex.exitcode`,
    value `124`
- Round 3 fresh bounded blank-context reviewer: `ACCEPT`.
  - Prompt:
    `artifacts/s7/s7-ibuffer-pc-20260609-104918/reviewer-round3.prompt.txt`
  - Final message:
    `artifacts/s7/s7-ibuffer-pc-20260609-104918/reviewer-round3-last-message.txt`
  - Stdout:
    `artifacts/s7/s7-ibuffer-pc-20260609-104918/reviewer-round3-codex.stdout.txt`
  - Stderr:
    `artifacts/s7/s7-ibuffer-pc-20260609-104918/reviewer-round3-codex.stderr.txt`
  - Exit code:
    `artifacts/s7/s7-ibuffer-pc-20260609-104918/reviewer-round3-codex.exitcode`,
    value `0`
  - Reviewer verdict: `ACCEPT`

## Final Status

Accepted by the worker's fresh bounded blank-context reviewer. The assigned
PTX-mode IBuffer PC mismatch assertion is resolved in the one allowed local
smoke, and the smoke advanced to a separate bounded PTX `ALU_OP`
pipeline-classification abort in `Subcore::get_fu()`. No real simulator metrics
were produced before the new blocker.
