# S7 Kernel 2 Bottleneck Attribution Worker Log

## Purpose

Attribute, or sharply narrow, why the `backprop` second PTX
performance-simulation kernel
`_Z24bpnn_adjust_weights_cudaPfiS_iS_S_` makes extremely slow progress after
all CTAs are resident.

This is S7 system integration and PTX-mode local smoke bring-up attribution. It
is not calibration, correlation search, config promotion, or metrics
promotion.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base commit: `db1673770b38b1f8ae0a6c0f92269307664e298f`
- Timestamp: `2026-06-09T21:14:10+08:00`
- Artifact root:
  `artifacts/s7/s7-kernel2-attribution-20260609-211410/`
- Required prior context read:
  - `docs/sm120-calibration/supervisor-log.md`
  - `docs/sm120-calibration/overall-plan.md`
  - `docs/sm120-calibration/worker-logs/worker-20260609-191215-s7-kernel2-progress.md`

## Assigned Scope

- Do not modify accepted/generated/latest configs.
- Do not write or promote calibration results.
- Do not claim calibration or correlation completion.
- Do not run full simulator workloads on `dsp5060`.
- Use only local bounded smoke runs.
- Prefer the existing `GPGPUSIM_KERNEL_PROGRESS_DEBUG=1` default-off
  diagnostic path.
- Keep diagnostics reviewable, read-only, and default-off.
- Distinguish these candidate causes if evidence reaches the target window:
  CTA barrier release/bookkeeping, SIMT/reconvergence near PC `0x2890`,
  scheduler issue/no-issue state, and post-barrier memory-return or scoreboard
  latency.

## Prior Interrupted Attempt And Reviewer Round 1

An interrupted attribution attempt created evidence under
`artifacts/s7/s7-kernel2-attribution-20260609-202252/` and launched one local
bounded smoke as ProcMan job `485`.

Round 1 fresh read-only reviewer verdict:

- Verdict: `CHANGES_NEEDED`
- Main findings:
  - The smoke only reached `next_cta=180`, `cta_completed_kernel=0`, so it did
    not cover the assigned all-CTAs-resident window.
  - The candidate attribution was under-supported because the target slow-tail
    state was missing.
  - No required worker log existed for the attribution task.
  - `Subcore::issue()` updated `m_last_issue_debug` and performed extra debug
    checks on the default path even when `GPGPUSIM_KERNEL_PROGRESS_DEBUG` was
    not enabled.

Supervisor rework authorization:

- Continue the same worker task.
- First fix the subcore issue diagnostic env-gating problem.
- Record the reviewer `CHANGES_NEEDED` result and authorization here.
- Run exactly one additional bounded local smoke with instrumentation because
  the first smoke did not reach `next_cta=256`.
- If the second smoke still does not reach the target window, report that
  precise blocker and do not launch a third smoke.

## Diagnostic Instrumentation

Existing/default-off environment:

- Enable: `GPGPUSIM_KERNEL_PROGRESS_DEBUG=1`
- Default: disabled when unset, empty, or `0`
- Interval: `GPGPUSIM_KERNEL_PROGRESS_INTERVAL`, default `50000`
- SM sample cap: `GPGPUSIM_KERNEL_PROGRESS_SM_LIMIT`, default `6`
- Output prefix: `GPGPUSIM-K2-PROGRESS`

Rework changes:

- `Subcore::issue()` now caches whether issue diagnostics are enabled at
  construction from `GPGPUSIM_KERNEL_PROGRESS_DEBUG`.
- All writes to `m_last_issue_debug` are guarded by that cached debug flag.
- Extra issue-debug barrier/membar/gridbar checks and selected-warp scoreboard
  count queries are only performed when the debug flag is enabled.
- The local subcore env helper now follows the global debug semantics: unset,
  empty, or `0` means disabled.

## Actions

- Re-read the required S7 documents and confirmed current branch/head:
  `dev-5060` at `db1673770b38b1f8ae0a6c0f92269307664e298f`.
- Inspected the interrupted attribution artifacts and reviewer output.
- Patched subcore issue diagnostics to be strictly env-gated.
- Created this required worker log.
- Ran validation after the gating patch:
  - `git diff --check`
  - `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`
- Rebuilt local release GPGPU-Sim runtime.
- Ran setup-only local smoke planning for
  `rodinia_2.0-ft:backprop-rodinia-2.0-ft:0` with `RTX5060_SM120_GEN`.
