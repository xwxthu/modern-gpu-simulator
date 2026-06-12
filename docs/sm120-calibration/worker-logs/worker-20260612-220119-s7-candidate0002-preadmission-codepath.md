# S7 Candidate 0002 Pre-Admission Code-Path Analysis

## Purpose

Analyze why bounded-sweep `candidate_0002` is CPU-heavy while still in the
pre-admission `select_kernel_none detail=tb_latency_pending` window, without
blindly running more sweep candidates.

This was a code-path analysis, not a metrics run and not a promotion run.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base checkpoint: `10d4cd1` (`docs: record SM120 candidate0002 deeper diagnostic`)
- Timestamp: `2026-06-12T22:01:19+08:00`
- Host: `dsp-ubuntu`
- ProcMan jobs launched by this worker: none

Pre-existing tracked modification observed and not edited:

- `docs/sm120-calibration/supervisor-log.md`

## Mandatory Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-214628-s7-candidate0002-deeper-dispatch-diagnostic.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-213551-s7-candidate0002-startup-diagnostic.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-201232-s7-candidate0001-final-dispatch-diagnostic.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-194351-s7-dispatch-bind-instrumentation.md`

## Code Paths Inspected

- Stream launch latency handoff:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/stream_manager.cc`
- GPU launch insertion, TB-latency decrement, kernel selection, CTA issue, and
  diagnostics:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-sim.cc`
  and `gpu-sim.h`
- Cluster CTA issue and no-ready reporting:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader.cc`
- Remodeled SM/subcore cycle paths:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/sm.cc`
  and `subcore.cc`
- Instruction prefetch stream-buffer path:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/first_level_instruction_cache.cc`
  and `stream_buffer.cc`

## Findings

### TB latency countdown location

`m_kernel_TB_latency` is decremented in `gpgpu_sim::decrement_kernel_latency()`.
That function is called late in the CORE-clock portion of `gpgpu_sim::cycle()`,
after:

1. clock-domain selection,
2. ICNT, DRAM, L2, and interconnect work for the applicable clock masks,
3. a parallel cluster loop,
4. occupancy/power-stat bookkeeping,
5. `gpu_sim_cycle++`,
6. `issue_block2core()`.

Then `decrement_kernel_latency()` runs, followed by
`maybe_print_kernel_progress_debug()`.

This means the diagnostic sequence at cycle `1` is expected: `issue_block2core`
and `select_kernel()` see a nonzero TB-latency counter, emit
`select_kernel_none detail=tb_latency_pending`, and only afterward does the
counter decrement for that core tick.

### What executes before CTA admission

While a kernel has CTAs left but `m_kernel_TB_latency > 0`,
`get_more_cta_left()` still returns true because it checks only whether any
running kernel has CTAs remaining. It does not consider TB latency.

As a result, each CORE-clock tick still enters the cluster path:

```text
gpgpu_sim::cycle()
  -> parallel for over n_simt_clusters
     -> if cluster has not_completed OR get_more_cta_left()
        -> simt_core_cluster::core_cycle()
           -> each SM::cycle()
  -> issue_block2core()
     -> cluster issue loop
        -> select_kernel()
           -> tb_latency_pending, returns NULL
  -> decrement_kernel_latency()
