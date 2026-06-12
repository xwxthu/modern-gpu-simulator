# S8 Release Checkpoint: SM120 RTX5060 Non-Promotion Package

## Scope

This is the final S8 documentation checkpoint for the current SM120 RTX5060
validation package on branch `dev-5060`.

Base checkpoint:

```text
440c716 docs: close SM120 S7 static compatibility
```

Current package status: review-ready non-promotion release checkpoint. The
promotion gate remains closed. No accepted/latest/generated configs,
calibration results, metrics artifacts, or promotion artifacts are promoted by
this checkpoint.

The existing uncommitted supervisor log stage-start entry was not edited by
this worker.

## What S0-S7 Achieved

The current package advances the macro SM120 calibration goal by preserving a
reviewable layering and calibration flow, not by selecting final parameters:

- SM120 configuration layering and generation scaffolding now separates common
  `SM120_BASE` architecture data from per-GPU overlays such as `RTX5060` and
  `RTX5070_TI`.
- CUDA 13.x-compatible calibration prerequisites, microbenchmark parsing, and
  draft stage-map support were added for directly measured SM120 facts.
- The S6 correlation harness can rank bounded candidate deltas from reviewed
  supplied metrics without running simulator commands in supplied-metrics mode.
- RTX5060 hardware target collection now has collector/provenance support,
  simulator-marker rejection, and repeated draft `backprop_4096` Nsight
  Systems CUDA-kernel timing evidence.
- A draft aggregate hardware-target schema and offline aggregator summarize
  repeated RTX5060 hardware runs while keeping the output non-promotion.
- A supplied-metrics manifest draft aligns aggregate hardware targets with the
  completed high-latency simulator slice.
- The S7 narrowed high-latency draft ranking compares exactly the completed
  `39/8` and `39/10` simulator candidates.
- RTX5070Ti static compatibility was closed for S7: generated alias/config
  paths still exist, protected RTX5070Ti outputs were not changed, and no
  RTX5060-only shared-code behavior was found after the metadata-only generator
  fix.

## Final S7 Result

The original bounded S7 design had four signatures:

| Original S7 candidate | `-latency_L0_to_L1` | `-prefetch_per_stream_buffer_size` | S8 status |
| --- | ---: | ---: | --- |
| `candidate_0001` | `37` | `8` | excluded/deprioritized for this pass; no completion-quality metrics |
| `candidate_0002` | `37` | `10` | excluded/deprioritized for this pass; diagnostic-only evidence |
| `candidate_0003` | `39` | `8` | completed draft simulator-only evidence, ProcMan job `486` |
| `candidate_0004` | `39` | `10` | completed draft simulator-only evidence, ProcMan job `487` |

The low `37` candidates are not permanently rejected, but they are excluded or
deprioritized for this pass unless supervisor signoff reopens them. Their
diagnostics are useful for future root-cause work, but they are not
calibration-quality metrics.

The high-latency narrowed S6 draft ranking is complete only for the
supervisor-approved two-candidate validation slice. Lower score is better:

| Rank | S7 candidate | Signature | ProcMan job | Draft score |
| ---: | --- | --- | ---: | ---: |
| 1 | `candidate_0004` | `39/10` | `487` | `0.523602` |
| 2 | `candidate_0003` | `39/8` | `486` | `0.525453` |

The best narrowed draft result is therefore `39/10`, but this is not
calibration, not a final config choice, and not evidence that the excluded
`37/*` points would rank worse if completed.

## Artifact Map

Checked-in documentation:

```text
docs/sm120-calibration/s7-low-latency-exclusion-and-high-latency-slice.md
docs/sm120-calibration/s7-high-latency-validation-package.md
docs/sm120-calibration/s7-hardware-target-provenance.md
docs/sm120-calibration/s7-aggregate-hardware-target-schema.md
docs/sm120-calibration/s7-supplied-metrics-manifest.md
docs/sm120-calibration/s7-narrowed-s6-draft-ranking.md
docs/sm120-calibration/s7-rtx5070ti-static-compatibility-closeout.md
docs/sm120-calibration/s8-release-checkpoint.md
```

Checked-in helper scripts and schema contracts relevant to the S7/S8 package:

```text
simulator-remodeled/util/tuner/collect_sm120_hardware_metrics.py
simulator-remodeled/util/tuner/ingest_sm120_simulator_candidate_metrics.py
simulator-remodeled/util/tuner/aggregate_sm120_hardware_targets.py
simulator-remodeled/util/tuner/build_sm120_supplied_metrics_manifest_draft.py
simulator-remodeled/util/tuner/search_sm120_correlation.py
simulator-remodeled/util/tuner/generate_sm120_configs.py
simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema/aggregate-hardware-target.schema.yaml
simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema/supplied-metrics-manifest-draft.schema.yaml
simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema/correlation-search.schema.yaml
```

Ignored draft artifacts, not committed:

```text
artifacts/s7/s7-hardware-target-provenance-20260613-030650/
artifacts/s7/s7-aggregate-hardware-target-20260613-033706/
artifacts/s7/s7-supplied-metrics-manifest-20260613-035906/
artifacts/s7/s7-narrowed-s6-draft-ranking-20260613-041903/
```

Warning: `artifacts/s7/` is ignored by `.gitignore`. These artifacts are local
draft evidence and are not part of the committed release checkpoint.

## Static Reproduction Commands

The following commands are suitable static or draft-artifact checks for this
checkpoint. They do not run simulator workloads, ProcMan jobs, or hardware
collection.

Generator/static compatibility check:

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
```

Python syntax checks:

```bash
python3 -m py_compile \
  simulator-remodeled/util/tuner/collect_sm120_hardware_metrics.py \
  simulator-remodeled/util/tuner/ingest_sm120_simulator_candidate_metrics.py \
  simulator-remodeled/util/tuner/aggregate_sm120_hardware_targets.py \
  simulator-remodeled/util/tuner/build_sm120_supplied_metrics_manifest_draft.py \
  simulator-remodeled/util/tuner/search_sm120_correlation.py \
  simulator-remodeled/util/tuner/generate_sm120_configs.py
```

Whitespace/protected-path review aid:

```bash
git diff --check
git status --short -- \
  simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated \
  simulator-remodeled/gpu-simulator/configs/generated \
  simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/calibration-results \
  artifacts
```

Draft aggregate hardware target regeneration, if the ignored S7 raw artifacts
are present locally:

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

Non-runnable supplied-metrics decision draft regeneration, if ignored source
artifacts are present locally:

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

Narrowed high-latency S6 draft ranking regeneration, if the ignored narrowed
manifest is present locally:

```bash
python3 simulator-remodeled/util/tuner/search_sm120_correlation.py \
  --repo-root . \
  --manifest artifacts/s7/s7-narrowed-s6-draft-ranking-20260613-041903/RTX5060-backprop-4096-high-latency-narrowed-s6-supplied-metrics.yaml \
  --output artifacts/s7/s7-narrowed-s6-draft-ranking-20260613-041903/RTX5060-backprop-4096-high-latency-narrowed-s6-draft-ranking-report.yaml \
  --generated-at 2026-06-12T20:19:03Z
```

Do not run simulator/ProcMan/hardware collection/S6 ranking beyond the
documented supplied-metrics report mode as part of this S8 checkpoint.

## Non-Promotion Boundary

Promotion remains closed because:

- the best `39/10` result is a narrowed draft scorer result, not calibration;
- the original four-candidate S7 sweep is incomplete;
- the `37/*` points have no completion-quality metrics and remain excluded or
  deprioritized for this pass;
- simulator candidate metrics are not hardware target metrics;
- the repeated RTX5060 hardware target and aggregate artifacts are draft,
  ignored, and not promotion-quality;
- no accepted/latest/generated config or calibration result was updated;
- no final RTX5060 promotion-gate reviewer approved a config delta;
- RTX5070Ti received static compatibility closeout only, not hardware or
  simulator validation.

## Residual Limitations

The package is intentionally narrow:

- Workload coverage is limited to the current `backprop_4096` validation
  target and does not represent broad benchmark behavior.
- The RTX5060 hardware provenance lacks a promotion-quality protocol for
  clock controls, warmup, thermal state, idle-GPU/background-load acceptance,
  and final target-selection thresholds.
- The aggregate target schema is draft review infrastructure; passing its CV
  checks does not make the target promotion-quality.
- The supplied-metrics ranking is complete only for the approved high-latency
  two-candidate slice.
- RTX5070Ti static compatibility does not prove RTX5070Ti runtime behavior.
- Existing ignored artifacts must be preserved or regenerated locally; they are
  not committed.

## Future Promotion-Gate Requirements

Before any SM120 RTX5060 config promotion, a future worker should provide:

- reviewed promotion-quality RTX5060 hardware collection protocol and repeated
  hardware targets, including clock/thermal/idle controls and acceptance
  thresholds;
- reviewed final search-space decision, including either completed `37/*`
  metrics or explicit supervisor approval to exclude them without claiming the
  original sweep is complete;
- runnable S6 supplied-metrics manifest with exact metric alignment and
  reviewer approval;
- final S6 ranking/report that is explicitly tied to the approved search
  space and target protocol;
- proposed config delta with protected-path review before any accepted/latest
  or generated config update;
- final RTX5060 promotion-gate review;
- RTX5070Ti hardware and/or simulator validation if the promoted surface can
  affect RTX5070Ti or if the final gate reviewer requires it;
- broader benchmark coverage beyond `backprop_4096`.

## S8 Recommendation

S8 is ready for supervisor review and commit as a documentation/release
checkpoint for the current non-promotion validation package. It should not be
treated as a promotion checkpoint.
