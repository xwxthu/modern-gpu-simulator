# S7 Narrowed S6 Draft Ranking

## Scope

This note records the supervisor-approved high-latency S7 validation slice
conversion into a runnable S6 supplied-metrics manifest and draft ranking
report. This is draft validation only. It is not promotion, not a config
selection decision, not the original four-candidate sweep, and not RTX5070Ti
compatibility signoff.

Generated ignored artifacts:

```text
artifacts/s7/s7-narrowed-s6-draft-ranking-20260613-041903/RTX5060-backprop-4096-high-latency-narrowed-s6-supplied-metrics.yaml
artifacts/s7/s7-narrowed-s6-draft-ranking-20260613-041903/RTX5060-backprop-4096-high-latency-narrowed-s6-draft-ranking-report.yaml
```

## Approval Boundary

The runnable draft manifest records the approved conversion facts:

- `supervisor_approved_narrowed_search_space: true`
- `reviewer_approved_exact_metric_alignment: true`
- `reviewer_approved_s6_manifest_conversion: true`
- `promotion_gate_approval: false`
- `rtx5070ti_compatibility_signoff: false`

It also marks `draft_not_applied`, `non_promotion`,
`high_latency_only`, `narrowed_s7_validation_slice`,
`not_original_four_candidate_sweep`, and `do_not_claim_calibrated`.

## Search Space

The S6 manifest expands to exactly two generated candidates:

| S6 generated candidate | S7 candidate | ProcMan job | `-latency_L0_to_L1` | `-prefetch_per_stream_buffer_size` |
| --- | --- | ---: | ---: | ---: |
| `candidate_0001` | `candidate_0003` | `486` | `39` | `8` |
| `candidate_0002` | `candidate_0004` | `487` | `39` | `10` |

The low-latency `37/*` points remain excluded/deprioritized for this S7 pass:

- `candidate_0001` from the original four-candidate design (`37/8`) has no
  completion-quality simulator candidate metrics.
- `candidate_0002` from the original four-candidate design (`37/10`) remains
  diagnostic-only evidence with no full benchmark result or candidate metrics.

The report ranking is therefore complete only for the narrowed high-latency
two-candidate search space.

## Metric Inputs

Target metrics are exactly the four aggregate CUDA `_time_ms` metrics:

- `cuda_kernel_avg_time_ms: 0.005456`
- `cuda_kernel_bpnn_adjust_weights_cuda_total_time_ms: 0.0085312`
- `cuda_kernel_bpnn_layerforward_cuda_total_time_ms: 0.0023808`
- `cuda_kernel_total_time_ms: 0.010912`

Candidate metrics exactly match the existing simulator-only artifacts:

```text
artifacts/s7/s7-target-selection-20260610-022405/RTX5060-job486-simulator-candidate-metrics-policy-draft.yaml
artifacts/s7/s7-bounded-sweep-20260610-024829/candidate_0004-simulator-candidate-metrics.yaml
```

No hardware target metrics were used as simulator candidate metrics.

## Ranking Result

`search_sm120_correlation.py` produced the draft report in supplied-metrics
mode without planned simulator commands. Lower score is better:

| Rank | S6 generated candidate | S7 candidate | Signature | Score |
| ---: | --- | --- | --- | ---: |
| 1 | `candidate_0002` | `candidate_0004` | `39/10` | `0.523602` |
| 2 | `candidate_0001` | `candidate_0003` | `39/8` | `0.525453` |

Within this narrowed validation slice, the best ranked candidate is `39/10`.
This is a draft scorer result only and must not be treated as calibrated.

## Reproduction

Report generation command:

```bash
python3 simulator-remodeled/util/tuner/search_sm120_correlation.py \
  --repo-root . \
  --manifest artifacts/s7/s7-narrowed-s6-draft-ranking-20260613-041903/RTX5060-backprop-4096-high-latency-narrowed-s6-supplied-metrics.yaml \
  --output artifacts/s7/s7-narrowed-s6-draft-ranking-20260613-041903/RTX5060-backprop-4096-high-latency-narrowed-s6-draft-ranking-report.yaml \
  --generated-at 2026-06-12T20:19:03Z
```

Validation confirmed:

- generated candidate count is `2`;
- target metric count is `4`;
- evaluation mode is `supplied_metrics`;
- planned simulator command count is `0`;
- best generated candidate is `candidate_0002`, corresponding to S7
  `candidate_0004` (`39/10`);
- ProcMan status remained `Nothing Active`.

## Protected Paths

No accepted/latest/generated config roots, calibration results, existing
candidate metrics, existing hardware target artifacts, or promotion artifacts
were modified. No simulator, ProcMan workload, or hardware collection was run.
