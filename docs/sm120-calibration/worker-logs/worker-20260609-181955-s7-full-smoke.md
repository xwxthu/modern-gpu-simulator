# S7 Full Smoke Boundary Worker Log

## Purpose

Run and triage one bounded local PTX-mode smoke for
`rodinia_2.0-ft:backprop-rodinia-2.0-ft:0` with `RTX5060_SM120_GEN`, starting
from the current evidence that the smoke has already produced first-kernel
metrics and reached second-kernel bind. The goal is to prove full application
completion or capture the next precise failure point after the observed
second-kernel bind.

This is S7 system integration and PTX-mode smoke bring-up defect triage. It is
not calibration or correlation.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base commit: `90d9b31`
- Timestamp: `2026-06-09T18:19:55+08:00`
- Initial tracked worktree: clean
- Artifact root: `artifacts/s7/s7-full-smoke-20260609-181955/`

## Inputs Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/worker-logs/worker-20260609-173154-s7-smoke-stall.md`
- `docs/sm120-calibration/worker-logs/worker-20260609-164753-s7-dp-latency.md`
- Prior smoke evidence under `artifacts/s7/s7-smoke-stall-20260609-173154/`

## Assigned Scope

- Run exactly one bounded local PTX smoke unless a narrow code fix is made.
- If the application completes, record real simulator metrics and functional
  result evidence without promoting or treating them as calibration/correlation.
- If it crashes, stalls, or times out at/after the second kernel, capture
  stdout/stderr, ProcMan state, process state, and coredump/GDB evidence where
  possible.
- Do not run simulator workloads on `dsp5060`.
- Do not modify accepted/generated/latest/calibration results.
- Do not commit.

## Actions

- Confirmed the base state:
  - branch `dev-5060`
  - HEAD `90d9b31`
  - tracked worktree clean at takeover
- Created artifact directory
  `artifacts/s7/s7-full-smoke-20260609-181955/`.
- Ran required start checks:
  - `git status --short --branch`
  - `git diff --check`
  - `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`
  - `python3 simulator-remodeled/util/job_launching/procman.py -p`
- Ran setup-only smoke planning. The first planning command intentionally
  preserved the missing-environment failure:
  `ERROR - Please run setup_environment before running this script`.
- Re-ran setup-only planning after sourcing the local GPGPU-Sim and app
  collection environments; it passed.
- Launched exactly one fresh local PTX smoke:
  - ProcMan job `483`
  - local server only
  - no `dsp5060` simulator run
  - benchmark/config unchanged:
    `rodinia_2.0-ft:backprop-rodinia-2.0-ft:0` + `RTX5060_SM120_GEN`
  - 30-minute wall-clock boundary with periodic 120-second sampling
- Captured periodic evidence:
  - ProcMan status
  - stdout/stderr size and tail
  - progress scans for kernel launch/bind, metrics, result, crash, assertion,
    and fatal/error lines
  - process and thread state
- At the 30-minute boundary, the job was still active and was killed through
  ProcMan after final diagnostics.
- Attempted GDB attach at timeout. Attach was blocked by ptrace/Yama policy.
- Checked `coredumpctl` after the timeout stop; no visible coredumps were
  found.
- Performed focused read-only analysis of the benchmark kernel and generated
  PTX to identify the failure boundary, but made no simulator code changes.

## Evidence Summary

The fresh bounded smoke was ProcMan job `483`:

- Launcher:
  `artifacts/s7/s7-full-smoke-20260609-181955/local-smoke-run.log`
- Final stdout/stderr copies:
  - `artifacts/s7/s7-full-smoke-20260609-181955/smoke-stdout-final.o483.log`
  - `artifacts/s7/s7-full-smoke-20260609-181955/smoke-stderr-final.e483.log`
- Final result search:
  `artifacts/s7/s7-full-smoke-20260609-181955/final-result-search.log`

The run reproduced real first-kernel metrics:

```text
gpu_tot_sim_cycle = 7729
gpu_tot_sim_insn = 4169728
gpgpu_simulation_time = 0 days, 0 hrs, 7 min, 2 sec (422 sec)
```

Those metrics are real simulator output for the first kernel only. They are not
calibration, correlation, promotion, or a full-smoke pass.

The run advanced past the previously observed second-kernel bind point and bound
the second kernel across SMs:

```text
GPGPU-Sim PTX: pushing kernel '_Z24bpnn_adjust_weights_cudaPfiS_iS_S_'
GPGPU-Sim uArch: Shader 29 bind to kernel 2 '_Z24bpnn_adjust_weights_cudaPfiS_iS_S_'
GPGPU-Sim uArch: Shader 17 bind to kernel 2 '_Z24bpnn_adjust_weights_cudaPfiS_iS_S_'
```

After that point, no second-kernel metrics, host-side result, checksum,
`Result stored`, `PASSED`, or `FAILED` line appeared before the 30-minute
boundary:

- `artifacts/s7/s7-full-smoke-20260609-181955/final-result-search.log`
- `artifacts/s7/s7-full-smoke-20260609-181955/run-dir-result-files.log`

Final output file sizes and mtimes show stdout stopped growing after
second-kernel bind:

```text
/tmp/...o483 249646 2026-06-09 18:32:02.182281418 +0800
/tmp/...e483 67 2026-06-09 18:23:00.386152290 +0800
```

Evidence:

- `artifacts/s7/s7-full-smoke-20260609-181955/smoke-output-stat-final.log`

The process was still CPU-bound at timeout rather than sleeping idle or already
crashed. At the final pre-kill sample:

- ProcMan running time: about `0:31:35`
- app process state: `Sl`
- app process CPU time: `3-12:44:33`
- many app threads were `Rl` with about `82-84%` CPU each
- stderr contained only:
  `libgomp: Invalid value for environment variable OMP_NUM_THREADS:`

Evidence:

- `artifacts/s7/s7-full-smoke-20260609-181955/procman-status-before-timeout-kill.log`
- `artifacts/s7/s7-full-smoke-20260609-181955/smoke-ps-before-timeout-kill.log`
- `artifacts/s7/s7-full-smoke-20260609-181955/smoke-threads-poll-15.log`
- `artifacts/s7/s7-full-smoke-20260609-181955/smoke-stderr-final.e483.log`

GDB/coredump evidence:

- `gdb -p` was attempted at timeout but blocked:
  `Could not attach to process... ptrace: Inappropriate ioctl for device.`
- `coredumpctl` reported `No coredumps found`; it also warned that the current
  user may not see all system/user coredump messages.

Evidence:

- `artifacts/s7/s7-full-smoke-20260609-181955/gdb-thread-bt-timeout.log`
- `artifacts/s7/s7-full-smoke-20260609-181955/coredumpctl-list-since-start.log`

Build-string note:

- The setup banner came from current repo HEAD `90d9b31`, but the job launcher
  copied the existing simulator build directory named
  `gpgpu-sim_git-commit-c4dbbc6828fe92a6a851da99da2135bae25842f3_modified_0.0`.
  Commit `90d9b31` is the documentation checkpoint after `c4dbbc6`; there were
  no simulator source changes between those commits. This worker made no code
  change and did not rebuild.

## Analysis And Root Cause

Full PTX smoke did not complete.

The next precise failure boundary is:

- second kernel:
  `_Z24bpnn_adjust_weights_cudaPfiS_iS_S_`
- mode:
  PTX performance simulation
- progress:
  launched, predecoded, and bound to SMs
- last durable simulator output:
  final SM bind for kernel 2
- timeout behavior:
  CPU-bound long run for about 30 minutes without second-kernel metrics,
  functional result output, crash, assertion, or stderr growth

The benchmark source and generated PTX indicate that the second kernel is a
fixed-size update kernel with one `bar.sync 0` and no PTX loop in the generated
SM120 PTX:

- source:
  `simulator-remodeled/gpu-app-collection/src/cuda/rodinia/2.0-ft/backprop/backprop_cuda_kernel.cu`
- PTX:
  `artifacts/s7/s7-full-smoke-20260609-181955/sim-smoke/backprop-rodinia-2.0-ft/4096___data_result_4096_txt/RTX5060_SM120_GEN/backprop-rodinia-2.7.sm_120.ptx`

The first kernel completed and wrote `gpgpu_inst_stats.txt`; a search for
second-kernel PTX line numbers did not find completed line-level stats for the
second kernel. This supports the boundary being inside second-kernel
performance simulation before completion/accounting flush, not host-side
result comparison.

No narrow root cause was proven in this worker. Without a usable GDB attach,
coredump, or simulator-internal progress counters at timeout, changing simulator
code now would be speculative. The next useful triage step is a fresh bounded
run with reviewable temporary instrumentation or debug permissions that can
report per-cycle/per-kernel progress after kernel 2 bind, such as active CTA
counts, completed CTA counts, per-SM active warp/barrier state, scheduler issue
state, and selected warp PCs.

## Changed Files

Documentation:

- `docs/sm120-calibration/worker-logs/worker-20260609-181955-s7-full-smoke.md`

Code/config/generated/calibration result changes:

- None.

Ignored/local artifacts:

- `artifacts/s7/s7-full-smoke-20260609-181955/`

## Validation

Start status:

```bash
git status --short --branch
```

- Evidence:
  `artifacts/s7/s7-full-smoke-20260609-181955/git-status-start.log`
- Result:
  branch `dev-5060`, HEAD ahead of origin, no tracked changes.

Whitespace check:

```bash
git diff --check
```

- Start evidence:
  `artifacts/s7/s7-full-smoke-20260609-181955/git-diff-check-start.log`,
  exit code `0`.
- Final evidence:
  `artifacts/s7/s7-full-smoke-20260609-181955/git-diff-check-final.log`,
  exit code `0`.

