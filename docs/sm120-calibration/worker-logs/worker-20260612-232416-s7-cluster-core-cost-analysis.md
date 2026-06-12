# S7 Cluster-Core Cost Analysis Worker Log

## Purpose

Analyze the pre-admission `cluster_core` host-time cost identified by the
candidate `0002` cycle-cost diagnostic, especially the OpenMP cluster loop and
inactive-SM fast-return path during TB-latency countdown.

This was not a bounded-sweep metrics run, not a calibration promotion run, and
not a full simulator diagnostic run.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Requested base checkpoint: `142335b`
  (`docs: record SM120 candidate0002 cycle-cost diagnostic`)
- Actual `git rev-parse --short HEAD`: `142335b`
- Timestamp: `2026-06-12T23:24:16+08:00`
- ProcMan jobs launched by this worker: none

Pre-existing tracked modification observed and not edited:

- `docs/sm120-calibration/supervisor-log.md`

## Mandatory Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-225310-s7-candidate0002-cycle-cost-diagnostic.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-220119-s7-candidate0002-preadmission-codepath.md`

## Code Paths Inspected

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-sim.cc`
  - `gpgpu_sim::cycle()`
  - `gpgpu_sim::get_more_cta_left()`
  - `gpgpu_sim::decrement_kernel_latency()`
  - `gpgpu_sim::select_kernel()`
  - `gpgpu_sim::issue_block2core()`
  - cycle-cost diagnostic emission
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-sim.h`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader.cc`
  - `simt_core_cluster::core_cycle()`
  - `simt_core_cluster::issue_block2core()`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/sm.cc`
  - inactive `SM::cycle()` fast-return behavior
  - `SM::issue_block2core()`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc`
- OpenMP scheduler/config controls in `gpu-sim.cc` and config references for
  `-is_custom_omp_scheduler_enabled` and
  `-custom_omp_scheduler_ratio_to_dynamic`.

## Evidence

The accepted cycle-cost diagnostic for `candidate_0002` showed these sampled
lines during pre-admission TB-latency countdown:

```text
cycle=1   cluster_core=209980 us total=210077 us
cycle=200 cluster_core=153949 us total=154313 us
```

The aggregate in that worker log was:

- `cluster_core`: about `77.19%` across the three sampled lines and about
  `99.95%` / `99.76%` at cycles `1` and `200`.
- `interconnect_memory`: about `22.72%`, dominated by the initial sampled
  cycle.
- `issue_block2core`: about `0.08%`.
- `diagnostic_emission`: about `0.0044%`.
- `stats_bookkeeping`: about `0.002%`.
- `decrement_kernel_latency`: about `0.0001%`.

The state was still pre-admission:

```text
select_kernel_none detail=tb_latency_pending
cta_launched_kernel=0
active_sms=0
next_cta=0,num_cta=256
```

No `select_kernel_current`, bind, or CTA launch was observed.

## Analysis

`gpgpu_sim::cycle()` still enters the CORE-clock cluster loop during the
pre-admission TB-latency countdown because `get_more_cta_left()` returns true
while the running kernel has CTAs remaining. `get_more_cta_left()` does not
consider `m_kernel_TB_latency`.

The relevant loop is:

```text
#pragma omp parallel for schedule(runtime)
for each cluster:
  if cluster.get_not_completed() || get_more_cta_left():
    cluster.core_cycle()
```

For the observed state:

- `get_more_cta_left()` is true globally.
- Every cluster is eligible to call `simt_core_cluster::core_cycle()`.
- `simt_core_cluster::core_cycle()` iterates the cores in the cluster and calls
  each SM `cycle()`.
- The remodeled inactive `SM::cycle()` path returns immediately when there are
  no active CTAs / no incomplete threads, so the per-SM semantic work should be
  small.

This supports the narrower root-cause classification:

- Supported: the sampled host-time cost is in the OpenMP cluster/core loop.
- Supported: diagnostic emission, `issue_block2core`, stats/bookkeeping, and
  TB-latency decrement are not material in the sampled cycle-cost lines.
- Supported by static code: the cost may be OpenMP parallel-region/scheduling
  overhead plus repeated per-cluster/per-SM inactive fast-return calls.
- Not yet separated by evidence: exact split between OpenMP overhead,
  condition/global CTA scans, and inactive SM `core_cycle()` body time.
- Not supported in the observed window: cluster admission, scheduler dispatch,
  SM bind/init, instruction prefetch, or L0I pathology.

## Improvement Evaluation

Evaluated low-risk options:

- Default-off finer instrumentation inside `cluster_core`: low risk and useful.
  It preserves simulator semantics and can split the existing coarse bucket.
- Avoiding the parallel region when no SM is active and all runnable kernels are
  TB-latency pending: likely beneficial, but semantics-changing. It would skip
  a clocked path that currently calls cluster/core cycle methods and needs more
  proof before becoming a simulator behavior change.
- OpenMP scheduling controls: current custom scheduler only changes schedule
  when `m_active_sms_this_cycle > 0`. In the observed inactive pre-admission
  state that control does not adapt the schedule. Changing it may affect
  broader execution behavior and is not low-risk without measurement.
- Pre-admission fast path: potentially useful but semantics-changing for the
  same reason as avoiding the parallel region.

## Changed Files

Code:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-sim.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-sim.h`

