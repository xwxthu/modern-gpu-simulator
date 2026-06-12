# S7 Candidate 0002 Residual-Attribution Diagnostic Worker Log

## Purpose

Run exactly one bounded local ProcMan diagnostic for bounded-sweep
`candidate_0002` using the refined `cluster_core` residual attribution fields
from checkpoint `d04d17a`.

This was diagnostic execution only. It was not calibration promotion, not an
S6 search/correlation run, and not a candidate-metrics generation run.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base checkpoint: `d04d17af6a3eff535a1b86f2d52e1f28637c9e5d`
  (`feat: refine cluster-core residual diagnostics`)
- Start timestamp: `2026-06-13T01:17:18+08:00`
- Worker-log draft timestamp: `2026-06-13T01:26:16+08:00`
- Host: `dsp-ubuntu`
- Artifact root:
  `artifacts/s7/s7-candidate0002-residual-attribution-diagnostic-20260613-011718/`
- Actual local ProcMan jobs submitted by this worker: exactly one, Job `14`

Initial tracked worktree state:

- Branch `dev-5060`, ahead of origin.
- Pre-existing tracked modification:
  `docs/sm120-calibration/supervisor-log.md`.

No source code files were edited by this worker.

## Mandatory Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/worker-logs/worker-20260613-003250-s7-cluster-core-residual-attribution.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-235505-s7-candidate0002-cluster-core-detail-diagnostic.md`
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
GPGPUSIM_CYCLE_COST_LIMIT=24
```

Stop gates:

- cycle `1801` or `select_kernel_current`,
- first bind / CTA launch,
- no output growth despite a CPU-heavy child process,
- repeated state without useful cycle progress,
- ProcMan stale/failure,
- strict wall cap no more than 25 minutes.

Actual stop gate:

```text
no-output-growth-child-cpu-heavy-repeated-early-pre-admission-state
```

The run was manually stopped after repeated no-output-growth polls. The monitor
tracked the ProcMan shell wrapper for CPU, but separate process-tree evidence
showed the child benchmark/simulator process CPU-heavy (`pcpu=931`) while stdout
remained unchanged and max observed cycle stayed at the early pre-admission
window.

## Actions

1. Verified HEAD `d04d17a`, branch `dev-5060`, ProcMan `Nothing Active`, and
   the pre-existing supervisor-log modification.
2. Created ignored artifact root under `artifacts/s7/`.
3. Added temporary alias
   `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`
   containing only `S7SWEEP_L0L1_37_PREFETCH_10`.
4. Ran setup-only planning for
   `RTX5060_SM120_GEN-S7SWEEP_L0L1_37_PREFETCH_10`; setup-only exited `0` and
   ProcMan remained `Nothing Active`.
5. Confirmed the release shared object contained the refined field names
   (`loop_accounted_us`, `eligibility_us`, `get_more_cta_left_calls`,
   `inactive_core_cycle_us`) before launching the actual job. The launcher
   banner still printed an older build-label commit
   `e3de9d2..._modified_3.0`; the binary string evidence confirms the runtime
   library had the refined `d04d17a` diagnostic format.
6. Submitted exactly one actual local ProcMan job, Job `14`, with startup,
   dispatch/progress, and refined cycle-cost diagnostics enabled.
7. Monitored ProcMan state, process tree, stdout/stderr growth, diagnostic
   lines, result files, and stop gates.
8. Stopped after repeated no-output-growth polls with a CPU-heavy child
   process and no useful cycle progress past the early pre-admission window.
9. Preserved stdout/stderr snapshots and key extracted diagnostic files.
10. Killed the active ProcMan job, verified final ProcMan `Nothing Active`, and
    removed the temporary alias.
11. Did not run metric ingestion, S6 search/report generation, config
    generation for promotion, calibration-result generation, hardware target
    collection, or promotion commands.

## Setup And Effective Config Evidence

Important setup artifacts:

- `logs/setup-only.log`
- `logs/setup-only.exitcode`
- `logs/procman-after-setup-only.log`
- `logs/rendered-config-paths.txt`
- `logs/effective-config-values.txt`
- `logs/effective-gpgpusim.config`
- `logs/refined-field-binary-evidence.txt`
- `logs/run-effective-config-values.txt`

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

Binary refined-field evidence:

```text
cluster_core_detail={calls=%llu,core_cycle_us=%llu,non_core_cycle_residual_us=%llu,loop_accounted_us=%llu,eligibility_us=%llu,get_not_completed_calls=%llu,get_not_completed_us=%llu,get_more_cta_left_calls=%llu,get_more_cta_left_true=%llu,get_more_cta_left_us=%llu,not_completed_core_cycle_calls=%llu,inactive_core_cycle_calls=%llu,not_completed_core_cycle_us=%llu,inactive_core_cycle_us=%llu,not_completed_clusters=%llu,more_cta_clusters=%llu,active_sms_scan_calls=%llu,active_sms_scan_us=%llu,accelwattch_stats_us=%llu}
```

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
- `logs/procman-at-manual-stop-gate.log`
- `logs/process-tree-at-manual-stop.log`
- `logs/process-poll-manual-stop.log`
- `logs/stdout-at-manual-stop.o14`
- `logs/stderr-at-manual-stop.e14`
- `logs/key-diagnostic-lines.txt`
- `logs/startup-lines.txt`
- `logs/dispatch-lines.txt`
- `logs/progress-lines.txt`
- `logs/cycle-cost-lines.txt`
- `logs/cycle-cost-summary.txt`
- `logs/result-files-at-stop.txt`
- `logs/procman-manual-kill.log`
- `logs/procman-after-manual-stop.log`
- `logs/procman-final.log`
- `logs/temp-alias-final.log`

Run submission evidence:

```text
Job 14 queued (backprop-rodinia-2.0-ft-4096___data_result_4096_txt RTX5060_SM120_GEN-S7SWEEP_L0L1_37_PREFETCH_10)
```

ProcMan immediate state:

```text
queuedJobs=0, activeJobs=1, completeJobs=0
status=RUNNING
```

Monitor summary:

```text
poll_elapsed=0   stdout_size=195740 max_cycle=1 detail=True select_current=False bind=False cta_launch=False result=none no_growth_polls=0
poll_elapsed=20  stdout_size=195740 max_cycle=1 detail=True select_current=False bind=False cta_launch=False result=none no_growth_polls=1
poll_elapsed=40  stdout_size=195740 max_cycle=1 detail=True select_current=False bind=False cta_launch=False result=none no_growth_polls=2
poll_elapsed=61  stdout_size=195740 max_cycle=1 detail=True select_current=False bind=False cta_launch=False result=none no_growth_polls=3
poll_elapsed=81  stdout_size=195740 max_cycle=1 detail=True select_current=False bind=False cta_launch=False result=none no_growth_polls=4
poll_elapsed=101 stdout_size=195740 max_cycle=1 detail=True select_current=False bind=False cta_launch=False result=none no_growth_polls=5
poll_elapsed=122 stdout_size=195740 max_cycle=1 detail=True select_current=False bind=False cta_launch=False result=none no_growth_polls=6
```

Manual stop process evidence:

```text
3379431 ... /bin/bash .../slurm.sim
3379432 ... pcpu=931 ... backprop-rodinia-2.0-ft 4096 ./data/result-4096.txt
```

Stop evidence:

```text
stop_reason=no-output-growth-child-cpu-heavy-repeated-early-pre-admission-state
job_id=14
max_observed_dispatch_cycle=201
max_cycle_cost_sample=200
select_kernel_current=False
bind_or_admission=False
cta_launch=False
cycle_cost_samples=3
startup_lines=46
dispatch_lines=69
progress_lines=2
result_files_present=False
```

No `result.txt` was present at stop. Final cleanup:

```text
logs/procman-final.log: Nothing Active
logs/temp-alias-final.log: empty; no temporary alias path remains
```

## Key Startup, Dispatch, And Progress Evidence

Startup diagnostics were captured (`46` startup lines) and confirm the run
passed runtime/device init, config and trace parsing, GPU/stream-manager
creation, simulator-thread startup, function registration, CUDA launch/grid
init, stream push, and simulator-thread work detection.

Dispatch/progress evidence stayed pre-admission:

```text
GPGPUSIM-DISPATCH-BIND cycle=0 ... stage=stream_kernel_launch_wait ... detail=launch_latency ... launch_latency=1799,tb_latency=1800
GPGPUSIM-DISPATCH-BIND cycle=0 ... stage=stream_kernel_launch_to_gpu ... launch_latency=0,tb_latency=1800
GPGPUSIM-DISPATCH-BIND cycle=0 ... stage=gpu_launch_insert ... detail=inserted_running_slot ... tb_latency=1800
GPGPUSIM-DISPATCH-BIND cycle=1 ... stage=select_kernel_none ... detail=tb_latency_pending ... next_cta=0,num_cta=256
GPGPUSIM-K2-PROGRESS cycle=1 ... cta_launched_kernel=0 ... active_sms=0 ...
GPGPUSIM-DISPATCH-BIND cycle=201 ... stage=select_kernel_none ... detail=tb_latency_pending ... tb_latency=1600
GPGPUSIM-CYCLE-COST cycle=200 ... tb_latency_pending_kernels=1 ... active_sms=0 ...
```

No `select_kernel_current`, `Shader N bind`, `cluster_set_kernel`,
`sm_set_kernel`, `cluster_issue_cta_to_sm`, `sm_issue_block_done`, or positive
`cta_launched_kernel` line was observed.

## Cycle-Cost Refined Field Summary

Captured sampled cycle-cost lines:

```text
GPGPUSIM-CYCLE-COST cycle=0 ... cost_us={... interconnect_memory=476838,cluster_core=181007,... total=658205} cluster_core_detail={calls=30,core_cycle_us=6,non_core_cycle_residual_us=180992,loop_accounted_us=15,eligibility_us=9,get_not_completed_calls=30,get_not_completed_us=4,get_more_cta_left_calls=30,get_more_cta_left_true=30,get_more_cta_left_us=5,not_completed_core_cycle_calls=0,inactive_core_cycle_calls=30,not_completed_core_cycle_us=0,inactive_core_cycle_us=6,not_completed_clusters=0,more_cta_clusters=30,active_sms_scan_calls=30,active_sms_scan_us=0,accelwattch_stats_us=0}
GPGPUSIM-CYCLE-COST cycle=1 ... cost_us={... interconnect_memory=26,cluster_core=224942,... total=225052} cluster_core_detail={calls=30,core_cycle_us=1,non_core_cycle_residual_us=224939,loop_accounted_us=3,eligibility_us=2,get_not_completed_calls=30,get_not_completed_us=1,get_more_cta_left_calls=30,get_more_cta_left_true=30,get_more_cta_left_us=1,not_completed_core_cycle_calls=0,inactive_core_cycle_calls=30,not_completed_core_cycle_us=0,inactive_core_cycle_us=1,not_completed_clusters=0,more_cta_clusters=30,active_sms_scan_calls=30,active_sms_scan_us=0,accelwattch_stats_us=0}
GPGPUSIM-CYCLE-COST cycle=200 ... cost_us={... interconnect_memory=35,cluster_core=219813,issue_block2core=42282,... total=262144} cluster_core_detail={calls=30,core_cycle_us=2,non_core_cycle_residual_us=219805,loop_accounted_us=8,eligibility_us=6,get_not_completed_calls=30,get_not_completed_us=4,get_more_cta_left_calls=30,get_more_cta_left_true=30,get_more_cta_left_us=2,not_completed_core_cycle_calls=0,inactive_core_cycle_calls=30,not_completed_core_cycle_us=0,inactive_core_cycle_us=2,not_completed_clusters=0,more_cta_clusters=30,active_sms_scan_calls=30,active_sms_scan_us=0,accelwattch_stats_us=0}
```

Aggregate over the three sampled cost records:

- `total`: `1145401 us`
- `cluster_core`: `625762 us`, `54.632570%` of sampled total
- `interconnect_memory`: `476899 us`, `41.635986%`
- `issue_block2core`: `42674 us`, `3.725682%`
- `diagnostic_emission`: `35 us`, `0.003056%`
- `stats_bookkeeping`: `19 us`, `0.001659%`
- `decrement_kernel_latency`: `1 us`, `0.000087%`

Aggregate refined detail:

- `calls`: `90`, exactly `30` sampled cluster/core calls per emitted sample.
- `core_cycle_us`: `9 us`.
- `inactive_core_cycle_calls`: `90`.
- `inactive_core_cycle_us`: `9 us`.
- `not_completed_core_cycle_calls`: `0`.
- `not_completed_core_cycle_us`: `0 us`.
- `not_completed_clusters`: `0`.
- `more_cta_clusters`: `90`, exactly `30` per emitted sample.
- `get_not_completed_calls`: `90`, `get_not_completed_us`: `9 us`.
- `get_more_cta_left_calls`: `90`, `get_more_cta_left_true`: `90`,
  `get_more_cta_left_us`: `8 us`.
- `eligibility_us`: `17 us`, matching `get_not_completed_us +
  get_more_cta_left_us`.
- `active_sms_scan_calls`: `90`, `active_sms_scan_us`: `0 us`.
- `accelwattch_stats_us`: `0 us`.
- `loop_accounted_us`: `26 us`.
- `non_core_cycle_residual_us`: `625736 us`, `99.995845%` of sampled
  `cluster_core`.
- Derived arithmetic: `accounted_detail_us=26`, and
  `non_core_cycle_residual_us + accounted_detail_us == cluster_core`.

Interpretation:

- This run did not reach the intended cycle `1200` window; output stopped after
  the cycle `200` sample while the child process remained CPU-heavy.
- The captured state is still pre-admission TB-latency countdown:
  no selected kernel, no bind/admission, no CTA launch, and no active SMs.
- Within the captured samples, refined fields keep attributing the sampled
  `cluster_core` wall bucket almost entirely to
  `non_core_cycle_residual_us`, while direct eligibility scans and inactive
  `core_cycle()` body time are tiny.
- `more_cta_clusters=90` and `get_more_cta_left_true=90` show every sampled
  cluster entered because CTAs remained, even though TB latency still prevented
  admission.
- Because only three sampled records were captured and the run stopped at cycle
  `201` for dispatch/progress evidence, with the final cycle-cost sample at
  `200`, this is weaker than the requested through-cycle-1200 evidence and
  should be treated as an early-stop diagnostic, not a replacement for the
  previous cycle-1200 cluster-core-detail run.

## Changed Files

Tracked documentation added by this worker:

- `docs/sm120-calibration/worker-logs/worker-20260613-012616-s7-candidate0002-residual-attribution-diagnostic.md`

Temporary file created and removed:

- `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`

Ignored artifacts created:

- `artifacts/s7/s7-candidate0002-residual-attribution-diagnostic-20260613-011718/`

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
- Temporary alias final state: absent.
- Artifact root is ignored by `.gitignore`.
- Protected generated/tested/accepted/latest config and calibration-result
  paths were clean.
- Scan for metrics/S6/report/promotion files under the artifact root was empty.

## Reviewer Rounds

### Round 1

Blank-context reviewer agent:

- Agent: `019ebce0-ba3d-7d50-b11b-03cae48d81ab`
- Verdict: `CHANGES_NEEDED`

Blocking findings:

- Replace the `Pending blank-context reviewer` placeholder with the completed
  reviewer round.
- Replace the draft final-status language with a final worker status after
  reviewer acceptance.

Reviewer verification notes:

- Exactly one local ProcMan job is supported: Job `14`.
- Candidate params `37/10` are evidenced in setup and run config values.
- Refined `d04d17a` fields are evidenced in binary strings and runtime
  `GPGPUSIM-CYCLE-COST` lines.
- Stop reason, max cycle `200`, no bind/admission/CTA launch, no result, and
  early-stop caveat are supported by artifacts.
- Final ProcMan cleanup, alias removal, protected-path cleanliness, and no
  metrics/S6/report/promotion artifact findings are supported.

Rework:

- Updated this reviewer section with the Round 1 result.
- Replaced the final recommendation draft wording with a reworked final-status
  section pending a fresh reviewer acceptance.

### Round 2

Blank-context reviewer agent:

- Agent: `019ebce3-282f-7ac0-90cd-647d40efcc80`
- Verdict: `CHANGES_NEEDED`

Blocking findings:

- The log still ended with Round 2 reviewer acceptance pending.
- The log used `max_observed_cycle=200`, but runtime artifacts also contained
  dispatch evidence at cycle `201`; cycle `200` was only the maximum
  cycle-cost sample.

Reviewer verification notes:

- Exactly one local ProcMan job is supported: Job `14`.
- Candidate params `37/10` are evidenced.
- Refined `d04d17a` fields are evidenced in binary strings and runtime output.
- Stop reason, no result, no bind/admission/CTA launch, and early-stop caveat
  are broadly supported.
- Final ProcMan state, alias cleanup, and no-promotion scans are supported.

Rework:

- Updated `logs/stop-summary.txt` to distinguish
  `max_observed_dispatch_cycle=201` from `max_cycle_cost_sample=200`.
- Updated this worker log to use the same distinction in stop evidence,
  dispatch evidence, and interpretation.
- Recorded the Round 2 reviewer result.

### Round 3

Blank-context reviewer agent:

- Agent: `019ebce6-2d48-7073-bd7d-4d30fe0a1609`
- Verdict: `ACCEPT`

Reviewer summary:

- Exactly one ProcMan job is supported: Job `14`.
- Candidate params `37/10` are evidenced in setup and run config values.
- Refined `d04d17a` fields are present in binary/output artifacts.
- Stop evidence distinguishes `max_observed_dispatch_cycle=201` from
  `max_cycle_cost_sample=200`, with no bind/admission/CTA launch and no result
  files.
- Cleanup is supported by final ProcMan `Nothing Active` and empty temporary
  alias scan.
- No promotion artifacts were found.
- Round 1 and Round 2 findings were addressed.

Residual limitation:

- This remains an early-stop diagnostic only. It captured dispatch evidence
  through cycle `201` and cycle-cost samples through cycle `200`, not the
  intended cycle `1200` or CTA admission/bind window.

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

The refined fields captured in Job `14` still point to the conservative
`non_core_cycle_residual_us` bucket inside pre-admission `cluster_core`, with
direct eligibility and inactive-core body time negligible in the sampled window.
However, this run only reached dispatch evidence through cycle `201` and
cycle-cost evidence through cycle `200`, instead of capturing through at least
cycle `1200`, so the result should be treated as a bounded early-stop
diagnostic rather than a full replacement for the prior enhanced cluster-core
evidence.
