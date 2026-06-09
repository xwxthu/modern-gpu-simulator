# S7 Kernel 2 Progress Diagnostic Worker Log

## Purpose

Add a small, default-off diagnostic probe to determine whether the
`backprop` second PTX performance-simulation kernel makes internal simulator
progress after launch/bind, and if not, classify the stuck state more precisely.

This is S7 system integration and PTX-mode smoke bring-up defect triage. It is
not calibration, correlation, or promotion.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base commit: `049ebc6`
- Timestamp: `2026-06-09T19:12:15+08:00`
- Initial tracked worktree: clean
- Artifact root: `artifacts/s7/s7-kernel2-progress-20260609-191215/`

## Inputs Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/worker-logs/worker-20260609-181955-s7-full-smoke.md`
- `docs/sm120-calibration/worker-logs/worker-20260609-173154-s7-smoke-stall.md`

## Assigned Scope

- Do not change accepted/generated/latest configs.
- Do not reduce benchmark/config scale; keep
  `rodinia_2.0-ft:backprop-rodinia-2.0-ft:0` with `RTX5060_SM120_GEN`.
- Do not run simulator workloads on `dsp5060`.
- Add only default-off, low-frequency diagnostic instrumentation unless a
  narrow root cause is proven.
- Run exactly one bounded local PTX smoke with instrumentation enabled.
- If a narrow root cause is proven and fixed, run exactly one post-fix local
  PTX smoke. Otherwise preserve diagnostics and define the next blocker.
- Do not commit.

## Instrumentation Design

Implemented a default-off environment-variable probe emitted from
`gpgpu_sim::cycle()` after CTA issue and kernel-latency decrement:

- Enable: `GPGPUSIM_KERNEL_PROGRESS_DEBUG=1`
- Cycle interval: `GPGPUSIM_KERNEL_PROGRESS_INTERVAL`, default `50000`
- SM sample cap: `GPGPUSIM_KERNEL_PROGRESS_SM_LIMIT`, default `6`
- Grep prefix: `GPGPUSIM-K2-PROGRESS`
- Also emits immediately when the running-kernel signature changes, including
  kernel uid or next CTA changes, so early kernel launch/bind progress is
  visible even before the interval expires.

Captured fields:

- global cycles: `gpu_sim_cycle`, `gpu_tot_sim_cycle`
- running kernel slot, uid, name, `next_cta`, `num_cta`, running/done flags
- CTA launch/complete counters and global CTA accounting
- global grid-barrier active/arrived/thread counts
- aggregate active CTA, not-completed threads, active SM count
- sampled cluster response FIFO occupancy
- sampled SM kernel uid, active CTA, not-done thread count, active warp count,
  functional-done warp count, warp instruction pipeline count, instruction
  buffer count, CTA barrier count, membar count, gridbar count, instruction
  miss count, atomic-pending count, selected active warp id/PC/active lanes,
  selected warp in-pipeline count, and outstanding store count
- remodeled SMs also report public LD/ST occupancy counters:
  `mem_normal` and `mem_shared`

Safety notes:

- The diagnostic path is off unless the enable environment variable is set.
- The probe uses read-only/public state. It intentionally does not call
  `warp_waiting_at_mem_barrier()` because that helper can clear membar state as
  a side effect.
- Deeper LD/ST and scheduler internals are private; this pass captures the
  safe public counters rather than widening simulator ownership boundaries.

## Actions

- Confirmed the base state:
  - branch `dev-5060`
  - HEAD `049ebc6`
  - tracked worktree clean at takeover
- Created artifact directory
  `artifacts/s7/s7-kernel2-progress-20260609-191215/`.
- Added the default-off kernel-progress diagnostic probe.
- Ran required checks after instrumentation:
  - `git diff --check`
  - `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`
- Rebuilt GPGPU-Sim after the diagnostic code change.
- Ran setup-only local smoke planning for
  `rodinia_2.0-ft:backprop-rodinia-2.0-ft:0` with `RTX5060_SM120_GEN`.
- Launched exactly one bounded local PTX smoke with:
  - ProcMan job `484`
  - `GPGPUSIM_KERNEL_PROGRESS_DEBUG=1`
  - `GPGPUSIM_KERNEL_PROGRESS_INTERVAL=50000`
  - `GPGPUSIM_KERNEL_PROGRESS_SM_LIMIT=8`
  - local server only
  - no `dsp5060` simulator run

## Evidence Summary

Job `484` was the single diagnostic smoke for this worker. It was stopped at
the bounded timeout after evidence capture; no second diagnostic smoke was run.

Final artifacts:

- stdout:
  `artifacts/s7/s7-kernel2-progress-20260609-191215/smoke-stdout-final.o484.log`
- stderr:
  `artifacts/s7/s7-kernel2-progress-20260609-191215/smoke-stderr-final.e484.log`
- key grep lines:
  `artifacts/s7/s7-kernel2-progress-20260609-191215/key-progress-lines.log`
