# S7 Remaining Bounded-Sweep Candidates Worker Log

## Purpose

Run the two remaining local S7 bounded-sweep candidates in sequence, ingest
their draft simulator candidate metrics, and if all four bounded-sweep
candidates are available, generate a reviewed draft S6 supplied-metrics
manifest plus a draft ranked S6 report under ignored `artifacts/s7/`.

This worker must not promote configs or calibration results.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base commit: `25463e5a7794857fb3b6f475674d0e76d39e041c`
- Timestamp: `2026-06-11T11:40:17+08:00`
- Host: `dsp-ubuntu`
- Worker role: `S7 bounded-sweep remaining-candidates execution worker`
- Execution artifact directory:
  `artifacts/s7/s7-bounded-sweep-20260610-024829/remaining-candidates-20260611-114017/`
- Actual run directories:
  - `artifacts/s7/s7-bounded-sweep-20260610-024829/sim-runs/candidate_0001`
- Planned but not created before this worker stopped:
  `artifacts/s7/s7-bounded-sweep-20260610-024829/sim-runs/candidate_0002`

## Required Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/s7-bounded-parameter-sweep-design.md`
- `docs/sm120-calibration/worker-logs/worker-20260611-113040-s7-single-candidate-recovery.md`
- `docs/sm120-calibration/worker-logs/worker-20260610-032557-s7-sweep-exec-prep.md`

## Hard Rules

- Simulator execution is local only on `dsp-ubuntu`; no simulator run on
  `dsp5060`.
- Run at most one ProcMan job at a time.
- Check `procman.py -p` before start, after each candidate, and at end; it
  must report `Nothing Active`.
- Use temporary alias file
  `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`.
- Remove the temporary alias file before final status.
- Do not modify accepted/generated/latest configs or `calibration-results/latest`.
- Keep logs under ignored `artifacts/s7/`.
- Do not rerun `candidate_0003`/job `486` or `candidate_0004`/job `487`.

## Actions

- `2026-06-11T11:40:17+08:00`: Confirmed branch `dev-5060`, commit
  `25463e5a7794857fb3b6f475674d0e76d39e041c`, host `dsp-ubuntu`, and
  ProcMan status `Nothing Active`.
- `2026-06-11T11:40:17+08:00`: Created this worker log.
- `2026-06-11T11:41:32+08:00`: Submitted `candidate_0001` to ProcMan
  after setup-only planning and effective-config checks.
- `2026-06-11T11:44:13+08:00`: Observed that ProcMan had a queued-only stale
  state: `queuedJobs=1`, `activeJobs=0`, `completeJobs=0`, with no matching
  simulator process or output files.
- `2026-06-11T11:44:13+08:00`: Attempted `procman.py -k`, but the legacy
  queued-only kill path crashed with `UnboundLocalError` before clearing the
  stale queue.
- `2026-06-12T16:08:43+08:00`: Supervisor fixed the ProcMan queued-only kill
  path, archived the stale state evidence, removed the live stale queue with
  `procman.py -k`, and deleted the temporary alias file.

## Evidence

Initial checks:

- `hostname`: `dsp-ubuntu`
- `python3 simulator-remodeled/util/job_launching/procman.py -p`:
  `Nothing Active`
- Relevant protected-path status before edits: clean.

Candidate `0001` setup and submit evidence:

- `logs/candidate_0001-setup-only.exitcode`: `0`
- `logs/candidate_0001-effective-config-values.log`:
  `-latency_L0_to_L1=37`, `-prefetch_per_stream_buffer_size=8`
- `logs/procman-before-candidate_0001.log`: `Nothing Active`
- `logs/candidate_0001-actual-run-submit.exitcode`: `0`
- `logs/candidate_0001-actual-run-submit.log`: `Job 1 queued`

Stale queue evidence:

- `logs/candidate_0001-procman-poll-1.log` showed:
  `queuedJobs=1, activeJobs=0, completeJobs=0`.
- `ps` inspection by supervisor found no live ProcMan manager, `slurm.sim`,
  `backprop`, or GPGPU-Sim process for the queued job.
- `/tmp` and the candidate run directory had no `.o1`, `.e1`, `result.txt`, or
  parseable simulator metric output for candidate `0001`.
- `logs/procman-kill-after-stale-candidate_0001.log` records the legacy
  `procman.py -k` crash:
  `UnboundLocalError: cannot access local variable 'activeJob'`.
- Supervisor archived live ProcMan state before cleanup under:
  `artifacts/s7/s7-bounded-sweep-20260610-024829/procman-queued-cleanup-20260611/live-state-before-cleanup/`.
- After the ProcMan fix, `live-procman-after-cleanup.log` reports
  `Nothing Active`.

## Candidate Results

- `candidate_0001`: not completed. It was submitted to ProcMan but never
  started; no simulator stdout/stderr, `PASSED`, or metrics were produced.
- `candidate_0002`: not started. Supervisor explicitly stopped this worker from
  launching it until the `candidate_0001` ProcMan stale queue was understood
  and cleaned.

## S6 Manifest And Report

No complete S6 manifest or ranked report was generated. Candidates `0001` and
`0002` still lack simulator candidate metrics.

## Validations

| Check | Result |
| --- | --- |
| Initial ProcMan clean | Pass |
| Candidate `0001` setup-only | Pass |
| Candidate `0001` effective config values | Pass |
| Candidate `0001` actual simulation completed | Fail; queued-only stale state before execution |
| Candidate `0001` metrics produced | No |
| Candidate `0002` started | No |
| Temporary alias removed | Pass, by supervisor cleanup |
| Final ProcMan clean | Pass after ProcMan queued-only cleanup fix |

## Reviewer Rounds

No reviewer round was completed for the original execution attempt because the
worker stopped at a ProcMan infrastructure blocker. Supervisor took ownership
of the ProcMan queued-only cleanup fix and will request independent review for
that recovery checkpoint.

## Changed Files

Tracked documentation:

- `docs/sm120-calibration/worker-logs/worker-20260611-114017-s7-remaining-candidates.md`

Tracked code, completed by supervisor recovery:

- `simulator-remodeled/util/job_launching/procman.py`

Temporary, to be removed before final status:

- None. `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`
  was removed by supervisor cleanup.

Ignored artifacts:

- `artifacts/s7/s7-bounded-sweep-20260610-024829/remaining-candidates-20260611-114017/`
- Candidate run outputs under
  `artifacts/s7/s7-bounded-sweep-20260610-024829/sim-runs/candidate_0001/`
  and
  `artifacts/s7/s7-bounded-sweep-20260610-024829/sim-runs/candidate_0002/`
- Candidate metrics and S6 draft outputs under
  `artifacts/s7/s7-bounded-sweep-20260610-024829/`

## Final Status

Partial and blocked by infrastructure. No candidate metrics were produced in
this attempt. The live stale ProcMan queue has been cleaned, and the remaining
bounded-sweep execution should be retried by a fresh worker after the ProcMan
queued-only cleanup fix is reviewed and committed.
