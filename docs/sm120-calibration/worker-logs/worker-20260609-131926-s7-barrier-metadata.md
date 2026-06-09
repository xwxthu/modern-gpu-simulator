# S7 Barrier Metadata Worker Log

## Purpose

Fix or precisely bound the PTX-mode barrier metadata assertion reached by the
previous S7 smoke:

```text
shader.cc:3867: void barrier_set_t::warp_reaches_barrier(...):
Assertion `bar_id != (unsigned)-1' failed.
```

Focused prior evidence from
`artifacts/s7/s7-ptx-functional-pc-20260609-122555/` showed:

- `bar_type = SYNC`
- `bar_id = 4294967295` (`(unsigned)-1`)
- the run had reached a `bar.sync 0` reconvergence region

The target fix was to propagate PTX functional barrier metadata into the
timing-side dynamic `warp_inst_t` instead of using a default-id workaround,
while leaving trace-mode behavior, generated configs, accepted configs,
calibration results, and barrier assertions unchanged.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base HEAD requested by supervisor:
  `7622468124f2cb4d146efc4dbaad96b14d6829fc`
- Actual `git rev-parse HEAD` at task start:
  `7622468124f2cb4d146efc4dbaad96b14d6829fc`
- Base subject: `fix: synchronize PTX functional PCs with SIMT stack`
- Timestamp: `2026-06-09T13:19:26+08:00`
- Artifact root: `artifacts/s7/s7-barrier-metadata-20260609-131926/`
- Initial tracked working tree: clean; only ignored artifacts/build outputs were
  present.

## Actions

- Read:
  - `docs/sm120-calibration/supervisor-log.md`
  - `docs/sm120-calibration/overall-plan.md`
  - `docs/sm120-calibration/worker-logs/worker-20260609-123740-s7-ptx-functional-pc.md`
- Verified the PTX barrier metadata path:
  - PTX decode classifies `BAR_OP` and `SST_OP` as `BARRIER_OP` and sets
    static `bar_type`/`red_type` in
    `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/cuda-sim.cc`.
  - Remodeled PTX decode obtains the canonical instruction through
    `gpgpu_context::ptx_fetch_inst(pc)` and clones it into a mutable dynamic
    `warp_inst_t` in
    `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc`.
  - PTX `bar_impl()` resolves runtime barrier operands and writes
    `bar_id`/`bar_count` onto the functional `ptx_instruction` in
    `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/instructions.cc`.
  - `ptx_thread_info::ptx_exec_inst()` already copies runtime memory metadata
    back to the dynamic `warp_inst_t`, but did not copy barrier metadata.
  - Remodeled `SM::issue_warp()` calls `func_exec_inst(*pipe_reg)` before
    routing `BARRIER_OP` to `m_barriers.warp_reaches_barrier()`.
  - `barrier_set_t::warp_reaches_barrier()` consumes `inst->bar_type`,
    `inst->bar_id`, and `inst->bar_count`, and correctly asserts that
    `bar_id` is valid.
- Implemented a narrow root-cause fix in `ptx_exec_inst()`:
  - after a PTX barrier instruction has functionally executed and resolved its
    metadata, copy `bar_type`, `red_type`, `bar_id`, and `bar_count` from the
    functional `ptx_instruction` into the dynamic timing `warp_inst_t`
  - gate the copy with `!skip` so predicated-off lanes do not propagate stale
    metadata
- Did not:
  - set default barrier id 0 as a workaround
  - remove or weaken `bar_id != (unsigned)-1`
  - skip barrier handling
  - edit accepted/generated configs, `latest`, calibration results, or metrics
  - run full simulator workloads on `dsp5060`

## Root Cause

In PTX mode, the canonical `ptx_instruction` and the dynamic timing
`warp_inst_t` are separate objects after remodeled IBuffer cloning. `bar_impl()`
correctly resolves the runtime operands of `bar.sync 0` and writes the valid
barrier id/count onto the functional `ptx_instruction`, but the dynamic
`warp_inst_t` still retained constructor defaults:

```text
bar_type = SYNC
bar_id = 4294967295
bar_count = 4294967295
```

Because `SM::issue_warp()` immediately routes the dynamic instruction to
`barrier_set_t::warp_reaches_barrier()` after functional execution, the barrier
set observed the stale default `bar_id` and hit the assertion.

## Changed Files

Code:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/cuda-sim.cc`

Documentation:

- `docs/sm120-calibration/worker-logs/worker-20260609-131926-s7-barrier-metadata.md`

Ignored/local artifacts:

- `artifacts/s7/s7-barrier-metadata-20260609-131926/`

## Validation Commands And Results

`git diff --check` passed before and after validation.

