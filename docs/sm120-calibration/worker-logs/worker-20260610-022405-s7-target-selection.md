# S7 Target Selection / Bounded Baseline S6 Worker Log

## Purpose

Close the immediate S7 blocker between hardware target metrics and simulator
candidate metrics by defining and implementing a reviewed target metric
selection policy. Produce a draft-only S6 supplied-metrics baseline report if
the existing job `486` simulator candidate evidence can be compared using only
simulator-comparable CUDA-kernel timing metrics.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base commit: `107ebd5fc73640fff5fe44aed4394b0bc0f9ce49`
- Timestamp: `2026-06-10T02:24:05+08:00`
- Worker role: `S7 Calibration Target Selection / Bounded Baseline S6`
- Worktree at start: tracked tree clean on `dev-5060`, ahead of origin.

## Required Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/s6-correlation-search.md`
- `docs/sm120-calibration/s7-hardware-target-metrics.md`
- `docs/sm120-calibration/s7-simulator-candidate-metrics-bridge.md`
- `docs/sm120-calibration/worker-logs/worker-20260610-012643-s7-sim-metrics-bridge.md`
- `simulator-remodeled/util/tuner/collect_sm120_hardware_metrics.py`
- `simulator-remodeled/util/tuner/ingest_sm120_simulator_candidate_metrics.py`
- Real ignored inputs:
  - `artifacts/s7/s7-hardware-target-20260610-003544/RTX5060-backprop-4096-hardware-target-draft.yaml`
  - `artifacts/s7/s7-hardware-target-20260610-003544/RTX5060-backprop-4096-s6-supplied-metrics-template.yaml`
  - `artifacts/s7/s7-kernel2-attribution-20260609-211410/RTX5060-job486-simulator-candidate-metrics-draft.yaml`

## Hard Rules Observed

- Did not run any simulator workload on `dsp5060`.
- Did not use job `486` as hardware target data.
- Did not fabricate `native_wall_time_seconds` or add it to simulator
  candidate metrics.
- Did not include `native_wall_time_seconds` in the S6 comparable target list.
- Did not promote accepted/generated/latest configs.
- Did not write or update `calibration-results/latest`.
- Kept regenerated real artifacts under ignored `artifacts/s7/`.

## Target Metric Policy

Implemented standard terms:

- Hardware characterization metrics: retained in the hardware target artifact
  for provenance and run review.
- Simulator-comparable calibration targets: copied into the S6 target
  handoff/template because simulator candidate metrics can produce comparable
  values.
- Excluded/non-comparable metrics: retained or reported as context, but not
  used as S6 calibration targets.

Current inclusion rule:

- Include only Nsight Systems CUDA kernel elapsed-time metrics ending in
  `_time_ms`, because the simulator candidate bridge derives comparable
  per-kernel time from `gpu_sim_cycle / (core_clock_mhz * 1000)`.
- Exclude native process metrics, including `native_wall_time_seconds`,
  `native_user_time_seconds`, `native_sys_time_seconds`, and
  `native_max_rss_kbytes`, from S6 handoff/template while retaining them as
  hardware characterization metrics.
- Exclude `cuda_kernel_invocations` from S6 targets for now. It remains context
  rather than a calibration timing target.

## Actions

Updated `simulator-remodeled/util/tuner/collect_sm120_hardware_metrics.py`:

- Added `calibration_target_policy()`.
- Added explicit metric roles in each hardware target metric record.
- Removed the previous ad hoc inclusion of `native_wall_time_seconds` in S6
  templates.
- Added a policy block to generated hardware target YAML.

Added focused policy tests:

- `simulator-remodeled/util/tuner/test_collect_sm120_hardware_metrics.py`
- The test verifies that `native_wall_time_seconds` is retained in
  `target_metrics` as `hardware_characterization`, excluded from
  `s6_supplied_metrics_handoff.target_metrics`, and absent from generated S6
  target handoff semantics.

Updated docs:

