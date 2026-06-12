# S7 Candidate 0002 Bounded Diagnostic Worker Log

## Purpose

Run one bounded local diagnostic for bounded-sweep `candidate_0002` with:

```text
-latency_L0_to_L1=37
-prefetch_per_stream_buffer_size=10
```

The purpose was to see whether the low L0-to-L1 latency with the larger
prefetch buffer progresses past dispatch/bind and into useful execution. This
was not a promotion run and did not generate or promote candidate metrics.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base checkpoint: `bc08ad8` (`docs: record SM120 final dispatch diagnostic`)
- Timestamp: `2026-06-12T20:43:02+08:00`
- Host: `dsp-ubuntu`
- Artifact root:
  `artifacts/s7/s7-candidate0002-bounded-diagnostic-20260612-204302/`
- Actual ProcMan job used: one, Job `9`

Pre-existing tracked modification observed and not edited by this worker:

- `docs/sm120-calibration/supervisor-log.md`

## Mandatory Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/s7-bounded-parameter-sweep-design.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-201232-s7-candidate0001-final-dispatch-diagnostic.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-194351-s7-dispatch-bind-instrumentation.md`

## Diagnostic Design

Candidate effective parameters:

```text
-latency_L0_to_L1 37
-prefetch_per_stream_buffer_size 10
```

Enabled diagnostics:

```text
GPGPUSIM_KERNEL_PROGRESS_DEBUG=1
GPGPUSIM_KERNEL_PROGRESS_INTERVAL=1000
GPGPUSIM_KERNEL_PROGRESS_SM_LIMIT=1
GPGPUSIM_KERNEL_DISPATCH_DEBUG=1
GPGPUSIM_KERNEL_DISPATCH_INTERVAL=200
```

Planned stop gates:

- normal dispatch/bind and early CTA launch comparable to `candidate_0001`,
- progress beyond early CTA launch toward all-resident or first completion,
- repeated unchanged dispatch/progress/output state,
- ProcMan stale/failure,
- strict wall timeout not exceeding 25 minutes.

## Actions

1. Verified current checkpoint, branch, and ProcMan state. Initial ProcMan was
   `Nothing Active`.
2. Created ignored artifact root under `artifacts/s7/`.
3. Added temporary alias
   `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`
   with only `S7SWEEP_L0L1_37_PREFETCH_10`.
4. Sourced local simulator and GPU app environments.
5. Ran setup-only planning successfully, exit code `0`.
6. Submitted exactly one local ProcMan job, Job `9`, with the required
   diagnostics enabled.
7. Monitored ProcMan polls, process snapshots, stdout/stderr snapshots, file
   growth, and run-directory state.
8. Stopped the run manually after about 7.5 minutes of RUNNING state with
   CPU-heavy simulator activity but zero stdout/stderr growth. This was a
   diagnostic gate for repeated unchanged no-output state, not a strict wall
   timeout.
9. Cleaned ProcMan, removed the temporary alias, and verified no protected
   paths or promotion outputs changed.

## Setup And Effective Config Evidence

Important setup artifacts:

- `logs/start-state.txt`
- `logs/setup-only.log`
- `logs/setup-only.exitcode`
- `logs/effective-config-values.txt`
- `logs/procman-after-setup-only.log`

The successful setup-only exit code was `0`.

Effective config evidence:

```text
64:-gpgpu_clock_domains 2640:2640:2640:14000
217:-latency_L0_to_L1 39
304:-is_instruction_prefetching_enabled 1
305:-prefetch_per_stream_buffer_size 8
349:-latency_L0_to_L1 37 -prefetch_per_stream_buffer_size 10
```

The base generated config still records the bootstrap `39/8` values. The
temporary extra-params override appended the active candidate value
`37/10`.

## ProcMan And Runtime Evidence

Important runtime artifacts:

- `logs/run-submit.log`: `Job 9 queued`
- `logs/run-submit.exitcode`: `0`
- `logs/procman-immediate.log`
- `logs/monitor.log`
- `logs/procman-before-manual-stop.log`
- `logs/process-before-manual-stop.log`
- `logs/procman-manual-kill.log`
- `logs/procman-after-manual-stop.log`
- `logs/final-state.txt`

Job `9` entered RUNNING immediately enough for the first monitor poll to
record one active job:

```text
elapsed=0 out=0 lines=0 result=none ... activeJobs=1 ... status=RUNNING
```

The run stayed RUNNING with no stdout growth through the last pre-stop monitor
polls:

```text
elapsed=416 out=0 lines=0 result=none ... status=RUNNING
elapsed=426 out=0 lines=0 result=none ... status=RUNNING
```

The final manual pre-stop ProcMan snapshot recorded:

```text
status=RUNNING ... runningTime=0:07:32 ... outF=/tmp/...o9 ... errF=/tmp/...e9
```

The simulator child was CPU-heavy:

```text
backprop-rodinia-2.0-ft ... elapsed 07:58 ... %CPU 1681 ... RSS 262400
```

No stdout/stderr snapshot files were preserved. The no-output claim is based
on every monitor poll recording `out=0 lines=0`, including the last RUNNING
polls before cleanup, plus the absence of any key-line files or simulator
result output:

```text
elapsed=416 out=0 lines=0 result=none ... status=RUNNING
elapsed=426 out=0 lines=0 result=none ... status=RUNNING
```

