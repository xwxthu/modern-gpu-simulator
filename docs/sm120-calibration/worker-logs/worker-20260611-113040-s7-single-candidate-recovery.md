# S7 Single-Candidate Execution Recovery Worker Log

## Purpose

Recover and validate the interrupted S7 single-candidate execution for
`candidate_0004`, ProcMan job `487`, without launching any new simulator job
and without editing accepted/generated/latest configs or non-documentation
files.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base commit at verification: `63ef91d73484c1e60de88b129603ac2dd6b87f8f`
- Timestamp: `2026-06-11T11:30:40+08:00`
- Worker role: `S7 single-candidate execution recovery`
- Worktree at start: one untracked temporary alias file was observed:
  `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`.
  Final recheck showed that file no longer exists.

## Required Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/worker-logs/worker-20260610-032557-s7-sweep-exec-prep.md`
- Execution logs under
  `artifacts/s7/s7-bounded-sweep-20260610-024829/single-candidate-0004-exec-20260610-033849/logs/`

Additional read-only evidence inspected:

- `artifacts/s7/s7-bounded-sweep-20260610-024829/sim-runs/candidate_0004/backprop-rodinia-2.0-ft/4096___data_result_4096_txt/RTX5060_SM120_GEN-S7SWEEP_L0L1_39_PREFETCH_10/backprop-rodinia-2.0-ft-4096___data_result_4096_txt.gpgpu-sim_git-commit-db1673770b38b1f8ae0a6c0f92269307664e298f_modified_14.0.o487`
- `artifacts/s7/s7-bounded-sweep-20260610-024829/sim-runs/candidate_0004/backprop-rodinia-2.0-ft/4096___data_result_4096_txt/RTX5060_SM120_GEN-S7SWEEP_L0L1_39_PREFETCH_10/backprop-rodinia-2.0-ft-4096___data_result_4096_txt.gpgpu-sim_git-commit-db1673770b38b1f8ae0a6c0f92269307664e298f_modified_14.0.e487`
- `artifacts/s7/s7-bounded-sweep-20260610-024829/sim-runs/candidate_0004/backprop-rodinia-2.0-ft/4096___data_result_4096_txt/RTX5060_SM120_GEN-S7SWEEP_L0L1_39_PREFETCH_10/result.txt`
- `artifacts/s7/s7-bounded-sweep-20260610-024829/candidate_0004-simulator-candidate-metrics.yaml`
- `artifacts/s7/s7-bounded-sweep-20260610-024829/RTX5060-backprop-4096-s7-bounded-sweep-s6-manifest.PARTIAL-2OF4.yaml`

## Hard Rules Observed

- Did not run a new simulator job.
- Did not run anything on `dsp5060`.
- Did not edit accepted/generated/latest configs.
- Did not edit non-documentation files.
- Did not clean the temporary alias file because this worker was scoped to
  read-only verification plus worker-level documentation.

## Actions

1. Confirmed branch, commit, and worktree state:
   `dev-5060`, `63ef91d73484c1e60de88b129603ac2dd6b87f8f`, with only
   `define-s7-bounded-sweep-temp.yml` untracked.
2. Read the required supervisor, overall-plan, setup worker, and execution
   logs.
3. Checked current ProcMan status with:
   `python3 simulator-remodeled/util/job_launching/procman.py -p`.
4. Inspected `candidate_0004` setup, submit, monitor, stdout, stderr, and
   result files for completion, PASS/FAIL, simulator metrics, and temporary
   output residue.
5. Checked whether post-run bridge artifacts already exist for
   `candidate_0004`.

## Evidence

Execution start evidence:

- `logs/start-timestamp.log`: `2026-06-10T03:39:09+08:00`
- `logs/start-branch.log`: `dev-5060`
- `logs/start-commit.log`: `63ef91d73484c1e60de88b129603ac2dd6b87f8f`
- `logs/start-procman-status.log`: `Nothing Active`

Setup evidence:

- `logs/candidate_0004-setup-only.exitcode`: `0`
- `logs/candidate_0004-effective-config-values.log`:
  - `-latency_L0_to_L1 last=39 line=349 expected=39`
  - `-prefetch_per_stream_buffer_size last=10 line=350 expected=10`

Submit evidence:

- `logs/procman-before-actual-run.log`: `Nothing Active`
- `logs/candidate_0004-actual-run-submit.exitcode`: `0`
- `logs/candidate_0004-actual-run-submit.log` records:
  - `Using configs: RTX5060_SM120_GEN-S7SWEEP_L0L1_39_PREFETCH_10`
  - `Job 487 queued`

Completion evidence:

- `logs/candidate_0004-monitor.exitcode`: `0`
- `logs/procman-after-monitor.log`: `Nothing Active`
- Current ProcMan check also reports `Nothing Active`.
- `logs/candidate_0004-run-dir-files-after-monitor.log` records the run-dir
  `.o487`, `.e487`, `gpgpusim.config`, `gpgpu_inst_stats.txt`, and
  `result.txt`.
- `logs/candidate_0004-tmp-files-after-monitor.log` records no matching
  `/tmp/*487` files remaining.

Simulator stdout evidence from the run-dir `.o487`:

- `gpu_sim_cycle = 38038`
- `gpu_sim_insn = 3866944`
- `gpu_tot_sim_cycle = 45760`
- `gpu_tot_sim_insn = 8036672`
- `gpgpu_simulation_time = 0 days, 0 hrs, 36 min, 43 sec (2203 sec)`
- `PASSED`
- `GPGPU-Sim: *** exit detected ***`

The same stdout includes kernel-progress completion for kernel 2:

- `cta_launched_kernel=256`
- `cta_completed_kernel=256`
- `running_kernels=[]`

Simulator stderr evidence:

- `.e487` contains only:
  `libgomp: Invalid value for environment variable OMP_NUM_THREADS:`
- No `FAILED`, crash, assert, segmentation fault, deadlock, or ProcMan-active
  residue was observed during this verification.

Bridge artifact evidence:

- `candidate_0004-simulator-candidate-metrics.yaml` exists and is
  `status: draft_not_applied`.
- It marks `application_passed: true`, `hardware_target_metrics: false`, and
  records the same key observations:
  - kernel 1 `gpu_tot_sim_cycle: 7722`
  - kernel 2 `gpu_sim_cycle: 38038`
  - kernel 2 `gpu_tot_sim_cycle: 45760`
  - kernel 2 `gpu_tot_sim_insn: 8036672`
- It derives draft simulator candidate metrics:
  - `cuda_kernel_total_time_ms: 0.017333333`
  - `cuda_kernel_avg_time_ms: 0.008666666`
  - `cuda_kernel_bpnn_layerforward_cuda_total_time_ms: 0.002925`
  - `cuda_kernel_bpnn_adjust_weights_cuda_total_time_ms: 0.014408333`
- `RTX5060-backprop-4096-s7-bounded-sweep-s6-manifest.PARTIAL-2OF4.yaml`
  exists and remains non-runnable with blockers:
  `candidate_metrics_not_marked_reviewed`, `missing_candidate_signatures:2`,
  and `input_template_status_template_not_runnable`.

## Temporary Alias State

An initial verification pass observed the temporary alias file:

```text
simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml
```

At that time its content was only the candidate `0004` alias:

```yaml
S7SWEEP_L0L1_39_PREFETCH_10:
    extra_params: |
        -latency_L0_to_L1 39
        -prefetch_per_stream_buffer_size 10
```

Final recheck:

- `ls simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`
  returned `No such file or directory`.
- `git status --short -- simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`
  showed no entry.

Conclusion: the alias is not needed to validate the already completed job
`487`, and by final verification it was already absent. No alias cleanup is
currently required.

## Validations

| Check | Result |
| --- | --- |
| Required docs read | Pass |
| Execution logs read | Pass |
| New simulator job launched | No |
| Branch and base commit recorded | Pass |
| Candidate effective config values match plan | Pass |
| ProcMan before run clean | Pass |
| Job `487` queued | Pass |
| Monitor completed cleanly | Pass |
| ProcMan after monitor clean | Pass |
| Current ProcMan clean | Pass |
| `/tmp/*487` residue absent after monitor | Pass |
| Run-dir `.o487` and `.e487` present | Pass |
| Simulator `PASSED` present | Pass |
| `GPGPU-Sim: *** exit detected ***` present | Pass |
| Key simulator metrics present | Pass |
| Candidate metrics bridge artifact exists | Pass, draft-only |
| Partial S6 manifest is runnable | No, intentionally blocked at 2 of 4 candidates |
| Temporary alias cleaned | Pass; final recheck shows the file is absent |

## Reviewer Rounds

No separate blank-context reviewer could be spawned from this worker interface;
no subagent/spawn tool is available in the current tool set. I performed a
reviewer-style self-check against the assigned acceptance questions:

- Did the verification accidentally run a new simulator job? No; only read-only
  inspection commands and `procman.py -p` were run.
- Is job `487` clearly complete rather than still active? Yes; monitor exitcode
  is `0`, post-monitor ProcMan is `Nothing Active`, current ProcMan is
  `Nothing Active`, stdout has `PASSED` and simulator exit, and `/tmp/*487`
  residue is absent.
- Are raw simulator metrics present? Yes; `gpu_sim_cycle`, `gpu_sim_insn`,
  `gpu_tot_sim_cycle`, and `gpu_tot_sim_insn` are present in `.o487`.
- Are derived candidate metrics present? Yes; a draft, not-applied
  `candidate_0004-simulator-candidate-metrics.yaml` exists.
- Is the S6 sweep complete? No; partial manifest says 2 of 4 supplied
  candidates and remains non-runnable.
- Does the temp alias need cleanup? No at final verification; it was observed
  earlier in the turn, but final recheck shows it is already absent.

Reviewer-style verdict: accept.

## Changed Files

Documentation-only:

- `docs/sm120-calibration/worker-logs/worker-20260611-113040-s7-single-candidate-recovery.md`

No code, configs, generated latest/accepted configs, or artifact files were
modified by this worker.

## Final Status

`candidate_0004` ProcMan job `487` is complete and passed. Key simulator
metrics and draft simulator-candidate metrics exist. ProcMan is clean. The
temporary alias file is absent at final verification, so no alias cleanup is
currently required.