```

For the remodeled SM implementation, `SM::cycle()` immediately returns when an
SM is inactive and has no incomplete threads. That limits semantic work before
CTA admission, but the simulator still pays the per-cycle overhead of the
clock-domain loop, the OpenMP parallel cluster loop, per-cluster/core calls,
occupancy/stat loops, CTA-selection scans, and optional diagnostics.

Instruction prefetch state is not active before the first CTA fetch because
there are no active warps yet. However, candidate `0002` has instruction
prefetching enabled and `-prefetch_per_stream_buffer_size=10`; that parameter
is more likely relevant after CTA bind/fetch begins than in the observed
cycle `1` to `201` window.

### Candidate 0001 comparison

The accepted `candidate_0001` final diagnostic showed the same pre-admission
TB-latency countdown:

```text
cycle=1    tb_latency=1800
cycle=201  tb_latency=1600
...
cycle=1601 tb_latency=200
cycle=1801 select_kernel_current ready
cycle=1801 cluster_set_kernel / sm_set_kernel / shader bind / CTA init
cycle=1806 cta_launched_kernel=180 active_sms=30
```

That diagnostic was CPU-heavy too: its preserved process snapshot showed about
15:41 elapsed and `%CPU 1683` before the bind/CTA stop gate. Therefore
candidate `0002` advancing only from cycle `1` to `201` over the bounded
observation is not, by itself, evidence that `candidate_0002` has a different
pre-admission semantic state. It is the same very slow wall-time-per-sim-cycle
region, stopped much earlier.

The observed difference is that candidate `0001` was allowed to run long enough
to reach cycle `1801` and bind CTAs, while candidate `0002` was stopped around
cycle `201` after repeated normalized no-ready/pre-admission state. No evidence
yet proves candidate `0002` would fail to reach the same cycle-1801 transition.

### Diagnostics overhead

The dispatch and progress diagnostics are default-off, but when enabled they
are not free:

- `maybe_print_dispatch_bind_debug()` builds a string signature at every call
  site before interval filtering.
- Emitted dispatch lines compute active CTA, not-completed thread, and active
  SM totals by scanning all clusters.
- `maybe_print_kernel_progress_debug()` similarly builds a running-kernel
  signature and, when emitted, scans clusters and appends sampled SM summaries.

This overhead is diagnostic-induced and can amplify the already expensive
pre-admission loop. It does not fully explain the behavior because the
candidate `0001` final diagnostic and candidate `0002` deeper diagnostic both
show CPU-heavy execution in the same TB-latency window, and the core simulator
still advances many clocked components per simulated core cycle even before
CTA admission.

### Classification

Current classification: expected expensive pre-admission simulator loop,
amplified by default-off diagnostics when enabled.

Root-cause confidence: medium-high for the immediate cycle `1` to `201`
behavior. Confidence is lower for the broader candidate timeout behavior,
because no diagnostic has yet observed candidate `0002` at cycle `1801` or
post-bind.

Not supported by current evidence:

- A cluster admission, scheduler, or SM bind pathology in the observed window.
- A specific `-prefetch_per_stream_buffer_size=10` pathology before CTA bind.
- A specific `-latency_L0_to_L1=37` pathology before CTA bind.

Still unknown:

- Whether candidate `0002` transitions normally at cycle `1801` if allowed to
  continue.
- Whether `prefetch_per_stream_buffer_size=10` or `latency_L0_to_L1=37`
  causes a post-bind instruction-fetch/prefetch pathology.
- How much of the wall-time cost is OpenMP parallel-region overhead versus
  diagnostics versus other per-cycle clock-domain bookkeeping.

## Change Decision

No simulator code change was made.

A tempting shortcut would be to skip the parallel cluster core-cycle path while
all SMs are inactive and all runnable kernels are still TB-latency pending.
That may be correct for this observed state because remodeled `SM::cycle()`
returns immediately with no active work, but it is not low-risk enough from
static analysis alone: the surrounding cycle function also advances stats,
clocked queues, occupancy accounting, and admission timing. A semantics change
should be tested behind a default-off experiment or validated with a focused
micro-diagnostic, not patched into S7 calibration flow here.

No default-off instrumentation change was made either. The useful next
instrumentation is a lightweight per-cycle cost profiler around the named
blocks in `gpgpu_sim::cycle()`, but adding it safely needs build validation and
one short run. This worker avoided consuming the allowed diagnostic run because
the supervisor asked first for targeted code-path analysis.

## Validation

Commands run:

```bash
git status --short
rg -n "m_kernel_TB_latency|select_kernel|issue_block2core|DISPATCH-BIND|KERNEL_PROGRESS" \
  simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim \
  simulator-remodeled/gpu-simulator/gpgpu-sim/src/stream_manager.cc
rg -n "prefetch_per_stream_buffer_size|latency_L0_to_L1|prefetch" \
  simulator-remodeled/gpu-simulator/gpgpu-sim/src
sed -n '<targeted ranges>' <inspected source/log files>
```

No build was required because no code changed. No simulator job was launched.
ProcMan state was not changed by this worker.

## Changed Files

Untracked documentation created for supervisor review:

- `docs/sm120-calibration/worker-logs/worker-20260612-220119-s7-candidate0002-preadmission-codepath.md`

No code files changed.

Pre-existing tracked modification still present and not edited:

- `docs/sm120-calibration/supervisor-log.md`

## No-Promotion Confirmation

- No accepted config was modified.
- No generated config was modified.
- No latest config was modified.
- No calibration result was modified.
- No job alias was modified.
- No S6 search/report was run.
- No candidate metrics were generated.
- No promotion path was touched.

## Recommendation

Do not promote `candidate_0002`.

Run one of these next, in order of preference:

1. Add a default-off, low-volume cycle-cost diagnostic around
   `gpgpu_sim::cycle()` sections for the TB-latency window, then run one short
   candidate `0002` diagnostic to cycle `1801` or an earlier wall cap. The
   diagnostic should report elapsed host time and counts for clock-domain
   sections, cluster core-cycle calls, `issue_block2core`, TB-latency decrement,
   and diagnostic emission.
2. If code changes are not desired, rerun candidate `0002` once with startup
   and dispatch diagnostics only, a larger wall cap, and a stop gate at
   cycle `1801` / first bind / first CTA launch. This tests whether it follows
   the same normal transition as candidate `0001`, but it will not explain host
   CPU distribution.
3. Do not run more sweep candidates until this pre-admission cost and the
   post-bind behavior of candidate `0002` are understood.

Final verdict: analysis-only, no workaround. The immediate pre-admission state
looks like an expensive but expected simulator loop, with diagnostics adding
overhead. It is not yet evidence for a scheduler/dispatch loop pathology or a
prefetch/L0I model pathology.

## Reviewer Rounds

### Round 1

Blank-context reviewer `019ebc24-6a10-7370-ad50-4fd3aa1bf4d8`
returned `CHANGES_NEEDED`.

Finding:

- The changed-files section incorrectly called this worker log a tracked
  changed file while `git status --short` showed it as untracked.

Fix:

- Updated the changed-files wording to `Untracked documentation created for
  supervisor review`.

Technical reviewer verdict after that documentation fix:

- Analysis is supported by source and comparison logs.
- No-code-change decision is appropriate because skipping the pre-admission
  cycle path could alter stats, cluster cycling, and admission timing.
- Next-step recommendation is concrete and safe.
- Residual risk: candidate `0002` still has not been observed through
  cycle `1801` or post-bind, so broader timeout behavior remains unknown.
