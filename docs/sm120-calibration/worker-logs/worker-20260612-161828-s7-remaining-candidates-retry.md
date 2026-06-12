# S7 Remaining Bounded-Sweep Candidates Retry Worker Log

## Purpose

Run remaining bounded-sweep candidates `candidate_0001` and `candidate_0002`
sequentially on local `dsp-ubuntu`, ingest draft simulator candidate metrics,
and if all four candidate metrics are present and consistent, create a reviewed
complete draft S6 supplied-metrics manifest and draft ranked report under
ignored `artifacts/s7/`.

No promotion is in scope.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base commit: `1a030e8d28e678d0a281ad0af3498f1c7da5fabe`
- Timestamp: `2026-06-12T16:18:28+08:00`
- Host: `dsp-ubuntu`
- Worker role: `S7 bounded-sweep remaining-candidates retry worker`
- Execution artifact directory:
  `artifacts/s7/s7-bounded-sweep-20260610-024829/remaining-candidates-retry-20260612-161828/`

## Required Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/s7-bounded-parameter-sweep-design.md`
- `docs/sm120-calibration/worker-logs/worker-20260611-114017-s7-remaining-candidates.md`
- `docs/sm120-calibration/worker-logs/worker-20260611-113040-s7-single-candidate-recovery.md`

## Hard Rules

- Simulator execution local only on `dsp-ubuntu`; no simulator run on
  `dsp5060`.
- Run at most one ProcMan job at a time.
- Use temporary alias file
  `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`.
- Remove the temporary alias file before final status.
- Do not modify accepted/generated/latest configs or `calibration-results/latest`.
- Keep logs under ignored `artifacts/s7/`.
- Do not rerun `candidate_0003`/job `486` or `candidate_0004`/job `487`.
- After each candidate submission, check ProcMan within 30 seconds and stop
  immediately on queued-only stale state.
- Stop on functional failure, no parseable metrics, ProcMan stale state, or
  no-progress runtime timeout.

## Actions

- `2026-06-12T16:18:28+08:00`: Confirmed host `dsp-ubuntu`, branch
  `dev-5060`, base commit `1a030e8d28e678d0a281ad0af3498f1c7da5fabe`, clean
  protected paths, and ProcMan status `Nothing Active`.
- `2026-06-12T16:19:56+08:00`: Created the required temporary alias file with
  aliases for `candidate_0001` and `candidate_0002`.
- `2026-06-12T16:19:56+08:00`: Ran setup-only planning for `candidate_0001`;
  the generated plan config had final values `-latency_L0_to_L1 37` and
  `-prefetch_per_stream_buffer_size 8`.
- `2026-06-12T16:19:57+08:00`: Submitted `candidate_0001`; ProcMan reported
  `Job 2 queued`.
- `2026-06-12T16:19:57+08:00`: Per the 30-second check rule, immediately
  checked ProcMan and process state. ProcMan showed `queuedJobs=1`,
  `activeJobs=0`, `completeJobs=0`; `ps` showed no matching ProcMan manager,
  `slurm.sim`, `backprop`, or GPGPU-Sim process; the run directory had no
  stdout/stderr/result progress. This matched the queued-only stale stop
  condition.
- `2026-06-12T16:20:00+08:00`: Ran fixed `procman.py -k`, which exited `0`,
  killed `0` active jobs, and dropped `1` queued job. Post-cleanup ProcMan
  status is `Nothing Active`.
- `2026-06-12T16:22:00+08:00`: Deleted the temporary alias file and stopped
  without launching `candidate_0002`.
- `2026-06-12T17:22:07+08:00`: Supervisor refined the ProcMan root cause
  after this retry: `procman.py -k` could clean queued-only state, but
  `spawnProcMan()` still launched the manager with a relative `__file__` while
  changing `cwd` to the job-launching directory, so the manager could exit
  before consuming queued jobs. The manager stderr was previously discarded.
- `2026-06-12T17:22:07+08:00`: Supervisor updated `procman.py` to launch the
  manager via `sys.executable` and `os.path.realpath(__file__)`, add manager
  stdout/stderr logs, and make custom `-f` state files absolute and honored on
  first submit.

## Evidence

- Initial `procman.py -p`: `Nothing Active`.
- `candidate_0001` setup-only:
  `artifacts/s7/s7-bounded-sweep-20260610-024829/remaining-candidates-retry-20260612-161828/logs/candidate_0001-setup-only.exitcode`
  is `0`.