Evidence:

- `artifacts/s7/s7-barrier-metadata-20260609-131926/git-diff-check-prebuild.log`
- `artifacts/s7/s7-barrier-metadata-20260609-131926/git-diff-check-final.log`
- exit codes both `0`

SM120 generated-config reproducibility check passed:

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
```

Evidence:

- `artifacts/s7/s7-barrier-metadata-20260609-131926/generate-check-only.log`
- `artifacts/s7/s7-barrier-metadata-20260609-131926/generate-check-only.exitcode`,
  value `0`

Release GPGPU-Sim rebuild passed with local CUDA 13.1:

```bash
export CUDA_INSTALL_PATH=${CUDA_INSTALL_PATH:-/usr/local/cuda-13.1}
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment
make -C simulator-remodeled/gpu-simulator/gpgpu-sim -j"$(nproc)"
```

Evidence:

- `artifacts/s7/s7-barrier-metadata-20260609-131926/rebuild-gpgpusim.log`
- `artifacts/s7/s7-barrier-metadata-20260609-131926/rebuild-gpgpusim.exitcode`,
  value `0`

Setup-only smoke plan passed:

```bash
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-barrier-metadata-20260609-131926-smoke-plan \
  -r artifacts/s7/s7-barrier-metadata-20260609-131926/sim-smoke-plan \
  -l local \
  -n
```

Evidence:

- `artifacts/s7/s7-barrier-metadata-20260609-131926/local-smoke-plan.log`
- `artifacts/s7/s7-barrier-metadata-20260609-131926/local-smoke-plan.exitcode`,
  value `0`

One post-fix local PTX smoke was launched and allowed to run to its next
assertion:

```bash
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-barrier-metadata-20260609-131926-smoke \
  -r artifacts/s7/s7-barrier-metadata-20260609-131926/sim-smoke \
  -l local \
  -c 4
```

Evidence:

- launch log:
  `artifacts/s7/s7-barrier-metadata-20260609-131926/local-smoke-run.log`
- job id: `476`
- procman final state:
  `artifacts/s7/s7-barrier-metadata-20260609-131926/procman-status-210s.log`
- result search:
  `artifacts/s7/s7-barrier-metadata-20260609-131926/smoke-result-search.log`

The assigned old blocker disappeared:

- no `bar_id != (unsigned)-1` assertion appears in the result search
- no `pc == inst.pc` regression appears in the result search
- the run progressed past the earlier barrier handling point

The smoke advanced to a new downstream blocker:

```text
subcore.cc:916: void Subcore::single_decode(...):
Assertion `pI->valid()' failed.
```

Focused evidence:

- `artifacts/s7/s7-barrier-metadata-20260609-131926/coredump-info-610918.log`
- `artifacts/s7/s7-barrier-metadata-20260609-131926/core.610918`
- `artifacts/s7/s7-barrier-metadata-20260609-131926/coredump-gdb-focused-decode-frame7-610918.log`

GDB frame 7 shows the new blocker is a non-null but default/invalid decoded
instruction at remodeled decode:

```text
Subcore::single_decode(..., pI=0x75135043cbf0, ...) at subcore.cc:916
pI->pc = 18446744073709551615
pI->m_decoded = false
pI->op = NO_OP
pI->isize = 0
```

No calibration or correlation metrics were produced, and no config was promoted.

## Reviewer Rounds

- Round 1 fresh read-only reviewer attempt failed before review due to Codex
  CLI option placement.
  - Exit code:
    `artifacts/s7/s7-barrier-metadata-20260609-131926/reviewer/reviewer-round1.exitcode`,
    value `2`
- Round 2 fresh blank-context read-only reviewer returned `ACCEPT`.
  - Reviewer found no blocking issues.
  - Reviewer confirmed the change is a root-cause metadata propagation fix,
    not a default-id workaround; trace mode is unaffected; no configs or
    metrics were promoted; validation is adequate for this blocker; and no
    cleaner narrower approach was identified.
  - Final reviewer message:
    `artifacts/s7/s7-barrier-metadata-20260609-131926/reviewer/reviewer-round2.last.txt`
  - Exit code:
    `artifacts/s7/s7-barrier-metadata-20260609-131926/reviewer/reviewer-round2.exitcode`,
    value `0`

## Final Status

Reviewer accepted. The code fix is complete and validated through build,
generator check, and one local PTX smoke. The old PTX barrier metadata assertion
is resolved for the smoke. The current precise blocker is now the downstream
remodeled PTX decode assertion at `Subcore::single_decode()` where `pI` is
non-null but invalid/default decoded. No calibration/correlation execution was
completed and no metrics/configs were promoted.
