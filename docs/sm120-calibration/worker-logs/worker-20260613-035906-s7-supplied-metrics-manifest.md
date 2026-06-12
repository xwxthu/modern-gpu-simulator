# Worker Log: S7 Supplied-Metrics Manifest Decision Draft

## Scope

Task: design and generate a non-runnable, review-gated supplied-metrics
manifest/search-space decision draft that aligns the aggregate RTX5060
hardware target with the high-latency simulator candidate slice:

- `candidate_0003` / ProcMan job `486`: `-latency_L0_to_L1=39`,
  `-prefetch_per_stream_buffer_size=8`;
- `candidate_0004` / ProcMan job `487`: `-latency_L0_to_L1=39`,
  `-prefetch_per_stream_buffer_size=10`.

Constraints honored:

- Did not run simulator jobs, ProcMan jobs, S6 search/ranking/correlation, or
  hardware collection.
- Did not promote configs or modify accepted/latest/generated config roots,
  calibration results, existing candidate metrics, existing hardware target
  artifacts, existing S6 reports, or promotion artifacts.
- Left the pre-existing uncommitted `docs/sm120-calibration/supervisor-log.md`
  modification untouched.

## Deliverables

Checked-in files:

- `simulator-remodeled/util/tuner/build_sm120_supplied_metrics_manifest_draft.py`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema/supplied-metrics-manifest-draft.schema.yaml`
- `docs/sm120-calibration/s7-supplied-metrics-manifest.md`
- `docs/sm120-calibration/worker-logs/worker-20260613-035906-s7-supplied-metrics-manifest.md`

Generated ignored artifact:

```text
artifacts/s7/s7-supplied-metrics-manifest-20260613-035906/RTX5060-backprop-4096-high-latency-supplied-metrics-manifest-draft.yaml
```

## Implementation Summary

The helper script validates:

- aggregate hardware target flags:
  `draft_not_applied`, `aggregate_draft: true`, `non_promotion: true`,
  `promotion_quality: false`, `hardware_target_metrics: true`,
  `simulator_smoke_metrics: false`;
- aggregate handoff keeps `ready_for_search_sm120_correlation: false`;
- each simulator candidate artifact is `draft_not_applied`,
  `simulator_candidate_metrics: true`, `hardware_target_metrics: false`,
  and has `application_passed: true`;
- supplied candidate signatures are exactly `39/8` and `39/10`;
- included metrics match aggregate hardware target handoff names exactly and
  are present numerically in both simulator candidate artifacts;
- output path is under ignored `artifacts/s7/` and avoids protected config,
  calibration, S6, latest, accepted, and promotion paths.
- job `486` keeps its historical `candidate_job486_bootstrap` source id, and
  the generated draft records `canonical_s7_candidate_id: candidate_0003` for
  that `39/8` entry.

The generated artifact records the original four-candidate sweep as
incomplete, lists the low `37`-cycle points as excluded/deprioritized for this
S7 pass, and records only the two-candidate high-latency slice.

## Current Metric Alignment

Included exact-name matches:

- `cuda_kernel_avg_time_ms`
- `cuda_kernel_bpnn_adjust_weights_cuda_total_time_ms`
- `cuda_kernel_bpnn_layerforward_cuda_total_time_ms`
- `cuda_kernel_total_time_ms`

Excluded:

- `cuda_kernel_invocations`, because it is not in the aggregate S6 handoff.
- native wall/user/sys/RSS metrics, because they are hardware characterization
  only and not simulator-comparable calibration targets.

## Runnable Status

The draft is deliberately non-runnable:

- `review_required: true`
- `template_not_runnable: true`
- `s6_manifest_runnable: false`
- `readiness.ready_for_search_sm120_correlation: false`
- `handoff.do_not_run_search_sm120_correlation_as_is: true`

Required approval fields remain false for narrowed-search conversion,
reviewer-approved metric alignment, reviewer-approved S6 manifest conversion,
promotion-gate approval, and RTX5070Ti compatibility signoff.

## Validation

Commands run:

```bash
python3 simulator-remodeled/util/tuner/build_sm120_supplied_metrics_manifest_draft.py \
  --repo-root . \
  --aggregate-hardware-target artifacts/s7/s7-aggregate-hardware-target-20260613-033706/RTX5060-backprop-4096-aggregate-hardware-target-draft.yaml \
  --candidate-metrics artifacts/s7/s7-target-selection-20260610-022405/RTX5060-job486-simulator-candidate-metrics-policy-draft.yaml \
  --candidate-metrics artifacts/s7/s7-bounded-sweep-20260610-024829/candidate_0004-simulator-candidate-metrics.yaml \
  --manifest-id rtx5060-backprop-4096-high-latency-supplied-metrics-manifest-20260613-035906 \
  --generated-at 2026-06-12T19:59:06Z \
  --output artifacts/s7/s7-supplied-metrics-manifest-20260613-035906/RTX5060-backprop-4096-high-latency-supplied-metrics-manifest-draft.yaml

