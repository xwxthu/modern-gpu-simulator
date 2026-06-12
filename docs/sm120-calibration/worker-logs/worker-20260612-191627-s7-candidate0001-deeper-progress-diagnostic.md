# S7 Candidate 0001 Deeper Progress Diagnostic Worker Log

## Purpose

Run one deeper, local, progress-gated diagnostic for bounded-sweep
`candidate_0001` (`-latency_L0_to_L1=37`,
`-prefetch_per_stream_buffer_size=8`) after the accepted early-progress
diagnostic. The target was a later semantic window: all CTAs launched/resident,
first CTA completion, or repeated unchanged scheduler/barrier/scoreboard/queue
state. This was not a full candidate rerun and did not produce or promote
candidate metrics.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base checkpoint: `47e9d5a30b1e70184471a417234290b8e888796c`
  (`docs: record SM120 candidate early progress`)
- Timestamp: `2026-06-12T19:16:27+08:00`
- Host: `dsp-ubuntu`
- Assigned scope: one local ProcMan diagnostic job, ignored artifacts under
  `artifacts/s7/`, documentation-only tracked output
- Artifact root:
  `artifacts/s7/s7-candidate0001-deeper-progress-diagnostic-20260612-213000/`

## Mandatory Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/s7-bounded-parameter-sweep-design.md`
- `docs/sm120-calibration/s7-validation-evidence-20260609.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-185413-s7-candidate0001-progress-diagnostic.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-182853-s7-candidate0001-timeout-analysis.md`

## Diagnostic Design

The diagnostic used the exact `candidate_0001` effective parameters:

- `-latency_L0_to_L1 37`
- `-prefetch_per_stream_buffer_size 8`

Default-off progress diagnostics were enabled:

```text
GPGPUSIM_KERNEL_PROGRESS_DEBUG=1
GPGPUSIM_KERNEL_PROGRESS_INTERVAL=1000
GPGPUSIM_KERNEL_PROGRESS_SM_LIMIT=1
```

Planned stop gates:

- all CTAs launched/resident or `next_cta` reaches a steady/max value,
- first nonzero `cta_completed_kernel`,
- repeated unchanged semantic state across progress samples and file/process
  observations,
- ProcMan stale/failure,
- wall timeout below the assigned 25-minute maximum.

The actual stop gate was repeated unchanged pre-launch semantic state for about
5 minutes wall time. The job was killed before the 25-minute cap.

## Actions

1. Confirmed repository, branch, base commit, local host, and initial ProcMan
   status. Initial ProcMan state was `Nothing Active`.
2. Created artifact directories under ignored
   `artifacts/s7/s7-candidate0001-deeper-progress-diagnostic-20260612-213000/`.
3. Attempted setup-only with the temporary alias. The first attempt failed
   before any ProcMan job because the alias had been accidentally created in
   the parent tree rather than this repo path. I removed the stray parent-tree
   alias and recreated the alias at
   `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`.
4. Reran setup-only successfully and recorded the generated config path and
   effective values.
5. Submitted exactly one local ProcMan job. It entered `activeJobs` as
   `RUNNING` with job output files under `/tmp/...o4` and `/tmp/...e4`.
6. Monitored ProcMan status, stdout/stderr line and byte counts, progress
   lines, process snapshots, and process tree.
7. Stopped the job after repeated unchanged progress state:
   stdout stayed at one progress sample, `cycle=1`, with
   `cta_launched_kernel=0`, `cta_completed_kernel=0`, `next_cta=0`,
   `active_cta=0`, and `active_sms=0`, while the simulator child process was
   CPU-saturated.
8. Copied stdout/stderr snapshots into the artifact root, recorded hashes,
   killed the active ProcMan job, removed the temporary alias, and verified
   final state. An attempted ProcMan clear command was invoked incorrectly and
   is not used as cleanup evidence; final cleanup rests on the kill log and
   repeated `Nothing Active` status.

