# S7 PTX Functional PC Worker Log

## Purpose

Fix or precisely bound the PTX-mode functional PC mismatch assertion reached by
the previous S7 smoke. The assigned blocker was:

```text
cuda-sim.cc:1968: void ptx_thread_info::ptx_exec_inst(...):
Assertion `pc == inst.pc' failed.
```

Focused prior evidence showed timing issued PTX instruction `inst.pc = 0x2460`
with `inst.op = INTP_OP`, `inst.sp_op = INT__OP`, and all 32 lanes active,
while lane 1 functional PC had already advanced to `0x24a0`.

The fix must keep timing issue and PTX functional PCs synchronized, preserve
SIMT divergence/reconvergence semantics, avoid removing the assertion or
skipping mismatched lanes, preserve trace-mode MICRO25/remodeled behavior, and
avoid SM120/RTX5060 hard-coded values or config promotion.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base HEAD: `19ec9615890084d002a323ef5d142a0e24bb677d`
- Base subject: `fix: classify PTX scalar ALU pipelines`
- Timestamp: `2026-06-09T12:37:40+08:00`
- Run id: `s7-ptx-functional-pc-20260609-122555`
- Artifact root: `artifacts/s7/s7-ptx-functional-pc-20260609-122555/`
- Initial tracked working tree for this task: clean at base HEAD before this
  task's source edits.

## Actions

- Read the supervisor log, overall plan, immediate PTX ALU pipeline worker log,
  and prior S7 IBuffer PC worker log.
- Inspected PTX functional execution and SIMT-stack control flow:
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/cuda-sim.cc`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/abstract_hardware_model.cc`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/abstract_hardware_model.h`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/sm.cc`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/ibuffer_remodeled.cc`
- Identified the root cause: remodeled `simt_stack::update()` was an empty
  imported stub. `SM::issue_warp()` still called `updateSIMTStack()` in PTX
  mode after functional execution, but the SIMT stack never consumed the
  per-lane functional next PCs. After the divergent branch at PTX PC `0x2458`,
  functional lanes moved to the immediate postdominator at `0x24a0`, while the
  timing model still fetched and issued stale fall-through PC `0x2460` with the
  old full active mask.
- Restored the standard post-dominator SIMT stack update logic in
  `abstract_hardware_model.cc`:
  - groups active lanes by functional next PC after execution
  - handles completed lanes, call/return entries, branch divergence, and
    reconvergence entries
  - records warp-divergence stats when a warp diverges
  - keeps the existing invariant that the SIMT-stack top PC equals the issued
    instruction PC before updating
- Added a PTX-mode stale IBuffer head check before remodeled issue in
  `Subcore::issue()`:
  - reads the current SIMT-stack top PC for the SM warp
  - if the decoded IBuffer head PC no longer matches the SIMT top PC, resets
    the warp next PC to the SIMT top and flushes that warp's IBuffer
  - continues scheduling so the next fetch/decode pulls from the reconverged or
    divergent-path PC rather than issuing stale decoded instructions
  - leaves trace mode untouched through the existing `!is_trace_mode` guard
- Fixed `IBuffer_Remodeled::flush(false)` in PTX mode by avoiding an
  unconditional `trace_shd_warp_t` cast. Trace mode still uses
  `trace_shd_warp_t::get_pc()`; PTX mode uses `shd_warp_t::get_pc()`.
- Bounded the next blocker with code-path evidence rather than changing it as
  part of this PC synchronization task: the new assertion is caused by missing
  PTX barrier id/count propagation into the dynamic timing `warp_inst_t`, not
  by another functional PC mismatch.
- Did not remove or weaken the `pc == inst.pc` assertion, skip lanes, edit
  accepted configs, edit generated config outputs, update calibration `latest`,
  run full simulator workloads on `dsp5060`, or produce fake metrics.

## Evidence

### Prior Blocker

Prior evidence came from:

- `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/coredump-gdb-focused-pc-mismatch-frame7-55046.log`

Focused prior state:

- frame: `ptx_thread_info::ptx_exec_inst()` at `cuda-sim.cc:1968`
- assertion: `pc == inst.pc`
- issued dynamic instruction `inst.pc = 0x2460`
- `inst.isize = 8`
- `inst.op = INTP_OP`
- `inst.sp_op = INT__OP`
- `inst.op_pipe = UNKOWN_OP` before FU issue writes it
- `inst.oprnd_type = INT_OP`
- `inst.memory_op = no_memory_op`
- `inst.m_fu_assigned` non-null
- functional lane `lane_id = 1` had `pc = 0x24a0`
- active mask contained all 32 lanes

Smoke stdout also showed the relevant PTX control-flow region:

```text
branch divergence @ PC=0x2458 ... @%p1 bra $L__BB0_2;
immediate post dominator @ PC=0x24a0 ... bar.sync 0;
```

This matched a stale timing-side fall-through instruction being issued after
functional SIMT execution had advanced lanes to the postdominator.

### Rebuild

Release GPGPU-Sim runtime rebuild with local CUDA passed. CUDA 13.2 was not
installed locally; the available local CUDA runtime used by recent S7 workers
was CUDA 13.1.

Evidence:

- `artifacts/s7/s7-ptx-functional-pc-20260609-122555/rebuild-gpgpusim.log`
- `artifacts/s7/s7-ptx-functional-pc-20260609-122555/rebuild-gpgpusim.exitcode`,
  value `0`

### Generator And Whitespace Checks

`python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`
passed.

Evidence:

- `artifacts/s7/s7-ptx-functional-pc-20260609-122555/generate-check-only.log`
- `artifacts/s7/s7-ptx-functional-pc-20260609-122555/generate-check-only.exitcode`,
  value `0`

`git diff --check` passed after the source changes and before this worker log
was added.

Evidence:

- `artifacts/s7/s7-ptx-functional-pc-20260609-122555/git-diff-check.log`
- `artifacts/s7/s7-ptx-functional-pc-20260609-122555/git-diff-check.exitcode`,
  value `0`

### Setup-Only Smoke Planning

Setup-only planning for
`rodinia_2.0-ft:backprop-rodinia-2.0-ft:0` and `RTX5060_SM120_GEN` passed.

Evidence:

- `artifacts/s7/s7-ptx-functional-pc-20260609-122555/local-smoke-plan.log`
- `artifacts/s7/s7-ptx-functional-pc-20260609-122555/local-smoke-plan.exitcode`,
  value `0`

### One Local Smoke

Exactly one local smoke was run after the build and checks passed.

Evidence:

- Smoke launch:
  `artifacts/s7/s7-ptx-functional-pc-20260609-122555/local-smoke-run.log`
- Job id: `475`
- Captured stdout/stderr under:
  `artifacts/s7/s7-ptx-functional-pc-20260609-122555/sim-smoke/`
- Result search:
  `artifacts/s7/s7-ptx-functional-pc-20260609-122555/smoke-result-search.log`

The assigned old assertion did not recur. The `== old PC mismatch ==` section
in `smoke-result-search.log` is empty. No real simulator metrics were produced.

The smoke advanced to a new downstream assertion:

```text
shader.cc:3867: void barrier_set_t::warp_reaches_barrier(...):
Assertion `bar_id != (unsigned)-1' failed.
```

New blocker evidence:

- `artifacts/s7/s7-ptx-functional-pc-20260609-122555/core.278826`
- `artifacts/s7/s7-ptx-functional-pc-20260609-122555/coredump-info-278826.log`
- `artifacts/s7/s7-ptx-functional-pc-20260609-122555/coredump-gdb-focused-barrier-278826.log`

Focused new-blocker state:

- frame: `barrier_set_t::warp_reaches_barrier()`
- assertion site: `shader.cc:3867`
- `bar_type = SYNC`
- `bar_id = 4294967295` (`(unsigned)-1`)
- warp id around `44`

The run reached the reconvergence/postdominator `bar.sync 0` region.

### New Barrier Blocker Bound

The downstream barrier assertion is separate from the assigned PC synchronization
blocker:

- `SM::issue_warp()` first executes PTX functionally via `func_exec_inst()` and
  then immediately routes `BARRIER_OP`/`MEMORY_BARRIER_OP` to
  `m_barriers.warp_reaches_barrier()`:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/sm.cc:372`
  and `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/sm.cc:388`.
- PTX `bar_impl()` decodes `bar.sync` operands and writes `bar_id`/`bar_count`
  onto the functional `ptx_instruction`:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/instructions.cc:1506`.
- `ptx_thread_info::ptx_exec_inst()` copies memory return metadata back into
  the issued dynamic `warp_inst_t` at
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/cuda-sim.cc:2202`,
  but does not copy PTX barrier id/count metadata.
- The timing-side `warp_inst_t` defaults `bar_id` and `bar_count` to
  `(unsigned)-1`, and `barrier_set_t::warp_reaches_barrier()` asserts that
  `bar_id` is valid at
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader.cc:3867`.

Thus the next precise blocker is PTX barrier metadata propagation from the
functional PTX instruction into the dynamic timing instruction before the
remodeled barrier set consumes it. This task did not change that path because
the requested PC mismatch was resolved and the one allowed smoke had already
advanced to this new assertion.

## Changed Files

Code:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/abstract_hardware_model.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/ibuffer_remodeled.cc`

Documentation:

- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/worker-logs/worker-20260609-123740-s7-ptx-functional-pc.md`

Ignored/local artifacts:

- `artifacts/s7/s7-ptx-functional-pc-20260609-122555/`

## Reviewer Rounds

- Round 1 fresh read-only reviewer attempt failed before review due to Codex CLI
  option placement.
  - Exit code:
    `artifacts/s7/s7-ptx-functional-pc-20260609-122555/reviewer/reviewer-round1.exitcode`,
    value `2`
- Round 2 fresh read-only reviewer returned `CHANGES_NEEDED`.
  - Reviewer found that this worker log was not visible under the repository
    root because it had been accidentally created in `/home/xiewx/accel-0608/`
    rather than `/home/xiewx/accel-0608/modern-gpu-simulator/`.
  - Reviewer also requested cleaner bounding of the downstream barrier metadata
    assertion.
  - Follow-up: recreated this worker log in the repository, updated
    `overall-plan.md` to stop naming the resolved PC mismatch as the current
    blocker, and added the explicit barrier metadata code-path evidence above.
- Round 3 fresh read-only reviewer returned `ACCEPT`.
  - Final message:
    `artifacts/s7/s7-ptx-functional-pc-20260609-122555/reviewer/reviewer-round3.last.txt`
  - Exit code:
    `artifacts/s7/s7-ptx-functional-pc-20260609-122555/reviewer/reviewer-round3.exitcode`,
    value `0`

## Final Status

Reviewer accepted. Final generator check-only and `git diff --check` passed
after the worker log and `overall-plan.md` updates. The assigned PTX functional
PC mismatch is resolved by the one allowed local smoke. The smoke is now blocked
by a separate PTX barrier metadata assertion at `shader.cc:3867`; no calibration
metrics were produced and no configs were promoted.
