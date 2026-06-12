# S7 High-Latency Validation Package

## Scope

This package records the actionable high-latency `39`-cycle S7 evidence slice
for the current SM120 RTX5060 calibration pass:

| Candidate | ProcMan job | `-latency_L0_to_L1` | `-prefetch_per_stream_buffer_size` | Status |
| --- | ---: | ---: | ---: | --- |
| `candidate_0003` | `486` | `39` | `8` | `PASS`, draft simulator-candidate metrics only |
| `candidate_0004` | `487` | `39` | `10` | `PASSED`, draft simulator-candidate metrics only |

This is documentation/artifact-only validation packaging. It did not run
ProcMan jobs, simulator jobs, S6 search/correlation, hardware collection, or
promotion commands. It does not modify accepted/generated/latest configs,
calibration results, hardware target metrics, candidate metrics, S6 reports, or
promotion artifacts.

## Source Artifacts

`candidate_0003` is represented by the job `486` baseline artifact:

```text
artifacts/s7/s7-target-selection-20260610-022405/RTX5060-job486-simulator-candidate-metrics-policy-draft.yaml
```

Key fields:

- Artifact candidate id: `candidate_job486_bootstrap`.
- Source label: `procman_job_486_smoke_candidate_only`.
- `status: draft_not_applied`.
- `simulator_candidate_metrics: true`.
- `hardware_target_metrics: false`.
- `parsed_simulator_observations.application_passed: true`.
- Simulator times observed: `390.0` and `2398.0` seconds.
- Kernel 1 `bpnn_layerforward_cuda`: `gpu_sim_cycle = 7729`,
  `gpu_tot_sim_cycle = 7729`, `gpu_tot_sim_insn = 4169728`,
  derived time `0.002927652 ms`.
- Kernel 2 `bpnn_adjust_weights_cuda`: `gpu_sim_cycle = 38089`,
  `gpu_tot_sim_cycle = 45818`, `gpu_tot_sim_insn = 8036672`,
  derived time `0.014427652 ms`.
- Comparable candidate metrics for `backprop_4096`:
  - `cuda_kernel_total_time_ms: 0.017355304`
  - `cuda_kernel_avg_time_ms: 0.008677652`
  - `cuda_kernel_bpnn_layerforward_cuda_total_time_ms: 0.002927652`
  - `cuda_kernel_bpnn_adjust_weights_cuda_total_time_ms: 0.014427652`

`candidate_0004` is represented by recovered job `487`:

```text
artifacts/s7/s7-bounded-sweep-20260610-024829/candidate_0004-simulator-candidate-metrics.yaml
```

Key fields:

- Artifact candidate id: `candidate_0004`.
- Source label: `s7-bounded-sweep-20260610-024829-candidate_0004`.
- `status: draft_not_applied`.
- `simulator_candidate_metrics: true`.
- `hardware_target_metrics: false`.
- `parsed_simulator_observations.application_passed: true`.
- Simulator times observed: `358.0` and `2203.0` seconds.
- Kernel 1 `bpnn_layerforward_cuda`: `gpu_sim_cycle = 7722`,
  `gpu_tot_sim_cycle = 7722`, `gpu_tot_sim_insn = 4169728`,
  derived time `0.002925 ms`.
- Kernel 2 `bpnn_adjust_weights_cuda`: `gpu_sim_cycle = 38038`,
  `gpu_tot_sim_cycle = 45760`, `gpu_tot_sim_insn = 8036672`,
  derived time `0.014408333 ms`.
- Comparable candidate metrics for `backprop_4096`:
  - `cuda_kernel_total_time_ms: 0.017333333`
  - `cuda_kernel_avg_time_ms: 0.008666666`
  - `cuda_kernel_bpnn_layerforward_cuda_total_time_ms: 0.002925`
  - `cuda_kernel_bpnn_adjust_weights_cuda_total_time_ms: 0.014408333`

## Comparable Delta