- final result/crash search:
  `artifacts/s7/s7-kernel2-progress-20260609-191215/final-functional-and-crash-search.log`
- final ProcMan state:
  `artifacts/s7/s7-kernel2-progress-20260609-191215/procman-status-final-check.log`

The diagnostic probe was enabled only through the environment for this run:

```text
GPGPUSIM-K2-PROGRESS enabled interval=50000 sm_limit=8 (env:GPGPUSIM_KERNEL_PROGRESS_DEBUG)
```

Kernel 1 still completed and produced first-kernel-only metrics:

```text
kernel_name = _Z22bpnn_layerforward_CUDAPfS_S_S_ii
gpu_tot_sim_cycle = 7729
gpu_tot_sim_insn = 4169728
gpgpu_simulation_time = 0 days, 0 hrs, 6 min, 26 sec (386 sec)
```

Kernel 2 launched and the probe reported the initial queued/running state:

```text
GPGPU-Sim PTX: pushing kernel '_Z24bpnn_adjust_weights_cudaPfiS_iS_S_' to stream 0, gridDim= (1,256,1) blockDim = (16,16,1)
GPGPUSIM-K2-PROGRESS cycle=7730 gpu_sim_cycle=1 gpu_tot_sim_cycle=7729 ... uid=2,name=_Z24bpnn_adjust_weights_cudaPfiS_iS_S_,next_cta=0,num_cta=256,running=0,done=0 ... active_cta=0 ... active_sms=0
```

Kernel 2 then made internal resident-CTA progress immediately after bind:

```text
GPGPUSIM-K2-PROGRESS cycle=9530 gpu_sim_cycle=1801 gpu_tot_sim_cycle=7729 cta_launched_kernel=30 cta_completed_kernel=0 ... next_cta=30,num_cta=256,running=1 ... active_cta=30 ... active_sms=30 ... pc=0x26d8
GPGPUSIM-K2-PROGRESS cycle=9535 gpu_sim_cycle=1806 gpu_tot_sim_cycle=7729 cta_launched_kernel=180 cta_completed_kernel=0 ... next_cta=180,num_cta=256,running=1 ... active_cta=180 ... active_sms=30 ... pc=0x26d8
```

By the final preserved sample, kernel 2 had launched all CTAs and completed
some CTAs, but was still far from kernel completion:

```text
GPGPUSIM-K2-PROGRESS cycle=36153 gpu_sim_cycle=28424 gpu_tot_sim_cycle=7729 cta_launched_kernel=256 cta_completed_kernel=76 ... next_cta=256,num_cta=256,running=1,done=0 ... active_cta=180 not_completed_threads=43648 active_sms=30
```

Sampled SM state near the timeout consistently showed many active/pipeline
warps around PC `0x2890`, with many CTA-barrier waiters and little evidence of
other blocking classes:

```text
sm0{kernel=2,cta=6,notdone=1344,aw=42,fdone=6,pipew=42,ibuf=0,bar=26,membar=0,gridbar=0,imiss=0,atomic=0,mem_normal=0,mem_shared=0,selw=0,pc=0x2890,active=32,pipe=3,stores=0}
sm2{kernel=2,cta=6,notdone=1536,aw=48,fdone=0,pipew=48,ibuf=0,bar=34,membar=0,gridbar=0,imiss=0,atomic=0,mem_normal=0,mem_shared=0,selw=0,pc=0x2890,active=32,pipe=3,stores=0}
```

The run produced 155 `GPGPUSIM-K2-PROGRESS` lines. The extra lines beyond the
50,000-cycle interval are expected because the probe also prints when the
running-kernel signature changes, including `next_cta` changes. This was still
bounded and grep-friendly for the 30-minute diagnostic run.

No second-kernel metrics, host functional output, pass/fail line, crash,
assertion, or coredump evidence appeared before the timeout stop. Stderr only
contained the pre-existing OpenMP warning:

```text
libgomp: Invalid value for environment variable OMP_NUM_THREADS:
```

## Analysis And Root Cause

The previous precise blocker is narrowed: kernel 2 is not dead at launch/bind
and is not a no-progress hang. It enters PTX performance simulation, binds SMs,
launches all 256 CTAs, completes 76 CTAs, and continues to report active
resident CTAs/warps before the bounded stop.

The smoke still does not complete. The evidence points to extremely slow
forward progress in the second kernel, dominated by CTA-barrier/near-barrier
state plus some pipeline and normal-memory activity:

- final sampled state: `next_cta=256/256`, `cta_completed_kernel=76`,
  `active_cta=180`, `active_sms=30`
- sampled SMs: `aw` about `41-48`, `pipew` about `40-48`, `ibuf=0`
- sampled CTA barrier waiters: usually about `bar=24-34`
- no sampled `membar`, `gridbar`, instruction miss, or atomic pending state
- normal-memory occupancy was small/nonzero in some samples and zero in others
- selected active warp PC was mostly `0x2890`