- `candidate_0001` effective config values:
  `artifacts/s7/s7-bounded-sweep-20260610-024829/remaining-candidates-retry-20260612-161828/logs/candidate_0001-effective-config-values.log`
  records `-latency_L0_to_L1 37` and
  `-prefetch_per_stream_buffer_size 8`.
- `candidate_0001` submit:
  `artifacts/s7/s7-bounded-sweep-20260610-024829/remaining-candidates-retry-20260612-161828/logs/candidate_0001-actual-run-submit.log`
  records `Job 2 queued`.
- Stale queue evidence:
  - `procman.py -p` immediately after submission showed `queuedJobs=1`,
    `activeJobs=0`, `completeJobs=0`.
  - `ps` inspection showed no matching ProcMan manager, `slurm.sim`,
    `backprop`, or GPGPU-Sim process.
  - The run directory had only setup files, with no simulator stdout/stderr or
    result output for job `2`.
- Cleanup evidence:
  `artifacts/s7/s7-bounded-sweep-20260610-024829/remaining-candidates-retry-20260612-161828/logs/procman-kill-after-stale-candidate_0001.log`
  records `Killing 0 jobs` and `Dropping 1 queued jobs`; exit code is `0`;
  final ProcMan status is `Nothing Active`.
- Existing metrics before retry:
  - `candidate_0003`: available from job `486` baseline artifact
    `artifacts/s7/s7-target-selection-20260610-022405/RTX5060-job486-simulator-candidate-metrics-policy-draft.yaml`
  - `candidate_0004`: available from
    `artifacts/s7/s7-bounded-sweep-20260610-024829/candidate_0004-simulator-candidate-metrics.yaml`
- ProcMan launch-fix validation evidence:
  - Mini validation with a Slurm-like script and absolute output/error paths
    showed job id `1`, `activeJobs=1`, `status=RUNNING`, final
    `Nothing Active`, and stdout lines `mini-start` / `mini-done`.
  - Earlier malformed mini tests now record manager traceback output in
    `*.manager.err`, confirming manager failures are visible instead of being
    discarded.

## Candidate Results

- `candidate_0001`: not completed. It was submitted, but it remained in a
  queued-only ProcMan state and never started; no simulator stdout, `PASSED`,
  or metrics were produced.
- `candidate_0002`: not started, per stop rule after `candidate_0001` stale
  queued-only state.

## S6 Manifest And Report

Not generated. Candidate metrics remain incomplete because `candidate_0001` and
`candidate_0002` produced no metrics in this retry.

## Validations

| Check | Result |
| --- | --- |
| Host is `dsp-ubuntu` | Pass |
| Initial ProcMan clean | Pass |
| Temporary alias used | Pass |
| `candidate_0001` setup-only | Pass |
| `candidate_0001` effective config values | Pass |
| `candidate_0001` active within 30 seconds | Fail; queued-only stale state |
| Stale queue cleaned with fixed `procman.py -k` | Pass |
| `candidate_0002` not launched after stale stop | Pass |
| Temporary alias removed | Pass |
| Final ProcMan clean | Pass |
| ProcMan manager launch fix mini validation | Pass, by supervisor follow-up |
| Metrics generated for `candidate_0001`/`candidate_0002` | No |
| S6 manifest/report generated | No |

## Reviewer Rounds

No blank-context reviewer/spawn tool is available in this worker interface.
Reviewer-style self-check:

- Did the worker stop after queued-only stale state? Yes.
- Was the stale queued ProcMan state cleaned with fixed `procman.py -k`? Yes,
  exit code `0`, `Dropping 1 queued jobs`, final `Nothing Active`.
- Was `candidate_0002` launched? No.
- Was the temporary alias removed? Yes.
- Were metrics or ranked reports fabricated? No.

Reviewer-style verdict: accept the stop/cleanup record; execution remains
blocked by repeated queued-only ProcMan behavior before simulator start.

## Changed Files

Tracked documentation:

- `docs/sm120-calibration/worker-logs/worker-20260612-161828-s7-remaining-candidates-retry.md`

Tracked code, completed by supervisor follow-up:

- `simulator-remodeled/util/job_launching/procman.py`

Temporary:

- None. `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`
  was removed before final status.

Ignored artifacts:

- `artifacts/s7/s7-bounded-sweep-20260610-024829/remaining-candidates-retry-20260612-161828/`

## Final Status

Stopped by hard rule after repeated queued-only ProcMan state for
`candidate_0001`. `candidate_0002` was not launched. No new candidate metrics,
complete S6 supplied-metrics manifest, or ranked report were produced. ProcMan
is clean and the temporary alias file has been deleted.