- Launched the supervisor-authorized second bounded local smoke as ProcMan job
  `486` with:
  - `GPGPUSIM_KERNEL_PROGRESS_DEBUG=1`
  - `GPGPUSIM_KERNEL_PROGRESS_INTERVAL=200000`
  - `GPGPUSIM_KERNEL_PROGRESS_SM_LIMIT=1`
  - wall-time boundary: 70 minutes
  - local server only

## Evidence

Second bounded smoke, ProcMan job `486`, completed and produced final
stdout/stderr under:

- `artifacts/s7/s7-kernel2-attribution-20260609-211410/smoke-stdout-final.o486.log`
- `artifacts/s7/s7-kernel2-attribution-20260609-211410/smoke-stderr-final.e486.log`

Job/process status:

- Launch command succeeded:
  `artifacts/s7/s7-kernel2-attribution-20260609-211410/local-smoke-run.exitcode`
  = `0`
- Final direct ProcMan state:
  `artifacts/s7/s7-kernel2-attribution-20260609-211410/procman-status-final-direct.log`
  reports `Nothing Active`.
- `procman-status-prekill.log` also reported `Nothing Active` before the
  cleanup command was issued, so the cleanup command did not terminate an
  active simulation.

Smoke result:

- Kernel 2:
  - `kernel_name = _Z24bpnn_adjust_weights_cudaPfiS_iS_S_`
  - `gpu_tot_sim_cycle = 45818`
  - `gpu_tot_sim_insn = 8036672`
- Overall runtime line:
  `gpgpu_simulation_time = 0 days, 0 hrs, 39 min, 58 sec (2398 sec)`
- Final application result: `PASSED`
- Summary refs:
  - `artifacts/s7/s7-kernel2-attribution-20260609-211410/final-evidence-grep.log`
  - `artifacts/s7/s7-kernel2-attribution-20260609-211410/smoke-result-summary.log`

Target-window evidence:

- Target window was reached at
  `smoke-stdout-final.o486.log:3068` and summarized in
  `kernel2-target-window-summary.log`.
- The target line has `next_cta=256`, `cta_completed_kernel=76`,
  `active_cta=180`, and `not_completed_threads=43648`.
- Sampled SM state at that point:
  - Dominant PC: `pc0=0x2890:27`
  - CTA barrier state:
    `active_warps=42,waiting_warps=26,active_cta=6,unreleased_ready=0,partial=5`
  - Scheduler state:
    `sc0{... issued=0,next=1,busy=0,valid=1,cand=10,ready=0,pc_mis=0,
    blk={sb=0,stall=0,waitbar=0,bar=10,membar=0,grid=0,ldgdep=0,fu=0,
    resq=0,l1c=0,greedy_l1c=0} ...}`
  - Memory-return/queue state:
    `mem_resp=0`, `mem_prt_active=0`, and all sampled `mem_q` entries are
    zero.
- The next sampled kernel-progress line,
  `smoke-stdout-final.o486.log:3069`, shows kernel 2 completed all CTAs:
  `cta_launched_kernel=256`, `cta_completed_kernel=256`, and
  `running_kernels=[]`.

Attribution:

- The slow post-resident segment is dominated by CTA barrier waiting/partial
  CTA-barrier state around PC `0x2890`.
- The sampled scheduler state is no-issue because no candidate warp is ready;
  the blocker counts are barrier-dominated (`bar=10` on sc0/sc1 and
  `bar=6` plus scoreboard for sc2 in the full target line).
- No sampled SIMT/reconvergence mismatch was observed at the target window
  (`pc_mis=0`, selected `pc` and `simt` match for barrier-selected warps).
- No sampled post-barrier memory-return or memory-queue tail was observed at
  the target window (`mem_resp=0`, `mem_prt_active=0`, queues zero).
- Scoreboard pressure is present earlier and on one sampled subcore candidate
  at the target line, but the all-CTAs-resident target sample is not explained
  by memory-return latency or a global load/store tail.
- No scoped root-cause fix was made because the evidence narrows the issue but
  does not prove a specific incorrect barrier-release/bookkeeping mutation.

## Changed Files

