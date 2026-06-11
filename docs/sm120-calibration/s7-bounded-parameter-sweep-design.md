# S7 Bounded Parameter Sweep Design

## Purpose

Advance S7 beyond the current single-candidate baseline without opening a broad
search. This design defines a small, reviewed parameter sweep for the existing
RTX5060 `backprop_4096` comparable target metrics and records why it is
plan-only until additional local simulator candidate metrics exist.

This is not calibration promotion. The promotion gate remains closed.

## Current Baseline

Baseline artifacts:

```text
artifacts/s7/s7-target-selection-20260610-022405/
```

Important files:

- `RTX5060-backprop-4096-s6-comparable-targets-template.yaml`
- `RTX5060-job486-simulator-candidate-metrics-policy-draft.yaml`
- `RTX5060-job486-s6-comparable-baseline-supplied-metrics.yaml`
- `RTX5060-job486-s6-comparable-baseline-report.yaml`

The current S6 comparable baseline uses local ProcMan job `486` as simulator
candidate evidence only. It compares one generated-config baseline candidate
against four simulator-comparable CUDA-kernel timing targets:

- `cuda_kernel_avg_time_ms = 0.0056`
- `cuda_kernel_bpnn_adjust_weights_cuda_total_time_ms = 0.008704`
- `cuda_kernel_bpnn_layerforward_cuda_total_time_ms = 0.002496`
- `cuda_kernel_total_time_ms = 0.0112`

The single-candidate score is `0.482422`. Job `486` metrics are not hardware
target metrics and are not calibration promotion.

## Candidate Keys

S6 accepts only bounded keys that satisfy all of these checks:

- active in the selected generated base config,
- owned by `calibration_result` in the SM120 schema,
- listed in S5/S6 stage `rf_prefetch_remodeled_parameters`,
- marked with `provenance: correlation_search`,
- bounded by explicit values or a finite range.

The generated RTX5060 base has:

```text
simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated/tested-cfgs/SM120_RTX5060/gpgpusim.config
```

Relevant active values:

- `-gpgpu_clock_domains 2640:2640:2640:14000`
- `-is_instruction_prefetching_enabled 1`
- `-latency_L0_to_L1 39`
- `-prefetch_per_stream_buffer_size 8`
- `-prefetch_num_stream_buffers 1`
- `-num_instruction_prefetches_per_cycle 1`

The selected sweep keys are:

| Key | Base | Values | Reason |
| --- | ---: | --- | --- |
| `-latency_L0_to_L1` | `39` | `37`, `39` | Directly active L0I timing knob. Two-point local sensitivity check around the bootstrap value. |
| `-prefetch_per_stream_buffer_size` | `8` | `8`, `10` | Active instruction-prefetch buffer size with prefetching enabled. Two-point local sensitivity check around the bootstrap value. |

The full expanded space is four candidates:

| Candidate | `-latency_L0_to_L1` | `-prefetch_per_stream_buffer_size` | Current metrics |
| --- | ---: | ---: | --- |
| `candidate_0001` | `37` | `8` | missing |
| `candidate_0002` | `37` | `10` | missing |
| `candidate_0003` | `39` | `8` | available from job `486` baseline |
| `candidate_0004` | `39` | `10` | available from recovered job `487` draft metrics |

Other `rf_prefetch_remodeled_parameters` keys are deliberately excluded for
this first multi-candidate S7 step. They are active and many are
`calibration_result` owned, but adding them would immediately multiply the
candidate count and would not be justified by the single-run `backprop_4096`
target. This sweep is intended only to validate a narrow L0I/prefetch
sensitivity path before any broader search.

## Draft Manifest

Plan-only S7 scaffold:

```text
artifacts/s7/s7-bounded-sweep-20260610-024829/RTX5060-backprop-4096-s7-bounded-sweep-plan.yaml
```

Draft S6 manifest, non-runnable until missing candidate metrics exist:

```text
artifacts/s7/s7-bounded-sweep-20260610-024829/RTX5060-backprop-4096-s7-bounded-sweep-s6-manifest.DRAFT-NONRUNNABLE.yaml
```

The S7 scaffold is intentionally:

- `schema_id: sm120_s7_bounded_sweep_plan_v1`,
- `status: template_not_runnable`,
- `s6_manifest_runnable: false`,
- populated with the four comparable CUDA timing targets,
- populated with the bounded two-key, four-candidate search space,
- populated with job `486` metrics only for the baseline signature
  `-latency_L0_to_L1=39`, `-prefetch_per_stream_buffer_size=8`.

The S6 draft uses `schema_id: sm120_correlation_search_manifest_v1` and the
bounded four-candidate search space, but it includes only one
`evaluation.candidate_metrics` entry. `search_sm120_correlation.py --dry-run`
must reject it until the missing candidate signatures have real local
simulator metrics.

Recovery after the interrupted candidate `0004` execution produced a draft
bridge artifact:

```text
artifacts/s7/s7-bounded-sweep-20260610-024829/candidate_0004-simulator-candidate-metrics.yaml
```

The recovered job was ProcMan job `487`, reported `PASSED`, and produced kernel
2 `gpu_tot_sim_cycle = 45760` and `gpu_tot_sim_insn = 8036672`. The artifact is
`status: draft_not_applied`, `simulator_candidate_metrics: true`, and
`hardware_target_metrics: false`.

