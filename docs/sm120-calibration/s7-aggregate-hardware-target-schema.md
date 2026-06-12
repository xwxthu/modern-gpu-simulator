# S7 Aggregate Hardware Target Schema

## Scope

This note defines the draft aggregate hardware-target schema and repeat
protocol for the repeated RTX5060 `backprop_4096` S7 hardware runs collected in:

```text
artifacts/s7/s7-hardware-target-provenance-20260613-030650/
```

It is a data-reduction and review aid only. It does not run simulator jobs,
ProcMan jobs, S6 search/correlation/ranking, hardware collection, config
generation, calibration promotion, or accepted/latest updates.

## Aggregate Contract

The checked-in schema contract is:

```text
simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema/aggregate-hardware-target.schema.yaml
```

Required aggregate flags are:

- `status: draft_not_applied`
- `aggregate_draft: true`
- `non_promotion: true`
- `promotion_quality: false`
- `hardware_target_metrics: true`
- `simulator_smoke_metrics: false`

Required provenance fields include source per-run target YAML paths and hashes,
repeatability summary path and hash, raw source hashes preserved by the per-run
collector, device/tool identity, simulator-marker rejection summary, excluded
native wall/user/sys/RSS metrics, threshold evaluation, blockers, and draft
handoff policy.

## Repeat Protocol

The implemented offline protocol accepts only repeated per-run target YAMLs
that are already marked draft hardware targets:

- every source YAML must have `status: draft_not_applied`;
- every source YAML must have `hardware_target_metrics: true`;
- every source YAML must have `simulator_smoke_metrics: false`;
- every native run must report `application_passed: true`;
- every native GNU time record must report `exit_status: 0`;
- the repeatability summary must report matching native/Nsight run counts,
  `all_application_passed: true`, `all_native_exit_zero: true`, and
  `promotion_quality: false`.

For the current draft aggregation, the selected target value is the mean by
default. Median is also supported by the script for review experiments. The
default threshold review aids are `2.0%` CV and `5.0%` range/mean. Passing
these thresholds does not make an aggregate promotion-quality because the
clock, warmup, thermal, idle-GPU, and background-load controls were not
approved before collection.

## Metric Policy

The aggregate retains all per-run target metrics and records repeatability
statistics for each metric: values, mean, median, min, max, sample stdev, CV,
and range/mean.

Only Nsight Systems CUDA kernel elapsed-time metrics are copied to the draft S6
target handoff:

- `cuda_kernel_total_time_ms`
- `cuda_kernel_avg_time_ms`
- `cuda_kernel_bpnn_layerforward_cuda_total_time_ms`
- `cuda_kernel_bpnn_adjust_weights_cuda_total_time_ms`

Native process wall/user/sys/RSS metrics are retained in
`excluded_native_wall_metrics` as hardware characterization only. They are not
S6 simulator-comparable calibration targets.

## Offline Aggregator

The checked-in script is:

```text
simulator-remodeled/util/tuner/aggregate_sm120_hardware_targets.py
```

Example command used for the current draft artifact:

```bash
python3 simulator-remodeled/util/tuner/aggregate_sm120_hardware_targets.py \
  --repo-root . \
  --repeatability-summary artifacts/s7/s7-hardware-target-provenance-20260613-030650/repeatability-summary.draft.json \
  --source-yaml artifacts/s7/s7-hardware-target-provenance-20260613-030650/RTX5060-backprop-4096-hardware-target-repeat-run1-draft.yaml \
  --source-yaml artifacts/s7/s7-hardware-target-provenance-20260613-030650/RTX5060-backprop-4096-hardware-target-repeat-run2-draft.yaml \
  --source-yaml artifacts/s7/s7-hardware-target-provenance-20260613-030650/RTX5060-backprop-4096-hardware-target-repeat-run3-draft.yaml \
  --source-yaml artifacts/s7/s7-hardware-target-provenance-20260613-030650/RTX5060-backprop-4096-hardware-target-repeat-run4-draft.yaml \
  --source-yaml artifacts/s7/s7-hardware-target-provenance-20260613-030650/RTX5060-backprop-4096-hardware-target-repeat-run5-draft.yaml \
  --target-id rtx5060-backprop-4096-aggregate-hardware-target-20260613-033706 \
  --generated-at 2026-06-12T19:37:06Z \
  --output artifacts/s7/s7-aggregate-hardware-target-20260613-033706/RTX5060-backprop-4096-aggregate-hardware-target-draft.yaml
```

The generated aggregate target remains ignored under `artifacts/s7/`.

## Promotion Boundary

This is implementation of a draft aggregation schema and repeat protocol, not
promotion. The aggregate remains blocking until a reviewer approves a
promotion-quality repeat protocol, a runnable S6 supplied-metrics manifest with
matching simulator candidate metrics, promotion-gate review, and RTX5070Ti
compatibility signoff.
