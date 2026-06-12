# S7 Candidate 0002 Startup Diagnostic Worker Log

## Purpose

Run exactly one bounded local ProcMan diagnostic for bounded-sweep
`candidate_0002` with newly added startup instrumentation enabled, to localize
the prior CPU-heavy silent path.

This was not a metrics run and not a promotion run.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base checkpoint: `984f64f` (`feat: add startup diagnostics`)
- Timestamp: `2026-06-12T21:35:51+08:00`
- Host: `dsp-ubuntu`
- Artifact root:
  `artifacts/s7/s7-candidate0002-startup-diagnostic-20260612-213551/`
- Actual local ProcMan jobs submitted: exactly one, Job `10`

Pre-existing tracked modification observed and not edited except by its owner:

- `docs/sm120-calibration/supervisor-log.md`

## Mandatory Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-204302-s7-candidate0002-bounded-diagnostic.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-211509-s7-startup-debug-instrumentation.md`
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
```

Stop gates:

- normal startup-to-dispatch-to-progress path observed,
- repeated unchanged startup/output state,
- no stderr/stdout growth despite CPU-heavy process,
- ProcMan stale/failure,
- wall time no more than 15 minutes.

The actual stop gate was:

```text
normal-startup-dispatch-progress-observed
```

## Actions

1. Verified checkpoint `984f64f`, branch state, and initial ProcMan state.
   ProcMan started as `Nothing Active`.
2. Created ignored artifact root under `artifacts/s7/`.
3. Added temporary alias
   `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`
   containing only `S7SWEEP_L0L1_37_PREFETCH_10`.
4. Ran setup-only planning for `RTX5060_SM120_GEN-S7SWEEP_L0L1_37_PREFETCH_10`.
   Setup-only exited `0`.
5. Submitted exactly one actual local ProcMan job, Job `10`, with startup,
   dispatch, and progress diagnostics enabled.
6. Monitored ProcMan, process state, stdout/stderr growth, diagnostic key
   lines, and result-file presence.
7. Stopped immediately after the first monitor poll because startup, dispatch,
   and progress diagnostics were all observed.
8. Manually cleaned ProcMan, removed the temporary alias, and verified final
   ProcMan state is `Nothing Active`.
9. Did not run any candidate-metrics ingestion, S6 scorer, config generation,
   calibration-result generation, or promotion command.

## Setup And Effective Config Evidence

Important setup artifacts:

- `logs/start-state.txt`
- `logs/setup-only.log`
- `logs/setup-only.exitcode`
- `logs/procman-after-setup-only.log`
- `logs/effective-config-values.txt`

Setup-only exit code:

```text
0
```

Effective config evidence:

```text
64:-gpgpu_clock_domains 2640:2640:2640:14000
217:-latency_L0_to_L1 39
304:-is_instruction_prefetching_enabled 1
305:-prefetch_per_stream_buffer_size 8
349:-latency_L0_to_L1 37 -prefetch_per_stream_buffer_size 10
```

The base generated config still records bootstrap `39/8`; the temporary
extra-params override appended the active `37/10` candidate values.

## ProcMan And Runtime Evidence

Important runtime artifacts:

- `logs/run-submit.log`
- `logs/run-submit.exitcode`
- `logs/procman-immediate.log`
- `logs/monitor.log`
- `logs/procman-at-stop-gate.log`
- `logs/process-at-stop-gate.log`
- `logs/procman-manual-kill.log`
- `logs/procman-after-manual-stop.log`
- `logs/procman-final-cleanup-kill.log`
- `logs/procman-final.log`
- `logs/temp-alias-final.log`

Run submission evidence:

```text
Job 10 queued (backprop-rodinia-2.0-ft-4096___data_result_4096_txt RTX5060_SM120_GEN-S7SWEEP_L0L1_37_PREFETCH_10)
```

The first monitor poll recorded the job in `RUNNING` with stdout and stderr
growth:

```text
elapsed=0 status=RUNNING ... out=193769 out_lines=1561 ... err=3153 err_lines=47 startup_lines=45 dispatch_lines=37 progress_lines=2 result=none
stop_reason=normal-startup-dispatch-progress-observed
```

Process evidence at the stop gate showed the simulator child was CPU-heavy:

```text
procId=916538 ... runningTime=0:00:30 ...
backprop-rodinia-2.0-ft ... %CPU 1287 ... RSS 262496
```

No `result.txt` was present:

```text
logs/result-files.txt: empty
```

Final cleanup state:

```text
logs/procman-final.log: Nothing Active
logs/temp-alias-final.log: empty
```

## Key Startup Evidence

Startup diagnostics appeared immediately on stderr. Important lines from
`logs/key-startup-lines.txt` include:

```text
GPGPUSIM-STARTUP enabled (env:GPGPUSIM_STARTUP_DEBUG)
GPGPUSIM-STARTUP stage=runtime_init_enter
GPGPUSIM-STARTUP stage=init_perf_enter config=gpgpusim.config
GPGPUSIM-STARTUP stage=option_parse_done config=gpgpusim.config
GPGPUSIM-STARTUP stage=gpu_config_init_done
GPGPUSIM-STARTUP stage=trace_config_parse_done
GPGPUSIM-STARTUP stage=gpu_created ptr=...
GPGPUSIM-STARTUP stage=stream_manager_created cuda_launch_blocking=1
GPGPUSIM-STARTUP stage=start_sim_thread_done api=1
GPGPUSIM-STARTUP stage=runtime_init_done device=...
GPGPUSIM-STARTUP stage=sim_thread_concurrent_enter
GPGPUSIM-STARTUP stage=register_function_done ... deviceFun=_Z22bpnn_layerforward_CUDAPfS_S_S_ handle=1
GPGPUSIM-STARTUP stage=cuda_launch_enter ...
GPGPUSIM-STARTUP stage=cuda_launch_config_ready ... grid=(1,256,1) block=(16,16,1)
GPGPUSIM-STARTUP stage=grid_init_finalize_done kernel_uid=1 kernel=_Z22bpnn_layerforward_CUDAPfS_S_S_ii
GPGPUSIM-STARTUP stage=cuda_launch_grid_init_done ... kernel_uid=1 kernel=_Z22bpnn_layerforward_CUDAPfS_S_S_ii
GPGPUSIM-STARTUP stage=sim_thread_work_detected sim_done=0
```

This localizes the prior pre-output uncertainty past runtime/device init,
config and trace parsing, GPU/stream-manager creation, simulator thread
startup, fat-binary/function registration, CUDA launch setup, grid
initialization, stream push, and simulator-thread work detection.

## Key Dispatch And Progress Evidence

Dispatch/progress lines from `logs/key-dispatch-progress-lines.txt` include:

```text
GPGPUSIM-DISPATCH-BIND enabled interval=200 (env:GPGPUSIM_KERNEL_DISPATCH_DEBUG)
GPGPUSIM-DISPATCH-BIND cycle=0 ... stage=stream_kernel_launch_wait ... detail=launch_latency ... launch_latency=1799,tb_latency=1800
GPGPUSIM-DISPATCH-BIND cycle=0 ... stage=stream_kernel_launch_to_gpu ... launch_latency=0,tb_latency=1800
GPGPUSIM-DISPATCH-BIND cycle=0 ... stage=gpu_launch_enter ...
GPGPUSIM-DISPATCH-BIND cycle=0 ... stage=gpu_launch_insert ... detail=inserted_running_slot ...
GPGPUSIM-DISPATCH-BIND cycle=1 ... stage=issue_block2core_begin ... kernel=none
GPGPUSIM-DISPATCH-BIND cycle=1 ... stage=select_kernel_none ... detail=tb_latency_pending ... next_cta=0,num_cta=256
GPGPUSIM-DISPATCH-BIND cycle=1 ... stage=cluster_no_kernel_or_no_cta ... detail=no_cta_ready ...
GPGPUSIM-K2-PROGRESS enabled interval=1000 sm_limit=1 (env:GPGPUSIM_KERNEL_PROGRESS_DEBUG)
GPGPUSIM-K2-PROGRESS cycle=1 ... cta_launched_kernel=0 cta_completed_kernel=0 ... running_kernels=[{slot=0,uid=1,...next_cta=0,num_cta=256,running=0,done=0}] ... active_sms=0 ...
```

This shows a normal startup-to-launch-to-initial-dispatch/progress path through
kernel insertion. The observed state at stop was the expected early TB-latency
pending window before CTA admission, not the earlier no-output silent path.

## Analysis

The previous `candidate_0002` diagnostic localized only a CPU-heavy no-output
state. With startup instrumentation enabled, the same candidate produced
stderr startup lines, stdout dispatch lines, and a kernel-progress sample on
the first monitor poll.

The silent path is therefore localized as follows:

- It is not before GPGPU-Sim startup diagnostics, config parse, GPU creation,
  stream-manager creation, simulator thread start, CUDA launch, grid init, or
  stream push.
- It is not before initial dispatch/progress diagnostic emission in this run.
- The observed bounded state is kernel `uid=1` inserted and waiting on
  `tb_latency_pending` at cycle `1`, with no CTA launched yet.

This does not prove candidate `0002` will complete or avoid the later
low-latency pathology. It only closes the prior "CPU-heavy but no first
diagnostic output" uncertainty for this instrumented run.

## Changed Files

Tracked files changed by this worker:

- `docs/sm120-calibration/worker-logs/worker-20260612-213551-s7-candidate0002-startup-diagnostic.md`

Temporary file added and removed before final state:

- `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`

Ignored/local artifacts:

- `artifacts/s7/s7-candidate0002-startup-diagnostic-20260612-213551/`

Pre-existing tracked modification still present:

- `docs/sm120-calibration/supervisor-log.md`

## No-Promotion Confirmation

- No candidate metrics were generated.
- No S6 report was generated.
- No accepted/latest configs were edited.
- No generated configs were edited.
- No calibration results were generated or promoted.
- No permanent job alias was added.
- Final ProcMan state is `Nothing Active`.
- Temporary alias was removed before final state.

## Recommended Next Supervisor Action

Do not promote `candidate_0002` metrics from this diagnostic; no metrics were
generated and the run was intentionally stopped at the first bounded gate.

Recommended next action: if further localization is needed, run one deeper
bounded candidate `0002` diagnostic from this now-observed initial
`tb_latency_pending` state toward CTA admission/bind or repeated-state
detection. Keep low `-latency_L0_to_L1=37` points out of promotion until the
later low-latency slowdown/livelock risk is understood.

## Reviewer Rounds

### Round 1

- Reviewer: blank-context subagent `019ebc0f-3657-7dc2-89eb-0ca0cded41d1`
- Verdict: `ACCEPT`
- Findings: no blocking findings.
- Reviewer summary:
  - Exactly one actual ProcMan job was submitted: Job `10`.
  - Final ProcMan artifact and live check both reported `Nothing Active`.
  - Temporary alias was removed.
  - Effective runtime config used `-latency_L0_to_L1 37` and
    `-prefetch_per_stream_buffer_size 10`.
  - Startup, dispatch, and progress diagnostics were enabled and observed.
  - Stop reason `normal-startup-dispatch-progress-observed` is supported by
    the first monitor poll.
  - No result file was produced, as expected for the intentionally stopped
    diagnostic.
  - No metrics, S6 reports, calibration results, promotion artifacts, or
    permanent alias/config edits were found.
  - Localization language is appropriately bounded and does not claim
    completion or promotion readiness.