SM120 generated-config reproducibility check:

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
```

- Start evidence:
  `artifacts/s7/s7-full-smoke-20260609-181955/generate-check-only-start.log`,
  exit code `0`.
- Final evidence:
  `artifacts/s7/s7-full-smoke-20260609-181955/generate-check-only-final.log`,
  exit code `0`.
- Output:
  generated `SM120_RTX5070_TI` and `SM120_RTX5060` bootstrap profiles with
  `gpgpu_keys=217` and `trace_keys=13`.

Setup-only local smoke planning:

```bash
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-full-smoke-20260609-181955-smoke-plan-env \
  -r artifacts/s7/s7-full-smoke-20260609-181955/sim-smoke-plan-env \
  -l local \
  -n
```

- Initial no-env attempt:
  `artifacts/s7/s7-full-smoke-20260609-181955/local-smoke-plan.log`,
  exit code `1`.
- Environment-sourced planning:
  `artifacts/s7/s7-full-smoke-20260609-181955/local-smoke-plan-env.log`,
  exit code `0`.

Exactly one bounded local PTX smoke:

```bash
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-full-smoke-20260609-181955-smoke \
  -r artifacts/s7/s7-full-smoke-20260609-181955/sim-smoke \
  -l local \
  -c 4
```

- Launcher evidence:
  `artifacts/s7/s7-full-smoke-20260609-181955/local-smoke-run.log`
- Launcher exit code:
  `artifacts/s7/s7-full-smoke-20260609-181955/local-smoke-run.exitcode`,
  value `0`.
- ProcMan job:
  `483`.
- Stop reason:
  `artifacts/s7/s7-full-smoke-20260609-181955/smoke-stop-reason.log`,
  value `wall-clock-timeout`.
- Final ProcMan:
  `artifacts/s7/s7-full-smoke-20260609-181955/procman-status-final-standalone.log`,
  `Nothing Active`.

Final status:

```bash
git status --short --branch
```

- Pre-review evidence:
  `artifacts/s7/s7-full-smoke-20260609-181955/git-status-final-pre-review.log`
- Pre-review result:
  only this worker log is untracked before review/final log updates.

Final after-review checks:

- `artifacts/s7/s7-full-smoke-20260609-181955/git-status-final-after-review.log`
  showed only this worker log untracked.
- `artifacts/s7/s7-full-smoke-20260609-181955/git-diff-check-final-after-review.log`
  exited `0`.
- `artifacts/s7/s7-full-smoke-20260609-181955/generate-check-only-final-after-review.log`
  exited `0`.
- `artifacts/s7/s7-full-smoke-20260609-181955/procman-status-final-after-review.log`
  showed `Nothing Active`.

Final post-log sanity checks:

- `artifacts/s7/s7-full-smoke-20260609-181955/git-status-final-final.log`
  showed only this worker log untracked.
- `artifacts/s7/s7-full-smoke-20260609-181955/git-diff-check-final-final.log`
  exited `0`.
- `artifacts/s7/s7-full-smoke-20260609-181955/generate-check-only-final-final.log`
  exited `0`.
- `artifacts/s7/s7-full-smoke-20260609-181955/procman-status-final-final.log`
  showed `Nothing Active`.

## Reviewer Rounds

Round 0:

- Reviewer command failed before launching a valid reviewer because `-a never`
  was passed after `codex exec` instead of before the subcommand.
- Evidence:
  - `artifacts/s7/s7-full-smoke-20260609-181955/reviewer/reviewer-round1.stderr.log`
  - `artifacts/s7/s7-full-smoke-20260609-181955/reviewer/reviewer-round1.exitcode`
- No changes were made from this invalid reviewer attempt.

Round 1:

- Fresh blank-context read-only reviewer returned `ACCEPT`.
- Evidence:
  - `artifacts/s7/s7-full-smoke-20260609-181955/reviewer/reviewer-round1b.stdout.log`
  - `artifacts/s7/s7-full-smoke-20260609-181955/reviewer/reviewer-round1b.stderr.log`
  - `artifacts/s7/s7-full-smoke-20260609-181955/reviewer/reviewer-round1b-final.txt`
  - `artifacts/s7/s7-full-smoke-20260609-181955/reviewer/reviewer-round1b.exitcode`
- Reviewer found the evidence substantively sufficient and did not require
  changes.

## Final Status

- Full smoke completion: not achieved.
- Functional result evidence: not produced; no `result.txt`, `checksum`,
  `Result stored`, `PASSED`, or `FAILED` line appeared before timeout.
- Real simulator metrics: first-kernel metrics were recorded but are not
  calibration, correlation, promotion, or a full-smoke pass.
- Precise next blocker: second-kernel PTX performance simulation becomes
  CPU-bound after `_Z24bpnn_adjust_weights_cudaPfiS_iS_S_` launch/SM bind and
  does not emit second-kernel metrics or functional output within the 30-minute
  bounded local run.
- Reviewer final verdict: `ACCEPT`.
- Code changes: none.
