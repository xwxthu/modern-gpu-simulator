# S7 RTX5060 Local Smoke And Correlation Prep Worker Log

## Purpose

Prepare the next S7 step after the real RTX5060 tuner microbenchmark draft:
local simulator smoke setup on the strong server and real supplied-metrics
correlation preparation. This worker did not run any full simulator workload on
`dsp5060`, did not write accepted configs, and did not write
`calibration-results/*/latest.yaml`.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Host: `dsp-ubuntu`
- Branch: `dev-5060`
- Base commit: `bade0d0bc4304f5aa3826b3ca572a14c3a30a22f`
- Base commit subject: `fix: restore CUDA 13 tuner microbench builds`
- Timestamp: `2026-06-09T00:08:56+08:00`
- Run id: `rtx5060-s7-local-smoke-20260609-000856`
- Artifact root: `artifacts/s7/rtx5060-s7-local-smoke-20260609-000856/`

## Inputs

- Real raw RTX5060 microbenchmark output:
  `artifacts/s7/rtx5060-s7-tuner-buildfix-20260608-233545/sm120-rtx5060-microbench.txt`
  - SHA256: `565a904d232f71c4b4ad6efeb524fb67a8d5b24e88644bc33b4b0d5393bbadf4`
- Real S5 microbenchmark draft:
  `artifacts/s7/rtx5060-s7-tuner-buildfix-20260608-233545/RTX5060-real-microbench-draft.yaml`
  - SHA256: `eb3d12bd2e23601a86c4e4ef9353e54c6913130ef6282880c69b824fb1caece9`
  - Status: `draft_not_applied`
- Prior worker log:
  `docs/sm120-calibration/worker-logs/worker-20260608-235102-s7-tuner-buildfix.md`

## Commands And Evidence

- Created run artifacts:
  `mkdir -p artifacts/s7/rtx5060-s7-local-smoke-20260609-000856`
  and copied the S7 validation manifest template.
- Generator check-only:
  `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`
  - Exit code: `0`
  - Evidence: `generate-check-only.log`
  - Output generated both `SM120_RTX5070_TI` and `SM120_RTX5060` bootstrap
    profiles with `gpgpu_keys=217` and `trace_keys=13`.
- S7 helper dry-run:
  `python3 simulator-remodeled/util/tuner/check_sm120_s7_validation.py --gpu RTX5060 --run-id rtx5060-s7-local-smoke-20260609-000856`
  - Exit code: `0`
  - Evidence: `s7-helper-dry-run.log`
  - Confirmed `RTX5060_SM120_GEN` and printed local smoke setup/run commands.
  - No ssh, no hardware command, and no simulator launch were performed by the
    helper.
- S6 fixture dry-run:
  `python3 simulator-remodeled/util/tuner/search_sm120_correlation.py --manifest simulator-remodeled/util/tuner/testdata/sm120_correlation_search_fixture.yaml --dry-run --print-planned-commands --command-candidate-limit 2`
  - Exit code: `0`
  - Evidence: `s6-fixture-dry-run.log`
  - Validated the synthetic harness only. The fixture metrics were not used as
    RTX5060 calibration evidence.
- Local smoke setup-only command:
  `python3 simulator-remodeled/util/job_launching/run_simulations.py -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 -C RTX5060_SM120_GEN -N rtx5060-s7-local-smoke-20260609-000856-smoke-plan -r artifacts/s7/rtx5060-s7-local-smoke-20260609-000856/sim-smoke-plan -l local -n`
  with `CUDA_INSTALL_PATH=/usr/local/cuda-13.2` defaulted by the runbook
  snippet, followed by local setup scripts.
  - Exit code: `1`
  - Evidence: `local-smoke-plan.log`
  - Failure: `common.PathMissing` for
    `/home/xiewx/accel-0608/modern-gpu-simulator/simulator-remodeled/gpu-simulator/gpgpu-sim/lib/gcc-13.3.0/cuda-13010/release`.
  - This was setup-only with `-n`; no `procman.py` launch happened.
- Local prerequisite inspection:
  `hostname`, `nvcc --version`, `gcc --version`, `g++ --version`, and `find`
  checks for local simulator/app build artifacts.
  - Evidence: `local-build-prereq-inspection.log`
  - Host: `dsp-ubuntu`
  - Local CUDA found by PATH: `/usr/local/cuda-13.1/bin/nvcc`,
    release `13.1 V13.1.115`
  - Missing: `simulator-remodeled/gpu-simulator/gpgpu-sim/lib`
  - Missing: `simulator-remodeled/gpu-app-collection/bin`
  - Missing: setup-only run directory
    `artifacts/s7/rtx5060-s7-local-smoke-20260609-000856/sim-smoke-plan`

## Smoke Decision

The planned benchmark is intentionally small:
`rodinia_2.0-ft:backprop-rodinia-2.0-ft:0`, PTX mode. However, setup-only did
not pass because the local simulator release library and gpu-app binary tree are
absent. The worker stopped before the actual local smoke command, as required by
the runbook. No full simulator was run on `dsp5060` or locally.

