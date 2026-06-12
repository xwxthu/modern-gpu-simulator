# S7 Cluster-Core Residual Attribution Worker Log

## Purpose

Implement a narrow default-off diagnostic refinement for the existing
`GPGPUSIM_CYCLE_COST_DEBUG` cluster/core attribution. The goal is to split the
remaining pre-admission `cluster_core` residual into more actionable buckets:
OpenMP-region/reduction residual, eligibility checks, repeated
`get_more_cta_left()` scans, and inactive cluster/core traversal.

This worker did not implement a semantic pre-admission fast path and did not run
ProcMan simulator diagnostics.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base checkpoint: `e3de9d2`
  (`docs: record SM120 cluster-core detail diagnostic`)
- Start timestamp: `2026-06-13T00:32:50+08:00`
- Draft completion timestamp: `2026-06-13T00:56:55+08:00`
- Host: `dsp-ubuntu`

Initial tracked worktree state:

- `git rev-parse --short HEAD`: `e3de9d2`
- Initial `git status --short --branch`: branch `dev-5060`, ahead of origin,
  with no listed file modifications.

Tracked modification observed during the worker and not edited:

- `docs/sm120-calibration/supervisor-log.md`

## Assigned Scope

- Extend the sampled `cluster_core_detail` diagnostic only under
  `GPGPUSIM_CYCLE_COST_DEBUG` when a cycle-cost sample is due.
- Preserve simulator behavior and old short-circuit logic when diagnostics are
  disabled.
- Avoid adding high overhead to non-sampled cycles.
- Use conservative diagnostic names that do not over-claim exact OpenMP
  scheduler time.
- Do not touch configs, generated/accepted/latest paths, calibration results,
  metrics, or promotion flow.
- Validate with `git diff --check`, release rebuild, ProcMan clean state,
  temporary alias absence, and protected-path cleanliness.
- Spawn a blank-context internal reviewer after draft completion.

## Mandatory Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-235505-s7-candidate0002-cluster-core-detail-diagnostic.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-232416-s7-cluster-core-cost-analysis.md`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-sim.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-sim.h`
- Relevant `shader.cc` cluster/core methods:
  `shader_core_ctx::cycle()`, `simt_core_cluster::core_cycle()`, and
  `simt_core_cluster::get_not_completed()`.

## Actions

1. Confirmed base checkpoint `e3de9d2` on `dev-5060`.
2. Reviewed prior accepted evidence showing candidate `0002` sampled
   pre-admission cost dominated by `cluster_core`, with
   `non_core_cycle_residual_us=496174`, `core_cycle_us=256`, and repeated
   `more_cta_clusters=30`.
3. Inspected `gpgpu_sim::cycle()`, `get_more_cta_left()`,
   `select_kernel()`, cluster `core_cycle()`, and shader inactive fast-return
   behavior.
4. Added a small `gpgpusim_cluster_core_detail` aggregate in `gpu-sim.h` and
   passed it to `maybe_print_cycle_cost_debug()`.
5. Split the CORE-clock cluster loop into two paths:
   - sampled path with detailed timers/counters;
   - non-sampled path preserving the old short-circuit behavior and only the
     existing `m_active_sms_this_cycle` reduction.
6. Extended `cluster_core_detail={...}` output with conservative buckets:
   - `loop_accounted_us`
   - `eligibility_us`
   - `get_not_completed_calls`
   - `get_not_completed_us`
   - `get_more_cta_left_calls`
   - `get_more_cta_left_true`
   - `get_more_cta_left_us`
   - `not_completed_core_cycle_calls`
   - `inactive_core_cycle_calls`
   - `not_completed_core_cycle_us`
   - `inactive_core_cycle_us`
   - `active_sms_scan_calls`
   - `active_sms_scan_us`
   - `accelwattch_stats_us`
7. Recomputed `non_core_cycle_residual_us` as:
   `cluster_core_us - (core_cycle_us + get_not_completed_us +
   get_more_cta_left_us + active_sms_scan_us + accelwattch_stats_us)`, clamped
   at zero.
8. Kept `non_core_cycle_residual_us` conservative: it still includes OpenMP
   parallel-region/scheduling/reduction cost plus unmeasured loop bookkeeping,
   and it is not labeled as exact OpenMP scheduler time.
9. Did not run ProcMan simulator jobs, bounded sweeps, metric ingestion,
   S6 reports, or promotion commands.

## Diagnostic Semantics

Disabled behavior is unchanged for the cluster eligibility path:

