# S7 Bounded Parameter Sweep Worker Log

## Purpose

Advance S7 from the current single-candidate S6 comparable baseline toward a
reviewed bounded multi-candidate parameter sweep. Prefer a defensible,
plan-only design unless local simulator execution is clearly low-risk and
well-bounded.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base commit: `df5898c28a057e1441c384ff6541c9fb67873946`
- Timestamp: `2026-06-10T02:48:29+08:00`
- Worker role: `S7 Bounded Parameter Sweep Design / Optional Execution`
- Worktree at start: tracked tree clean on `dev-5060`, ahead of origin.
- Host: `dsp-ubuntu`

## Required Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/s6-correlation-search.md`
- `docs/sm120-calibration/s7-hardware-target-metrics.md`
- `docs/sm120-calibration/s7-simulator-candidate-metrics-bridge.md`
- `docs/sm120-calibration/worker-logs/worker-20260610-022405-s7-target-selection.md`

Additional inspected evidence:

- `artifacts/s7/s7-target-selection-20260610-022405/`
- `simulator-remodeled/util/tuner/search_sm120_correlation.py`
- `simulator-remodeled/util/tuner/ingest_sm120_simulator_candidate_metrics.py`
- `simulator-remodeled/util/tuner/parse_sm120_microbench.py`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema/sm120.schema.yaml`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated/tested-cfgs/SM120_RTX5060/gpgpusim.config`
- `simulator-remodeled/util/job_launching/common.py`
- `simulator-remodeled/util/job_launching/configs/define-standard-cfgs.yml`

## Hard Rules Observed

- Did not run any simulator workload on `dsp5060`.
- Did not copy the main workspace to `dsp5060`.
- Did not use hardware metrics as candidate metrics.
- Did not fabricate candidate metrics for unrun candidates.
- Did not promote accepted/generated/latest configs.
- Did not update `calibration-results/latest`.
- Kept generated real artifacts under ignored `artifacts/s7/`.

## Baseline Artifact Inspection

Existing target-selection artifact root:

```text
artifacts/s7/s7-target-selection-20260610-022405/
```

Files inspected:

- `RTX5060-backprop-4096-s6-comparable-targets-template.yaml`
- `RTX5060-job486-simulator-candidate-metrics-policy-draft.yaml`
- `RTX5060-job486-s6-comparable-baseline-supplied-metrics.yaml`
- `RTX5060-job486-s6-comparable-baseline-report.yaml`

Baseline facts:

- S6 baseline manifest schema: `sm120_correlation_search_manifest_v1`.
- Baseline status: `draft_not_applied`.
- Baseline candidate count: `1`.
- Baseline search keys:
  - `-latency_L0_to_L1 = 39`
  - `-prefetch_per_stream_buffer_size = 8`
- Baseline comparable target metrics:
  - `cuda_kernel_avg_time_ms`
  - `cuda_kernel_bpnn_adjust_weights_cuda_total_time_ms`
  - `cuda_kernel_bpnn_layerforward_cuda_total_time_ms`
  - `cuda_kernel_total_time_ms`
- Baseline score: `0.482422`.

The hardware target template is `template_not_runnable` until search
parameters and local simulator candidate metrics are filled. The existing job
`486` candidate metrics are simulator candidate evidence only.

## S6 Constraints Confirmed

The S6 harness requires:

- `schema_id: sm120_correlation_search_manifest_v1`
- `search.stage: rf_prefetch_remodeled_parameters`
- `candidate_strategy: cartesian_product`
- `max_candidates` from `1` to `64`
- each parameter key active in the selected generated base config
- schema owner `calibration_result`
- provenance `correlation_search`
- every generated candidate covered exactly once by
  `evaluation.candidate_metrics`
- every target metric available and numeric for every candidate.

The bridge emits a runnable S6 supplied-metrics manifest only when `--reviewed`
is supplied and the complete candidate space is covered. Otherwise it emits a
non-runnable scaffold.

## Candidate Space Design

Checked-in design document:

```text
docs/sm120-calibration/s7-bounded-parameter-sweep-design.md
```

Ignored plan-only scaffold:

```text
artifacts/s7/s7-bounded-sweep-20260610-024829/RTX5060-backprop-4096-s7-bounded-sweep-plan.yaml
artifacts/s7/s7-bounded-sweep-20260610-024829/RTX5060-backprop-4096-s7-bounded-sweep-s6-manifest.DRAFT-NONRUNNABLE.yaml
```

Selected keys:

- `-latency_L0_to_L1`, base value `39`, values `[37, 39]`.
- `-prefetch_per_stream_buffer_size`, base value `8`, values `[8, 10]`.

Justification:

- Both keys are active in generated
  `SM120_RTX5060/gpgpusim.config`.
- Both keys are schema-owned by `calibration_result` in `gpgpusim.config`.
- Both keys are listed under S5/S6
  `rf_prefetch_remodeled_parameters`.
- Both are already used by the one-candidate baseline, so extending them gives
  a minimal multi-candidate path.
- `-is_instruction_prefetching_enabled 1` is active, so the prefetch buffer
  size knob is live in this config.
- The expanded search has only four candidates.

Excluded keys:

- Other `rf_prefetch_remodeled_parameters` keys are active, but adding them
  would expand the search beyond a minimal two-knob sensitivity step. Several
  affect register-file, scheduler, PRT, or interwarp coalescing behavior and
  are not justified by a single-run backprop timing target.

