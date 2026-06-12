# S7 Candidate 0002 Progress-Aware Rerun Worker Log

## Purpose

Run exactly one bounded ProcMan/simulator diagnostic for bounded-sweep
`candidate_0002` with a progress-aware stop policy, to replace the premature
Job `14` stop-policy artifact with deeper pre-admission evidence if possible.

This was diagnostic execution only. It was not calibration promotion, not an
S6 correlation/search run, and not a candidate-metrics generation run.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base checkpoint: `6ff16fc96e9862619becee4dccab5217e8edeeb0`
  (`docs: analyze SM120 residual diagnostic stop policy`)
- Start timestamp: `2026-06-13T01:59:27+08:00`
- Worker-log draft timestamp: `2026-06-13T02:15:11+08:00`
- Host: `dsp-ubuntu`
- Artifact root:
  `artifacts/s7/s7-candidate0002-progress-aware-rerun-20260613-015927/`
- Actual local ProcMan/simulator jobs submitted by this worker: exactly one,
  Job `15`

Initial tracked worktree state:

```text
## dev-5060...origin/dev-5060 [ahead 71]
 M docs/sm120-calibration/supervisor-log.md
```

The supervisor-log modification was pre-existing and was not edited by this
worker.

## Mandatory Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/worker-logs/worker-20260613-014600-s7-residual-diagnostic-stop-policy-analysis.md`
- `docs/sm120-calibration/worker-logs/worker-20260613-012616-s7-candidate0002-residual-attribution-diagnostic.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-235505-s7-candidate0002-cluster-core-detail-diagnostic.md`
- Immediately relevant Job `13` and Job `14` artifacts under:
  - `artifacts/s7/s7-candidate0002-cluster-core-detail-diagnostic-20260612-235505/logs/`
  - `artifacts/s7/s7-candidate0002-residual-attribution-diagnostic-20260613-011718/logs/`

## Diagnostic Design

Candidate effective parameter overrides:

```text
-latency_L0_to_L1 37
-prefetch_per_stream_buffer_size 10
```

Temporary config alias:

```text
RTX5060_SM120_GEN-S7SWEEP_L0L1_37_PREFETCH_10
```

Benchmark:

```text
rodinia_2.0-ft:backprop-rodinia-2.0-ft:0
```

Actual job:

```text
Job 15 queued (backprop-rodinia-2.0-ft-4096___data_result_4096_txt RTX5060_SM120_GEN-S7SWEEP_L0L1_37_PREFETCH_10)
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
GPGPUSIM_CYCLE_COST_INTERVAL=50
GPGPUSIM_CYCLE_COST_LIMIT=48
```

Progress-aware stop policy:

- Strict wall cap: `25` minutes.
- Stop early on dispatch/progress cycle `>= 1801`.
- Stop early on cycle-cost sample `>= 1800`.
- Stop early on `select_kernel_current`, bind/admission, CTA launch,
  `PASSED`/`FAILED`, simulator/ProcMan exit, or sustained process-tree CPU
  time not increasing.
- Do not kill solely because stdout/stderr has not grown while the
  benchmark/simulator child remains CPU-heavy and the target simulated cycle
  has not been reached.
- Track process-tree CPU ticks for the ProcMan wrapper PID and descendants,
  not only the wrapper PID.

## Actions

1. Verified branch `dev-5060`, HEAD `6ff16fc`, ProcMan `Nothing Active`, and
   the pre-existing supervisor-log modification.
2. Created ignored artifact root under `artifacts/s7/`.
3. Added temporary alias
   `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`
   containing only the `37/10` candidate overrides.
4. Ran setup-only planning for
   `RTX5060_SM120_GEN-S7SWEEP_L0L1_37_PREFETCH_10`; setup-only exited `0` and
   ProcMan remained `Nothing Active`.
5. Attempted one launch with an absolute custom `-r` path; it failed before
   queuing any ProcMan job because `run_simulations.py` misinterpreted the
   absolute run directory as a simulator-dir suffix. ProcMan remained
   `Nothing Active`; this did not submit or run a simulator job.
6. Submitted exactly one actual local ProcMan/simulator diagnostic: Job `15`.
7. Monitored ProcMan state, process tree, stdout/stderr size, parsed
   dispatch/progress cycles, parsed cycle-cost samples, result markers, and
   process-tree CPU ticks.
8. Stopped at the progress gate after the monitor observed dispatch cycle
   `1807`, progress cycle `1806`, cycle-cost sample `1850`,
   `select_kernel_current`, bind/admission, and CTA launch evidence.
