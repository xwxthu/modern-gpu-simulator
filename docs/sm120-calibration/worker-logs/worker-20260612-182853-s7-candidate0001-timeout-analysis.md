# S7 Candidate 0001 Timeout Analysis Worker Log

## Purpose

Diagnose why bounded-sweep `candidate_0001`
(`-latency_L0_to_L1=37`, `-prefetch_per_stream_buffer_size=8`) entered
ProcMan `RUNNING` after checkpoint `4534e04` but timed out after about
43 minutes without `result.txt`, `PASSED`, simulator exit marker, or
parseable simulator metrics.

This analysis does not promote configs, does not claim calibration-quality
results, and does not rerun the full candidate.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Required base checkpoint: `556c0cf13f0eca70f7c6f4f31f047afd86601f87`
  (`docs: record post-ProcMan SM120 candidate timeout`)
- Current timestamp: `2026-06-12T18:28:53+08:00`
- Worker role: S7 timeout root-cause analysis worker
- Changed tracked files: this documentation log only
- Ignored diagnostic artifact root:
  `artifacts/s7/s7-candidate0001-timeout-analysis-20260612-200000/`

## Mandatory Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/s7-bounded-parameter-sweep-design.md`
- `docs/sm120-calibration/s7-validation-evidence-20260609.md`
- `docs/sm120-calibration/s7-simulator-candidate-metrics-bridge.md`
- `docs/sm120-calibration/worker-logs/worker-20260611-113040-s7-single-candidate-recovery.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-173032-s7-remaining-candidates-post-procman-fix.md`

## Artifacts Inspected

Timeout artifacts:

- `artifacts/s7/s7-bounded-sweep-20260610-024829/remaining-candidates-post-procman-fix-20260612-173032/`
- `artifacts/s7/s7-bounded-sweep-20260610-024829/sim-runs/candidate_0001-post-procman-fix-20260612-173032/`

Passing/comparison artifacts:

- `artifacts/s7/s7-bounded-sweep-20260610-024829/candidate_0004-simulator-candidate-metrics.yaml`
- `artifacts/s7/s7-bounded-sweep-20260610-024829/sim-runs/candidate_0004/`
- `artifacts/s7/s7-target-selection-20260610-022405/RTX5060-job486-simulator-candidate-metrics-policy-draft.yaml`
- `artifacts/s7/s7-kernel2-attribution-20260609-211410/`

## Actions

1. Confirmed the working directory was
   `/home/xiewx/accel-0608/modern-gpu-simulator`.
2. Read all mandatory docs and prior worker logs.
3. Inspected `candidate_0001` timeout stdout/stderr snapshots, ProcMan logs,
   run directory, and effective `gpgpusim.config`.
4. Compared `candidate_0001` effective config against passing
   `candidate_0003`/job `486` and `candidate_0004`/job `487`.
5. Compared the last `candidate_0001` stdout stage against passing stdout
   around the same kernel-1 launch stage.
6. Ran one bounded local diagnostic ProcMan job under ignored artifacts with
   default-off progress diagnostics enabled. The job was killed immediately
   after it proved the progress diagnostic path was active. It was not allowed
   to complete and did not produce candidate metrics.
7. Removed the temporary alias and confirmed final ProcMan state was
   `Nothing Active`.

## Static Evidence

### ProcMan And Timeout State

The post-ProcMan-fix worker recorded:

- `candidate_0001-actual-run-submit.log`: `Job 1 queued`.
- `candidate_0001-procman-immediate.log`: `queuedJobs=0`,
  `activeJobs=1`, `status=RUNNING`.
- `candidate_0001-procman-before-timeout-cleanup.log`: still `RUNNING`,
  `runningTime=0:43:14`, `maxVmSize=5454032896`.
- `candidate_0001-process-before-timeout-cleanup.log`: shell process plus
  active simulator child. The child had elapsed `43:30`, `%CPU 1455`, RSS
  `404384`, VSZ `5312624`.
- Final cleanup logs report `Killing 1 jobs`, then final status
  `Nothing Active`.

This rules out the previous queued-only ProcMan manager-launch failure as the
active blocker for this run. The simulator process was alive and CPU-active at
timeout.

### Last Meaningful Stdout Progress

The timeout stdout snapshot is:

- `artifacts/s7/s7-bounded-sweep-20260610-024829/remaining-candidates-post-procman-fix-20260612-173032/logs/candidate_0001-timeout-stdout.o1`
- Size at cleanup: `182K`
- Line count: `1554`

The last meaningful simulator-visible stage is kernel 1 launch and SM binding:

- Kernel: first kernel, `_Z22bpnn_layerforward_CUDAPfS_S_S_ii`
- Launch line: `pushing kernel ... gridDim= (1,256,1) blockDim = (16,16,1)`
- Last line: `GPGPU-Sim uArch: Shader 29 bind to kernel 1 ...`

No `GPGPUSIM-K2-PROGRESS` lines, no `gpu_sim_cycle`, no
`gpu_tot_sim_cycle`, no `gpgpu_simulation_time`, no `PASSED`, no `FAILED`,
and no `GPGPU-Sim: *** exit detected ***` were present in that timeout
snapshot.

The last visible PC data before the hang is reconvergence analysis for kernel
1:

- Branch at `PC=0x2458`, postdominator `PC=0x24a0` (`bar.sync 0`)
- Branch at `PC=0x2580`, postdominator `PC=0x25a8` (`bar.sync 0`)
- Branch at `PC=0x25c0`, postdominator `PC=0x25e8` (`bar.sync 0`)
- Branch at `PC=0x2600`, postdominator `PC=0x2628` (`bar.sync 0`)
- Branch at `PC=0x2640`, postdominator `PC=0x2668`
- Branch at `PC=0x2690`, postdominator `PC=0x26d0` (`ret`)

There are no scheduler, scoreboard, barrier-state, CTA-completion, or queue
diagnostic samples in the failed run. That is an instrumentation/monitoring
gap for the timeout run.

### Comparison To Passing Runs At Same Stage

Passing job `486` and passing job `487` both include progress diagnostics.
Around the same stage:

- After the same `pushing kernel` line, job `486` emitted
  `GPGPUSIM-K2-PROGRESS enabled interval=200000 sm_limit=1`.
- It emitted `cycle=1`, then after `Shader 29 bind`, it emitted
  `cycle=1801`, `cta_launched_kernel=30`, `next_cta=30`, `active_sms=30`,
  sampled `pc=0x2400`.
- It then advanced through kernel 1 CTA completions and later produced
  metric blocks.
- Job `487` completed with `PASSED`, simulator exit marker, kernel 1
  `gpu_tot_sim_cycle=7722`, kernel 2 `gpu_tot_sim_cycle=45760`, and
  application `gpgpu_simulation_time = ... 2203 sec`.

The failed run reached the point immediately before the first post-bind
progress sample that passing diagnostic runs recorded. Because the failed run
did not have progress diagnostics enabled, the artifact cannot distinguish
between:

- very slow progress after shader binding,
- livelock/deadlock shortly after binding,
- or a long silent interval caused by stdout not being sampled at a useful
  semantic level.

It does show that by 43 minutes the run had not reached the first kernel
metric block, whereas passing candidate `0004` completed the full application
in `2203 sec` (`36 min 43 sec`) and passing candidate `0003` completed in
`2398 sec` (`39 min 58 sec`).

## Config Drift Check

Effective `gpgpusim.config` comparison used the run-generated configs:

- `candidate_0001`:
  `artifacts/s7/s7-bounded-sweep-20260610-024829/sim-runs/candidate_0001-post-procman-fix-20260612-173032/.../RTX5060_SM120_GEN-S7SWEEP_L0L1_37_PREFETCH_8/gpgpusim.config`
- `candidate_0003`/job `486`:
  `artifacts/s7/s7-kernel2-attribution-20260609-211410/sim-smoke/.../RTX5060_SM120_GEN/gpgpusim.config`
- `candidate_0004`/job `487`:
  `artifacts/s7/s7-bounded-sweep-20260610-024829/sim-runs/candidate_0004/.../RTX5060_SM120_GEN-S7SWEEP_L0L1_39_PREFETCH_10/gpgpusim.config`

Observed diffs:

- `candidate_0001` vs `candidate_0003`: exactly one effective key differs,
  `-latency_L0_to_L1 37` vs `39`.
- `candidate_0001` vs `candidate_0004`: exactly two effective keys differ,
  `-latency_L0_to_L1 37` vs `39` and
  `-prefetch_per_stream_buffer_size 8` vs `10`.
