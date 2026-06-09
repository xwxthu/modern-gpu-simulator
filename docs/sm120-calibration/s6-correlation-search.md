# SM120 S6 Targeted Correlation Search MVP

## Purpose

S6 adds a small manifest-driven harness for parameters that S5 cannot determine
directly from official facts, `system_config`, or focused microbenchmarks. It is
for narrow, staged correlation searches only. It does not perform broad brute
force tuning, does not run full simulator workloads, and does not claim a real
RTX5060 calibration.

The script is:

```bash
python3 simulator-remodeled/util/tuner/search_sm120_correlation.py --help
```

The checked-in fixture is synthetic:

- Manifest: `simulator-remodeled/util/tuner/testdata/sm120_correlation_search_fixture.yaml`
- Report: `simulator-remodeled/util/tuner/testdata/sm120_correlation_search_fixture_report.yaml`

## Scope

The S6 MVP searches only keys that are:

- Active in the selected S4 generated bootstrap config.
- Owned by `calibration_result` in
  `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema/sm120.schema.yaml`.
- Listed in the S5/S6 stage map as `rf_prefetch_remodeled_parameters`.
- Explicitly marked with `provenance: correlation_search`.
- Bounded by either an explicit `values` list or a `range` with `start`, `stop`,
  `step`, and `max_values`.

The hard MVP limits are intentionally small:

- At most 16 values for one parameter.
- At most 64 expanded candidates for one manifest.
- One search stage per manifest.

Unknown keys, owner mismatches, stage mismatches, unbounded ranges, duplicate
keys, and spaces larger than `max_candidates` fail before any report is written.

## Manifest Contract

The machine-readable contract is:

```text
simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema/correlation-search.schema.yaml
```

A manifest describes:

- GPU and architecture.
- S4 generated base `gpgpusim.config` and mirrored `trace.config`.
- Benchmark cases.
- Target hardware metrics with weights and normalization epsilon.
- Bounded candidate parameters.
- Evaluation metrics for every generated candidate.
- Optional command-planning fields.

S6 currently supports two evaluation modes:

- `fixture`: synthetic metrics for CI/local validation.
- `supplied_metrics`: metrics from simulator runs performed outside this
  harness.

The harness itself does not run or parse simulator workloads. S7 now provides a
separate draft-only ingestion bridge for local simulator artifacts:

```bash
python3 simulator-remodeled/util/tuner/ingest_sm120_simulator_candidate_metrics.py --help
```

The bridge can convert per-kernel simulator cycles into candidate metrics with
the same CUDA-kernel timing names used by the S7 hardware target collector. It
does not fabricate native wall time, does not treat simulator metrics as
hardware targets, and emits a non-runnable scaffold unless reviewed search
parameters and candidate metrics are complete.

## Report Semantics

Reports always use:

```yaml
status: draft_not_applied
handoff:
  do_not_claim_calibrated: true
```

The ranking metric is weighted normalized error:

```text
sum(weight * abs(simulated - target) / max(abs(target), epsilon)) / sum(weight)
```

Lower score is better. The top-ranked candidate is still only a draft. S6 never
writes or updates:

- Flat SM120 `tested-cfgs`.
- S4 generated `configs/generated/tested-cfgs`.
- `calibration-results/<GPU>/latest.yaml`.

The script also refuses report output paths inside protected tested-config and
accepted-latest locations.

## Fixture Workflow

Generate and compare the synthetic report:

```bash
python3 simulator-remodeled/util/tuner/search_sm120_correlation.py \
  --manifest simulator-remodeled/util/tuner/testdata/sm120_correlation_search_fixture.yaml \
  --output /tmp/sm120_correlation_search_fixture_report.yaml \
  --generated-at 2026-06-08T13:56:32Z \
  --fixture-only \
  --emit-planned-commands \
  --command-candidate-limit 2

diff -u \
  simulator-remodeled/util/tuner/testdata/sm120_correlation_search_fixture_report.yaml \
  /tmp/sm120_correlation_search_fixture_report.yaml
```

Dry-run validation and planned-command printing:

```bash
python3 simulator-remodeled/util/tuner/search_sm120_correlation.py \
  --manifest simulator-remodeled/util/tuner/testdata/sm120_correlation_search_fixture.yaml \
  --dry-run \
  --print-planned-commands \
  --command-candidate-limit 2
```

The printed commands are plan-only. They include `-n` so
`run_simulations.py` would set up run directories without launching jobs. The
report also includes a temporary `extra_params` alias snippet for
`gpgpusim.config` deltas. Current command planning intentionally rejects
`trace.config` candidate deltas because the existing launcher appends
`trace.config` after `extra_params`; those searches need a reviewed temporary
trace config in a future step. S6 does not edit `define-standard-cfgs.yml`; a
real local experiment should add a reviewed temporary alias outside the
committed calibration artifacts, then remove `-n` only when intentionally
launching on the strong local simulator server.

Negative fixtures:

```bash
python3 simulator-remodeled/util/tuner/search_sm120_correlation.py \
  --manifest simulator-remodeled/util/tuner/testdata/sm120_correlation_search_invalid_unknown_key.yaml \
  --dry-run

python3 simulator-remodeled/util/tuner/search_sm120_correlation.py \
  --manifest simulator-remodeled/util/tuner/testdata/sm120_correlation_search_invalid_unbounded.yaml \
  --dry-run
```

Both commands should fail.

## Composition With S5 And S7

S5 remains the preferred source for directly measurable values. Use S6 only
after the manifest identifies a small set of remaining parameters that cannot
be isolated by official facts or microbenchmarks.

S6 output is a ranked draft report. A future S7 validation flow may:

1. Run reviewed planned commands on the strong local simulator server.
2. Collect simulator metrics into a `supplied_metrics` manifest.
3. Review the ranked report.
4. Copy only accepted owner-matched `calibration_result` entries into a staged
   delta or `latest.yaml`.

That final copy is intentionally outside S6.
