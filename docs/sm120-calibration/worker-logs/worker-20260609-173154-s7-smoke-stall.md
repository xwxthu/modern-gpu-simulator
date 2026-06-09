# S7 Smoke Stall Triage Worker Log

## Purpose

Triage the current S7 PTX-mode smoke issue after the DP latency fix:

- The prior local smoke reached first-kernel performance simulation and SM
  binding.
- It did not show first-kernel metrics within the bounded wait used by that
  worker.
- The question for this worker is whether that is a true deadlock/livelock, a
  pipeline/accounting no-progress bug, an overly short bounded wait or slow
  configuration, or insufficient evidence from the prior stop.

This is S7 system integration and PTX-mode smoke bring-up defect triage. It is
not calibration or correlation.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base commit: `c4dbbc6`
- Timestamp: `2026-06-09T17:31:54+08:00`
- Initial tracked worktree: clean
- Artifact root: `artifacts/s7/s7-smoke-stall-20260609-173154/`

## Inputs Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/worker-logs/worker-20260609-164753-s7-dp-latency.md`
- `docs/sm120-calibration/worker-logs/worker-20260609-160932-s7-function-call-stack.md`
- Prior bounded-run evidence under
  `artifacts/s7/s7-dp-latency-20260609-164753/`

## Assigned Scope

- Determine whether the post-DP-fix bounded smoke was a real
  deadlock/livelock/stall, a simulator pipeline/accounting no-progress bug, an
  overly short wait or slow configuration, or insufficiently evidenced.
- Make a narrow clean fix only if a root cause is located.
- Otherwise precisely define the next blocker and required evidence.
- Do not run the simulator on `dsp5060`.
- Do not promote partial smoke progress to a full pass, metrics calibration, or
  correlation.
- Do not modify accepted/generated/latest/calibration results.
- Do not commit.

## Actions

- Confirmed the base state:
  - branch `dev-5060`
  - HEAD `c4dbbc6`
  - clean tracked worktree at takeover
- Reviewed the prior DP-latency smoke evidence:
  - job `481`
  - reached first-kernel PTX launch and `Shader 29 bind to kernel 1`
  - was stopped at about `0:08:01`
  - did not include first-kernel metrics before that stop
- Compared the earlier function-call-stack smoke:
  - it had reached the same first-kernel metrics
    (`gpu_tot_sim_cycle = 7729`, `gpu_tot_sim_insn = 4169728`)
  - it then crashed in the second kernel before the DP-latency fix
- Rebuilt the GPGPU-Sim runtime locally after confirming generated SM120 config
  consistency.
- Ran setup-only local smoke planning for
  `rodinia_2.0-ft:backprop-rodinia-2.0-ft:0` with `RTX5060_SM120_GEN`.
- Launched exactly one fresh local PTX smoke after rebuild:
  - ProcMan job `482`
  - local server only
  - no `dsp5060` simulator run
- Captured periodic evidence while the smoke was running:
  - ProcMan status
  - stdout/stderr file sizes
  - process CPU state
  - progress searches for launch, bind, metrics, crash, and assertion lines
- Stopped the fresh smoke with ProcMan only after first-kernel metrics and
  second-kernel bind were captured. This was a deliberate bounded triage stop,
  not a full smoke pass.
- Did not change simulator code or committed configs.

## Analysis And Verdict

The observed issue is not proven to be a first-kernel deadlock, livelock, or
pipeline/accounting no-progress bug.

The fresh run reached first-kernel metrics before it was stopped:

```text
gpu_tot_sim_cycle = 7729
gpu_tot_sim_insn = 4169728
gpgpu_simulation_time = 0 days, 0 hrs, 7 min, 21 sec (441 sec)
```

It then launched and bound the second kernel:

```text
GPGPU-Sim PTX: pushing kernel '_Z24bpnn_adjust_weights_cudaPfiS_iS_S_'
GPGPU-Sim uArch: Shader 29 bind to kernel 2 '_Z24bpnn_adjust_weights_cudaPfiS_iS_S_'
```

Evidence:

- `artifacts/s7/s7-smoke-stall-20260609-173154/smoke-result-search-before-stop.log`
- `artifacts/s7/s7-smoke-stall-20260609-173154/copied-smoke-result-search.log`
- `artifacts/s7/s7-smoke-stall-20260609-173154/final-smoke-result-search.log`

The prior bounded wait was therefore too short for a reliable first-kernel-stall
claim, or it stopped just before the relevant output became visible. The fresh
run shows first-kernel metrics after roughly `441 sec` of reported simulation
time, while the prior run was killed at about `0:08:01` ProcMan runtime without
capturing metrics. The safest verdict is:

- prior evidence was insufficient to call a first-kernel stall;
- no root-cause simulator code defect for first-kernel metrics was reproduced;
- no code fix is justified for this specific issue.

This does not establish a full PTX smoke pass. The fresh run was stopped after
capturing first-kernel metrics and second-kernel bind, so second-kernel
completion and full application completion remain unproven.

## Changed Files

Documentation:

- `docs/sm120-calibration/worker-logs/worker-20260609-173154-s7-smoke-stall.md`

Code/config/generated/calibration result changes:

- None.

Ignored/local artifacts:

- `artifacts/s7/s7-smoke-stall-20260609-173154/`

## Validation

Whitespace check:

```bash
git diff --check
```

- Initial evidence:
  `artifacts/s7/s7-smoke-stall-20260609-173154/git-diff-check-initial.log`
- Final pre-log evidence:
  `artifacts/s7/s7-smoke-stall-20260609-173154/git-diff-check-final.log`
- After-log evidence:
  `artifacts/s7/s7-smoke-stall-20260609-173154/git-diff-check-after-log.log`
- Exit codes: `0`

SM120 generated-config reproducibility check:

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
```

- Initial evidence:
  `artifacts/s7/s7-smoke-stall-20260609-173154/generate-check-only-initial.log`
- Final evidence:
  `artifacts/s7/s7-smoke-stall-20260609-173154/generate-check-only-final.log`
- Exit codes: `0`

GPGPU-Sim runtime rebuild:

```bash
export CUDA_INSTALL_PATH=${CUDA_INSTALL_PATH:-/usr/local/cuda-13.1}
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment
make -C simulator-remodeled/gpu-simulator/gpgpu-sim -j"$(nproc)"
```

- Evidence:
  `artifacts/s7/s7-smoke-stall-20260609-173154/rebuild-gpgpusim.log`
- Exit code:
  `artifacts/s7/s7-smoke-stall-20260609-173154/rebuild-gpgpusim.exitcode`,
  value `0`

Setup-only local smoke planning:

```bash
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-smoke-stall-20260609-173154-smoke-plan \
  -r artifacts/s7/s7-smoke-stall-20260609-173154/sim-smoke-plan \
  -l local \
  -n
```

- Evidence:
  `artifacts/s7/s7-smoke-stall-20260609-173154/local-smoke-plan-after-rebuild.log`
- Exit code:
  `artifacts/s7/s7-smoke-stall-20260609-173154/local-smoke-plan-after-rebuild.exitcode`,
  value `0`

Exactly one fresh local PTX smoke after rebuild:

```bash
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-smoke-stall-20260609-173154-smoke \
  -r artifacts/s7/s7-smoke-stall-20260609-173154/sim-smoke \
  -l local \
  -c 4