No `result.txt` was present under the run directory.

## Stop Reason

Semantic stop reason:

```text
manual-stop-no-stdout-growth-after-7min-running
```

The monitor wrapper also recorded:

```text
failed-to-enter-running
```

That monitor stop reason is not the semantic diagnosis. It was emitted after
the manual kill changed ProcMan from RUNNING to no active job while the wrapper
was still polling. The preserved poll and process snapshots show that Job `9`
did enter RUNNING and stayed RUNNING for about 7.5 minutes before manual
cleanup.

## Key Diagnostic Evidence

Unlike the accepted `candidate_0001` final dispatch diagnostic, this
`candidate_0002` run produced no dispatch-bind lines, no kernel-progress
lines, no shader bind line, no CTA launch evidence, no simulator metrics, and
no pass/fail result before the diagnostic stop.

The preserved state is therefore a pre-diagnostic-output no-growth state:

```text
RUNNING ProcMan job
CPU-heavy simulator child
monitor-reported stdout=0 bytes / 0 lines through the RUNNING window
result.txt absent
```

## Analysis Answers

### 1. Does candidate_0002 follow the normal launch/TB/bind/CTA-init path?

Not observed. The job entered RUNNING, but it did not produce any
`GPGPUSIM-DISPATCH-BIND`, `GPGPUSIM-K*-PROGRESS`, shader bind, or CTA-init
lines before the diagnostic gate.

### 2. Does it get past early CTA launch? What semantic state does it reach?

No evidence shows it reached early CTA launch. The deepest observed semantic
state is an active, CPU-heavy local simulator process with no simulator stdout
or stderr output after about 7.5 minutes. Because stdout was empty, this run
does not localize the state to stream launch latency, TB latency pending,
cluster admission, SM bind, CTA initialization, or all-resident execution.

### 3. Does prefetch buffer size 10 avoid candidate_0001 ambiguity?

No. The larger prefetch buffer does not provide evidence of avoiding the
low-latency pathology. It looks at least as problematic for this diagnostic
window: `candidate_0001` final dispatch evidence reached TB-latency countdown,
shader bind, and `cta_launched_kernel=180`, while this `candidate_0002` run
produced no dispatch/progress output at all before cleanup.

The confidence is limited because the run was intentionally stopped after the
repeated no-output diagnostic gate rather than allowed to the 25-minute hard
cap or completion.

### 4. Recommended next supervisor action

Do not run `candidate_0002` to completion for metrics yet, and do not generate
candidate metrics from this run.

Recommended next step: exclude or pause the low `-latency_L0_to_L1=37` sweep
points from metric promotion until the pre-output/early-dispatch slow path is
understood, or add earlier startup/first-output instrumentation around the
native app/simulator initialization boundary before another low-latency run.

If supervisor needs one more diagnostic, it should target why a CPU-heavy
RUNNING process can remain silent before the first dispatch/progress line,
rather than extending the candidate sweep or running `candidate_0002` to
completion.

## Recommendation

Verdict: `candidate_0002` did not demonstrate useful progress. It did not
reproduce the accepted `candidate_0001` normal dispatch/bind/CTA-init path
within the bounded diagnostic window.

Recommendation: do not promote or complete `candidate_0002` metrics now. Pause
the low-latency sweep points and investigate the pre-output/early-dispatch
silent CPU-heavy path, or adjust the sweep design to avoid `-latency_L0_to_L1=37`
until this behavior is explained.

Confidence: medium. The cleanup and no-progress evidence are strong for this
run, but the exact simulator semantic state is not localized because no
diagnostic lines were emitted.

## Changed Files

Untracked documentation created for supervisor review:

- `docs/sm120-calibration/worker-logs/worker-20260612-204302-s7-candidate0002-bounded-diagnostic.md`

Pre-existing tracked modification not made by this worker:

- `docs/sm120-calibration/supervisor-log.md`

Ignored artifacts:

- `artifacts/s7/s7-candidate0002-bounded-diagnostic-20260612-204302/`

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
`019ebbe6-8abf-7303-bd20-2381f844a786`.

Verdict: `CHANGES_NEEDED`.

Reviewer finding:

- The diagnostic evidence, one-job limit, cleanup, no-promotion state, and
  recommendation were otherwise supported, but this log cited
  `stdout-before-manual-stop.o9` and `stderr-before-manual-stop.e9` even though
  those snapshot files were absent from the artifact directory.

Corrective action:

- Removed the nonexistent snapshot files from the artifact list.
- Revised the no-output evidence to rely on `monitor.log`'s repeated
  `out=0 lines=0` RUNNING polls and absent `result.txt`/key-line output.

Round 2 blank-context reviewer:
`019ebbe6-8abf-7303-bd20-2381f844a786`.

Verdict: `ACCEPT`.

Reviewer confirmed:

- The corrected log no longer cites nonexistent stdout/stderr snapshots.
- The no-output claim is supported by `monitor.log` RUNNING polls with
  `out=0 lines=0`, including elapsed `416` and `426` seconds.
- Exactly one ProcMan job was submitted, Job `9`.
- Current ProcMan is `Nothing Active`.
- The temporary alias is absent.
- No result, key-line, metrics, promotion artifact, or protected-path change
  was found beyond this worker log and the pre-existing supervisor-log
  modification.
