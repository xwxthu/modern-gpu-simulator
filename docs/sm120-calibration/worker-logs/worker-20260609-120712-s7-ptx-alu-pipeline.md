# S7 PTX ALU Pipeline Worker Log

## Purpose

Fix or precisely bound the PTX-mode remodeled ALU pipeline classification
blocker reached by the previous S7 smoke. The assigned blocker was:

```text
ERROR. EXECUTION PIPELINE FOR THIS INSTRUCTION NOT IMPLEMENTED
```

at `Subcore::get_fu()`, with focused decoded PTX state:

```text
pc=0x2420, isize=8, op=ALU_OP, sp_op=INT__OP,
op_pipe=UNKOWN_OP, oprnd_type=INT_OP, memory_op=no_memory_op
```

The fix must classify decoded PTX integer/scalar ALU operations before
remodeled FU selection. It must not map all `UNKOWN_OP` instructions to an
arbitrary pipeline, suppress the abort without understanding it, edit accepted
configs, or introduce SM120/RTX5060 hard-coded values.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base HEAD: `a103a0ebd4d084ca55b378d99d9566878ca05b9a`
- Base subject: `fix: handle variable PTX instruction fetch PCs`
- Timestamp: `2026-06-09T12:07:12+08:00`
- Run id: `s7-ptx-alu-pipeline-20260609-113915`
- Artifact root: `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/`
- Completion tracked changes: PTX classification code plus this worker log.

## Actions

- Read the supervisor log, overall plan, immediate S7 IBuffer PC worker log,
  and the prior S7 L1C latency worker context.
- Inspected PTX opcode/latency classification in:
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/cuda-sim.cc`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/ptx_ir.h`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/opcodes.def`
- Inspected remodeled FU dispatch and issue behavior in:
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/functional_unit.cc`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/register_file.cc`
- Identified the root cause: PTX `set_opcode_and_latency()` initializes
  instructions to generic `ALU_OP`. Some opcode cases set concrete architectural
  op classes such as `SP_OP`, `DP_OP`, `INTP_OP`, `SFU_OP`, or
  `TENSOR_CORE_OP`, but scalar leftovers such as `mov`, shifts, converts,
  bitwise ops, set/select, and predicate set could remain generic `ALU_OP`.
  The legacy non-remodeled scheduler can tolerate broader ALU classes, but
  remodeled `Subcore::get_fu()` dispatches by `pI->op` and intentionally aborts
  on unimplemented generic `ALU_OP`.
- Added `ptx_instruction::set_remaining_alu_pipeline_archop()` in PTX predecode.
  It runs after the existing operand-type and special-operation helpers:
  - only acts while `op == ALU_OP`
  - maps `SETP_OP` to `PREDICATE_OP`
  - maps remaining scalar ALU opcode leftovers by existing `sp_op` metadata:
    FP to `SP_OP`, DP to `DP_OP`, FP special to `SFU_OP`, tensor to
    `TENSOR_CORE_OP`, and INT variants to `INTP_OP`
  - leaves `OTHER_OP`, `TEX__OP`, and unlisted opcodes unchanged
- Did not change `op_pipe` as a fallback. In the remodeled path, `get_fu()`
  chooses a functional unit from `pI->op`; the FU later writes `op_pipe` during
  issue.
- Did not change trace/SASS metadata paths, memory/control/special-op handling,
  accepted configs, generated config outputs, calibration `latest`, or fake
  metrics.

## Evidence

### Prior Blocker

Prior evidence came from:

- `artifacts/s7/s7-ibuffer-pc-20260609-104918/coredump-gdb-focused-pipeline-thread1-3995085.log`

Focused state:

- frame: `Subcore::get_fu(this=..., pI=...)`
- `pI->pc = 0x2420`
- `pI->isize = 8`
- `pI->op = ALU_OP`
- `pI->sp_op = INT__OP`
- `pI->op_pipe = UNKOWN_OP`
- `pI->oprnd_type = INT_OP`
- `pI->memory_op = no_memory_op`
- `pI->m_decoded = true`

The corresponding PTX smoke source contains the early scalar ALU pattern that
exercises this path, including `mov`, `setp`, and `shl` instructions in
`backprop-rodinia-2.7.sm_120.ptx`.

### Rebuild

Release GPGPU-Sim runtime rebuild with local CUDA passed.

Evidence:

- `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/rebuild-gpgpusim.log`
- `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/rebuild-gpgpusim.exitcode`,
  value `0`

### Generator And Whitespace Checks

`python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`
passed.

Evidence:

- `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/generate-check-only.log`
- `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/generate-check-only.exitcode`,
  value `0`

`git diff --check` passed before and after the smoke.

Evidence:

- `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/git-diff-check.log`
- `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/git-diff-check.exitcode`,
  value `0`
- `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/git-diff-check-post-smoke.log`
- `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/git-diff-check-post-smoke.exitcode`,
  value `0`

### Setup-Only Smoke Planning

Setup-only planning for
`rodinia_2.0-ft:backprop-rodinia-2.0-ft:0` and `RTX5060_SM120_GEN` passed.

Evidence:

- `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/local-smoke-plan.log`
- `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/local-smoke-plan.exitcode`,
  value `0`

### One Local Smoke

Exactly one local smoke was run after the build and checks passed.

Evidence:

- Smoke launch:
  `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/local-smoke-run.log`
- Job id: `474`
- Captured stdout/stderr under:
  `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/sim-smoke/`
- Result search:
  `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/smoke-result-search.log`

The assigned old abort did not recur. The `== old pipeline abort ==` section in
`smoke-result-search.log` is empty. No real simulator metrics were produced.

The smoke advanced to a new downstream assertion:

```text
cuda-sim.cc:1968: void ptx_thread_info::ptx_exec_inst(...):
Assertion `pc == inst.pc' failed.
```