- `candidate_0003` vs `candidate_0004`: exactly one effective key differs,
  `-prefetch_per_stream_buffer_size 8` vs `10`.

Selected common active values:

- `-gpgpu_clock_domains 2640:2640:2640:14000`
- `-is_instruction_prefetching_enabled 1`
- `-prefetch_num_stream_buffers 1`
- `-num_instruction_prefetches_per_cycle 1`

Conclusion: no accidental config drift was found in the effective simulator
configs. The timeout point differs from passing candidate `0003` only by
lowering `-latency_L0_to_L1` from `39` to `37`.

## Diagnostic Run

Static evidence was insufficient to decide whether candidate `0001` was stuck
or merely progressing silently, so I ran one bounded diagnostic job locally on
this server.

Diagnostic artifact root:

```text
artifacts/s7/s7-candidate0001-timeout-analysis-20260612-200000/
```

Diagnostic setup:

- Temporary alias:
  `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`
- Alias content: only `S7SWEEP_L0L1_37_PREFETCH_8`
- Setup-only output:
  `logs/candidate_0001-diagnostic-setup-only-rerun.log`
- Effective config:
  `logs/candidate_0001-diagnostic-effective-config.log`
- Effective diagnostic values:
  - `-latency_L0_to_L1 37`
  - `-prefetch_per_stream_buffer_size 8`
  - `-gpgpu_clock_domains 2640:2640:2640:14000`
  - `-is_instruction_prefetching_enabled 1`
  - `-prefetch_num_stream_buffers 1`
  - `-num_instruction_prefetches_per_cycle 1`

Diagnostic run environment:

```bash
GPGPUSIM_KERNEL_PROGRESS_DEBUG=1
GPGPUSIM_KERNEL_PROGRESS_INTERVAL=1000
GPGPUSIM_KERNEL_PROGRESS_SM_LIMIT=1
```

Diagnostic run result:

- Submit log: `logs/candidate_0001-diagnostic-run-submit-rerun.log`
- ProcMan immediate status:
  `logs/candidate_0001-diagnostic-procman-immediate.log`
  reported `activeJobs=1`, `status=RUNNING`.
- Stdout snapshot:
  `logs/candidate_0001-diagnostic-stdout-final-snapshot.o2`
- Final ProcMan status:
  `logs/diagnostic-procman-final-status.log` reported `Nothing Active`.
- Temporary alias final state: absent.

The diagnostic stdout emitted:

- `GPGPUSIM-K2-PROGRESS enabled interval=1000 sm_limit=1`
- `GPGPUSIM-K2-PROGRESS cycle=1 gpu_sim_cycle=1 ...`

The diagnostic was stopped immediately after that evidence because it answered
one narrow question: progress diagnostics are functional for candidate
`0001` when explicitly enabled. It did not run long enough to sample the
original late state after `Shader 29 bind`; therefore it does not prove forward
progress or deadlock after shader binding.

One setup-only attempt initially failed because I accidentally created the
temporary alias outside the assigned repo tree. I removed that file, created
the alias inside `/home/xiewx/accel-0608/modern-gpu-simulator`, and proceeded
only after setup-only succeeded. No ProcMan job was launched during the failed
setup-only attempt.

## Analysis Answers

### 1. Last Meaningful Simulator Progress In Candidate 0001

The failed timeout run reached kernel 1
`_Z22bpnn_layerforward_CUDAPfS_S_S_ii`, completed reconvergence/predecode, and
bound shaders through `Shader 29` to kernel 1. It did not print any parseable
stats, CTA progress, scheduler, scoreboard, barrier, or queue samples. The
only PC evidence is the kernel-1 reconvergence listing described above.

### 2. Config Differences Versus Passing Candidate 0003 And 0004

No accidental config drift was found. `candidate_0001` differs from passing
`candidate_0003` only by `-latency_L0_to_L1 37` vs `39`. It differs from
passing `candidate_0004` by the two intended sweep parameters:
`-latency_L0_to_L1 37` vs `39` and
`-prefetch_per_stream_buffer_size 8` vs `10`.

### 3. Slow Forward Progress Or Stuck State

The evidence proves candidate `0001` was much slower than passing runs in
wall-clock terms: after about `43:14` ProcMan runtime it had not reached the
first kernel metric block, while candidate `0004` completed the full
application in `36:43` and candidate `0003` completed in `39:58`.