A partial bridge scaffold now records the available `2/4` candidate metrics:

```text
artifacts/s7/s7-bounded-sweep-20260610-024829/RTX5060-backprop-4096-s7-bounded-sweep-s6-manifest.PARTIAL-2OF4.yaml
```

This partial file uses `schema_id:
sm120_s6_supplied_metrics_bridge_scaffold_v1`, has
`s6_manifest_runnable: false`, and explicitly says
`do_not_run_search_sm120_correlation_as_is: true`. It is not a runnable
`sm120_correlation_search_manifest_v1` for `search_sm120_correlation.py`.
Candidate signatures `0001` and `0002` remain missing.

## Execution Commands

Use setup-only planning first. Do not run anything on `dsp5060`.

```bash
cd /home/xiewx/accel-0608/modern-gpu-simulator
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment

python3 simulator-remodeled/util/job_launching/procman.py -p
```

For each candidate, add a temporary extra-params alias in
`simulator-remodeled/util/job_launching/configs/define-standard-cfgs.yml` only
after reviewer approval, run setup-only, then remove the alias when the
candidate is complete. Example for the `37,8` candidate:

```yaml
S7SWEEP_L0L1_37_PREFETCH_8:
    extra_params: "-latency_L0_to_L1 37
        -prefetch_per_stream_buffer_size 8"
```

Setup-only:

```bash
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN-S7SWEEP_L0L1_37_PREFETCH_8 \
  -N s7-bounded-sweep-20260610-024829-candidate-0001-plan \
  -r artifacts/s7/s7-bounded-sweep-20260610-024829/sim-plan/candidate_0001 \
  -l local \
  -n
```

Execution, only if explicitly approved after setup-only review:

```bash
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN-S7SWEEP_L0L1_37_PREFETCH_8 \
  -N s7-bounded-sweep-20260610-024829-candidate-0001 \
  -r artifacts/s7/s7-bounded-sweep-20260610-024829/sim-runs/candidate_0001 \
  -l local \
  -c 4
```

After each completed candidate, reduce metrics with the bridge:

```bash
python3 simulator-remodeled/util/tuner/ingest_sm120_simulator_candidate_metrics.py \
  --gpu RTX5060 \
  --stdout <candidate-smoke-stdout.log> \
  --gpgpusim-config <candidate-run-gpgpusim.config> \
  --candidate-id candidate_0001 \
  --candidate-value=-latency_L0_to_L1=37 \
  --candidate-value=-prefetch_per_stream_buffer_size=8 \
  --source-kind local_ptx_s7_bounded_sweep_simulator_run \
  --source-label s7-bounded-sweep-20260610-024829-candidate_0001 \
  --output artifacts/s7/s7-bounded-sweep-20260610-024829/candidate_0001-simulator-candidate-metrics.yaml
```

When all four candidate metrics exist and are reviewed, create a real S6
`supplied_metrics` manifest with `--reviewed`, then run:

```bash
python3 simulator-remodeled/util/tuner/search_sm120_correlation.py \
  --manifest artifacts/s7/s7-bounded-sweep-20260610-024829/RTX5060-backprop-4096-s7-bounded-sweep-supplied-metrics.yaml \
  --output artifacts/s7/s7-bounded-sweep-20260610-024829/RTX5060-backprop-4096-s7-bounded-sweep-report.yaml \
  --emit-planned-commands \
  --command-candidate-limit 4
```

## Stopping Criteria

Stop before launching any candidate if:

- `procman.py -p` is not `Nothing Active`,
- setup-only planning fails,
- the temporary alias would modify accepted, generated, or latest calibration
  configs,
- the host is `dsp5060` or the command would run on `dsp5060`,
- the run directory is outside ignored `artifacts/s7/`.

Stop during execution if:

- one candidate exceeds 30 minutes without producing the expected kernel
  metric block and is not making bounded progress toward completion,
- any candidate fails functionally,
- any candidate produces no parseable simulator stdout metrics,
- ProcMan state is stale or not clean after a candidate,
- the first non-baseline candidate differs only negligibly from the baseline
  and reviewer decides the remaining candidates are not worth the runtime.

Do not generate a ranked S6 report until every generated candidate has reviewed
local simulator candidate metrics for all four target metrics.

## Execution Decision

No new simulator jobs were run for the original design step. The local job
`486` baseline already required substantial smoke bring-up and recorded
simulator times of `390.0` and `2398.0` seconds in the candidate-metrics
artifact.

A later interrupted execution of candidate `0004` was recovered as complete
ProcMan job `487`. This leaves two missing local simulator candidate metrics:
`candidate_0001` and `candidate_0002`. The correct next action is a separate
execution worker for those two candidates, followed by a reviewed real S6
ranked draft report only if all four candidate metrics are complete.

## Promotion Policy

This design does not update:

- flat SM120 `tested-cfgs`,
- generated SM120 `tested-cfgs`,
- `calibration-results/<GPU>/latest.yaml`,
- `calibration-results/latest`.

All real generated artifacts remain under ignored `artifacts/s7/`.