```text
cluster_not_completed = cluster.get_not_completed() != 0
if !cluster_not_completed:
  more_cta_left = get_more_cta_left()
if cluster_not_completed || more_cta_left:
  cluster.core_cycle()
```

When a cycle-cost sample is due, the diagnostic path intentionally measures
both eligibility predicates for every cluster so it can attribute repeated
`get_more_cta_left()` scans and condition cost. `get_more_cta_left()` is a
read-only scan of running kernels; no admission or scheduling fast path was
added.

## Evidence

Key source changes:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-sim.h`
  - Added `gpgpusim_cluster_core_detail`.
  - Changed `maybe_print_cycle_cost_debug()` to take the detail aggregate.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-sim.cc`
  - Added a small subtract helper to clamp residuals at zero.
  - Printed the new sampled fields inside `cluster_core_detail={...}`.
  - Used a sampled-only OpenMP reduction for detailed timing/counters.
  - Preserved the old non-sampled short-circuit path.

Expected interpretation:

- `eligibility_us` is `get_not_completed_us + get_more_cta_left_us`.
- `inactive_core_cycle_us` approximates inactive traversal through
  `simt_core_cluster::core_cycle()` and inactive SM fast-return bodies.
- `not_completed_core_cycle_us` captures `core_cycle()` calls where the cluster
  already had incomplete work.
- `non_core_cycle_residual_us` remains a conservative host-wall residual around
  OpenMP region/scheduling/reductions and unmeasured loop bookkeeping.

## Validation

Commands run:

```bash
git diff --check
source simulator-remodeled/gpu-simulator/gpgpu-sim/setup_environment >/tmp/gpgpusim-setup.log
make -C simulator-remodeled/gpu-simulator/gpgpu-sim -j2
python3 simulator-remodeled/util/job_launching/procman.py -p
find /home/xiewx/accel-0608 -name 'define-s7-bounded-sweep-temp.yml' -print
git status --short -- simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated simulator-remodeled/gpu-simulator/configs/generated simulator-remodeled/gpu-simulator/gpgpu-sim/configs/tested-cfgs simulator-remodeled/gpu-simulator/configs/tested-cfgs simulator-remodeled/gpu-simulator/gpgpu-sim/configs/accepted simulator-remodeled/gpu-simulator/configs/accepted simulator-remodeled/gpu-simulator/gpgpu-sim/configs/latest simulator-remodeled/gpu-simulator/configs/latest simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/calibration-results
```

Results:

- `git diff --check`: passed after final source state.
- Release rebuild: passed after final source state.
- Build warnings were existing classes: RapidJSON deprecated iterator warnings,
  overloaded-virtual warnings, and existing `shader.cc:4439` maybe-uninitialized
  warning.
- ProcMan final state: `Nothing Active`.
- Temporary alias check: no `define-s7-bounded-sweep-temp.yml` found under
  `/home/xiewx/accel-0608`.
- Protected generated/tested/accepted/latest config and calibration-result path
  check: clean.

No ProcMan job was launched by this worker.

## Changed Files

Code:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-sim.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-sim.h`

Documentation:

- `docs/sm120-calibration/worker-logs/worker-20260613-003250-s7-cluster-core-residual-attribution.md`

Pre-existing and not owned by this worker:

- `docs/sm120-calibration/supervisor-log.md`

## Reviewer Rounds

### Round 1

Blank-context reviewer agent:

- Agent: `019ebcc5-fb3a-7c70-ad94-52b62f30e965`
- Verdict: `ACCEPT`

Reviewer summary:

- No blocking findings.
- The non-sampled path preserves the old `get_more_cta_left()` short-circuit.
- Detailed timers/counters are behind `cycle_cost_due`, which is CORE-clock
  gated.
- OpenMP counters use reductions; no new race was identified.
- No semantic pre-admission fast path was found.

Reviewer validation note:

- The reviewer ran `git diff --check` only.
- The reviewer did not run ProcMan jobs and did not independently rebuild the
  simulator.

## No-Promotion Confirmation

- No generated config was modified.
- No accepted config was modified.
- No latest config was modified.
- No calibration result was modified.
- No metrics artifact was generated.
- No S6 correlation/search/report command was run.
- No ProcMan simulator job was launched.
- No semantic fast path was implemented.

## Final Status

Accepted by internal reviewer. The implementation is default-off, limited to
cycle-cost sampled diagnostics, and intended to make the remaining
pre-admission `cluster_core` residual actionable without changing simulator
semantics.
