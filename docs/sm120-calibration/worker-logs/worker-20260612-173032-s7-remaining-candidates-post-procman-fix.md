# S7 Remaining Candidates Post-ProcMan-Fix Worker Log

## Purpose

Run the remaining bounded-sweep simulator candidates `candidate_0001` and
`candidate_0002` locally after the ProcMan absolute-path fix, collect draft
simulator candidate metrics, and, if all four candidate metrics are available,
generate a reviewed complete draft S6 supplied-metrics manifest and draft ranked
report under ignored `artifacts/s7/`.

No promotion is in scope.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base commit: `4534e048f23359a7ea1a05638e079bec3a234a34`
- Base checkpoint: `4534e04 fix: launch ProcMan manager by absolute path`
- Timestamp: `2026-06-12T17:30:32+08:00`
- Host: `dsp-ubuntu`
- Worker role: `S7 remaining bounded-sweep candidates post-ProcMan-fix worker`
- Execution artifact directory:
  `artifacts/s7/s7-bounded-sweep-20260610-024829/remaining-candidates-post-procman-fix-20260612-173032/`

## Required Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/s7-bounded-parameter-sweep-design.md`
- `docs/sm120-calibration/s7-simulator-candidate-metrics-bridge.md`
- `docs/sm120-calibration/worker-logs/worker-20260611-113040-s7-single-candidate-recovery.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-161828-s7-remaining-candidates-retry.md`

## Hard Rules

- Work only in `/home/xiewx/accel-0608/modern-gpu-simulator`.
- Do not revert or overwrite others' edits.
- Simulator execution must be local on this server only; do not run simulator
  workloads on `dsp5060`.
- Run at most one ProcMan job at a time.
- Use only temporary alias file
  `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`;
  remove it before final status.
- Do not modify accepted/generated/latest configs or `calibration-results/latest`.
- Do not promote configs or claim calibration-quality results.
- Keep run logs and generated runtime artifacts under ignored `artifacts/s7/`.
- Do not rerun `candidate_0003`/job `486` or `candidate_0004`/job `487`.
- After each candidate submission, check ProcMan within 30 seconds. Stop if the
  job does not enter active/running state or if ProcMan becomes stale.
- Stop on functional failure, no parseable metrics, ProcMan stale state, or
  no-progress runtime timeout. Clean ProcMan and remove temporary alias before
  returning.

## Start State

- Host check: `dsp-ubuntu`.
- Initial ProcMan status: `Nothing Active`.
- Branch/status: `dev-5060`, ahead of origin; pre-existing modified file
  `docs/sm120-calibration/supervisor-log.md`.
- Temporary alias file absent at start.
- Existing candidate metrics:
  - `candidate_0003`: job `486` baseline metrics exist; not rerun.
  - `candidate_0004`: job `487` metrics exist; not rerun.
  - `candidate_0001`: missing.
  - `candidate_0002`: missing.

## Actions

- `2026-06-12T17:30:32+08:00`: Read mandatory context and confirmed base
  checkpoint, host, branch/status, and clean ProcMan state.
- `2026-06-12T17:31:00+08:00`: Created the required temporary alias file with
  only `candidate_0001` and `candidate_0002` aliases.
- `2026-06-12T17:31:01+08:00`: Ran setup-only planning for `candidate_0001`;
  the generated config had final values `-latency_L0_to_L1 37` and
  `-prefetch_per_stream_buffer_size 8`.
- `2026-06-12T17:31:16+08:00`: Submitted `candidate_0001` locally with
  ProcMan. Immediate ProcMan check showed `queuedJobs=0`, `activeJobs=1`, and
  `status=RUNNING`.
- `2026-06-12T17:49:16+08:00`: Monitored `candidate_0001`; ProcMan still
  showed one active job and the child `backprop-rodinia-2.0-ft` process was
  CPU-active.
- `2026-06-12T18:04:30+08:00`: At about 32.7 minutes, ProcMan still showed one
  active job. The child process remained CPU-active, and stdout had advanced
  from 180 KiB to 182 KiB, so the run received a short bounded extension rather
  than immediate cleanup.
- `2026-06-12T18:14:44+08:00`: At about 42.7 minutes, ProcMan still showed one
  active job, no `result.txt`, no `PASSED`, no simulator exit marker, and no
  parseable simulator metrics. Stopped under the no-progress runtime-timeout
  rule for this bounded worker.
- `2026-06-12T18:15:00+08:00`: Copied timeout stdout/stderr evidence to the
  worker artifact log directory, ran `procman.py -k`, removed the temporary
  alias file, and confirmed ProcMan cleanup.
- `2026-06-12T18:16:00+08:00`: Ran a final `procman.py -k` to clear ProcMan's
  completed record for the killed job. Final ProcMan status is `Nothing Active`.

## Evidence

Initial evidence:

- `python3 simulator-remodeled/util/job_launching/procman.py -p` returned
  `Nothing Active`.
- `hostname` returned `dsp-ubuntu`.
- `git rev-parse HEAD` returned
  `4534e048f23359a7ea1a05638e079bec3a234a34`.

Candidate `0001` start evidence:

- Setup log:
  `artifacts/s7/s7-bounded-sweep-20260610-024829/remaining-candidates-post-procman-fix-20260612-173032/logs/candidate_0001-setup-only.log`
- Setup exit code:
  `artifacts/s7/s7-bounded-sweep-20260610-024829/remaining-candidates-post-procman-fix-20260612-173032/logs/candidate_0001-setup-only.exitcode`
  is `0`.
