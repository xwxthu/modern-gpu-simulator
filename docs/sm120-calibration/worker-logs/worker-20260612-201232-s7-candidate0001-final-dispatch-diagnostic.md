# S7 Candidate 0001 Final Dispatch Diagnostic Worker Log

## Purpose

Run one bounded local reproduction/diagnostic for bounded-sweep
`candidate_0001` with final dispatch-bind instrumentation from checkpoint
`d390d8e feat: add dispatch-bind diagnostics`.

The diagnostic goal was to locate whether the long interval is in stream launch
latency, TB latency pending, cluster admission, SM bind, SM CTA
initialization, or post-bind progress. This was not a calibration metrics run
and did not promote any result.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base checkpoint: `d390d8e040b2186e39d15e962a88a7f05bb8760b`
  (`feat: add dispatch-bind diagnostics`)
- Timestamp: `2026-06-12T20:12:32+08:00`
- Host: `dsp-ubuntu`
- Artifact root:
  `artifacts/s7/s7-candidate0001-final-dispatch-diagnostic-20260612-201232/`
- Actual ProcMan job used: one, Job `8`

Pre-existing tracked modification observed and not edited by this worker:

- `docs/sm120-calibration/supervisor-log.md`

## Mandatory Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-194351-s7-dispatch-bind-instrumentation.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-191627-s7-candidate0001-deeper-progress-diagnostic.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-185413-s7-candidate0001-progress-diagnostic.md`

## Diagnostic Design

Candidate effective parameters:

```text
-latency_L0_to_L1 37
-prefetch_per_stream_buffer_size 8
```

Enabled diagnostics:

```text
GPGPUSIM_KERNEL_PROGRESS_DEBUG=1
GPGPUSIM_KERNEL_PROGRESS_INTERVAL=1000
GPGPUSIM_KERNEL_PROGRESS_SM_LIMIT=1
GPGPUSIM_KERNEL_DISPATCH_DEBUG=1
GPGPUSIM_KERNEL_DISPATCH_INTERVAL=200
```

The dispatch interval `200` was used because the preceding final-code
instrumentation validation used this cadence, and it gives direct visibility
across the 1800-cycle launch/TB gates without excessive output volume.

Planned stop gates:

- normal transition through launch/TB latency into ready/select/bind/CTA init,
- repeated unchanged state around one dispatch-bind stage over a meaningful
  window,
- post-bind CTA launch samples comparable to earlier diagnostics,
- ProcMan stale/failure,
- strict wall timeout below 20 minutes.

## Actions

1. Verified checkpoint, branch, and initial ProcMan state. Initial ProcMan was
   `Nothing Active`; no temp alias existed.
2. Created ignored artifact root under `artifacts/s7/`.
3. Added temporary extra-params alias
   `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`.
4. Recorded two setup-only failures before any actual ProcMan job:
   - `logs/setup-only.log`: failed because the simulator environment was not
     sourced.
   - `logs/setup-only-rerun.log`: failed because `GPUAPPS_ROOT` was unset and
     expanded as a literal path component.
5. Sourced `setup_environment_no_git.sh release`, explicitly set
   `GPUAPPS_ROOT` to the local app tree, and reran setup-only successfully.
6. Submitted exactly one local ProcMan job, Job `8`, with the diagnostics
   enabled. It entered `RUNNING`.
7. Monitored ProcMan state, stdout/stderr snapshots, file growth, process
   snapshots, progress lines, and dispatch-bind lines.
8. The monitor observed bind/CTA evidence and killed the job. A near-simultaneous
   manual cleanup command had also been issued when the wall cap was close; both
   paths captured the same final stdout size and key evidence. Final ProcMan
   state was then verified as `Nothing Active`.
9. Removed the temporary alias and verified protected paths/no-promotion state.

## Setup And Effective Config Evidence

Important setup artifacts:

- `logs/start-state.txt`
- `logs/setup-only.log`
- `logs/setup-only.exitcode`
- `logs/setup-only-rerun.log`
- `logs/setup-only-rerun.exitcode`
- `logs/setup-only-rerun2.log`
- `logs/setup-only-rerun2.exitcode`
- `logs/effective-config-values-rerun2.txt`

The successful setup-only exit code was `0`.

Effective config evidence:

```text
64:-gpgpu_clock_domains 2640:2640:2640:14000
217:-latency_L0_to_L1 39
304:-is_instruction_prefetching_enabled 1
305:-prefetch_per_stream_buffer_size 8
349:-latency_L0_to_L1 37 -prefetch_per_stream_buffer_size 8
```