9. Preserved stdout/stderr snapshots, monitor logs, process-tree logs,
   effective config values, and extracted diagnostic lines.
10. Killed the active ProcMan job after preserving stop artifacts, verified
    final ProcMan `Nothing Active`, and removed the temporary alias.
11. Did not run metric ingestion, S6 search/report generation, config
    generation for promotion, calibration-result generation, hardware target
    collection, or promotion commands.

## Setup And Effective Config Evidence

Important setup artifacts:

- `logs/setup-only.log`
- `logs/setup-only.exitcode`
- `logs/procman-after-setup-only.log`
- `logs/temp-alias-content.yml`
- `logs/run-effective-config-values.txt`
- `logs/run-effective-gpgpusim.config`

Setup-only exit code:

```text
0
```

ProcMan after setup-only:

```text
Nothing Active
```

Actual run effective config values:

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

- `logs/run-submit-actual.log`
- `logs/run-submit-actual.exitcode`
- `logs/procman-immediate-actual.log`
- `logs/monitor.log`
- `logs/process-tree-poll-*.log`
- `logs/procman-poll-*.log`
- `logs/key-lines-poll-*.txt`
- `logs/procman-at-stop-gate.log`
- `logs/process-tree-at-stop-gate.log`
- `logs/stdout-at-stop.o15`
- `logs/stderr-at-stop.e15`
- `logs/startup-lines.txt`
- `logs/dispatch-lines.txt`
- `logs/progress-lines.txt`
- `logs/cycle-cost-lines.txt`
- `logs/cycle-cost-summary.txt`
- `logs/milestone-lines.txt`
- `logs/run-summary.json`
- `logs/stop-reason.txt`
- `logs/procman-manual-kill.log`
- `logs/procman-final.log`
- `logs/temp-alias-final.log`

Run submission:

```text
ProcMan spawned [pid=3698241]
Job 15 queued (backprop-rodinia-2.0-ft-4096___data_result_4096_txt RTX5060_SM120_GEN-S7SWEEP_L0L1_37_PREFETCH_10)
```

ProcMan immediate state:

```text
queuedJobs=0, activeJobs=1, completeJobs=0
status=RUNNING
procId=3698245
```

Stop-decision monitor line:

```text
poll=25 elapsed=508 wrapper_pids=[3698245] tree_pids=[3698245, 3698246] stdout_size=592545 stderr_size=3212 size_delta=297677 cpu_ticks=1847665 cpu_delta=93602 max_dispatch=1807 max_progress=1806 max_cycle_cost=1850 select_current=True bind=True cta_launch=True passed_failed=False
```

Stop reason:

```text
dispatch_or_progress_cycle_ge_1801
```

Process-tree CPU evidence at stop:

```text
3698245 ... pcpu=0.0  time=00:00:00 slurm.sim
3698246 ... pcpu=2615 time=05:31:33 backprop-rodinia-2.0-ft 4096 ./data/result-4096.txt
```

Monitor process-tree CPU ticks increased at every poll. Examples:

```text
poll=00 cpu_ticks=1147405
poll=10 cpu_ticks=1366600 cpu_delta=18557
poll=20 cpu_ticks=1580876 cpu_delta=19213
poll=25 cpu_ticks=1847665 cpu_delta=93602
```

Short stdout gaps were tolerated while child CPU time increased, for example:

```text
poll=02 size_delta=0 cpu_delta=17683 max_cycle_cost=1200
poll=03 size_delta=959 cpu_delta=24086 max_cycle_cost=1250
poll=14 size_delta=0 cpu_delta=24865 max_cycle_cost=1450
poll=15 size_delta=968 cpu_delta=21187 max_cycle_cost=1500
```

ProcMan at stop gate still showed the job `RUNNING`; manual cleanup killed it.
Final cleanup:

```text
logs/procman-final.log: Nothing Active
logs/temp-alias-final.log: empty; no temporary alias path remains
```

## Key Diagnostic Evidence

Startup diagnostics were captured (`46` lines), confirming the run passed
runtime/device init, config and trace parsing, GPU and stream-manager creation,
simulator-thread startup, function registration, CUDA launch/grid init, stream
push, and simulator-thread work detection.

Pre-admission samples advanced past Job `14`:

```text
GPGPUSIM-CYCLE-COST cycle=1200 ... tb_latency=599 ... cta_launched_kernel=0 active_sms=0
GPGPUSIM-CYCLE-COST cycle=1450 ... tb_latency=349 ... cta_launched_kernel=0 active_sms=0
GPGPUSIM-CYCLE-COST cycle=1750 ... tb_latency=49  ... cta_launched_kernel=0 active_sms=0
```

The run then crossed the expected admission point:

```text
GPGPUSIM-DISPATCH-BIND cycle=1801 ... stage=select_kernel_current ... tb_latency=0
GPGPUSIM-DISPATCH-BIND cycle=1801 ... stage=cluster_set_kernel cluster=0 sm=0 ...
GPGPUSIM-DISPATCH-BIND cycle=1801 ... stage=sm_set_kernel sm=0 ...
GPGPU-Sim uArch: Shader 0 bind to kernel 1 '_Z22bpnn_layerforward_CUDAPfS_S_S_ii'
GPGPUSIM-DISPATCH-BIND cycle=1801 ... stage=cluster_issue_cta_to_sm cluster=0 sm=0 ...
GPGPUSIM-DISPATCH-BIND cycle=1801 ... stage=sm_issue_block_done ... active_cta=1 ... detail=cta_initialized
GPGPUSIM-DISPATCH-BIND cycle=1801 ... stage=issue_block2core_cluster_issued ... cta_launched_kernel=1
```

Progress diagnostics after admission:

```text
GPGPUSIM-K2-PROGRESS cycle=1801 ... cta_launched_kernel=30  active_cta=30  active_sms=30 ... pc=0x2400
GPGPUSIM-K2-PROGRESS cycle=1802 ... cta_launched_kernel=60  active_cta=60  active_sms=30 ... pc=0x2400
GPGPUSIM-K2-PROGRESS cycle=1806 ... cta_launched_kernel=180 active_cta=180 active_sms=30 ... pc=0x2400
```

At the monitor stop decision:

- Max dispatch cycle: `1807`.
- Max progress cycle: `1806`.
- Max cycle-cost sample: `1850`.
- `select_kernel_current`: observed.
- Bind/admission: observed.
- CTA launch: observed.
- Result/PASSED/FAILED: not observed.
- Metrics/result file: not produced.
- Simulator exit: not observed before manual cleanup.

Because the simulator was still running while stop artifacts were copied, the
preserved stdout snapshot contains additional lines beyond the monitor stop
decision: max dispatch `2007` and max cycle-cost `2000`. These later snapshot
lines are useful as extra evidence but are not the stop decision. The snapshot
shows the run had reached `cta_launched_kernel=180`, `active_sms=30`, and
`cluster_cta_admission_blocked ... detail=can_issue_1block_false` for the
remaining clusters at cycle `2007`.

## Cycle-Cost Summary

Preserved stdout contains `43` cycle-cost samples through cycle `2000`.
Aggregate sampled cost:

```text
total=2263123 us
cluster_core=2068888 us (91.417391% of total)
interconnect_memory=168177 us (7.431191% of total)
issue_block2core=25487 us (1.126187% of total)
diagnostic_emission=347 us (0.015333% of total)
stats_bookkeeping=114 us (0.005037% of total)
decrement_kernel_latency=1 us (0.000044% of total)
```

Aggregate refined `cluster_core_detail`:

```text
calls=1260
core_cycle_us=15989
non_core_cycle_residual_us=2050959
loop_accounted_us=17929
eligibility_us=1933
get_not_completed_calls=1260
get_not_completed_us=1555
get_more_cta_left_calls=1260
get_more_cta_left_true=1260
get_more_cta_left_us=378
not_completed_core_cycle_calls=120
inactive_core_cycle_calls=1140
not_completed_core_cycle_us=13134
inactive_core_cycle_us=2855
not_completed_clusters=120
more_cta_clusters=1260
active_sms_scan_calls=1260
active_sms_scan_us=7
accelwattch_stats_us=0
```

Interpretation:

- Job `15` confirms Job `14` was stopped prematurely by policy: with child
  process-tree CPU tracking and no short stdout-gap kill, the same candidate
  point progressed from cycle `200` to the intended `1800/1801` window.
- The deeper pre-admission samples still show `cluster_core` dominated by
  conservative residual, while direct eligibility and inactive-core body time
  remain small.
- At cycle `1801`, TB latency reaches zero and the simulator normally selects
  the kernel, binds shaders, initializes CTAs, and launches CTAs. This rules
  out a pre-admission semantic deadlock for `candidate_0002` in this diagnostic
  window.
