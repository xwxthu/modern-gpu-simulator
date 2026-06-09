# S7 Bounded Sweep Execution Preparation Worker Log

## Purpose

Prepare the reviewed four-candidate S7 bounded sweep for execution without
performing broad simulator execution. Do setup-only planning and alias
validation for the three missing non-baseline candidates.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base commit: `63372a00a70ba8cc8ef30fce23c6890adf1d772b`
- Timestamp: `2026-06-10T03:25:57+08:00`
- Host: `dsp-ubuntu`
- Worker role: `S7 Bounded Sweep Execution Preparation`
- Worktree at start: tracked tree clean on `dev-5060`, ahead of origin.

## Required Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/s7-bounded-parameter-sweep-design.md`
- `docs/sm120-calibration/worker-logs/worker-20260610-024829-s7-bounded-sweep.md`
- `docs/sm120-calibration/s7-simulator-candidate-metrics-bridge.md`

Additional inspected files:

- `artifacts/s7/s7-bounded-sweep-20260610-024829/RTX5060-backprop-4096-s7-bounded-sweep-plan.yaml`
- `artifacts/s7/s7-bounded-sweep-20260610-024829/RTX5060-backprop-4096-s7-bounded-sweep-s6-manifest.DRAFT-NONRUNNABLE.yaml`
- `simulator-remodeled/util/job_launching/common.py`
- `simulator-remodeled/util/job_launching/run_simulations.py`
- `simulator-remodeled/util/job_launching/configs/define-standard-cfgs.yml`

## Hard Rules Observed

- Did not run any simulator workload on `dsp5060`.
- Did not copy the workspace to `dsp5060`.
- Did not promote accepted/generated/latest configs.
- Did not update `calibration-results/latest`.
- Did not fabricate simulator candidate metrics.
- Did not commit or leave temporary alias changes.
- Kept generated setup artifacts under ignored `artifacts/s7/`.

## ProcMan And Host Gate

Pre-setup command:

```bash
python3 simulator-remodeled/util/job_launching/procman.py -p
```

Result: `Nothing Active`.

Host check:

```text
dsp-ubuntu
```

This is not `dsp5060`.

Final ProcMan command:

```bash
python3 simulator-remodeled/util/job_launching/procman.py -p
```

Result: `Nothing Active`, recorded in:

```text
artifacts/s7/s7-bounded-sweep-20260610-024829/final-procman-status.log
```

## Alias Strategy

The launcher reads all YAML files matching:

```text
simulator-remodeled/util/job_launching/configs/define-*.yml
```

and composes config names as `BASE-EXTRA`. Therefore the cleanest temporary
alias strategy was to create a throwaway file:

```text
simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml
```

with only the three missing extra-param aliases, run setup-only, then delete
the file. This avoided editing `define-standard-cfgs.yml`.

Temporary aliases used:

```yaml
S7SWEEP_L0L1_37_PREFETCH_8:
    extra_params: |
        -latency_L0_to_L1 37
        -prefetch_per_stream_buffer_size 8

S7SWEEP_L0L1_37_PREFETCH_10:
    extra_params: |
        -latency_L0_to_L1 37
        -prefetch_per_stream_buffer_size 10

S7SWEEP_L0L1_39_PREFETCH_10:
    extra_params: |
        -latency_L0_to_L1 39
        -prefetch_per_stream_buffer_size 10
```

Evidence:

- `define-standard-cfgs.yml` SHA256 before and after:
  `4fbd298025547954b1ae6d1e1d6c70a67226254b25de4b5c834076663e683268`
- Final `git diff -- simulator-remodeled/util/job_launching/configs/define-standard-cfgs.yml simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml` was empty.
- Final `git status --short -- simulator-remodeled/util/job_launching/configs/define-standard-cfgs.yml simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml` was empty.
- `find /home/xiewx/accel-0608 -path '*/define-s7-bounded-sweep-temp.yml' -print` returned no paths after cleanup.

Note: one initial `apply_patch` invocation was rooted at
`/home/xiewx/accel-0608` rather than the repo and briefly created the temporary
alias file outside `modern-gpu-simulator`. It was deleted before any successful
setup-only run. The successful alias file was created at the correct in-repo
path and was removed before final validation.

## Setup-Only Runs

All setup-only runs used:

```bash
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment
```

An initial shell preflight with `set -u` failed while sourcing the legacy setup
script because `OPENCL_REMOTE_GPU_HOST` was unset. It did not create a run
directory or launch a job. ProcMan remained `Nothing Active`. Subsequent
setup-only runs used normal sourced environment behavior.

Candidate `0001` command:

```bash
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN-S7SWEEP_L0L1_37_PREFETCH_8 \
  -N s7-bounded-sweep-20260610-024829-candidate-0001-plan \
  -r artifacts/s7/s7-bounded-sweep-20260610-024829/sim-plan/candidate_0001 \
  -l local \
  -n
```

Candidate `0002` command:

```bash
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN-S7SWEEP_L0L1_37_PREFETCH_10 \
  -N s7-bounded-sweep-20260610-024829-candidate-0002-plan \
  -r artifacts/s7/s7-bounded-sweep-20260610-024829/sim-plan/candidate_0002 \
  -l local \
  -n
```

Candidate `0004` command:

```bash
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN-S7SWEEP_L0L1_39_PREFETCH_10 \
  -N s7-bounded-sweep-20260610-024829-candidate-0004-plan \
  -r artifacts/s7/s7-bounded-sweep-20260610-024829/sim-plan/candidate_0004 \
  -l local \
  -n
```

Setup logs:

- `artifacts/s7/s7-bounded-sweep-20260610-024829/setup-logs/candidate_0001-setup-only.log`
- `artifacts/s7/s7-bounded-sweep-20260610-024829/setup-logs/candidate_0002-setup-only.log`
- `artifacts/s7/s7-bounded-sweep-20260610-024829/setup-logs/candidate_0004-setup-only.log`

Each setup log printed `Running Simulations`, the expected config alias, and
the expected appended parameters. None printed `Job <id> queued`.

## Setup Artifact Verification

Generated setup-only run directories:

- `artifacts/s7/s7-bounded-sweep-20260610-024829/sim-plan/candidate_0001/backprop-rodinia-2.0-ft/4096___data_result_4096_txt/RTX5060_SM120_GEN-S7SWEEP_L0L1_37_PREFETCH_8/`
- `artifacts/s7/s7-bounded-sweep-20260610-024829/sim-plan/candidate_0002/backprop-rodinia-2.0-ft/4096___data_result_4096_txt/RTX5060_SM120_GEN-S7SWEEP_L0L1_37_PREFETCH_10/`
- `artifacts/s7/s7-bounded-sweep-20260610-024829/sim-plan/candidate_0004/backprop-rodinia-2.0-ft/4096___data_result_4096_txt/RTX5060_SM120_GEN-S7SWEEP_L0L1_39_PREFETCH_10/`

Each contains the expected setup files: `gpgpusim.config`, `justrun.sh`,
`slurm.sim`, copied config support files, and a copied local simulator runtime
under `gpgpu-sim-builds/`.

Effective config verification:

```text
candidate_0001: -latency_L0_to_L1 last=37 line=349 expected=37
candidate_0001: -prefetch_per_stream_buffer_size last=8 line=350 expected=8
candidate_0002: -latency_L0_to_L1 last=37 line=349 expected=37
candidate_0002: -prefetch_per_stream_buffer_size last=10 line=350 expected=10
candidate_0004: -latency_L0_to_L1 last=39 line=349 expected=39
candidate_0004: -prefetch_per_stream_buffer_size last=10 line=350 expected=10
```

Recorded in:

```text
artifacts/s7/s7-bounded-sweep-20260610-024829/final-setup-only-verification.log
```

No simulator output evidence was present in the setup-only directories:

- no `.o*` or `.e*` simulator output/error files,
- no `procman*` or `torque_out*` files,
- no `gpu_sim_cycle`, `gpu_tot_sim_cycle`, `PASSED`, or `FAILED` markers.

## Execution Decision

No actual simulator job was run by this worker.

Reason:

- The task explicitly preferred setup-only execution preparation.
- The prior job `486` simulator-candidate metrics artifact records
  `parsed_simulator_observations.gpgpu_simulation_time_seconds_observed:
  [390.0, 2398.0]`.
- Three new missing non-baseline candidates remain necessary before a valid
  four-candidate S6 ranking can be produced.
- Launching one candidate would still expose substantial runtime risk while
  leaving the S6 manifest non-runnable because two other candidate signatures
  would remain missing.

Because no candidate was run, no simulator candidate metrics were produced and
no S6 readiness/report status changed.

## S6 Readiness Check

The draft S6 manifest was intentionally still non-runnable:

```bash
python3 simulator-remodeled/util/tuner/search_sm120_correlation.py \
  --manifest artifacts/s7/s7-bounded-sweep-20260610-024829/RTX5060-backprop-4096-s7-bounded-sweep-s6-manifest.DRAFT-NONRUNNABLE.yaml \
  --output artifacts/s7/s7-bounded-sweep-20260610-024829/should-not-exist-report.yaml \
  --dry-run
```