## Execution Decision

No new local simulator jobs were run.

Reason:

- The job `486` candidate-metrics artifact records simulator runtime
  observations of `390.0` and `2398.0` seconds.
- A four-candidate sweep would require three new candidate runs beyond the
  baseline, multiplying a runtime that is already substantial.
- S6 cannot produce a valid multi-candidate `supplied_metrics` report until all
  generated candidates have real local simulator metrics.
- Running additional jobs in this worker would be higher risk than a
  documentation/artifact-only bounded plan.

The plan records setup-only and execution commands for a future execution
worker, with explicit ProcMan and host gating.

## ProcMan State

Correct ProcMan clean-state check:

```bash
python3 simulator-remodeled/util/job_launching/procman.py -p
```

Result:

```text
Nothing Active
```

Note: an initial positional `procman.py status` probe was rejected by the old
CLI with `FileNotFoundError: status`; it did not launch a simulator job. The
correct `-p` form was then used.

## Changed Files

Tracked docs:

- `docs/sm120-calibration/s7-bounded-parameter-sweep-design.md`
- `docs/sm120-calibration/worker-logs/worker-20260610-024829-s7-bounded-sweep.md`

Ignored generated artifacts:

- `artifacts/s7/s7-bounded-sweep-20260610-024829/RTX5060-backprop-4096-s7-bounded-sweep-plan.yaml`
- `artifacts/s7/s7-bounded-sweep-20260610-024829/RTX5060-backprop-4096-s7-bounded-sweep-s6-manifest.DRAFT-NONRUNNABLE.yaml`

No code changes were required. No tests were added.

## Validation

| Command | Result |
| --- | --- |
| `python3 simulator-remodeled/util/job_launching/procman.py -p` | pass; `Nothing Active` |
| S7 bounded plan YAML parser/semantic checks | pass; both artifacts have `4` generated candidates, `1` supplied baseline metric entry, and `4` comparable `_time_ms` targets |
| Expected failure: bridge readiness against one baseline candidate for four-candidate template | pass; bridge emitted non-runnable scaffold with blockers `missing_candidate_signatures:3` and `input_template_status_template_not_runnable` |
| Expected failure: S6 dry-run rejects the non-runnable S6 draft because three candidate signatures are missing | pass; failed with `evaluation candidate_metrics missing 3 generated candidates` |
| Expected failure: S6 dry-run rejects the S7 plan scaffold schema | pass; failed with `manifest schema_id must be sm120_correlation_search_manifest_v1` |
| `PYTHONDONTWRITEBYTECODE=1 python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only` | pass; generated `SM120_RTX5070_TI` and `SM120_RTX5060` with `gpgpu_keys=217`, `trace_keys=13` |
| `git diff --check` | pass |
| Protected config/latest scoped `git status --short -- ...` | pass; empty output |
| `git check-ignore -v artifacts/s7/s7-bounded-sweep-20260610-024829/...` | pass; both generated artifacts are ignored by `.gitignore:4:artifacts/s7/` |

Protected config/latest scoped paths:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/tested-cfgs`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated/tested-cfgs`
- `simulator-remodeled/gpu-simulator/configs/generated/tested-cfgs`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/base`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/overlays`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/calibration-results`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema`

## Artifact Hashes

```text
1f2e51d8356dc32ab62b08f4f3b1409a0b41fd239f02557823efb945c30408ca  artifacts/s7/s7-bounded-sweep-20260610-024829/RTX5060-backprop-4096-s7-bounded-sweep-plan.yaml
d72856f42b8320318560d874587d273d72f79b5cc6b26723e3f55d149cb4a445  artifacts/s7/s7-bounded-sweep-20260610-024829/RTX5060-backprop-4096-s7-bounded-sweep-s6-manifest.DRAFT-NONRUNNABLE.yaml
```

## Reviewer Rounds

Reviewer round 1:

- Reviewer: fresh blank-context Codex read-only reviewer.
- Output:
  `artifacts/s7/s7-bounded-sweep-20260610-024829/reviewer-round1-final.txt`
- Verdict: `ACCEPT`.
- Findings: none blocking.
- Reviewer confirmed:
  - The two sweep keys are active in the generated RTX5060 config, owned by
    `calibration_result`, and present in the S5/S6
    `rf_prefetch_remodeled_parameters` stage map.
  - The target metrics are simulator-comparable CUDA timing metrics only.
  - Candidate metrics are simulator candidate evidence and explicitly not
    hardware target metrics.
  - The draft S6 manifest is correctly non-runnable because three generated
    candidate metric signatures are missing.
  - Avoiding new local simulator execution is defensible given prior runtime
    evidence and the need for three additional candidate runs.
  - Protected accepted/generated/latest config paths are untouched.
- Residual risks:
  - The sweep remains plan-only; no multi-candidate sensitivity evidence exists
    yet.
  - Hardware target data remains single-run draft evidence.

## Final Status

Accepted after fresh blank-context reviewer round 1.

This worker produced a reviewed bounded sweep design and ignored plan-only
artifacts. No local simulator jobs were run, no runnable multi-candidate S6
report was generated, and promotion remains closed until missing candidate
metrics are collected and reviewed.