The base generated config still contains `-latency_L0_to_L1 39`, but the
appended extra-params override records the active candidate value `37` plus
`prefetch_per_stream_buffer_size 8`.

## ProcMan And Runtime Evidence

Important runtime artifacts:

- `logs/run-submit.log`: `Job 8 queued`
- `logs/procman-immediate.log`: queued initially
- `logs/enter-running-result.txt`: `running-at-001`
- `logs/procman-enter-running-001.log`: active `RUNNING`
- `logs/monitor.log`: sampled monitor summary
- `logs/key-lines-before-stop.log`: final monitor key lines
- `logs/stdout-before-stop.o8`
- `logs/stderr-before-stop.e8`
- `logs/process-before-stop.log`
- `logs/procman-before-stop.log`
- `logs/procman-after-stop.log`
- `logs/procman-final.log`: `Nothing Active`

Job `8` was CPU-heavy while alive. `logs/process-before-manual-kill.log`
records:

```text
backprop-rodinia-2.0-ft ... elapsed 15:41 ... %CPU 1683 ... RSS 262584
```

Final preserved stdout/stderr snapshots:

```text
logs/stdout-before-stop.o8      2703 lines, 554941 bytes
logs/stderr-before-stop.e8         2 lines,     67 bytes
```

The monitor stop reason was:

```text
bind-or-cta-evidence-observed
```

`logs/diagnostic-stop-reason-manual.txt` also records
`wall-timeout-manual-cleanup-monitor-overrun` because I issued a manual cleanup
when the monitor was close to the wall cap and had not returned promptly. The
monitor then returned with the bind/CTA gate. Both final snapshots have the same
stdout/stderr size.

## Key Dispatch Evidence

Primary summary artifact:

```text
logs/key-dispatch-summary-lines.txt
```

The run showed normal stream launch to GPU insertion:

```text
stage=stream_kernel_launch_wait detail=launch_latency ... launch_latency=1799 tb_latency=1800
stage=stream_kernel_launch_to_gpu ... launch_latency=0 tb_latency=1800
stage=gpu_launch_enter ... tb_latency=1800
stage=gpu_launch_insert detail=inserted_running_slot ... tb_latency=1800
```

It then spent the long wall interval in GPU-side TB latency pending. The
specific `select_kernel_none` lines counted down:

```text
cycle=1    detail=tb_latency_pending ... tb_latency=1800
cycle=201  detail=tb_latency_pending ... tb_latency=1600
cycle=401  detail=tb_latency_pending ... tb_latency=1400
cycle=601  detail=tb_latency_pending ... tb_latency=1200
cycle=801  detail=tb_latency_pending ... tb_latency=1000
cycle=1001 detail=tb_latency_pending ... tb_latency=800
cycle=1201 detail=tb_latency_pending ... tb_latency=600
cycle=1401 detail=tb_latency_pending ... tb_latency=400
cycle=1601 detail=tb_latency_pending ... tb_latency=200
```

After TB latency reached zero, the run transitioned normally:

```text
cycle=1801 stage=select_kernel_current detail=ready ... tb_latency=0
cycle=1801 stage=cluster_set_kernel cluster=0 sm=0 ...
cycle=1801 stage=sm_set_kernel sm=0 ...
GPGPU-Sim uArch: Shader 0 bind to kernel 1
cycle=1801 stage=cluster_issue_cta_to_sm cluster=0 sm=0 ...
cycle=1801 stage=sm_issue_block_enter sm=0 ...
cycle=1801 stage=sm_issue_block_done sm=0 detail=cta_initialized ... next_cta=1
```

The same bind/CTA initialization sequence repeated across SMs. By cycle `1806`:

```text
cta_launched_kernel=180
active_cta=180
active_sms=30
sampled PC=0x2400
barrier waiting=0
memory queues=0
```

At cycle `1807`, dispatch-bind reported:

```text
stage=cluster_cta_admission_blocked detail=can_issue_1block_false
cta_launched_kernel=180 active_cta=180 active_sms=30
```

This is post-bind capacity pressure after six CTAs per SM, not the long
pre-bind interval.

## Analysis Answers

### 1. Which stage dominates or repeats?

The long observed wall interval is dominated by GPU-side TB latency pending,
reported as:

```text
stage=select_kernel_none detail=tb_latency_pending
```