- Submit log:
  `artifacts/s7/s7-bounded-sweep-20260610-024829/remaining-candidates-post-procman-fix-20260612-173032/logs/candidate_0001-actual-run-submit.log`
  records `Job 1 queued`.
- Immediate ProcMan check:
  `artifacts/s7/s7-bounded-sweep-20260610-024829/remaining-candidates-post-procman-fix-20260612-173032/logs/candidate_0001-procman-immediate.log`
  records `activeJobs=1` and `status=RUNNING`.

Candidate `0001` timeout/cleanup evidence:

- Timeout stdout snapshot:
  `artifacts/s7/s7-bounded-sweep-20260610-024829/remaining-candidates-post-procman-fix-20260612-173032/logs/candidate_0001-timeout-stdout.o1`
- Timeout stderr snapshot:
  `artifacts/s7/s7-bounded-sweep-20260610-024829/remaining-candidates-post-procman-fix-20260612-173032/logs/candidate_0001-timeout-stderr.e1`
- `candidate_0001-timeout-stdout.o1` has no `gpu_sim_cycle`,
  `gpu_tot_sim_cycle`, `PASSED`, `FAILED`, or `GPGPU-Sim: *** exit detected ***`
  lines.
- `candidate_0001-tmp-files-before-timeout-cleanup.log` records stdout at
  182 KiB and stderr at 67 bytes before cleanup.
- `procman-kill-after-timeout-candidate_0001.log` records `Killing 1 jobs`.
- `procman-final-clean.log` records `Killing 0 jobs` after the killed job
  moved to ProcMan completed state.
- `procman-final-status.log` records `Nothing Active`.
- `git check-ignore -v` confirmed the runtime/log artifacts are ignored under
  `artifacts/s7/`.

## Candidate Results

- `candidate_0001`: not completed. It entered `activeJobs` as `RUNNING` within
  the 30-second submission check, but exceeded the bounded runtime window
  without producing `result.txt`, `PASSED`, simulator exit marker, or parseable
  simulator metrics. The run was stopped and cleaned under the no-progress
  runtime-timeout rule.
- `candidate_0002`: not launched, per hard rule to stop after
  `candidate_0001` produced no parseable metrics/runtime timeout.
- `candidate_0003`: existing job `486` metrics were not rerun.
- `candidate_0004`: existing job `487` metrics were not rerun.

## Generated Files

- No new simulator candidate metrics YAML was produced for `candidate_0001`
  because no parseable metric block was available.
- No complete S6 supplied-metrics manifest or ranked report was generated
  because all four candidate metrics are still not available.
- Ignored runtime/log artifacts were produced under:
  `artifacts/s7/s7-bounded-sweep-20260610-024829/remaining-candidates-post-procman-fix-20260612-173032/`
  and
  `artifacts/s7/s7-bounded-sweep-20260610-024829/sim-runs/candidate_0001-post-procman-fix-20260612-173032/`.

## Validations

| Check | Result |
| --- | --- |
| Required context read | Pass |
| Host is local `dsp-ubuntu`, not `dsp5060` | Pass |
| Initial ProcMan clean | Pass |
| Temporary alias file used | Pass |
| `candidate_0001` setup-only exit code | Pass, `0` |
| `candidate_0001` effective config values | Pass, `37` and `8` |
| `candidate_0001` active within 30 seconds | Pass |
| At most one ProcMan job at a time | Pass |
| `candidate_0002` not launched after timeout | Pass |
| Metrics generated for `candidate_0001` | No, no parseable metrics |
| Complete S6 manifest/report generated | No, candidate metrics incomplete |
| Temporary alias removed | Pass |
| Final ProcMan clean | Pass, `Nothing Active` |
| Protected configs/latest paths clean | Pass |
| Artifact paths ignored | Pass |
| `git diff --check` for touched tracked file/temp alias path | Pass |

## Reviewer Rounds

- Round 1 blank-context reviewer: `019ebb55-5fa3-7421-8e4c-59b2cd30e847`.
- Verdict: `ACCEPT`.
- Findings: no blocking findings.
- Reviewer confirmed:
  - `candidate_0001` was launched locally and entered `RUNNING`.
  - Runtime timeout/no parseable metrics is supported by timeout and ProcMan
    evidence.
  - Cleanup evidence is present, including final `Nothing Active`.
  - `candidate_0002` was not launched after the stop condition.
  - No evidence of `candidate_0003`/`candidate_0004` reruns was found in the new
    artifact set.
  - Temporary alias is absent; snapshot contains only the two allowed aliases.
  - Git status shows only this new worker log as this worker's tracked addition;
    the modified supervisor log is pre-existing.
  - Ignored artifacts are under `artifacts/s7/`; protected generated/latest and
    calibration paths show no status changes.

## Changed Files

Tracked documentation:

- `docs/sm120-calibration/worker-logs/worker-20260612-173032-s7-remaining-candidates-post-procman-fix.md`

Ignored artifacts:

- `artifacts/s7/s7-bounded-sweep-20260610-024829/remaining-candidates-post-procman-fix-20260612-173032/`
- `artifacts/s7/s7-bounded-sweep-20260610-024829/sim-plan/candidate_0001-post-procman-fix-20260612-173032/`
- `artifacts/s7/s7-bounded-sweep-20260610-024829/sim-runs/candidate_0001-post-procman-fix-20260612-173032/`

Temporary, removed before final status:

- `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`

## Final Status

Stopped by hard rule after `candidate_0001` runtime timeout with no parseable
simulator metrics. `candidate_0002` was not launched. ProcMan is clean, the
temporary alias file is absent, protected configs/latest paths were not changed,
and no complete S6 supplied-metrics manifest or ranked report was generated.