Expected result:

```text
error: evaluation candidate_metrics missing 3 generated candidates
exit=1
```

Recorded in:

```text
artifacts/s7/s7-bounded-sweep-20260610-024829/final-s6-draft-nonrunnable-check.log
```

## Validation

| Command | Result |
| --- | --- |
| `python3 simulator-remodeled/util/job_launching/procman.py -p` before setup | pass; `Nothing Active` |
| `run_simulations.py ... -n` for candidates `0001`, `0002`, `0004` | pass; setup-only directories created |
| setup-only config delta verifier | pass; last effective values match candidate plan |
| setup-only no-execution grep/file check | pass; no queued jobs or simulator output markers |
| temporary alias cleanup checks | pass; no temp alias file remains and standard config hash unchanged |
| `git diff --check` | pass |
| `PYTHONDONTWRITEBYTECODE=1 python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only` | pass; generated `SM120_RTX5070_TI` and `SM120_RTX5060`, each with `gpgpu_keys=217`, `trace_keys=13` |
| protected config/latest scoped status check | pass; empty output |
| artifact ignored check | pass; `.gitignore:4:artifacts/s7/` covers artifact root, setup logs, and run config |
| draft S6 non-runnable check | pass; expected failure due to `3` missing generated candidates |
| final ProcMan check | pass; `Nothing Active` |

Validation artifacts:

- `artifacts/s7/s7-bounded-sweep-20260610-024829/final-git-diff-check.log`
- `artifacts/s7/s7-bounded-sweep-20260610-024829/final-generate-sm120-check-only.log`
- `artifacts/s7/s7-bounded-sweep-20260610-024829/final-protected-config-status.log`
- `artifacts/s7/s7-bounded-sweep-20260610-024829/final-artifact-ignore-check.log`
- `artifacts/s7/s7-bounded-sweep-20260610-024829/final-procman-status.log`
- `artifacts/s7/s7-bounded-sweep-20260610-024829/final-setup-only-verification.log`
- `artifacts/s7/s7-bounded-sweep-20260610-024829/final-s6-draft-nonrunnable-check.log`

## Changed Files

Tracked:

- `docs/sm120-calibration/worker-logs/worker-20260610-032557-s7-sweep-exec-prep.md`

Temporary, removed before final status:

- `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`

Ignored artifacts:

- setup-only logs and run directories under
  `artifacts/s7/s7-bounded-sweep-20260610-024829/`

No accepted/generated/latest configs were changed.

## Reviewer Rounds

- Initial reviewer CLI attempt failed before model start because the
  `approval_policy` value was over-quoted. This produced no review verdict.
  Evidence:
  `artifacts/s7/s7-bounded-sweep-20260610-024829/reviewer-round-exec-prep/reviewer-stderr.txt`
  before rerun.
- Round 1 fresh blank-context read-only reviewer:
  - Prompt:
    `artifacts/s7/s7-bounded-sweep-20260610-024829/reviewer-round-exec-prep/reviewer-prompt.txt`
  - Command:
    `codex exec -C /home/xiewx/accel-0608/modern-gpu-simulator --sandbox read-only -c approval_policy=never --ephemeral --output-last-message artifacts/s7/s7-bounded-sweep-20260610-024829/reviewer-round-exec-prep/reviewer-final.txt - < artifacts/s7/s7-bounded-sweep-20260610-024829/reviewer-round-exec-prep/reviewer-prompt.txt`
  - Artifacts:
    `artifacts/s7/s7-bounded-sweep-20260610-024829/reviewer-round-exec-prep/reviewer-final.txt`,
    `artifacts/s7/s7-bounded-sweep-20260610-024829/reviewer-round-exec-prep/reviewer-stdout.txt`,
    `artifacts/s7/s7-bounded-sweep-20260610-024829/reviewer-round-exec-prep/reviewer-stderr.txt`,
    `artifacts/s7/s7-bounded-sweep-20260610-024829/reviewer-round-exec-prep/reviewer-exitcode`
  - Verdict: `ACCEPT`
  - Findings: none.
  - Reviewer confirmed setup-only evidence is sufficient, no launch evidence
    exists, temporary aliases and protected paths are clean, artifacts are
    ignored, the decision not to run a non-baseline candidate is justified, and
    promotion remains closed.

## Final Status

Accepted after fresh blank-context reviewer round 1.

This worker prepared the missing three non-baseline S7 bounded-sweep candidates
for execution by validating temporary aliases and setup-only run directories.
No actual simulator job was run, no simulator candidate metrics were produced,
the draft S6 manifest remains intentionally non-runnable, and promotion remains
closed.