## Evidence

### Setup And Effective Config

Important setup artifacts:

- `logs/start-state.txt`
- `logs/setup-only.log`
- `logs/setup-only.exitcode`
- `logs/setup-only-rerun.log`
- `logs/setup-only-rerun.exitcode`
- `logs/setup-gpgpusim-config-paths.txt`
- `logs/effective-config-values.txt`

The first setup-only attempt failed before launch because
`S7SWEEP_L0L1_37_PREFETCH_8` was not found. No ProcMan job was launched for
that failed setup-only attempt.

The successful setup-only rerun used:

```text
RTX5060_SM120_GEN-S7SWEEP_L0L1_37_PREFETCH_8
```

The effective config evidence in `logs/effective-config-values.txt` records:

- line 64: `-gpgpu_clock_domains 2640:2640:2640:14000`
- line 217: base `-latency_L0_to_L1 39`
- line 304: `-is_instruction_prefetching_enabled 1`
- line 305: `-prefetch_per_stream_buffer_size 8`
- line 306: `-prefetch_num_stream_buffers 1`
- line 307: `-num_instruction_prefetches_per_cycle 1`
- line 349: appended candidate override
  `-latency_L0_to_L1 37 -prefetch_per_stream_buffer_size 8`

### ProcMan And Runtime

Important ProcMan/runtime artifacts:

- `logs/procman-before-launch.log`: `Nothing Active`
- `logs/run-submit.log`: `Job 4 queued`
- `logs/procman-immediate.log`: `queuedJobs=0`, `activeJobs=1`,
  `status=RUNNING`
- `logs/procman-poll-001.log`: still `RUNNING`, `runningTime=0:00:30`
- `logs/procman-poll-002.log`: still `RUNNING`, `runningTime=0:02:31`
- `logs/procman-before-kill.log`: still `RUNNING`, `runningTime=0:05:01`
- `logs/procman-kill.log`
- `logs/procman-after-kill.log`: `Nothing Active`
- `logs/procman-clear.log`: records an incorrectly invoked `-c` command and
  is not cleanup evidence
- `logs/procman-final.log`: `Nothing Active`

The simulator application child was alive and CPU-saturated:

- `logs/process-tree-poll-002.log` records
  `backprop-rodinia-2.0-ft ...` as a child of `slurm.sim`, elapsed `03:27`,
  `%CPU 2926`, RSS `262464`, VSZ `2363508`.
- `logs/process-before-kill.log` records the same child at elapsed `05:20`,
  `%CPU 2357`, RSS `262464`, VSZ `2363508`.
- `logs/pstree-poll-002.log` records the simulator child plus many worker
  threads.

### Progress And File Growth

Preserved output snapshots:

- `logs/stdout-before-kill.o4`
- `logs/stderr-before-kill.e4`
- `logs/stdout-stderr-sha256.txt`

The key stdout lines are preserved in `logs/stdout-key-lines.txt`:

- line 1522: kernel 1 pushed:
  `_Z22bpnn_layerforward_CUDAPfS_S_S_ii`, grid `(1,256,1)`, block `(16,16,1)`
- line 1523: progress diagnostics enabled with interval `1000`, SM limit `1`
- line 1524: the only progress sample:
  `cycle=1`, `gpu_sim_cycle=1`, `gpu_tot_sim_cycle=0`,
  `cta_launched_kernel=0`, `cta_completed_kernel=0`, `next_cta=0`,
  `num_cta=256`, `running=0`, `done=0`, `active_cta=0`,
  `not_completed_threads=0`, `active_sms=0`, all cluster response queues `0`

File growth observations:

- `logs/file-growth-poll-001.log`: stdout `184351` bytes, stderr `67` bytes.
- `logs/file-growth-poll-002.log`: stdout remained `1524` lines and
  `184351` bytes; stderr remained `2` lines and `67` bytes.