```

- Launcher evidence:
  `artifacts/s7/s7-smoke-stall-20260609-173154/local-smoke-run.log`
- Launcher exit code:
  `artifacts/s7/s7-smoke-stall-20260609-173154/local-smoke-run.exitcode`,
  value `0`
- ProcMan job:
  `482`
- Runtime build string:
  `gpgpu-sim_git-commit-c4dbbc6828fe92a6a851da99da2135bae25842f3_modified_0.0`
- Fresh smoke output:
  - `artifacts/s7/s7-smoke-stall-20260609-173154/smoke-stdout-before-stop.o482.log`
  - `artifacts/s7/s7-smoke-stall-20260609-173154/smoke-stderr-before-stop.e482.log`
  - `artifacts/s7/s7-smoke-stall-20260609-173154/smoke-stdout-after-kill.o482.log`
  - `artifacts/s7/s7-smoke-stall-20260609-173154/smoke-stderr-after-kill.e482.log`

Progress evidence:

- At ProcMan runtime `0:08:32`, job `482` was active:
  `artifacts/s7/s7-smoke-stall-20260609-173154/procman-status-poll-3.log`.
- Process evidence at the same poll showed the application consuming CPU, not
  sleeping idle:
  `artifacts/s7/s7-smoke-stall-20260609-173154/smoke-ps-poll-3.log`.
- Stdout continued to grow during the bounded window:
  `artifacts/s7/s7-smoke-stall-20260609-173154/smoke-output-stat-poll-1.log`,
  `smoke-output-stat-poll-2.log`, `smoke-output-stat-poll-3.log`, and
  `smoke-output-stat-before-stop.log`.
- Before stop, output already contained:
  - first-kernel launch and bind
  - `gpu_tot_sim_cycle = 7729`
  - `gpu_tot_sim_insn = 4169728`
  - first-kernel `gpgpu_simulation_time = ... (441 sec)`
  - second-kernel launch and bind
- After ProcMan kill, status showed active jobs `0`, complete jobs `1`:
  `artifacts/s7/s7-smoke-stall-20260609-173154/procman-status-after-kill-15s.log`.

GDB attach:

- A diagnostic GDB attach was attempted and blocked by ptrace policy.
- Evidence:
  `artifacts/s7/s7-smoke-stall-20260609-173154/gdb-thread-bt-poll-2.log`
- This did not block the final verdict because stdout/proc/process evidence was
  sufficient to reject the first-kernel-stall hypothesis.

Final status capture:

- `artifacts/s7/s7-smoke-stall-20260609-173154/git-status-before-log-final.log`
  showed a clean tracked tree before this worker log was created.
- `artifacts/s7/s7-smoke-stall-20260609-173154/git-status-after-log.log`
  captured the status after the log was added.
- `artifacts/s7/s7-smoke-stall-20260609-173154/git-status-after-log-correct-path.log`
  captured the corrected repo-path status with only this worker log untracked.
- `artifacts/s7/s7-smoke-stall-20260609-173154/git-status-final.log`
  captured the final status after the accepted reviewer verdict was recorded.

## Reviewer Rounds

Round 1:

- Reviewer command failed at first because `codex exec` does not accept the
  top-level `--ask-for-approval` option after the `exec` subcommand. This
  produced no review content.
- The corrected fresh read-only reviewer then returned `CHANGES_NEEDED`.
- Evidence:
  - `artifacts/s7/s7-smoke-stall-20260609-173154/reviewer/reviewer-round1.stdout.log`
  - `artifacts/s7/s7-smoke-stall-20260609-173154/reviewer/reviewer-round1.stderr.log`
  - `artifacts/s7/s7-smoke-stall-20260609-173154/reviewer/reviewer-round1-final.txt`
- Finding:
  The intended worker log was missing from the repo path, because it had been
  created one directory above the repo. The reviewer also agreed that the
  available smoke evidence does not support a confirmed first-kernel stall and
  that the run is only an incomplete manually stopped smoke.
- Response:
  Added the worker log at the correct repo path.

Round 2:

- Fresh read-only reviewer returned `CHANGES_NEEDED`.
- Evidence:
  - `artifacts/s7/s7-smoke-stall-20260609-173154/reviewer/reviewer-round2.stdout.log`
  - `artifacts/s7/s7-smoke-stall-20260609-173154/reviewer/reviewer-round2.stderr.log`
  - `artifacts/s7/s7-smoke-stall-20260609-173154/reviewer/reviewer-round2-final.txt`
- Finding:
  The worker log still had `Round 2` and `Final Status` marked pending. The
  reviewer otherwise found the smoke conclusions supported, with exactly one
  fresh local smoke documented as job `482`, first-kernel metrics plus
  second-kernel bind shown, and no full-pass/calibration/correlation overclaim.
- Response:
  Updated this reviewer section with the Round 2 result. Final status remains
  pending until a fresh reviewer accepts the completed log.

Round 3:

- Fresh read-only reviewer returned `ACCEPT`.
- Evidence:
  - `artifacts/s7/s7-smoke-stall-20260609-173154/reviewer/reviewer-round3.stdout.log`
  - `artifacts/s7/s7-smoke-stall-20260609-173154/reviewer/reviewer-round3.stderr.log`
  - `artifacts/s7/s7-smoke-stall-20260609-173154/reviewer/reviewer-round3-final.txt`
- Reviewer confirmed the worker log and evidence are substantively sufficient:
  no unsupported first-kernel stall conclusion, no full-pass/calibration/
  correlation overclaim, exactly one fresh local smoke, and a precise remaining
  blocker.

## Final Status

Complete.

Worker verdict:

- The prior bounded smoke evidence was insufficient to call a first-kernel
  deadlock/livelock/stall.
- The fresh local smoke reproduced progress past the disputed point and emitted
  first-kernel metrics before being stopped.
- No first-kernel pipeline/accounting root-cause bug was reproduced, so no code
  fix is justified for this specific issue.
- This is not a full smoke pass. The precise next blocker is full PTX smoke
  completion beyond the observed second-kernel bind, with bounded evidence if it
  crashes or stalls later.

Reviewer final verdict: `ACCEPT`.
