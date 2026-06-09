# S7 Simulator Candidate Metrics Bridge

## Purpose

S7 now has a draft-only bridge from local simulator run artifacts to S6
`evaluation.mode: supplied_metrics` candidate inputs. The bridge is separate
from the S7 hardware target collector and keeps the hardware/simulator boundary
explicit.

The script is:

```bash
python3 simulator-remodeled/util/tuner/ingest_sm120_simulator_candidate_metrics.py --help
```

## Metric Mapping

The bridge parses local simulator stdout blocks with `kernel_name`,
`kernel_launch_uid`, `gpu_sim_cycle`, `gpu_sim_insn`, `gpu_tot_sim_cycle`, and
`gpu_tot_sim_insn`. It reads `-gpgpu_clock_domains` from the simulator run
`gpgpusim.config` and derives per-kernel time as:

```text
gpu_sim_cycle / (core_clock_mhz * 1000) = total_time_ms
```

Kernel names are mapped to hardware target metric names by demangling with
`c++filt`, stripping argument lists, and applying the same normalization helper
used by `collect_sm120_hardware_metrics.py`. Explicit `--kernel-stub-map`
overrides are available when demangling does not match the hardware collector
stub.

Supported mapped candidate metrics include:

- `cuda_kernel_total_time_ms`
- `cuda_kernel_avg_time_ms`
- `cuda_kernel_<kernel_stub>_total_time_ms`

The bridge deliberately does not map `native_wall_time_seconds`; local
simulator stdout/config artifacts do not contain native hardware wall-clock
time.

## Draft-Only Behavior

Outputs use `status: draft_not_applied`, record
`simulator_candidate_metrics: true`, and record
`hardware_target_metrics: false`. The bridge refuses protected config and
calibration-result output paths.

An S6 manifest is emitted as runnable only when:

- The input S6 template is not `template_not_runnable`.
- Search parameters are present and bounded.
- The caller passes `--reviewed`.
- Candidate entries cover every generated candidate exactly once.
- Every target metric has a numeric candidate value.

Otherwise the bridge writes
`schema_id: sm120_s6_supplied_metrics_bridge_scaffold_v1` with
`s6_manifest_runnable: false` and explicit blockers. This scaffold must not be
fed to `search_sm120_correlation.py`.

## Fixture Validation

Fixture parse plus valid fixture S6 report:

```bash
python3 simulator-remodeled/util/tuner/ingest_sm120_simulator_candidate_metrics.py \
  --gpu RTX5060 \
  --stdout simulator-remodeled/util/tuner/testdata/sm120_sim_candidate_stdout.txt \
  --gpgpusim-config simulator-remodeled/util/tuner/testdata/sm120_sim_candidate_gpgpusim.config \
  --candidate-id candidate_0001 \
  --candidate-value=-latency_L0_to_L1=39 \
  --source-label fixture-sim \
  --generated-at 2026-06-09T00:00:00Z \
  --fixture-only \
  --output /tmp/sm120_sim_candidate_metrics.yaml \
  --s6-template simulator-remodeled/util/tuner/testdata/sm120_sim_candidate_s6_template.yaml \
  --s6-manifest-output /tmp/sm120_sim_candidate_s6_manifest.yaml \
  --reviewed

python3 simulator-remodeled/util/tuner/search_sm120_correlation.py \
  --manifest /tmp/sm120_sim_candidate_s6_manifest.yaml \
  --output /tmp/sm120_sim_candidate_s6_report.yaml \
  --generated-at 2026-06-09T00:00:00Z \
  --fixture-only
```

Focused parser tests:

```bash
python3 -m unittest simulator-remodeled/util/tuner/test_ingest_sm120_simulator_candidate_metrics.py
```

## Job 486 Candidate Evidence

ProcMan job `486` may be used only as local simulator candidate evidence, not
as hardware target data. The bridge can parse it into ignored draft artifacts
under:

```text
artifacts/s7/s7-kernel2-attribution-20260609-211410/
```

Current draft reduction:

- `RTX5060-job486-simulator-candidate-metrics-draft.yaml`
- `RTX5060-job486-s6-supplied-metrics-scaffold.yaml`

The scaffold is intentionally non-runnable. It blocks on the hardware template
still including `native_wall_time_seconds`, empty template search parameters,
and `template_not_runnable` status.
