# Worker Log: S7 Aggregate Hardware Target Schema

## Scope

Task: design and implement a draft aggregate hardware-target schema and repeat
protocol over the repeated RTX5060 `backprop_4096` per-run draft target YAMLs
from:

```text
artifacts/s7/s7-hardware-target-provenance-20260613-030650/
```

Constraints honored:

- Did not run simulator jobs, ProcMan jobs, S6 search/correlation/ranking, or
  hardware collection.
- Did not modify accepted/latest/generated config roots, calibration results,
  existing candidate metrics, existing per-run hardware target draft files, S6
  reports, or promotion artifacts.
- Left the pre-existing uncommitted `docs/sm120-calibration/supervisor-log.md`
  modification untouched.

## Deliverables

Checked-in files:

- `simulator-remodeled/util/tuner/aggregate_sm120_hardware_targets.py`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema/aggregate-hardware-target.schema.yaml`
- `docs/sm120-calibration/s7-aggregate-hardware-target-schema.md`
- `docs/sm120-calibration/worker-logs/worker-20260613-033706-s7-aggregate-hardware-target-schema.md`

Generated ignored artifact:

```text
artifacts/s7/s7-aggregate-hardware-target-20260613-033706/RTX5060-backprop-4096-aggregate-hardware-target-draft.yaml
```

## Implementation Summary

The aggregate script reads per-run draft hardware target YAMLs and
`repeatability-summary.draft.json`, validates the draft/non-simulator boundary,
and emits a single aggregate draft target YAML.

Validation includes:

- all source YAMLs are `draft_not_applied`;
- all source YAMLs set `hardware_target_metrics: true`;
- all source YAMLs set `simulator_smoke_metrics: false`;
- all native runs report application pass and exit status zero;
- repeatability summary run counts match the source YAML count;
- repeatability summary remains `promotion_quality: false`.

The aggregate output records:

- source per-run artifacts and SHA256 hashes;
- repeatability summary SHA256;
- raw source hashes preserved by the per-run collector;
- device/tool identity files;
- mean/median/min/max/stdev/CV/range statistics;
- selected metric statistic policy (`mean` for the generated draft);
- CV and range threshold review aids;
- simulator-marker rejection policy summary;
- excluded native wall/user/sys/RSS metrics;
- non-promotion handoff policy and blockers.

## Current Draft Metrics

The generated aggregate uses the mean statistic. The S6 handoff remains
non-runnable and contains only simulator-comparable CUDA timing targets:

- `cuda_kernel_total_time_ms: 0.010912`
- `cuda_kernel_avg_time_ms: 0.005456`
- `cuda_kernel_bpnn_layerforward_cuda_total_time_ms: 0.0023808`
- `cuda_kernel_bpnn_adjust_weights_cuda_total_time_ms: 0.0085312`

Native wall/user/sys/RSS metrics are retained only as excluded hardware
characterization metrics.

## Promotion Status

This is an implementation of a draft aggregate schema/protocol, not promotion.
The generated output explicitly keeps:

- `status: draft_not_applied`
- `aggregate_draft: true`
- `non_promotion: true`
- `promotion_quality: false`
- `hardware_target_metrics: true`
- `simulator_smoke_metrics: false`

Remaining blockers are hardware-control protocol approval, reviewed S6
supplied-metrics manifest, promotion-gate review, and RTX5070Ti compatibility
signoff.

## Validation

Commands run:

```bash
python3 simulator-remodeled/util/tuner/aggregate_sm120_hardware_targets.py ... --output artifacts/s7/s7-aggregate-hardware-target-20260613-033706/RTX5060-backprop-4096-aggregate-hardware-target-draft.yaml
python3 -m py_compile simulator-remodeled/util/tuner/aggregate_sm120_hardware_targets.py
python3 - <<'PY'
import yaml
from pathlib import Path
p = Path('artifacts/s7/s7-aggregate-hardware-target-20260613-033706/RTX5060-backprop-4096-aggregate-hardware-target-draft.yaml')
d = yaml.safe_load(p.read_text())
assert d['status'] == 'draft_not_applied'
assert d['aggregate_draft'] is True
assert d['non_promotion'] is True
assert d['promotion_quality'] is False
assert d['hardware_target_metrics'] is True
assert d['simulator_smoke_metrics'] is False
assert d['source_validation']['all_source_runs_draft'] is True
assert d['source_validation']['all_native_exit_zero'] is True
assert d['source_validation']['all_application_passed'] is True
assert d['s6_supplied_metrics_handoff']['ready_for_search_sm120_correlation'] is False
assert len(d['s6_supplied_metrics_handoff']['target_metrics']) == 4
PY
```

Additional post-review validation:

```bash
python3 - <<'PY'
import hashlib, yaml
from pathlib import Path
script = Path('simulator-remodeled/util/tuner/aggregate_sm120_hardware_targets.py')
p = Path('artifacts/s7/s7-aggregate-hardware-target-20260613-033706/RTX5060-backprop-4096-aggregate-hardware-target-draft.yaml')
text = p.read_text()
assert '&id' not in text and '*id' not in text
assert 'source_yaml_policy_checked: true' in text
d = yaml.safe_load(text)
assert d['aggregator']['script_sha256'] == hashlib.sha256(script.read_bytes()).hexdigest()
assert all(m['repeatability']['n'] == 5 for m in d['target_metrics'])
PY
```

## Reviewer

Blank-context `multi_agent_v1.spawn_agent` reviewer creation failed because the
agent thread limit was reached, so the required fallback was a separate local
read-only `codex exec --sandbox read-only` reviewer process. Reviewer prompts
and outputs are recorded under:

```text
artifacts/s7/s7-aggregate-hardware-target-20260613-033706/
```

Round 1 verdict: `REVISE`.

Findings addressed:

- The first version trusted repeatability-summary mean/median/stdev/CV/range
  after checking only `n` and `values`. The script now recomputes statistics
  from source YAML target values and checks summary statistics for consistency.
- The first version did not require every metric to appear in every source run.
  The script now rejects partial per-metric coverage.
- The script also validates the source YAML simulator-marker rejection policy
  and emits the aggregate YAML without anchors/aliases for simpler review.

Round 2 verdict: `ACCEPT`.

Reviewer confirmed:

- no blocking findings remained;
- round 1 fixes were addressed;
- protected tested/generated/latest/calibration/S6 output paths appeared
  untouched;
- the generated aggregate is ignored by `.gitignore` via `artifacts/s7/`;
- the aggregate remains draft/non-promotion with S6 handoff readiness false;
- reviewer checks were read-only/static/YAML/JSON only, with no simulator,
  ProcMan, S6 ranking/search/correlation, or hardware collection.