- `docs/sm120-calibration/s6-correlation-search.md`
- `docs/sm120-calibration/s7-hardware-target-metrics.md`
- `docs/sm120-calibration/s7-simulator-candidate-metrics-bridge.md`

Generated ignored target-selection artifacts under:

```text
artifacts/s7/s7-target-selection-20260610-022405/
```

Important generated artifacts:

- `RTX5060-backprop-4096-hardware-target-policy-draft.yaml`
- `RTX5060-backprop-4096-s6-comparable-targets-template.yaml`
- `RTX5060-job486-simulator-candidate-metrics-policy-draft.yaml`
- `RTX5060-job486-s6-comparable-baseline-template.yaml`
- `RTX5060-job486-s6-comparable-baseline-supplied-metrics.yaml`
- `RTX5060-job486-s6-comparable-baseline-report.yaml`
- `reviewer-round1-codex.txt`

The hardware policy artifact was regenerated locally from the real
`s7-hardware-target-20260610-003544` native/Nsight input files. No new remote
collection was performed.

## Baseline S6 Result

Produced a single-candidate S6 `evaluation.mode: supplied_metrics` manifest and
ranked report as baseline validation only:

```text
artifacts/s7/s7-target-selection-20260610-022405/RTX5060-job486-s6-comparable-baseline-supplied-metrics.yaml
artifacts/s7/s7-target-selection-20260610-022405/RTX5060-job486-s6-comparable-baseline-report.yaml
```

Baseline search parameters:

- `-latency_L0_to_L1 = 39`
- `-prefetch_per_stream_buffer_size = 8`

Both are active in the generated RTX5060 base config, schema-owned by
`calibration_result`, listed in the S6 `rf_prefetch_remodeled_parameters`
stage, and fixed to one value each for a one-candidate baseline.

Comparable S6 target metrics:

- `cuda_kernel_avg_time_ms = 0.0056`
- `cuda_kernel_bpnn_adjust_weights_cuda_total_time_ms = 0.008704`
- `cuda_kernel_bpnn_layerforward_cuda_total_time_ms = 0.002496`
- `cuda_kernel_total_time_ms = 0.0112`

Job `486` candidate metrics used:

- `cuda_kernel_total_time_ms = 0.017355304`
- `cuda_kernel_avg_time_ms = 0.008677652`
- `cuda_kernel_bpnn_layerforward_cuda_total_time_ms = 0.002927652`
- `cuda_kernel_bpnn_adjust_weights_cuda_total_time_ms = 0.014427652`

S6 report summary:

- `evaluation_mode: supplied_metrics`
- `candidate_count: 1`
- `target_metric_count: 4`
- `best_candidate_id: candidate_0001`
- `best_score: 0.482422`
- `changed_key_count: 0`
- `status: draft_not_applied`
- `handoff.do_not_claim_calibrated: true`

This is not calibration promotion. It validates that comparable hardware
targets and simulator candidate metrics can now flow through S6 scoring without
using native wall time.

## Artifact Hashes

```text
2c76b1190651d373326b443721f415736061b02fea515cd7aa76050be07b73b6  artifacts/s7/s7-target-selection-20260610-022405/RTX5060-backprop-4096-hardware-target-policy-draft.yaml
44dbf0eb44963115846ff7ddc527207fe0a9a5e33d921b379ebff9dd081a059e  artifacts/s7/s7-target-selection-20260610-022405/RTX5060-backprop-4096-s6-comparable-targets-template.yaml
bd33e7fef56d26c7a87dbcb862d104f74896c36e0a41f6137db1a9301a7da603  artifacts/s7/s7-target-selection-20260610-022405/RTX5060-job486-s6-comparable-baseline-report.yaml
2a2e07c4c9bb8a48b50c85a3978d7a67b1ae9920b089540e0421c5fa1f55c6ec  artifacts/s7/s7-target-selection-20260610-022405/RTX5060-job486-s6-comparable-baseline-supplied-metrics.yaml
666279612fd23a8820b75f011be1dc471fd8d4a4dbcbcf0aa7bdeca2f3a0fb63  artifacts/s7/s7-target-selection-20260610-022405/RTX5060-job486-s6-comparable-baseline-template.yaml
0557b12f4287ee74a34545f9efe7d1910e45c009936157b8ece53cf7109ff3a1  artifacts/s7/s7-target-selection-20260610-022405/RTX5060-job486-simulator-candidate-metrics-policy-draft.yaml
```