The interval is not stream launch latency after the first handoff, not
cluster admission, not SM bind, and not SM CTA initialization. Cluster
`no_cta_ready` lines appear as a consequence of no ready kernel during
TB-latency pending, but the specific cause is the kernel TB latency countdown.

### 2. Normal transition or repeated stuck state?

Final instrumentation shows a normal transition:

```text
stream launch latency -> GPU launch insertion -> TB latency pending countdown
-> select_kernel_current ready -> cluster_set_kernel/sm_set_kernel
-> shader bind -> cluster_issue_cta_to_sm -> sm_issue_block_done
```

There is no repeated stuck state in cluster admission, SM bind, or CTA
initialization in this run. CTA launch samples at cycles `1801` through `1806`
are comparable to the accepted early progress diagnostic.

### 3. Evidence for next action?

Evidence supports proceeding to `candidate_0002` with the same diagnostics and
a more targeted stop policy, rather than excluding/fixing the low-latency point
based on pre-bind evidence.

The caveat is that this diagnostic still did not run to the later 43-minute
timeout region. It proves the dispatch-bind path is normal through early CTA
launch and that the previously ambiguous long pre-bind interval is TB latency
pending plus very slow wall-time advancement, not a cluster/SM bind/init
failure. If `candidate_0002` is run, keep dispatch/progress diagnostics enabled
or use a monitor gate that continues beyond all-resident/first-completion.

## Recommendation

Proceed with `candidate_0002` only as a bounded diagnostic or carefully
monitored run; do not exclude the low `-latency_L0_to_L1=37` point based on
dispatch-bind. The next run should not treat early pre-bind silence as a bind
failure: the final instrumentation shows the simulator can spend many wall
minutes in TB latency pending while simulator cycles advance slowly, then bind
normally.

Do not promote metrics from this run. It was killed at the diagnostic gate and
has no complete simulator metrics.

Confidence: medium-high for the dispatch-bind location and early-transition
diagnosis; medium for the broader timeout recommendation because the later
43-minute region remains unobserved.

## Changed Files

Untracked documentation created for supervisor review:

- `docs/sm120-calibration/worker-logs/worker-20260612-201232-s7-candidate0001-final-dispatch-diagnostic.md`

Pre-existing tracked modification not made by this worker:

- `docs/sm120-calibration/supervisor-log.md`

Ignored artifacts:

- `artifacts/s7/s7-candidate0001-final-dispatch-diagnostic-20260612-201232/`

Temporary file removed before final status:

- `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`

## Final State And No-Promotion Confirmation

- Final ProcMan state: `Nothing Active`.
- Final temporary alias state: absent.
- Runtime/log artifacts are under ignored `artifacts/s7/`.
- No job was run on `dsp5060`.
- No candidate metrics were generated or promoted.
- No S6 manifest, ranked report, accepted/latest config, generated config, or
  latest calibration file was produced.
- Protected-path check found no tracked changes under accepted/generated/latest
  config or calibration-result paths.

## Reviewer Rounds

Round 1 blank-context reviewer:
`019ebbd4-65e9-77a1-b2a1-6360ec3f8ba9`.

Verdict: `CHANGES_NEEDED`.

Reviewer findings:

- The diagnostic analysis is supported by
  `logs/key-dispatch-summary-lines.txt`: launch handoff, TB latency countdown,
  normal ready/select/bind/CTA-init transition, and an honest caveat that the
  later 43-minute timeout region was not reached.
- Cleanup/no-promotion evidence is mostly sound: final ProcMan is
  `Nothing Active`, temp alias is absent, artifacts are under ignored
  `artifacts/s7/`, protected-path status is empty, and no metrics were
  promoted.
- Blocking issue: this log called the new worker log "tracked
  documentation", but it is untracked pending supervisor review. The saved
  `logs/git-status-final.txt` artifact was also captured before this log
  existed.

Corrective action:

- Refreshed `logs/git-status-final.txt` after creating this log. It now records
  the pre-existing modified `supervisor-log.md` and this untracked worker log.
- Updated the changed-files section to say "Untracked documentation created
  for supervisor review".

Round 2 blank-context reviewer:
`019ebbd4-65e9-77a1-b2a1-6360ec3f8ba9`.

Verdict: `ACCEPT`.

Reviewer confirmed:

- The worker log now correctly identifies the new log as untracked
  documentation created for supervisor review.
- Refreshed `logs/git-status-final.txt` matches current status: modified
  pre-existing `supervisor-log.md` plus the untracked worker log.
- Reviewer Rounds records the Round 1 finding and corrective action clearly.
- No new contradiction was found in the corrected sections.
