# S7 Candidate 0002 Cycle-Cost Diagnostic Worker Log

## Purpose

Run exactly one bounded local ProcMan diagnostic for bounded-sweep
`candidate_0002` with the new cycle-cost diagnostics enabled, to determine
host-time distribution while attempting to progress toward cycle `1801`, first
bind, first CTA launch, or a strict stop gate.

This was not a metrics run, not an S6 correlation run, and not a calibration
promotion run.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Requested base checkpoint: `7f2c4e7` (`feat: add cycle-cost diagnostics`)
- Initial `git rev-parse HEAD`: `7f2c4e7271b439dfdcf0c73c5e5cd4ae8e4d927a`
- Timestamp: `2026-06-12T22:53:10+08:00`
- Host: `dsp-ubuntu`
- Artifact root:
  `artifacts/s7/s7-candidate0002-cycle-cost-diagnostic-20260612-225310/`
- Actual local ProcMan jobs submitted: exactly one, Job `12`

Initial tracked worktree state was clean except the pre-existing tracked
modification to:

- `docs/sm120-calibration/supervisor-log.md`

The launcher banner for Job `12` printed simulator build label
`gpgpu-sim_git-commit-3611fc2d254e78d0353a6ed7104f8a7449208f2d_modified_3.0`.
The repository HEAD was the requested `7f2c4e7`, and the executable emitted
`GPGPUSIM-CYCLE-COST` lines, confirming it contained the cycle-cost
diagnostics.

## Mandatory Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-222108-s7-cycle-cost-diagnostics.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-220119-s7-candidate0002-preadmission-codepath.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-214628-s7-candidate0002-deeper-dispatch-diagnostic.md`
- `docs/sm120-calibration/s7-bounded-parameter-sweep-design.md`

## Diagnostic Design

Candidate effective parameters:

```text
-latency_L0_to_L1=37
-prefetch_per_stream_buffer_size=10
```

Enabled diagnostics:

```text
GPGPUSIM_STARTUP_DEBUG=1
GPGPUSIM_KERNEL_DISPATCH_DEBUG=1
GPGPUSIM_KERNEL_DISPATCH_INTERVAL=200
GPGPUSIM_KERNEL_PROGRESS_DEBUG=1
GPGPUSIM_KERNEL_PROGRESS_INTERVAL=1000
GPGPUSIM_KERNEL_PROGRESS_SM_LIMIT=1
GPGPUSIM_CYCLE_COST_DEBUG=1
GPGPUSIM_CYCLE_COST_INTERVAL=200
GPGPUSIM_CYCLE_COST_LIMIT=16
```

Stop gates:

- cycle `1801` / `select_kernel_current`,
- CTA admission, shader/SM bind, or first CTA launch,
- repeated state with no useful cycle progress,
- no output growth despite CPU-heavy process,
- ProcMan stale/failure,
- wall time no more than 25 minutes.

Actual stop gate:

```text
no-output-growth-cpu-heavy
```

The job was stopped after about 5.5 minutes of monitor runtime, well under the
25-minute cap.

## Actions

1. Verified current checkpoint `7f2c4e7`, initial ProcMan state
   `Nothing Active`, and clean tracked worktree except the pre-existing
   supervisor-log modification.
2. Created ignored artifact root under `artifacts/s7/`.
3. Added temporary alias
   `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`
   containing only `S7SWEEP_L0L1_37_PREFETCH_10`.
4. Ran setup-only planning for
   `RTX5060_SM120_GEN-S7SWEEP_L0L1_37_PREFETCH_10`; setup-only exited `0`.
5. Submitted exactly one actual local ProcMan job, Job `12`, with startup,
   dispatch, progress, and cycle-cost diagnostics enabled.
6. Monitored ProcMan state, process state, stdout/stderr growth, key
   diagnostics, cycle-cost lines, result presence, and stop gates.
7. Stopped after repeated no-output-growth polls while the simulator child
   remained CPU-heavy, with the run still at pre-admission cycle `201`.
8. Preserved stdout/stderr snapshots and extracted key diagnostic lines.
9. Killed the active ProcMan job, verified final ProcMan state
   `Nothing Active`, and removed the temporary alias.
10. Did not run candidate metric ingestion, S6 search/report generation, config
    generation, calibration-result generation, or promotion commands.

## Setup And Effective Config Evidence

Important setup artifacts:

- `logs/start-state.txt`
- `logs/setup-only.log`
- `logs/setup-only.exitcode`
- `logs/procman-after-setup-only.log`
- `logs/rendered-config-paths.txt`
- `logs/effective-config-values.txt`
- `logs/effective-gpgpusim.config`

Setup-only exit code:

```text
0
```

ProcMan after setup-only:

```text
Nothing Active
```

Effective config evidence:

```text
64:-gpgpu_clock_domains 2640:2640:2640:14000
217:-latency_L0_to_L1 39
304:-is_instruction_prefetching_enabled 1
305:-prefetch_per_stream_buffer_size 8
306:-prefetch_num_stream_buffers 1
307:-num_instruction_prefetches_per_cycle 1
349:-latency_L0_to_L1 37
350:-prefetch_per_stream_buffer_size 10
```

The generated base config still contains bootstrap `39/8`; the temporary
extra-params override appended the active candidate values `37/10`.

## ProcMan And Runtime Evidence

Important runtime artifacts:

- `logs/run-submit.log`
- `logs/run-submit.exitcode`
- `logs/job-id.txt`
- `logs/procman-immediate.log`
- `logs/monitor.log`
- `logs/procman-poll-*.log`
- `logs/process-poll-*.log`
- `logs/key-lines-poll-*.txt`
- `logs/procman-at-stop-gate.log`
- `logs/process-tree-at-stop.log`
- `logs/stop-reason.txt`
- `logs/stdout-at-stop.o12`
- `logs/stderr-at-stop.e12`
- `logs/key-diagnostic-lines.txt`
- `logs/cycle-cost-lines.txt`
- `logs/result-files-at-stop.txt`
- `logs/procman-manual-kill.log`
- `logs/procman-after-manual-stop.log`
- `logs/procman-final-cleanup-kill.log`
- `logs/procman-final.log`
- `logs/temp-alias-final.log`

Run submission evidence:

```text
Job 12 queued (backprop-rodinia-2.0-ft-4096___data_result_4096_txt RTX5060_SM120_GEN-S7SWEEP_L0L1_37_PREFETCH_10)
```

Initial monitor evidence showed immediate diagnostics:

```text
poll=00 elapsed=0 status=RUNNING out=194757 out_lines=1564 err=3212 err_lines=48 startup=46 dispatch=37 progress=2 cycle_cost=3 max_cycle=2 bind= cta= result=none cpu=1337
```

The run later reached cycle `201` but remained pre-admission:

```text
poll=08 elapsed=164 status=RUNNING out=203281 out_lines=1597 err=3212 err_lines=48 startup=46 dispatch=69 progress=2 cycle_cost=4 max_cycle=201 bind= cta= result=none cpu=941
```

The stop gate fired after repeated no-output-growth polls while CPU use stayed
high:

```text
poll=16 elapsed=328 status=RUNNING out=203281 out_lines=1597 err=3212 err_lines=48 startup=46 dispatch=69 progress=2 cycle_cost=4 max_cycle=201 bind= cta= result=none cpu=905
```

No `result.txt` was present at stop. Final cleanup state:

```text
logs/procman-final.log: Nothing Active
logs/temp-alias-final.log: no such file or directory
```

## Key Startup, Dispatch, And Progress Evidence

Startup diagnostics confirm the run passed runtime/device init, config and
trace parsing, GPU and stream-manager creation, simulator-thread startup,
function registration, CUDA launch setup, grid initialization, stream push, and
simulator-thread work detection.

Key dispatch/progress lines:

```text
GPGPUSIM-DISPATCH-BIND cycle=0 ... stage=stream_kernel_launch_wait ... detail=launch_latency ... launch_latency=1799,tb_latency=1800
GPGPUSIM-DISPATCH-BIND cycle=0 ... stage=stream_kernel_launch_to_gpu ... launch_latency=0,tb_latency=1800
GPGPUSIM-DISPATCH-BIND cycle=0 ... stage=gpu_launch_insert ... detail=inserted_running_slot ... tb_latency=1800
GPGPUSIM-DISPATCH-BIND cycle=1 ... stage=select_kernel_none ... detail=tb_latency_pending ... next_cta=0,num_cta=256
GPGPUSIM-K2-PROGRESS cycle=1 ... cta_launched_kernel=0 ... next_cta=0,num_cta=256 ... active_sms=0 ...
GPGPUSIM-DISPATCH-BIND cycle=201 ... stage=select_kernel_none ... detail=tb_latency_pending ... tb_latency=1600
```

No `select_kernel_current`, `Shader N bind`, `cluster_set_kernel`,
`sm_set_kernel`, `cluster_issue_cta_to_sm`, `sm_issue_block_done`, or positive
`cta_launched_kernel` line was observed before stop.

## Cycle-Cost Summary

Captured sampled cycle-cost lines:

```text
GPGPUSIM-CYCLE-COST cycle=0 ... cost_us={clock_domain=2,interconnect_memory=183896,cluster_core=260968,stats_bookkeeping=8,issue_block2core=275,decrement_kernel_latency=1,diagnostic_emission=32,total=445186}
GPGPUSIM-CYCLE-COST cycle=1 ... cost_us={clock_domain=0,interconnect_memory=24,cluster_core=209980,stats_bookkeeping=2,issue_block2core=67,decrement_kernel_latency=0,diagnostic_emission=2,total=210077}
GPGPUSIM-CYCLE-COST cycle=200 ... cost_us={clock_domain=0,interconnect_memory=33,cluster_core=153949,stats_bookkeeping=9,issue_block2core=316,decrement_kernel_latency=0,diagnostic_emission=2,total=154313}
```

Interpretation:

- Dominant bucket after startup/initial memory work: `cluster_core`.
  - Cycle `1`: `cluster_core=209980 us`, about `99.95%` of sampled total.
  - Cycle `200`: `cluster_core=153949 us`, about `99.76%` of sampled total.
- Aggregate over the three sampled cost lines:
  - `cluster_core=624897 us`, about `77.19%`.
  - `interconnect_memory=183953 us`, about `22.72%`, dominated by the first
    sampled cycle.
  - `issue_block2core=658 us`, about `0.08%`.
  - `diagnostic_emission=36 us`, about `0.004%`.
  - `stats_bookkeeping=19 us`, about `0.002%`.
  - `decrement_kernel_latency=1 us`, about `0.0001%`.
- Diagnostic emission is visible but not material in the sampled cycle-cost
  bucket totals.
- `cluster_core`, `stats_bookkeeping`, `issue_block2core`, and
  `decrement_kernel_latency` are all visible in the diagnostic output.
- The evidence points to the pre-admission wall cost being dominated by the
  cluster/core loop, not by diagnostic printing, `issue_block2core`, stats
  bookkeeping, or TB-latency decrement itself.

## Analysis

This diagnostic did not reach cycle `1801`, `select_kernel_current`, shader/SM
bind, CTA admission, or CTA launch. It did reach the same early
pre-admission TB-latency window as the prior `candidate_0002` diagnostics and
advanced from cycle `1` to cycle `201`.

The useful new information is host-time distribution: the sampled
pre-admission cycles are overwhelmingly dominated by `cluster_core`, while
`diagnostic_emission`, `issue_block2core`, stats bookkeeping, and
`decrement_kernel_latency` are small. The initial cycle also paid substantial
`interconnect_memory` time, but this was not present in the later sampled
pre-admission cycles.

This supports the prior code-path analysis that the costly region is the
cluster/core path being executed during TB-latency countdown while no CTAs are
ready. It does not provide evidence of a post-bind prefetch/L0I pathology,
because the run did not reach bind or CTA launch.

## Changed Files

Tracked documentation added by this worker:

- `docs/sm120-calibration/worker-logs/worker-20260612-225310-s7-candidate0002-cycle-cost-diagnostic.md`

Temporary file created and removed:

- `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`

Ignored artifacts created:

- `artifacts/s7/s7-candidate0002-cycle-cost-diagnostic-20260612-225310/`

Pre-existing tracked modification still present and not edited:

- `docs/sm120-calibration/supervisor-log.md`

## Reviewer Rounds

- Round 1: Kepler (`019ebc5b-d8f9-7793-978b-cb627aa3ab91`) returned
  `ACCEPT`.
  - Key checks: exactly one actual ProcMan job, Job `12`; requested
    diagnostics and intervals present in captured stdout/stderr; effective
    candidate overrides are `37/10`; stop reason and cleanup are supported by
    monitor and ProcMan evidence; cycle-cost arithmetic matches
    `logs/cycle-cost-lines.txt`; no bind/CTA/result evidence; no metrics,
    S6, or promotion artifacts under the artifact root; temporary alias is
    removed; final ProcMan state is `Nothing Active`; changed-files list is
    accurate.

Final reviewer status: accepted.

## No-Promotion Confirmation

- No accepted config was modified.
- No generated config was modified.
- No latest config was modified.
- No calibration result was modified.
- No persistent job alias was modified.
- No S6 search/report was run.
- No candidate metrics were generated.
- No hardware target metrics were generated.
- Temporary alias was removed before final state.
- Final ProcMan state is `Nothing Active`.

## Recommendation

Do not promote `candidate_0002`.

Recommended next supervisor action: investigate or instrument the
pre-admission `cluster_core` cost directly, preferably around the OpenMP
cluster loop and inactive-SM fast-return path, before any further bounded-sweep
execution or metric promotion. A semantics-changing optimization should be
reviewed separately from this diagnostic evidence.
