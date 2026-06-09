# S7 Simulator Candidate Metrics Bridge Worker Log

## Purpose

Implement a draft-only path from local simulator run artifacts to S6
`evaluation.mode: supplied_metrics` candidate inputs, or document blockers when
the current artifacts cannot form a clean runnable S6 manifest.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base commit: `d184039b9978b10951d01136f8500e53273e13ba`
- Timestamp: `2026-06-10T01:26:43+08:00`
- Worker role: `S7 Simulator Candidate Metrics Ingestion / S6 Supplied-Metrics Bridge`
- Worktree at start:
  - `docs/sm120-calibration/supervisor-log.md` had a pre-existing
    modification not made by this worker.

## Required Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/s6-correlation-search.md`
- `docs/sm120-calibration/s7-hardware-target-metrics.md`
- `docs/sm120-calibration/worker-logs/worker-20260610-003954-s7-hardware-target-metrics.md`
- `simulator-remodeled/util/tuner/search_sm120_correlation.py`
- `simulator-remodeled/util/tuner/collect_sm120_hardware_metrics.py`
- Job `486` local simulator artifacts under
  `artifacts/s7/s7-kernel2-attribution-20260609-211410/`
- S7 hardware target artifact under
  `artifacts/s7/s7-hardware-target-20260610-003544/`

## Hard Rules Observed

- Did not run any simulator workload on `dsp5060`.
- Did not copy the main workspace to `dsp5060`.
- Did not use job `486` as hardware target data.
- Did not fabricate missing `native_wall_time_seconds` candidate metrics.
- Did not write accepted/generated/latest configs.
- Did not write `calibration-results/latest`.
- Did not create a real S6 ranked report from job `486`.
- Kept generated validation and real/draft outputs under ignored
  `artifacts/s7/`.

## Actions

Added reusable bridge:

```text
simulator-remodeled/util/tuner/ingest_sm120_simulator_candidate_metrics.py
```

The bridge parses local simulator stdout/kernel stat blocks and the simulator
run `gpgpusim.config`. It derives per-kernel CUDA-style timing candidate
metrics from:

```text
gpu_sim_cycle / (core_clock_mhz * 1000) = total_time_ms
```

Metric-name mapping uses `c++filt` demangling, strips kernel argument lists,
and reuses `collect_sm120_hardware_metrics.normalize_metric_name`. This maps
job `486` kernels to target-compatible metric names:

- `_Z22bpnn_layerforward_CUDAPfS_S_S_ii` ->
  `cuda_kernel_bpnn_layerforward_cuda_total_time_ms`
- `_Z24bpnn_adjust_weights_cudaPfiS_iS_S_` ->
  `cuda_kernel_bpnn_adjust_weights_cuda_total_time_ms`

The bridge also emits:

- `cuda_kernel_total_time_ms`
- `cuda_kernel_avg_time_ms`
- `cuda_kernel_invocations`

It deliberately does not map or fabricate `native_wall_time_seconds`.

Added fixture inputs and tests:

- `simulator-remodeled/util/tuner/testdata/sm120_sim_candidate_stdout.txt`
- `simulator-remodeled/util/tuner/testdata/sm120_sim_candidate_gpgpusim.config`
- `simulator-remodeled/util/tuner/testdata/sm120_sim_candidate_s6_template.yaml`
- `simulator-remodeled/util/tuner/test_ingest_sm120_simulator_candidate_metrics.py`

Updated docs:

- `docs/sm120-calibration/s6-correlation-search.md`
- `docs/sm120-calibration/s7-simulator-candidate-metrics-bridge.md`

## Evidence

Validation artifact root:

```text
artifacts/s7/s7-sim-metrics-bridge-20260610-012419/
```

Important validation outputs:

- Fixture candidate metrics:
  `artifacts/s7/s7-sim-metrics-bridge-20260610-012419/sm120_sim_candidate_metrics.yaml`
- Fixture supplied-metrics manifest:
  `artifacts/s7/s7-sim-metrics-bridge-20260610-012419/sm120_sim_candidate_s6_manifest.yaml`
- Fixture S6 ranked report:
  `artifacts/s7/s7-sim-metrics-bridge-20260610-012419/sm120_sim_candidate_s6_report.yaml`
- Job `486` candidate metrics:
  `artifacts/s7/s7-sim-metrics-bridge-20260610-012419/RTX5060-job486-simulator-candidate-metrics-draft.yaml`
- Job `486` S6 bridge scaffold:
  `artifacts/s7/s7-sim-metrics-bridge-20260610-012419/RTX5060-job486-s6-supplied-metrics-scaffold.yaml`

The job `486` candidate metric reduction records:

- `cuda_kernel_total_time_ms = 0.017355304`
- `cuda_kernel_avg_time_ms = 0.008677652`
- `cuda_kernel_bpnn_layerforward_cuda_total_time_ms = 0.002927652`
- `cuda_kernel_bpnn_adjust_weights_cuda_total_time_ms = 0.014427652`
- `hardware_target_metrics: false`
- `simulator_candidate_metrics: true`

The job `486` scaffold is intentionally non-runnable:

- `schema_id: sm120_s6_supplied_metrics_bridge_scaffold_v1`
- `status: draft_not_applied`
- `s6_manifest_runnable: false`
- Blockers:
  - `search_parameters_missing`
  - `search_max_candidates_not_positive`
  - `missing_target_metrics:1`
  - `input_template_status_template_not_runnable`
- Missing target metric:
  `backprop_4096.native_wall_time_seconds`