## Validation

All required validations passed:

| Command | Result |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest simulator-remodeled/util/tuner/test_collect_sm120_hardware_metrics.py simulator-remodeled/util/tuner/test_ingest_sm120_simulator_candidate_metrics.py` | pass, 7 tests |
| `python3 -m py_compile simulator-remodeled/util/tuner/collect_sm120_hardware_metrics.py simulator-remodeled/util/tuner/ingest_sm120_simulator_candidate_metrics.py simulator-remodeled/util/tuner/search_sm120_correlation.py` | pass |
| `python3 simulator-remodeled/util/tuner/search_sm120_correlation.py --manifest artifacts/s7/s7-target-selection-20260610-022405/RTX5060-job486-s6-comparable-baseline-supplied-metrics.yaml --dry-run` | pass; `candidates=1`, `best=candidate_0001`, `score=0.482422` |
| `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only` | pass |
| `git diff --check` | pass |
| Protected config/latest scoped `git status --short -- ...` | pass; empty output |
| Fixture collector generation plus policy assertion | pass; `9` hardware target metrics and `4` S6 template targets |
| Simulator-marker rejection check with `gpu_tot_sim_cycle` | expected failure; collector rejected simulator marker with exit code `1` |

Protected config/latest scoped paths checked:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/tested-cfgs`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated/tested-cfgs`
- `simulator-remodeled/gpu-simulator/configs/generated/tested-cfgs`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/base`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/overlays`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/calibration-results`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema`

## Changed Files

Tracked code/tests/docs:

- `simulator-remodeled/util/tuner/collect_sm120_hardware_metrics.py`
- `simulator-remodeled/util/tuner/test_collect_sm120_hardware_metrics.py`
- `docs/sm120-calibration/s6-correlation-search.md`
- `docs/sm120-calibration/s7-hardware-target-metrics.md`
- `docs/sm120-calibration/s7-simulator-candidate-metrics-bridge.md`
- `docs/sm120-calibration/worker-logs/worker-20260610-022405-s7-target-selection.md`

Ignored generated outputs:

- `artifacts/s7/s7-target-selection-20260610-022405/`

## Reviewer Rounds

Reviewer round 1:

- Reviewer: fresh blank-context Codex read-only reviewer.
- Output:
  `artifacts/s7/s7-target-selection-20260610-022405/reviewer-round1-codex.txt`
- Verdict: `ACCEPT`.
- Findings: none blocking.
- Notes:
  - Confirmed the collector includes only Nsight CUDA `*_time_ms` metrics in
    S6 target handoff.
  - Confirmed `native_wall_time_seconds` is retained only as hardware
    characterization and excluded from S6 templates/manifests/reports.
  - Confirmed the simulator bridge does not fabricate native wall time and
    rejects it if supplied as a candidate metric.
  - Confirmed the single-candidate baseline is draft validation evidence, not
    calibration promotion.
  - Confirmed tests pass and accepted/generated/latest config paths are not
    modified.

No reviewer-requested rework was required.

## Current Status

Accepted after fresh blank-context reviewer round 1. The immediate S7 blocker
is closed for the current hardware/candidate artifacts: S6 target handoff now
uses only simulator-comparable CUDA-kernel timing metrics, and a draft-only
single-candidate S6 baseline report validates the bridge/scorer path.

Remaining limitations:

- The baseline report is a one-candidate validation baseline only. It does not
  establish calibration quality.
- The hardware target data is still a single-run draft hardware
  characterization artifact.
- Promotion gate remains closed pending broader RTX5060/RTX5070Ti validation
  and explicit supervisor promotion instruction.
