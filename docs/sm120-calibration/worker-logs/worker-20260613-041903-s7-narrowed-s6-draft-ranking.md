# Worker Log: S7 Narrowed S6 Draft Ranking

Timestamp: `2026-06-13 04:19:03 CST`

Worker: S7 narrowed S6 draft conversion worker

## Scope

Convert the approved high-latency S7 validation slice into a runnable S6
supplied-metrics manifest and draft ranking report under ignored
`artifacts/s7/`. This is draft validation only, not promotion.

## Required Context Read

- `docs/sm120-calibration/supervisor-log.md`, latest search-space decision
  entry at `2026-06-13 04:17:21 CST`.
- `docs/sm120-calibration/overall-plan.md`.
- `docs/sm120-calibration/s7-supplied-metrics-manifest.md`.
- `docs/sm120-calibration/s7-aggregate-hardware-target-schema.md`.
- `docs/sm120-calibration/s7-high-latency-validation-package.md`.
- `docs/sm120-calibration/s7-low-latency-exclusion-and-high-latency-slice.md`.
- `simulator-remodeled/util/tuner/search_sm120_correlation.py`.
- Existing non-runnable decision draft:
  `artifacts/s7/s7-supplied-metrics-manifest-20260613-035906/RTX5060-backprop-4096-high-latency-supplied-metrics-manifest-draft.yaml`.
- Source aggregate and simulator candidate artifacts.

## Inputs

Aggregate hardware target:

```text
artifacts/s7/s7-aggregate-hardware-target-20260613-033706/RTX5060-backprop-4096-aggregate-hardware-target-draft.yaml
```

Simulator candidate metrics:

```text
artifacts/s7/s7-target-selection-20260610-022405/RTX5060-job486-simulator-candidate-metrics-policy-draft.yaml
artifacts/s7/s7-bounded-sweep-20260610-024829/candidate_0004-simulator-candidate-metrics.yaml
```

## Work Performed

- Created ignored artifact directory:
  `artifacts/s7/s7-narrowed-s6-draft-ranking-20260613-041903/`.
- Transformed the S7 decision draft into an S6 runnable
  `sm120_correlation_search_manifest_v1` manifest using the existing scorer
  schema.
- Kept the search space to exactly two generated candidates:
  `39/8` and `39/10`.
- Kept the target metrics to exactly the four aggregate CUDA `_time_ms`
  metrics.
- Used only existing simulator-only candidate metrics from jobs `486` and
  `487`.
- Ran `search_sm120_correlation.py` in supplied-metrics report mode only.
- Added documentation note:
  `docs/sm120-calibration/s7-narrowed-s6-draft-ranking.md`.

No code helper or schema changes were necessary.

## Artifacts Produced

Runnable S6 manifest:

```text
artifacts/s7/s7-narrowed-s6-draft-ranking-20260613-041903/RTX5060-backprop-4096-high-latency-narrowed-s6-supplied-metrics.yaml
```

Draft ranking report:

```text
artifacts/s7/s7-narrowed-s6-draft-ranking-20260613-041903/RTX5060-backprop-4096-high-latency-narrowed-s6-draft-ranking-report.yaml
```

## Scorer Command

```bash
python3 simulator-remodeled/util/tuner/search_sm120_correlation.py \
  --repo-root . \
  --manifest artifacts/s7/s7-narrowed-s6-draft-ranking-20260613-041903/RTX5060-backprop-4096-high-latency-narrowed-s6-supplied-metrics.yaml \
  --output artifacts/s7/s7-narrowed-s6-draft-ranking-20260613-041903/RTX5060-backprop-4096-high-latency-narrowed-s6-draft-ranking-report.yaml \
  --generated-at 2026-06-12T20:19:03Z
```

Result: pass; report written under `artifacts/s7/`.

## Ranking

Lower `weighted_normalized_error` is better.

| Rank | S6 generated candidate | S7 candidate | Signature | Score |
| ---: | --- | --- | --- | ---: |
| 1 | `candidate_0002` | `candidate_0004` | `39/10` | `0.523602` |
| 2 | `candidate_0001` | `candidate_0003` | `39/8` | `0.525453` |

Best candidate in the narrowed draft report: `39/10`, corresponding to S7
`candidate_0004` / ProcMan job `487`.

## Validation

Validated with a Python/YAML assertion script:

- manifest schema id is `sm120_correlation_search_manifest_v1`;
- manifest marks `draft_not_applied`, `non_promotion`,
  `high_latency_only`, `narrowed_s7_validation_slice`,
  `not_original_four_candidate_sweep`, and `do_not_claim_calibrated`;
- approval facts match the supervisor-approved conversion facts;
- search expands to exactly `2` candidates;
- search values are exactly `-latency_L0_to_L1: 39` and
  `-prefetch_per_stream_buffer_size: 8, 10`;
- target metrics are exactly the four CUDA `_time_ms` metrics;
- candidate metric signatures are exactly `39/8` and `39/10`;
- report evaluation mode is `supplied_metrics`;
- report target metric count is `4`;
- report planned command count is `0`;
- report rank 1 is `39/10` and rank 2 is `39/8`.

ProcMan status check:

```text
python3 /home/xiewx/accel-0608/accel-sim-framework/util/job_launching/procman.py --printState
Nothing Active
```

## Guardrails

- Did not run simulator workloads.
- Did not run ProcMan jobs.
- Did not run hardware collection.
- Did not modify accepted/latest/generated config roots.
- Did not modify calibration results, existing candidate metrics, existing
  hardware target artifacts, or promotion artifacts.
- Did not edit `docs/sm120-calibration/supervisor-log.md`.
- Did not make a config promotion decision.

## Reviewer

The multi-agent spawn attempt failed with `agent thread limit reached`, so the
required reviewer workflow used a separate read-only local Codex reviewer
process. Prompt and output were preserved under the ignored artifact directory:

```text
artifacts/s7/s7-narrowed-s6-draft-ranking-20260613-041903/reviewer-prompt.txt
artifacts/s7/s7-narrowed-s6-draft-ranking-20260613-041903/reviewer-output.txt
```

Reviewer verdict: accepted, with no blocking findings.

Reviewer confirmed:

- manifest is under ignored `artifacts/s7/` and carries the required
  `draft_not_applied`, `non_promotion`, `high_latency_only`,
  `narrowed_s7_validation_slice`, `not_original_four_candidate_sweep`, and
  `do_not_claim_calibrated` markings;
- search space is exactly `39/8` and `39/10`;
- target metrics are exactly the four CUDA `_time_ms` metrics and match the
  aggregate S6 handoff;
- candidate metrics match the simulator-only source artifacts for jobs `486`
  and `487`;
- report uses `supplied_metrics`, has `target_metric_count: 4`,
  `planned_command_count: 0`, and `planned_simulator_commands: []`;
- report/docs clearly scope the ranking to the narrowed two-candidate slice,
  not the original four-candidate sweep;
- ProcMan returned `Nothing Active`;
- no tracked protected config/calibration/source metric artifact paths were
  modified.