- `logs/final-progress-before-kill.log`: at `2026-06-12T19:15:32+08:00`,
  stdout still remained `1524` lines and `184351` bytes; stderr remained
  `2` lines and `67` bytes.

No `Shader N bind`, no cycle `1001`, no post-bind cycle `1801`, no
`gpu_tot_sim_cycle` block, no `PASSED`, no `FAILED`, and no simulator exit
marker appeared in this diagnostic stdout.

### Comparison To Prior Evidence

The prior accepted early-progress diagnostic for the same candidate captured
normal post-bind launch progress through cycles `1801` to `1806`, with
`cta_launched_kernel` and `next_cta` advancing from `30` to `180`.

This deeper diagnostic did not reach that same early launch burst. It remained
unchanged before shader binding at `cycle=1`, with `next_cta=0`, for about
5 minutes wall time while the simulator child was CPU-active. This is therefore
a different observed state from the prior early diagnostic and from passing job
`486` around the same semantic stage.

## Analysis Answers

### 1. Does candidate_0001 progress beyond the early CTA launch burst? To what semantic gate?

No. In this deeper diagnostic, candidate `0001` did not even reach the prior
early CTA launch burst. The run pushed kernel 1 and emitted the initial
progress sample at `cycle=1`, then repeated unchanged output/file state until
the repeated-state gate was reached. The semantic gate reached was:

```text
repeated unchanged pre-shader-bind / pre-CTA-launch state
```

### 2. Do CTA launch/completion counts, active CTAs, sampled PC, barrier/scheduler/scoreboard/queue fields continue changing, or do they repeat unchanged?

They repeat unchanged in the available progress diagnostics:

- `cta_launched_kernel=0`
- `cta_completed_kernel=0`
- `next_cta=0`
- `num_cta=256`
- `running=0`
- `done=0`
- `active_cta=0`
- `not_completed_threads=0`
- `active_sms=0`
- `gridbar_active=0`
- all cluster response queues `0`

The diagnostic did not reach the richer post-bind per-SM sample that includes
sampled PC, barrier, scheduler, scoreboard, and memory queue summaries. The
important negative evidence is that the run stayed before that diagnostic
window despite an alive, CPU-heavy simulator process.

### 3. If it stalls, where does it stall?

Observed stall location:

- kernel uid/name: `uid=1`,
  `_Z22bpnn_layerforward_CUDAPfS_S_S_ii`
- kernel launch: grid `(1,256,1)`, block `(16,16,1)`
- last progress cycle: `cycle=1`, `gpu_sim_cycle=1`,
  `gpu_tot_sim_cycle=0`
- CTA state: `cta_launched_kernel=0`, `cta_completed_kernel=0`,
  `next_cta=0`, `num_cta=256`, `active_cta=0`
- active SMs: `0`
- PC/barrier/scheduler/scoreboard fields: unavailable because the run did not
  reach shader bind or a post-bind SM sample
- memory/queue fields available: all `cluster*_respq=0`; no post-bind `mem_q`
  or instruction-prefetch queue sample was reached
- process state: simulator child `backprop-rodinia-2.0-ft` alive under
  `slurm.sim`, CPU-heavy (`%CPU` in the thousands), RSS about `262464` KiB

This places the observed repeated unchanged state after kernel push and
progress-diagnostic enablement, but before shader binding and before CTA
launch.

### 4. Recommendation

Do not extend the candidate timeout as the next step. This diagnostic shows a
CPU-heavy repeated unchanged state before CTA launch within 5 minutes, not a
clear slow-but-changing execution window.

Do not run `candidate_0002` blindly yet. It shares the low
`-latency_L0_to_L1=37` value and could enter the same ambiguous pre-launch
state.