The evidence does not prove whether it was making forward progress after
`Shader 29 bind`. The process was CPU-active at timeout, but the stdout
snapshot lacked progress diagnostics. That combination is more consistent
with a simulator/model livelock or extreme slowdown than a ProcMan or launcher
failure, but the exact state is unobserved.

### 4. Likely Parameter Cause And Candidate 0002 Value

Because `candidate_0003` (`39,8`) passed and `candidate_0004` (`39,10`)
passed, while `candidate_0001` (`37,8`) timed out with no config drift, the
strongest available signal points to `-latency_L0_to_L1=37` as the likely
trigger. The evidence does not isolate whether the failure requires
interaction with `-prefetch_per_stream_buffer_size=8`, because `candidate_0002`
(`37,10`) has not been run.

However, running `candidate_0002` before resolving candidate `0001` is not the
best next step. If the low L0-to-L1 latency triggers a simulator/model
livelock or pathological scheduling state, `candidate_0002` is likely to hit
the same failure family and add another ambiguous timeout. Candidate `0002`
becomes valuable only after the low-latency path has targeted diagnostics or a
short progress-gated run design.

### 5. Recommended Next Action

Do not simply extend the bounded timeout and do not blindly run candidate
`0002`.

Recommended next action:

1. Add or enable targeted progress diagnostics for candidate `0001` by default
   in the execution worker, with a short watchdog that records kernel uid,
   CTA launched/completed, dominant PC, barrier state, scheduler blockers,
   scoreboard blockers, instruction-cache/prefetch state, and file growth at
   fixed intervals.
2. Rerun only a short progress-gated candidate `0001` diagnostic, stopping
   after it reaches either:
   - the first post-bind progress samples comparable to job `486`/`487`,
   - a repeated unchanged state across several samples,
   - or a strict short wall timeout.
3. If diagnostics show repeated unchanged CTA/PC/barrier/scheduler state, treat
   the low `-latency_L0_to_L1=37` point as a simulator/model bug or invalid
   pathological point and exclude it with rationale until fixed.
4. If diagnostics show steady progress but much slower runtime, then consider
   a longer timeout for `candidate_0001` and then run `candidate_0002` to
   isolate the prefetch-buffer interaction.

Current recommendation classification: targeted diagnostics first. Confidence
is medium. The evidence is strong for "not ProcMan, not config drift, not
enough timeout evidence to claim normal slow progress"; it is not yet strong
enough to declare a specific simulator deadlock/livelock site.

## Reviewer Rounds

Round 1 blank-context reviewer: `019ebb62-0ce7-7e11-9b3f-87ee417e4166`.

Verdict: `ACCEPT`.

Reviewer findings:

- Evidence quality is sufficient. Timeout state is backed by the
  pre-timeout ProcMan and process logs, showing one active CPU-heavy simulator
  process after about 43 minutes, followed by clean kill/final
  `Nothing Active`.
- Conclusions are appropriately bounded. The worker does not overclaim
  deadlock and correctly distinguishes "no metric/progress output by timeout"
  from proof of a specific stuck state.
- Config-drift conclusion follows from cited effective configs.
- Diagnostic hard rules were respected: ignored `artifacts/s7/` root, local
  execution, one active diagnostic ProcMan job, cleanup after kill, final
  `Nothing Active`, and temporary alias absent.
- Recommendation is actionable: targeted progress diagnostics plus a short
  progress-gated candidate `0001` rerun before trying candidate `0002`.

Reviewer minor note: diagnostic submit log says `Job 2 queued`, but ProcMan
evidence shows only one active diagnostic job. This is ProcMan/job numbering,
not a rule violation.

## Changed Files

Tracked documentation:

- `docs/sm120-calibration/worker-logs/worker-20260612-182853-s7-candidate0001-timeout-analysis.md`

Ignored artifacts:

- `artifacts/s7/s7-candidate0001-timeout-analysis-20260612-200000/`

Temporary files:

- `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`
  was created for the diagnostic and removed before final status.

Protected paths:

- No accepted configs were modified.
- No generated/latest configs were modified.
- No `calibration-results/latest` path was modified.
- No promotion was performed.

## Final State Before Review

- Final ProcMan state: `Nothing Active`.
- Temporary alias state: absent.
- Candidate metrics generated: none.
- Complete S6 manifest/report generated: none.
- Calibration promotion: none.