## Validation

All required validations passed unless marked as an expected negative:

| Command | Result |
| --- | --- |
| `python3 -m py_compile simulator-remodeled/util/tuner/ingest_sm120_simulator_candidate_metrics.py` | pass |
| `python3 -m unittest simulator-remodeled/util/tuner/test_ingest_sm120_simulator_candidate_metrics.py` | pass, 6 tests |
| Fixture bridge generation to ignored `artifacts/s7/...` | pass |
| Fixture S6 report with `search_sm120_correlation.py` | pass |
| Job `486` bridge generation to ignored `artifacts/s7/...` | pass |
| Job `486` scaffold passed to `search_sm120_correlation.py --dry-run` | expected failure; schema id is not an S6 manifest |
| `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only` | pass |
| `git diff --check` | pass |
| Protected config/latest scoped status check | pass; empty output |

Validation exit-code ledger:

```text
artifacts/s7/s7-sim-metrics-bridge-20260610-012419/validation-exitcodes.txt
```

## Changed Files

Code and tests:

- `simulator-remodeled/util/tuner/ingest_sm120_simulator_candidate_metrics.py`
- `simulator-remodeled/util/tuner/test_ingest_sm120_simulator_candidate_metrics.py`
- `simulator-remodeled/util/tuner/testdata/sm120_sim_candidate_stdout.txt`
- `simulator-remodeled/util/tuner/testdata/sm120_sim_candidate_gpgpusim.config`
- `simulator-remodeled/util/tuner/testdata/sm120_sim_candidate_s6_template.yaml`

Docs:

- `docs/sm120-calibration/s6-correlation-search.md`
- `docs/sm120-calibration/s7-simulator-candidate-metrics-bridge.md`
- `docs/sm120-calibration/worker-logs/worker-20260610-012643-s7-sim-metrics-bridge.md`

Ignored generated outputs:

- `artifacts/s7/s7-sim-metrics-bridge-20260610-012419/`
- Earlier exploratory draft outputs under
  `artifacts/s7/s7-kernel2-attribution-20260609-211410/`

Pre-existing unrelated modification not made by this worker:

- `docs/sm120-calibration/supervisor-log.md`

## Reviewer Rounds

Reviewer round 1:

- Reviewer: fresh blank-context Codex read-only reviewer.
- Output:
  `artifacts/s7/s7-sim-metrics-bridge-20260610-012419/reviewer-round1-codex.txt`
- Verdict: `CHANGES_NEEDED`.
- Findings:
  - The S6 readiness gate did not reject duplicate candidate metric entries.
  - The S6 readiness gate did not check expanded search-space size against
    `search.max_candidates`.

Rework after round 1:

- Added duplicate candidate signature detection before runnable S6 manifest
  output.
- Added `len(expected_signatures) <= search.max_candidates` readiness check.
- Added focused unit tests for both negative cases.
- Reran validation at `2026-06-10T01:34:39+08:00`; the unit test suite now
  reports 4 tests and all validation exit codes are unchanged except the
  expected scaffold negative check remains exit code `1`.

Reviewer round 2:

- Reviewer: fresh blank-context Codex read-only reviewer.
- Output:
  `artifacts/s7/s7-sim-metrics-bridge-20260610-012419/reviewer-round2-codex.txt`
- Verdict: `CHANGES_NEEDED`.
- Findings:
  - Loaded `--candidate-artifact` YAML could smuggle unsupported/fabricated
    metrics such as `native_wall_time_seconds`.
  - The bridge readiness gate still duplicated only part of S6 manifest
    validation and could mark an invalid S6 manifest runnable.

Rework after round 2:

- Added a loaded-candidate metric filter. Candidate artifacts are now limited
  to bridge-supported simulator metric names:
  `cuda_kernel_*_time_ms` and `cuda_kernel_invocations`.
- Added runnable-manifest validation through the existing S6 harness functions
  in `search_sm120_correlation.py` before the bridge can emit
  `schema_id: sm120_correlation_search_manifest_v1`.
- Added focused unit tests for:
  - rejecting loaded candidate artifacts with `native_wall_time_seconds`;
  - converting S6 validation failures into non-runnable readiness blockers.
- Reran validation at `2026-06-10T01:46:13+08:00`; the unit test suite now
  reports 6 tests, the fixture bridge still generates an S6 report, and the
  job `486` scaffold remains non-runnable.

Reviewer round 3:

- Reviewer: fresh blank-context Codex read-only reviewer.
- Output:
  `artifacts/s7/s7-sim-metrics-bridge-20260610-012419/reviewer-round3-codex.txt`
- Verdict: `ACCEPT`.
- Summary: reviewer reported no findings and verified that duplicate candidate
  entries are blocked, expanded search spaces are checked against
  `max_candidates`, loaded candidate YAML is filtered to simulator-candidate
  metric names only, runnable S6 output goes through the existing
  `search_sm120_correlation.py` validation path, job `486` remains simulator
  candidate evidence only, `native_wall_time_seconds` remains unmapped, no job
  `486` ranked report exists, and protected generated/accepted/latest paths are
  unchanged.

## Current Status

Accepted after fresh blank-context reviewer round 3. The bridge is complete as
a draft-only ingestion path. Current real job `486` evidence produces candidate
CUDA-kernel timing metrics and a non-runnable S6 scaffold; it does not produce
a valid real S6 ranked report because the hardware template still includes
`native_wall_time_seconds`, has no reviewed bounded search parameters, and is
itself `template_not_runnable`.