python3 -m py_compile simulator-remodeled/util/tuner/build_sm120_supplied_metrics_manifest_draft.py
```

Static YAML assertions:

```bash
python3 - <<'PY'
import yaml
from pathlib import Path
p = Path('artifacts/s7/s7-supplied-metrics-manifest-20260613-035906/RTX5060-backprop-4096-high-latency-supplied-metrics-manifest-draft.yaml')
d = yaml.safe_load(p.read_text())
assert d['status'] == 'draft_not_applied'
assert d['review_required'] is True
assert d['template_not_runnable'] is True
assert d['s6_manifest_runnable'] is False
assert d['non_promotion'] is True
assert d['promotion_quality'] is False
assert d['readiness']['ready_for_search_sm120_correlation'] is False
assert d['handoff']['do_not_run_search_sm120_correlation_as_is'] is True
assert d['search_space_decision']['original_four_candidate_sweep_complete'] is False
assert len(d['evaluation']['candidate_metrics']) == 2
assert len(d['target_metrics']) == 4
for field, value in d['readiness']['required_approval_fields_before_any_runnable_conversion'].items():
    assert value is False, field
PY
```

Additional validation also asserted the generator script hash, candidate order
`39/8` then `39/10`, and exact target metric set:

```bash
python3 - <<'PY'
import hashlib, yaml
from pathlib import Path
script = Path('simulator-remodeled/util/tuner/build_sm120_supplied_metrics_manifest_draft.py')
p = Path('artifacts/s7/s7-supplied-metrics-manifest-20260613-035906/RTX5060-backprop-4096-high-latency-supplied-metrics-manifest-draft.yaml')
d = yaml.safe_load(p.read_text())
assert d['generator']['script_sha256'] == hashlib.sha256(script.read_bytes()).hexdigest()
expected = {'cuda_kernel_avg_time_ms','cuda_kernel_bpnn_adjust_weights_cuda_total_time_ms','cuda_kernel_bpnn_layerforward_cuda_total_time_ms','cuda_kernel_total_time_ms'}
assert {m['metric'] for m in d['target_metrics']} == expected
assert [c['values'] for c in d['evaluation']['candidate_metrics']] == [
    {'-latency_L0_to_L1': '39', '-prefetch_per_stream_buffer_size': '8'},
    {'-latency_L0_to_L1': '39', '-prefetch_per_stream_buffer_size': '10'},
]
PY
```

Negative S6 guard check:

```bash
python3 simulator-remodeled/util/tuner/search_sm120_correlation.py \
  --manifest artifacts/s7/s7-supplied-metrics-manifest-20260613-035906/RTX5060-backprop-4096-high-latency-supplied-metrics-manifest-draft.yaml \
  --output /tmp/should-not-write-s7-draft-report.yaml \
  --generated-at 2026-06-12T19:59:06Z
```

Expected result:

```text
error: manifest schema_id must be sm120_correlation_search_manifest_v1
```

This exited during header validation before S6 search-space validation,
candidate generation, scoring, ranking, report writing, or correlation.

## Reviewer

Blank-context `multi_agent_v1.spawn_agent` reviewer creation failed because the
agent thread limit was reached, so the required fallback was a separate local
read-only `codex exec --sandbox read-only` reviewer process.

Round 1 verdict: `ACCEPT`.

Reviewer confirmed:

- the artifact is explicitly non-runnable/review-gated;
- the original four-candidate sweep is marked incomplete and the `39/8` plus
  `39/10` narrowed slice is explicit;
- exact metric-name inclusion is enforced and only four handoff metrics are
  included;
- the hardware/simulator boundary is preserved;
- protected-root and promotion safeguards are reasonable.

Residual findings addressed after ACCEPT:

- Tightened output containment from substring matching to a strict
  `relative_to(repo_root / "artifacts/s7")` check.
- Added `canonical_s7_candidate_id` so the `candidate_job486_bootstrap`
  source id remains visibly mapped to `candidate_0003` for the `39/8` slice.

Round 2 follow-up verdict: `ACCEPT`.

Reviewer confirmed strict `artifacts/s7` containment is enforced before write
and canonical mapping records `39/8` job `486` as `candidate_0003` and
`39/10` as `candidate_0004`. No findings.