Recommended next action: add targeted code instrumentation or fix around the
kernel-dispatch/shader-bind path for low `-latency_L0_to_L1=37`, then rerun a
short progress-gated diagnostic. The instrumentation should capture where time
is spent between the initial `cycle=1` progress sample and the first
`Shader N bind`/CTA launch, because the existing progress diagnostics only
become semantically rich after bind. If the added instrumentation identifies a
valid but extremely slow loop, then consider a narrowly justified timeout
extension; otherwise exclude or fix the low-L0-to-L1 point before running
`candidate_0002`.

Confidence: medium-high that this observed diagnostic state is pathological or
requires instrumentation/fix before more sweep execution. Confidence is lower
on the exact code site because the available diagnostics stop before
post-bind PC/barrier/scheduler fields exist.

## Changed Files

Tracked documentation:

- `docs/sm120-calibration/worker-logs/worker-20260612-191627-s7-candidate0001-deeper-progress-diagnostic.md`

Pre-existing tracked modification not made by this worker:

- `docs/sm120-calibration/supervisor-log.md`

Ignored artifacts:

- `artifacts/s7/s7-candidate0001-deeper-progress-diagnostic-20260612-213000/`

Temporary files removed before final status:

- `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`
- accidental parent-tree stray alias at
  `/home/xiewx/accel-0608/simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`

## Final ProcMan State

Final ProcMan status:

```text
Nothing Active
```

The final status is recorded in `logs/procman-final.log`.

## Temporary Alias State

Final temporary alias state: absent.

`logs/temp-alias-final-find.txt` is empty, confirming no
`define-s7-bounded-sweep-temp.yml` remained under `/home/xiewx/accel-0608`.

## Cleanup And No-Promotion Confirmation

- Runtime/log artifacts are under ignored `artifacts/s7/`.
- No accepted configs were modified.
- No generated configs were modified.
- No `calibration-results/latest` path was modified.
- No simulator candidate metrics YAML was generated.
- No complete S6 manifest, ranked report, accepted/latest config, generated
  config, or latest calibration file was produced or promoted.
- The only actual ProcMan diagnostic job was job `4`; the earlier setup-only
  failure launched no ProcMan job.

## Reviewer Rounds

Round 1 blank-context reviewer:
`019ebb8d-84b5-7d73-8314-de1cf7817c8d`.

Verdict: `CHANGES_NEEDED`.

Blocking finding:

- Cleanup wording claimed ProcMan was "killed and cleared", but
  `logs/procman-clear.log` shows `procman.py: error: -c option requires 1
  argument`. The reviewer confirmed final state was still clean because
  `logs/procman-after-kill.log` and `logs/procman-final.log` both record
  `Nothing Active`.

Corrective action:

- Updated the actions and evidence sections to stop claiming successful
  ProcMan clear. Cleanup evidence now relies on `logs/procman-kill.log`,
  `logs/procman-after-kill.log`, and `logs/procman-final.log`.

Reviewer also confirmed:

- Temporary alias removal is supported by empty
  `logs/temp-alias-final-find.txt`.
- Evidence quality is otherwise good: setup failure/success, effective
  overrides, single submitted job, stable progress sample, no file growth,
  CPU-heavy child process, stdout/stderr hashes, and final cleanup are covered.
- No-promotion claims are supported by available evidence.
- The recommendation follows from the repeated pre-CTA-launch state at
  `cycle=1`.

Round 2 blank-context reviewer:
`019ebb8e-ef3f-7c90-acf4-180b8353d9d1`.

Verdict: `ACCEPT`.

Reviewer confirmed:

- The prior cleanup wording issue is fixed. The log now states that the
  ProcMan clear command was invoked incorrectly and is not cleanup evidence.
- Evidence quality is sufficient: setup failure/success, effective overrides,
  one queued job, stable `cycle=1` progress, no file growth, CPU-heavy child,
  and stdout/stderr hashes are backed by artifacts.
- Cleanup/no-promotion, final ProcMan state, and temporary alias state are
  covered by the referenced logs.
- Required fields are present.
- The recommendation follows from the observed repeated pre-CTA-launch state
  at `cycle=1`.