## Supplied Metrics Prep

Prepared:
`artifacts/s7/rtx5060-s7-local-smoke-20260609-000856/RTX5060-s6-supplied-metrics.TEMPLATE.yaml`

This is a template skeleton only:

- `evaluation.mode: supplied_metrics`
- `candidate_metrics: []`
- `status: template_blocked_no_local_smoke_metrics`
- References the real RTX5060 S5 draft and raw microbenchmark hashes.
- Uses a minimal S6 candidate skeleton around
  `-gpgpu_reg_file_port_throughput`, an active `calibration_result` key in the
  S6 `rf_prefetch_remodeled_parameters` stage.
- Does not fabricate hardware targets or simulator metrics.

No real S6 ranking report was generated because S6 requires complete
`candidate_metrics` for every generated candidate.

## Artifact Hashes

- `RTX5060-s6-supplied-metrics.TEMPLATE.yaml`:
  `91333cbe38eff2688c7219a5f8049471df50c84f09c42f463bd60c2905c43633`
- `generate-check-only.log`:
  `331bc785a318910d503f4c8e7b92f1d6eba86b98694cfe4828bb9750ce81734b`
- `s7-helper-dry-run.log`:
  `687fad2ed030a61fa7d80b232d9f3ed678aed7b4e9adeb617595884741b99d5b`
- `s6-fixture-dry-run.log`:
  `8ad9c0780b9f5c6b74f5be4297a3f3e4336881fabbb119361ddb3ad68517a778`
- `local-smoke-plan.log`:
  `6e851dd2aec7fc77f5b1e5b76c8979dae142d1462e6a39a19993bfaefdbd6d5c`
- `local-build-prereq-inspection.log`:
  `7c45df02be4dfa9b48e92a828331b6610ae2c08e8558815c22cfb4c978825bc7`
- `validation-manifest.yaml`:
  `b3d1e23709d3862e1caece7420487b0d266e2e3141e622f41695c548492a5270`
- Aggregate artifact hash manifest:
  `artifacts/s7/rtx5060-s7-local-smoke-20260609-000856/artifact-files.sha256`

## Required Checks

- `git diff --check`
  - Exit code: `0`
  - Evidence: `git-diff-check.log`, `post-review-git-diff-check.log`
  - Empty output.
- `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`
  - Exit code: `0`
  - Evidence: `final-generate-check-only.log`,
    `post-review-generate-check-only.log`
  - Output generated both `SM120_RTX5070_TI` and `SM120_RTX5060` bootstrap
    profiles with `gpgpu_keys=217` and `trace_keys=13`.
- accepted/generated config scoped status check
  - Command:
    `git status --short -- <SM120 tested/generated config paths and calibration-results path>`
  - Exit code: `0`
  - Evidence: `accepted-generated-config-scoped-status.log`,
    `post-review-accepted-generated-config-scoped-status.log`
  - Empty output.
  - No accepted config, generated tested config, calibration-result file, or
    `latest.yaml` path was modified.

## Changed Files

Tracked documentation/log changes:

- `docs/sm120-calibration/worker-logs/worker-20260609-000856-s7-local-smoke.md`

Ignored artifact evidence:

- `artifacts/s7/rtx5060-s7-local-smoke-20260609-000856/`

No accepted config, generated tested config, staged delta, or `latest.yaml`
write was made.

## Reviewer Rounds

- Codex CLI reviewer attempt:
  - Intended mode: read-only blank-context review.
  - Result: no verdict; local `codex exec` rejected approval-related CLI
    arguments before starting the review.
  - Evidence:
    `artifacts/s7/rtx5060-s7-local-smoke-20260609-000856/reviewer-round1-codex.stderr.txt`
    and
    `artifacts/s7/rtx5060-s7-local-smoke-20260609-000856/reviewer-round1-codex.exitcode`
    (`2`).
- Round 1 blank-context reviewer: ACCEPT.
  - Reviewer runner: Claude CLI fallback with read-only Bash tools and edit
    tools disallowed.
  - Exit code: `0`
  - Output:
    `artifacts/s7/rtx5060-s7-local-smoke-20260609-000856/reviewer-round1-claude.txt`
  - Output SHA256:
    `48653a53352dde50cbf6470ff3b2bbee94debf10477823f0e684d21ee9af5199`
  - Reviewer rationale: readiness checks passed, setup-only failure was
    honestly documented, no fake supplied metrics were created, no full
    simulator was launched on `dsp5060`, and protected config/latest paths were
    unchanged.

## Final Status

Partial/blocked with reviewer ACCEPT. Local readiness and dry-run harness checks
passed, and a real supplied_metrics template was prepared without fake metrics.
Local simulator smoke remains blocked because setup-only cannot find the local
simulator release library or gpu-app binary tree. Correlation remains
dry-run/template-only until real local simulator metrics exist.