Delta is `candidate_0004` (`39/10`) minus `candidate_0003` (`39/8`) for
directly comparable simulator metrics:

| Metric | `39/8` job `486` | `39/10` job `487` | Delta | Relative delta |
| --- | ---: | ---: | ---: | ---: |
| `cuda_kernel_total_time_ms` | `0.017355304` | `0.017333333` | `-0.000021971` | `-0.126595%` |
| `cuda_kernel_avg_time_ms` | `0.008677652` | `0.008666666` | `-0.000010986` | `-0.126601%` |
| `cuda_kernel_bpnn_layerforward_cuda_total_time_ms` | `0.002927652` | `0.002925` | `-0.000002652` | `-0.090585%` |
| `cuda_kernel_bpnn_adjust_weights_cuda_total_time_ms` | `0.014427652` | `0.014408333` | `-0.000019319` | `-0.133903%` |
| Kernel 1 `gpu_sim_cycle` | `7729` | `7722` | `-7` | `-0.090568%` |
| Kernel 2 `gpu_sim_cycle` | `38089` | `38038` | `-51` | `-0.133897%` |
| Kernel 2 `gpu_tot_sim_cycle` | `45818` | `45760` | `-58` | `-0.126588%` |
| Kernel 2 `gpu_tot_sim_insn` | `8036672` | `8036672` | `0` | `0.0%` |

Within this two-point high-latency slice, increasing
`-prefetch_per_stream_buffer_size` from `8` to `10` at fixed
`-latency_L0_to_L1=39` slightly reduces the simulator-derived timing metrics
for the `backprop_4096` case. The observed difference is small and comes from
local simulator candidate metrics, not hardware target evidence.

## Non-Promotion Boundary

This package is not a promotion artifact and is not a complete S6
four-candidate sweep.

Reasons:

- Both artifacts are `draft_not_applied`.
- Both artifacts explicitly mark `simulator_candidate_metrics: true` and
  `hardware_target_metrics: false`.
- The metrics are derived from local simulator stdout plus `gpgpusim.config`;
  they are not real RTX5060 hardware timing targets.
- `candidate_0001` (`37/8`) and `candidate_0002` (`37/10`) are excluded or
  deprioritized for the current S7 pass and still lack completion-quality
  candidate metrics.
- The existing partial scaffold remains intentionally non-runnable:

```text
artifacts/s7/s7-bounded-sweep-20260610-024829/RTX5060-backprop-4096-s7-bounded-sweep-s6-manifest.PARTIAL-2OF4.yaml
```

That scaffold records the available `39/8` and `39/10` metrics but keeps the
handoff closed with `do_not_run_search_sm120_correlation_as_is: true` and
missing signatures for the other two designed candidates.

## Evidence Needed Before Promotion Or Compatibility Signoff

Promotion remains closed until separate reviewed evidence supplies at least:

- RTX5060 hardware target metrics with promotion-quality provenance, not just
  the current single-run draft target.
- A reviewed S6 `supplied_metrics` manifest with complete candidate coverage
  for the chosen search space, every target metric numeric for every candidate,
  and explicit reviewer approval before running/ranking it.
- A ranked S6 draft report generated only from reviewed supplied metrics.
- Completion-quality evidence for any reopened low-latency `37`-cycle
  candidate, or an explicit supervisor-approved search-space reduction that
  does not claim the original four-candidate sweep is complete.
- Promotion-gate reviewer approval for any proposed config delta.
- RTX5070Ti compatibility review/signoff for the final promoted surface,
  beyond the earlier static helper check if the final gate reviewer requires
  it.

## Macro Goal Impact

This package advances the macro SM120 calibration goal without claiming final
parameters. It narrows the current S7 evidence base to the two completed
high-latency simulator candidates, makes the `39/8` versus `39/10` comparison
explicit, preserves the hardware/simulator boundary, and documents why the
promotion gate remains closed. That gives the next supervisor step a concrete,
reviewable high-latency slice while avoiding accidental promotion from an
incomplete bounded sweep.