The generated PTX maps the relevant region to the second kernel around
`bar.sync 0` at PTX line 200 and the following branch/update tail at lines
201-225 in
`artifacts/s7/s7-kernel2-progress-20260609-191215/sim-smoke/backprop-rodinia-2.0-ft/4096___data_result_4096_txt/RTX5060_SM120_GEN/backprop-rodinia-2.7.sm_120.ptx`.

No narrow root cause fix is justified from this evidence alone. The next
blocker is targeted attribution inside kernel 2 after all CTAs are resident:
identify whether the slow progress is caused by barrier-release bookkeeping,
SIMT PC/reconvergence behavior around `0x2890`, scheduler issue/no-issue
conditions, or memory-return/scoreboard latency for the post-barrier global
load/store tail.

Because no root cause fix was made, no post-fix smoke was run.

## Changed Files

Code:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-sim.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-sim.h`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader.h`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader_core_wrapper.h`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/sm.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/sm.h`

Documentation:

- `docs/sm120-calibration/worker-logs/worker-20260609-191215-s7-kernel2-progress.md`

Config/generated/calibration result changes:

- None.

## Validation

- `git diff --check`: pass
  - `artifacts/s7/s7-kernel2-progress-20260609-191215/git-diff-check-after-instrumentation.exitcode`
  - `artifacts/s7/s7-kernel2-progress-20260609-191215/git-diff-check-after-kernel-signature.exitcode`
- `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`: pass
  - `artifacts/s7/s7-kernel2-progress-20260609-191215/generate-check-only-after-instrumentation.exitcode`
  - `artifacts/s7/s7-kernel2-progress-20260609-191215/generate-check-only-after-kernel-signature.exitcode`
- GPGPU-Sim rebuild: pass
  - `artifacts/s7/s7-kernel2-progress-20260609-191215/rebuild-gpgpusim.exitcode`
- Setup-only local smoke planning: pass
  - `artifacts/s7/s7-kernel2-progress-20260609-191215/local-smoke-plan.exitcode`
- Bounded diagnostic local PTX smoke: timed out by boundary, evidence captured
  - `artifacts/s7/s7-kernel2-progress-20260609-191215/local-smoke-run.exitcode`
  - job `484`, final stdout/stderr copied to artifacts
  - final ProcMan check: pass, `Nothing Active`
- Final `git diff --check`: pass
  - `artifacts/s7/s7-kernel2-progress-20260609-191215/git-diff-check-final.exitcode`
- Final `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`: pass
  - `artifacts/s7/s7-kernel2-progress-20260609-191215/generate-check-only-final.exitcode`

## Reviewer Rounds

Round 1 fresh blank-context read-only reviewer:

- Timestamp: `2026-06-09T20:06:xx+08:00`
- Artifacts:
  `artifacts/s7/s7-kernel2-progress-20260609-191215/reviewer/round1/`
- Exit code: `0`
- Verdict: `ACCEPT`

Reviewer summary:

- Instrumentation is default-off via `GPGPUSIM_KERNEL_PROGRESS_DEBUG`, named
  clearly enough for this S7 diagnostic, and scoped to read-only progress
  sampling from `gpgpu_sim::cycle()`.
- The `GPGPUSIM-K2-PROGRESS` path is grep-friendly; 155 lines for the bounded
  run is acceptable, and the signature-change extra lines are documented.
- Evidence supports the conclusion that kernel 2 launched, bound SMs, launched
  all 256 CTAs, completed 76 CTAs, and had active CTAs/warps, ruling out a
  launch/bind no-progress hang.
- The worker does not overclaim full smoke pass, calibration, correlation,
  config promotion, or root-cause fix.
- Changed files and validation evidence are accurately documented.
- Reviewer recommends retaining the instrumentation for now as default-off
  diagnostic code. A future long-term merge may rename the `K2` prefix if it
  becomes a general kernel-progress diagnostic, but this is not blocking.

## Final Status

Final verdict: diagnostic triage complete, root cause not fixed.

Instrumentation is retained as default-off diagnostic code. It is enabled only
with `GPGPUSIM_KERNEL_PROGRESS_DEBUG=1`; no generated, accepted, latest, or
calibration/correlation configs were modified.

Kernel-2 conclusion:

- Kernel 2 is not stuck at launch/bind and is not a no-progress hang.
- It launches all 256 CTAs and completes 76 CTAs in the bounded diagnostic run.
- It remains too slow to finish within the bounded smoke window, with sampled
  state concentrated around many CTA-barrier/near-barrier warps at PC `0x2890`
  plus some pipeline and normal-memory activity.

Precise next blocker:

- Determine why `_Z24bpnn_adjust_weights_cudaPfiS_iS_S_` makes extremely slow
  progress after all CTAs are resident: barrier-release bookkeeping,
  SIMT/reconvergence behavior near `0x2890`, scheduler issue/no-issue
  conditions, or memory-return/scoreboard latency in the post-barrier
  load/store tail.

No supervisor rework is requested for this worker result unless the supervisor
wants the diagnostic prefix generalized before keeping the code longer term.
