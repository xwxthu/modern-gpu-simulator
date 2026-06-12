# S7 Candidate 0002 Deeper Dispatch Diagnostic Worker Log

## Purpose

Run exactly one deeper bounded local ProcMan diagnostic for bounded-sweep
`candidate_0002`, starting from the previously observed early
`tb_latency_pending` state and watching for CTA admission/bind, first CTA
launch, or repeated-state detection.

This was not a metrics run and not a promotion run.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base checkpoint: `ed2ab24` (`docs: record SM120 candidate0002 startup diagnostic`)
- Timestamp: `2026-06-12T21:46:28+08:00`
- Host: `dsp-ubuntu`
- Artifact root:
  `artifacts/s7/s7-candidate0002-deeper-dispatch-diagnostic-20260612-214628/`
- Actual local ProcMan jobs submitted: exactly one, Job `11`

Pre-existing tracked modification observed and not edited by this worker:

- `docs/sm120-calibration/supervisor-log.md`

## Mandatory Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-213551-s7-candidate0002-startup-diagnostic.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-201232-s7-candidate0001-final-dispatch-diagnostic.md`
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

- observe CTA admission/bind/CTA launch,
- observe repeated unchanged `tb_latency`/dispatch/progress state after enough
  samples,
- no output growth despite CPU-heavy process,
- ProcMan stale/failure,
- wall time no more than 20 minutes.

The actual stop gate was:

```text
repeated-unchanged-state
```

The job was stopped at about 3 minutes of ProcMan runtime, well under the
20-minute cap.

## Actions

1. Verified current checkpoint `ed2ab24`, clean worktree except the
   pre-existing supervisor-log modification, and initial ProcMan state
   `Nothing Active`.
2. Created ignored artifact root under `artifacts/s7/`.
3. Added temporary alias
   `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`
   containing only `S7SWEEP_L0L1_37_PREFETCH_10`.
4. Ran setup-only planning for
   `RTX5060_SM120_GEN-S7SWEEP_L0L1_37_PREFETCH_10`; setup-only exited `0`.
5. Submitted exactly one actual local ProcMan job, Job `11`, with startup,
   dispatch-bind, and progress diagnostics enabled.
6. Monitored ProcMan state, process tree, stdout/stderr growth,
   startup/dispatch/progress lines, CTA evidence, and result-file presence.
7. Stopped after repeated unchanged pre-admission dispatch/progress state was
   observed with no CTA admission/bind/launch evidence.
8. Removed the temporary alias and verified final ProcMan state is
   `Nothing Active`.
9. Did not run candidate metric ingestion, S6 search/report generation, config
   generation, calibration-result generation, or promotion commands.

## Setup And Effective Config Evidence

Important setup artifacts:

- `logs/start-state.txt`
- `logs/env-source-status.txt`
- `logs/setup-only.log`
- `logs/setup-only.exitcode`
- `logs/procman-after-setup-only.log`
- `logs/rendered-config-paths.txt`
- `logs/effective-config-values.txt`
- `logs/effective-gpgpusim.config`

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
306:-prefetch_num_stream_buffers 1
307:-num_instruction_prefetches_per_cycle 1
349:-latency_L0_to_L1 37 -prefetch_per_stream_buffer_size 10
```

The generated base config still contains bootstrap `39/8`; the temporary
extra-params override appended the active candidate values `37/10`.

## ProcMan And Runtime Evidence

Important runtime artifacts:

- `logs/run-submit.log`
- `logs/run-submit.exitcode`
- `logs/job-id.txt`
- `logs/procman-immediate.log`
- `logs/monitor.log`
- `logs/procman-poll-*.log`
- `logs/key-lines-poll-*.txt`
- `logs/startup-lines-poll-*.txt`
- `logs/key-diagnostic-lines.txt`
- `logs/process-tree-at-stop.log`
- `logs/stdout-at-stop.o11`
- `logs/stderr-at-stop.e11`
- `logs/stop-reason.txt`
- `logs/procman-at-stop-gate.log`
- `logs/procman-manual-kill.log`
- `logs/procman-after-manual-stop.log`
- `logs/procman-final-cleanup-kill.log`
- `logs/procman-final.log`
- `logs/temp-alias-final.log`

Run submission evidence:

```text
Job 11 queued (backprop-rodinia-2.0-ft-4096___data_result_4096_txt RTX5060_SM120_GEN-S7SWEEP_L0L1_37_PREFETCH_10)
```

The monitor recorded `RUNNING` state with startup, dispatch, and progress
output:

```text
poll=000 elapsed=0 status=RUNNING ... out=193722 out_lines=1561 err=3212 err_lines=48 startup_lines=46 dispatch_lines=37 progress_lines=2 bind_lines=0 cta_lines=0 result=none state="cycle=0 stage=cluster_no_kernel_or_no_cta detail=no_cta_ready"
```

Later the run emitted one more dispatch interval, still with no CTA evidence:

```text
poll=011 elapsed=115 status=RUNNING ... out=201760 out_lines=1593 err=3212 err_lines=48 startup_lines=46 dispatch_lines=69 progress_lines=2 bind_lines=0 cta_lines=0 result=none state="cycle=0 stage=cluster_no_kernel_or_no_cta detail=no_cta_ready"
poll=012 elapsed=125 status=RUNNING ... out=201760 out_lines=1593 err=3212 err_lines=48 startup_lines=46 dispatch_lines=69 progress_lines=2 bind_lines=0 cta_lines=0 result=none state="cycle=0 stage=cluster_no_kernel_or_no_cta detail=no_cta_ready"
```

Process-tree evidence at the stop gate showed the ProcMan shell wrapper plus a
CPU-heavy simulator child:

```text
1024912 ... 0.0 ... /bin/bash .../slurm.sim
1024913 ... 1373 ... backprop-rodinia-2.0-ft 4096 ./data/result-4096.txt
```

No `result.txt` was present:

```text
logs/result-files-at-stop.txt: empty
```

Final cleanup state:

```text
logs/procman-final.log: Nothing Active
logs/temp-alias-final.log: no such file or directory
```

## Key Startup Evidence

Startup diagnostics appeared on stderr. Important lines from
`logs/key-diagnostic-lines.txt` include:

```text
GPGPUSIM-STARTUP enabled (env:GPGPUSIM_STARTUP_DEBUG)
GPGPUSIM-STARTUP stage=runtime_init_enter
GPGPUSIM-STARTUP stage=option_parse_done config=gpgpusim.config
GPGPUSIM-STARTUP stage=gpu_config_init_done
GPGPUSIM-STARTUP stage=trace_config_parse_done
GPGPUSIM-STARTUP stage=gpu_created ptr=...
GPGPUSIM-STARTUP stage=stream_manager_created cuda_launch_blocking=1
GPGPUSIM-STARTUP stage=start_sim_thread_done api=1
GPGPUSIM-STARTUP stage=runtime_init_done device=...
GPGPUSIM-STARTUP stage=sim_thread_concurrent_enter
GPGPUSIM-STARTUP stage=register_function_done ... deviceFun=_Z22bpnn_layerforward_CUDAPfS_S_S_ handle=1
GPGPUSIM-STARTUP stage=cuda_launch_config_ready ... grid=(1,256,1) block=(16,16,1)
GPGPUSIM-STARTUP stage=grid_init_finalize_done kernel_uid=1 kernel=_Z22bpnn_layerforward_CUDAPfS_S_S_ii
GPGPUSIM-STARTUP stage=cuda_launch_grid_init_done ... kernel_uid=1 kernel=_Z22bpnn_layerforward_CUDAPfS_S_S_ii
GPGPUSIM-STARTUP stage=stream_manager_push_done stream=0 blocking=1
GPGPUSIM-STARTUP stage=sim_thread_work_detected sim_done=0
```

This confirms the run passed runtime/device init, config/trace parse, GPU and
stream-manager creation, simulator thread startup, function registration, CUDA
launch setup, grid initialization, stream push, and simulator-thread work
detection.

## Key Dispatch And Progress Evidence

The run reached GPU launch insertion and the same early TB-latency pending
region seen in the previous startup diagnostic:

```text
GPGPUSIM-DISPATCH-BIND cycle=0 ... stage=stream_kernel_launch_wait ... detail=launch_latency ... launch_latency=1799,tb_latency=1800
GPGPUSIM-DISPATCH-BIND cycle=0 ... stage=stream_kernel_launch_to_gpu ... launch_latency=0,tb_latency=1800
GPGPUSIM-DISPATCH-BIND cycle=0 ... stage=gpu_launch_enter ... tb_latency=1800
GPGPUSIM-DISPATCH-BIND cycle=0 ... stage=gpu_launch_insert ... detail=inserted_running_slot ... tb_latency=1800
GPGPUSIM-DISPATCH-BIND cycle=1 ... stage=select_kernel_none ... detail=tb_latency_pending ... next_cta=0,num_cta=256
GPGPUSIM-K2-PROGRESS cycle=1 ... cta_launched_kernel=0 ... running_kernels=[{slot=0,uid=1,...next_cta=0,num_cta=256,running=0,done=0}] ... active_sms=0 ...
GPGPUSIM-DISPATCH-BIND cycle=201 ... stage=select_kernel_none ... detail=tb_latency_pending ... tb_latency=1600
```

Across monitor polls, CTA evidence counters stayed absent:

```text
bind_lines=0 cta_lines=0
```

No `Shader N bind`, `cluster_set_kernel`, `sm_set_kernel`,
`cluster_issue_cta_to_sm`, `sm_issue_block_done`, or positive
`cta_launched_kernel` line was observed before stop.

## Analysis

This deeper diagnostic does not show CTA admission, SM bind, or CTA launch for
`candidate_0002`. It does show that the run again reaches kernel insertion and
early TB-latency pending:

- kernel `uid=1` is inserted into the running slot,
- `select_kernel_none detail=tb_latency_pending` appears at cycle `1`,
- a later dispatch interval at cycle `201` still reports
  `detail=tb_latency_pending` with `tb_latency=1600`,
- kernel progress remains at `cta_launched_kernel=0`, `next_cta=0`, and
  `active_sms=0`,
- the simulator child is CPU-heavy while ProcMan remains `RUNNING`.

The monitor's normalized state string stayed at
`cycle=0 stage=cluster_no_kernel_or_no_cta detail=no_cta_ready` because the
last cluster line in each sampled interval is a consequence of no ready CTA.
The more specific dispatch evidence inside the same samples identifies the
cause as pre-admission `tb_latency_pending`, not cluster admission failure.

Compared with the accepted candidate `0001` final dispatch diagnostic,
candidate `0002` did not reach the normal cycle-1801 transition to
`select_kernel_current`, `cluster_set_kernel`, `sm_set_kernel`, shader bind, or
CTA initialization within this bounded observation window. The useful result is
therefore a repeated early pre-admission state, not a post-bind diagnosis.

## Changed Files

Tracked files changed by this worker:

- `docs/sm120-calibration/worker-logs/worker-20260612-214628-s7-candidate0002-deeper-dispatch-diagnostic.md`

Temporary file added and removed before final state:

- `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`

Ignored/local artifacts:

- `artifacts/s7/s7-candidate0002-deeper-dispatch-diagnostic-20260612-214628/`

Pre-existing tracked modification still present:

- `docs/sm120-calibration/supervisor-log.md`

## No-Promotion Confirmation

- No candidate metrics were generated.
- No S6 report was generated.
- No accepted/latest config was changed.
- No generated config was changed.
- No calibration result was generated.
- No promotion artifact was generated.
- Final ProcMan state was `Nothing Active`.

## Reviewer Rounds

### Round 1

Blank-context reviewer `019ebc1b-258b-7cc1-a4f0-9249d72a33cb`
returned `ACCEPT`.

Reviewer summary:

- Exactly one actual ProcMan job is supported by `run-submit.log` and
  `logs/job-id.txt`: Job `11`.
- Diagnostics are supported by `GPGPUSIM-STARTUP`,
  `GPGPUSIM-DISPATCH-BIND`, and `GPGPUSIM-K2-PROGRESS` lines.
- Required setup, effective-config, ProcMan/process, stdout/stderr, key-line,
  result-absence, stop-reason, and cleanup artifacts are present.
- Stop gate was under 20 minutes.
- Final cleanup is supported by `procman-final.log: Nothing Active` and
  removed temporary alias evidence.
- CTA/bind/launch conclusion is accurate: `gpu_launch_insert` was followed by
  `select_kernel_none detail=tb_latency_pending` at cycles `1` and `201`,
  with `cta_launched_kernel=0`, `active_sms=0`, and no bind/CTA issue lines.
- No metrics/S6/accepted/latest/calibration/promotion artifact was found in
  the referenced artifact root.

Reviewer nuance:

- The stop reason should be read as repeated normalized no-ready-CTA /
  pre-admission state. Detailed `tb_latency` progressed from `1800` to `1600`,
  and this log already avoids claiming a post-bind failure.

No rework was required.
