# S7 Supplied-Metrics Manifest Decision Draft

## Scope

This note defines the current RTX5060 supplied-metrics manifest/search-space
decision for the SM120 S7 calibration pass. It aligns the aggregate hardware
target draft with the completed high-latency simulator candidate slice, but it
does not create a runnable S6 manifest and does not promote configs.

The generated draft artifact is:

```text
artifacts/s7/s7-supplied-metrics-manifest-20260613-035906/RTX5060-backprop-4096-high-latency-supplied-metrics-manifest-draft.yaml
```

It is ignored under `artifacts/s7/` and is marked `draft_not_applied`,
`review_required`, `template_not_runnable`, `s6_manifest_runnable: false`,
`non_promotion`, and `promotion_quality: false`.

## Source Inputs

Aggregate hardware target:

```text
artifacts/s7/s7-aggregate-hardware-target-20260613-033706/RTX5060-backprop-4096-aggregate-hardware-target-draft.yaml
```

Simulator candidate metrics:

```text
artifacts/s7/s7-target-selection-20260610-022405/RTX5060-job486-simulator-candidate-metrics-policy-draft.yaml
artifacts/s7/s7-bounded-sweep-20260610-024829/candidate_0004-simulator-candidate-metrics.yaml
```

The generator validates that the aggregate target is draft/non-promotion
hardware target evidence and that both simulator candidate artifacts are
draft simulator-only metrics with `hardware_target_metrics: false`.

## Search-Space Decision

The original four-candidate bounded sweep is incomplete. The current S7 pass
excludes or deprioritizes the low-latency points:

| Candidate | `-latency_L0_to_L1` | `-prefetch_per_stream_buffer_size` | Current status |
| --- | ---: | ---: | --- |
| `candidate_0001` | `37` | `8` | excluded/deprioritized; no completion-quality metrics |
| `candidate_0002` | `37` | `10` | excluded/deprioritized; diagnostic-only evidence |
| `candidate_0003` | `39` | `8` | high-latency draft simulator metrics, job `486` |
| `candidate_0004` | `39` | `10` | high-latency draft simulator metrics, job `487` |

The draft therefore records a narrowed high-latency slice only:

- fixed `-latency_L0_to_L1: 39`;
- varying `-prefetch_per_stream_buffer_size: 8, 10`;
- two supplied simulator candidates, not the original four-candidate sweep.

This narrowed slice is not silently treated as complete S6 search coverage.
Runnable S6 remains blocked unless the supervisor explicitly approves a
narrowed search-space conversion and a reviewer accepts the exact metric
alignment and manifest conversion.

## Metric Alignment

Only exact metric-name matches between the aggregate hardware handoff and both
candidate metric artifacts are included:

| Metric | Aggregate target | `39/8` candidate | `39/10` candidate |
| --- | ---: | ---: | ---: |
| `cuda_kernel_avg_time_ms` | `0.005456` | `0.008677652` | `0.008666666` |
| `cuda_kernel_bpnn_adjust_weights_cuda_total_time_ms` | `0.0085312` | `0.014427652` | `0.014408333` |
| `cuda_kernel_bpnn_layerforward_cuda_total_time_ms` | `0.0023808` | `0.002927652` | `0.002925` |
| `cuda_kernel_total_time_ms` | `0.010912` | `0.017355304` | `0.017333333` |

`cuda_kernel_invocations` is excluded because it is not in the aggregate S6
handoff. Native wall/user/sys/RSS metrics remain hardware characterization
only and are not simulator-comparable calibration targets.

## Generator And Contract

Checked-in helper:

```text
simulator-remodeled/util/tuner/build_sm120_supplied_metrics_manifest_draft.py
```

Checked-in draft contract:

```text
simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema/supplied-metrics-manifest-draft.schema.yaml
```

Reproduction command:

```bash
python3 simulator-remodeled/util/tuner/build_sm120_supplied_metrics_manifest_draft.py \
  --repo-root . \
  --aggregate-hardware-target artifacts/s7/s7-aggregate-hardware-target-20260613-033706/RTX5060-backprop-4096-aggregate-hardware-target-draft.yaml \
  --candidate-metrics artifacts/s7/s7-target-selection-20260610-022405/RTX5060-job486-simulator-candidate-metrics-policy-draft.yaml \
  --candidate-metrics artifacts/s7/s7-bounded-sweep-20260610-024829/candidate_0004-simulator-candidate-metrics.yaml \
  --manifest-id rtx5060-backprop-4096-high-latency-supplied-metrics-manifest-20260613-035906 \
  --generated-at 2026-06-12T19:59:06Z \
  --output artifacts/s7/s7-supplied-metrics-manifest-20260613-035906/RTX5060-backprop-4096-high-latency-supplied-metrics-manifest-draft.yaml
```

The helper refuses protected output paths and requires output under
`artifacts/s7/` using a strict repository-relative containment check. It is
not an S6 search/ranking/correlation runner.

The job `486` source artifact keeps its historical
`candidate_job486_bootstrap` id, so the generated draft also records
`canonical_s7_candidate_id: candidate_0003` for the `39/8` entry.

## Runnable Boundary

The generated draft sets:

- `readiness.ready_for_search_sm120_correlation: false`;
- `s6_manifest_runnable: false`;
- `handoff.do_not_run_search_sm120_correlation_as_is: true`.

Required approval fields remain false:

- `supervisor_approved_narrowed_search_space`;
- `reviewer_approved_exact_metric_alignment`;
- `reviewer_approved_s6_manifest_conversion`;
- `promotion_gate_approval`;
- `rtx5070ti_compatibility_signoff`.

S6 ranking/search/correlation remains blocked.