Documentation:

- `docs/sm120-calibration/worker-logs/worker-20260612-232416-s7-cluster-core-cost-analysis.md`

The code change extends existing default-off `GPGPUSIM_CYCLE_COST_DEBUG`
output with:

```text
cluster_core_detail={calls=<n>,core_cycle_us=<us>,
non_core_cycle_residual_us=<us>,not_completed_clusters=<n>,
more_cta_clusters=<n>}
```

Notes:

- `calls` counts sampled cluster `core_cycle()` invocations.
- `core_cycle_us` is a reduction of timed per-cluster `core_cycle()` calls.
- `non_core_cycle_residual_us` is a rough residual
  `cluster_core_wall_us - reduced_core_cycle_us`; under OpenMP parallel
  execution it is not a precise scheduler-only measurement.
- The added timers and counters run only when a cycle-cost sample is due.
- The disabled path preserves the prior short-circuit around
  `get_more_cta_left()` for active clusters.

## Validation

Commands:

```bash
git diff --check
source simulator-remodeled/gpu-simulator/gpgpu-sim/setup_environment >/tmp/gpgpusim-setup.log
make -C simulator-remodeled/gpu-simulator/gpgpu-sim -j2
```

Results:

- `git diff --check`: passed.
- `make -C simulator-remodeled/gpu-simulator/gpgpu-sim -j2`: passed after the
  final source state.
- The build produced existing warning classes, including RapidJSON deprecated
  iterator warnings, overloaded-virtual warnings, and an existing
  `shader.cc:4439` maybe-uninitialized warning.

No ProcMan job, simulator diagnostic run, bounded sweep, candidate metric
ingestion, or S6 search/report command was run.

## Reviewer Rounds

### Round 1

Blank-context reviewer agent:

- Agent: `019ebc69-66a5-7272-9694-83cf6cc5aff5`
- Verdict: `ACCEPT`

Reviewer finding:

- Low severity: the original field name `openmp_and_condition_us` could be
  over-interpreted because the value subtracts reduced per-thread call time
  from OpenMP-region wall time.

Action taken:

- Renamed the field to `non_core_cycle_residual_us`.
- Rebuilt after the rename.

Reviewer accepted:

- The prior cycle-cost evidence supports `cluster_core` dominance.
- Static code supports the narrower interpretation of OpenMP loop overhead plus
  inactive fast-return work.
- The instrumentation is default-off, uses OpenMP reductions, and does not show
  a data race or disabled-path semantic change.
- A semantic fast path should not be implemented before a focused diagnostic.

## No-Promotion Confirmation

- No accepted config was modified.
- No generated config was modified.
- No latest config was modified.
- No calibration result was modified.
- No job alias was modified.
- No S6 search/report was run.
- No candidate metrics were generated.
- No promotion path was touched.

## Final Recommendation

Do not promote `candidate_0002`.

Current verdict: pre-admission sampled cost is dominated by the cluster/core
OpenMP loop, but the exact split between OpenMP/scheduling overhead and
inactive cluster/SM fast-return work remains unmeasured.

Recommended next supervisor action:

Run exactly one bounded local `candidate_0002` diagnostic, if desired, with
`GPGPUSIM_CYCLE_COST_DEBUG=1` using the enhanced `cluster_core_detail` fields,
plus only the minimum startup/dispatch diagnostics needed to confirm state. Stop
at cycle `1801`, first bind/CTA launch, or a strict wall cap. Use the result to
decide whether a default-off experimental pre-admission fast path or OpenMP
scheduling experiment is justified.

Do not implement a semantics-changing pre-admission fast path yet.