New blocker evidence:

- `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/core.55046`
- `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/coredump-info-55046.log`
- `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/coredump-gdb-focused-pc-mismatch-frame7-55046.log`

Focused new-blocker state:

- frame: `ptx_thread_info::ptx_exec_inst()` at `cuda-sim.cc:1968`
- issued dynamic instruction `inst.pc = 0x2460`
- `inst.isize = 8`
- `inst.op = INTP_OP`
- `inst.sp_op = INT__OP`
- `inst.op_pipe = UNKOWN_OP` before FU issue writes it
- `inst.oprnd_type = INT_OP`
- `inst.memory_op = no_memory_op`
- `inst.m_fu_assigned = 0x5fd26761e900`
- functional lane `lane_id = 1` has `pc = 0x24a0`
- active mask contains all 32 lanes

This shows the assigned ALU pipeline classification blocker is resolved: the
issued instruction is now a concrete `INTP_OP` with a selected FU. The remaining
failure is a separate PTX functional PC mismatch after divergence near the
`bar.sync 0` region.

## Changed Files

Code:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/cuda-sim.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/ptx_ir.h`

Documentation:

- `docs/sm120-calibration/worker-logs/worker-20260609-120712-s7-ptx-alu-pipeline.md`

Ignored/local artifacts:

- `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/`

## Reviewer Rounds

- Round 1 fresh reviewer attempt failed before review due to incorrect Codex
  CLI option usage.
  - Prompt:
    `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/reviewer-round1.prompt.txt`
  - Exit code:
    `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/reviewer-round1-codex.exitcode`,
    value `2`
- Round 2 fresh reviewer attempt also failed before review due to another CLI
  option usage error.
  - Exit code:
    `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/reviewer-round2-codex.exitcode`,
    value `2`
- Round 3 fresh reviewer attempt was stopped after it ran for several minutes
  without producing a final verdict.
  - Exit code recorded as:
    `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/reviewer-round3-codex.exitcode`,
    value `124`
- Round 4 fresh bounded read-only reviewer returned `ACCEPT`.
  - Prompt:
    `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/reviewer-round4.prompt.txt`
  - Final message:
    `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/reviewer-round4-last-message.txt`
  - Exit code:
    `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/reviewer-round4-codex.exitcode`,
    value `0`
  - Reviewer note: no blocking scope issue in the classifier path; memory/control
    are still handled earlier, `TEX__OP`/`OTHER_OP` remain unchanged, and the
    old failure state now has an explicit `INTP_OP` FU path.

## Final Status

The assigned PTX ALU pipeline classification blocker is fixed for the local S7
smoke. The smoke now reaches a new downstream PTX execution PC mismatch in
`ptx_thread_info::ptx_exec_inst()` at `cuda-sim.cc:1968`. That blocker is
bounded by coredump/GDB evidence above and should be handled as a separate S7
follow-up. No configs were promoted, no calibration metrics were claimed, and no
full simulator workload was run on `dsp5060`.