- This does not prove calibration quality, full benchmark completion, or
  post-admission correctness. The run was intentionally stopped after the
  diagnostic progress gate and produced no result or metrics.

## Changed Files

Tracked documentation added by this worker:

- `docs/sm120-calibration/worker-logs/worker-20260613-015927-s7-candidate0002-progress-aware-rerun.md`

Temporary file created and removed:

- `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`

Ignored artifacts created:

- `artifacts/s7/s7-candidate0002-progress-aware-rerun-20260613-015927/`

Pre-existing tracked modification still present and not edited:

- `docs/sm120-calibration/supervisor-log.md`

## Validation

Commands:

```bash
git diff --check
PYTHONDONTWRITEBYTECODE=1 python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
python3 simulator-remodeled/util/job_launching/procman.py -p
find /home/xiewx/accel-0608 -name 'define-s7-bounded-sweep-temp.yml' -print
git status --short -- simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated simulator-remodeled/gpu-simulator/configs/generated simulator-remodeled/gpu-simulator/gpgpu-sim/configs/tested-cfgs simulator-remodeled/gpu-simulator/configs/tested-cfgs simulator-remodeled/gpu-simulator/gpgpu-sim/configs/accepted simulator-remodeled/gpu-simulator/configs/accepted simulator-remodeled/gpu-simulator/gpgpu-sim/configs/latest simulator-remodeled/gpu-simulator/configs/latest simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/calibration-results
```

Results:

- `git diff --check`: passed.
- `generate_sm120_configs.py --check-only`: passed.
- Final ProcMan state: `Nothing Active`.
- Temporary alias final scan: empty; no
  `define-s7-bounded-sweep-temp.yml` remained under `/home/xiewx/accel-0608`.
- Protected generated/tested/accepted/latest config and calibration-result
  paths were clean.
- Tracked worktree changes after validation were limited to this new worker log
  plus the pre-existing supervisor-log modification.

## Reviewer Rounds

### Round 1

Blank-context reviewer:

- Primary multi-agent spawn attempt failed twice with `agent thread limit
  reached`.
- Fallback reviewer was run as a separate local blank-context `codex exec`
  process in read-only sandbox mode.
- Reviewer artifact:
  `artifacts/s7/s7-candidate0002-progress-aware-rerun-20260613-015927/logs/internal-reviewer-round1.log`
- Verdict: `ACCEPT`

Reviewer summary:

- Exactly one actual ProcMan/simulator run is supported: Job `15`. The earlier
  failed launch attempt happened before job queueing and left ProcMan
  `Nothing Active`.
- Effective run config includes appended active overrides
  `-latency_L0_to_L1 37` and `-prefetch_per_stream_buffer_size 10`.
- Progress-aware stop hit `dispatch_or_progress_cycle_ge_1801` at monitor poll
  `25`, with dispatch `1807`, progress `1806`, cycle-cost `1850`,
  bind/admission, and CTA launch observed.
- Process-tree CPU tracking included wrapper and child PIDs, with CPU ticks
  increasing through the stop gate.
- Cycle-cost diagnostics used interval `50` and include refined
  `cluster_core_detail`.
- Final ProcMan state is `Nothing Active`; the temporary alias is absent.
- Protected config/result/S6/metrics/hardware/promotion paths are clean.
- Current tracked status shows only the pre-existing supervisor-log
  modification plus this new worker log.

No rework was required.

## No-Promotion Confirmation

- No accepted config was modified.
- No generated config was modified.
- No latest config was modified.
- No calibration result was modified.
- No persistent job alias was modified.
- No S6 search/report was run.
- No candidate metrics were generated.
- No hardware target metrics were generated.
- No promotion artifacts were generated.
- Temporary alias was removed before final state.
- Final ProcMan state is `Nothing Active`.

## Final Recommendation

Final status: diagnostic complete and accepted by internal reviewer.

Do not promote `candidate_0002`.

The progress-aware rerun replaces Job `14` as the better diagnostic execution
artifact for this question. It shows the same `37/10` candidate point can
progress through the intended `1800/1801` window when monitored by simulated
cycle and child process-tree CPU time rather than short stdout-growth gaps. It
also shows normal kernel selection, bind/admission, and CTA launch at cycle
`1801`.

This remains diagnostic evidence only. The run was intentionally stopped after
the progress gate, produced no result or metrics, and does not establish full
benchmark completion, calibration quality, or post-admission correctness.