Code:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/ldst_unit_sm.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/ldst_unit_sm.h`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/sm.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/sm.h`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.h`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/scoreboard.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/scoreboard.h`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/scoreboard_reads.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/scoreboard_reads.h`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader.h`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader_core_wrapper.h`

Documentation:

- `docs/sm120-calibration/worker-logs/worker-20260609-211410-s7-kernel2-attribution.md`

Pre-existing dirty context file, not changed as part of this worker
finalization:

- `docs/sm120-calibration/supervisor-log.md`

Config/generated/calibration result changes:

- None.

## Validation

- `git diff --check`: pass
  - `artifacts/s7/s7-kernel2-attribution-20260609-211410/git-diff-check-after-gating.exitcode`
- `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`: pass
  - `artifacts/s7/s7-kernel2-attribution-20260609-211410/generate-check-only-after-gating.exitcode`
- GPGPU-Sim rebuild after gating patch: pass
  - `artifacts/s7/s7-kernel2-attribution-20260609-211410/rebuild-gpgpusim.exitcode`
- Setup-only local smoke planning: pass
  - `artifacts/s7/s7-kernel2-attribution-20260609-211410/local-smoke-plan.exitcode`
- Bounded diagnostic local PTX smoke:
  - ProcMan job `486`
  - result: completed, stdout contains `PASSED`
  - target window reached at `next_cta=256`
  - final ProcMan direct status: `Nothing Active`
  - artifacts:
    - `artifacts/s7/s7-kernel2-attribution-20260609-211410/smoke-stdout-final.o486.log`
    - `artifacts/s7/s7-kernel2-attribution-20260609-211410/smoke-stderr-final.e486.log`
- Final validation after the last source patch:
  - `git diff --check`: pass
    - `artifacts/s7/s7-kernel2-attribution-20260609-211410/git-diff-check-final.exitcode`
  - `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`:
    pass
    - `artifacts/s7/s7-kernel2-attribution-20260609-211410/generate-check-only-final.exitcode`
  - GPGPU-Sim rebuild: pass
    - `artifacts/s7/s7-kernel2-attribution-20260609-211410/final-rebuild-gpgpusim.exitcode`
  - Direct ProcMan final status check: pass
    - `artifacts/s7/s7-kernel2-attribution-20260609-211410/procman-status-final-direct.exitcode`
    - `artifacts/s7/s7-kernel2-attribution-20260609-211410/procman-status-final-direct.log`

## Reviewer Rounds

Round 1 fresh blank-context read-only reviewer:

- Artifact root:
  `artifacts/s7/s7-kernel2-attribution-20260609-202252/reviewer/round1/`
- Verdict: `CHANGES_NEEDED`
- Required rework: cover the post-resident kernel-2 window if possible, add the
  missing worker log, and strictly env-gate subcore issue diagnostics.

Round 2 fresh blank-context read-only reviewer:

- Artifact root:
  `artifacts/s7/s7-kernel2-attribution-20260609-211410/reviewer/round2/`
- Verdict: `ACCEPT`
- Reviewer found no blocking issues.
- Reviewer confirmed:
  - the authorized second smoke reached the target window and then completed
    with `PASSED`;
  - the candidate attribution is supported by the sampled barrier-dominated
    no-issue state, `pc_mis=0`, and zero sampled memory response/PRT/queues;
  - `Subcore::issue()` diagnostic snapshot updates and extra diagnostic probes
    are guarded by `GPGPUSIM_KERNEL_PROGRESS_DEBUG`;
  - no accepted/generated/latest config or calibration-result paths were
    modified;
  - residual risk is sample coverage only: the attribution narrows the
    bottleneck but does not prove a specific incorrect barrier-bookkeeping
    mutation.
- Artifacts:
  - `artifacts/s7/s7-kernel2-attribution-20260609-211410/reviewer/round2/reviewer-prompt.txt`
  - `artifacts/s7/s7-kernel2-attribution-20260609-211410/reviewer/round2/reviewer-output.log`
  - `artifacts/s7/s7-kernel2-attribution-20260609-211410/reviewer/round2/reviewer-final.txt`
  - `artifacts/s7/s7-kernel2-attribution-20260609-211410/reviewer/round2/reviewer-exitcode`

## Final Status

Complete for this S7 attribution task. Final verdict: kernel-2 slow progress in
the sampled all-CTAs-resident window is attributable to CTA-barrier
waiting/partial-barrier state around PC `0x2890`, with scheduler no-issue
because sampled candidates are not ready. The bounded evidence rules out, for
the sampled target window, a SIMT/reconvergence mismatch (`pc_mis=0`) and a
post-barrier memory-return/queue tail (`mem_resp=0`, `mem_prt_active=0`,
queues zero). No speculative root-cause fix was made.

This worker has not claimed calibration/correlation completion and has not
promoted generated/latest configs or calibration results.
