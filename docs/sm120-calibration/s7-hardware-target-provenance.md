# S7 Hardware Target Provenance

## Scope

This note records the S7 RTX5060 hardware-target provenance state for the
`backprop_4096` validation target after the high-latency simulator-only
package. It preserves the boundary between real hardware target metrics and
local simulator candidate metrics.

No simulator, ProcMan, S6 search/correlation, config generation, calibration
promotion, or accepted/latest artifact update was run for this collection.
The only GPU-dependent work was lightweight native execution and Nsight Systems
CUDA-kernel profiling on `dsp5060`.

## New Draft Provenance Artifact

Artifact root:

```text
artifacts/s7/s7-hardware-target-provenance-20260613-030650/
```

Raw collection includes:

- Five native runs:
  `native/native-stdout-run{1..5}.txt`,
  `native/native-stderr-run{1..5}.txt`, and
  `native/native-time-run{1..5}.txt`.
- Five Nsight Systems runs:
  `nsys/backprop-nsys-run{1..5}.nsys-rep`,
  `nsys/backprop-nsys-run{1..5}.sqlite`, and
  `nsys/backprop-nsys-run{1..5}_cuda_gpu_kern_sum_cuda_gpu_kern_sum.csv`.
- Per-run draft hardware target YAMLs:
  `RTX5060-backprop-4096-hardware-target-repeat-run{1..5}-draft.yaml`.
- Per-run non-runnable S6 templates:
  `RTX5060-backprop-4096-s6-supplied-metrics-template-run{1..5}.yaml`.
- Repeatability summary:
  `repeatability-summary.draft.json`.
- Provenance and integrity:
  `remote-tool-versions.txt`, `nvidia-smi-query.csv`,
  `local-inputs.sha256`, and `local-artifacts.sha256`.

All per-run collector outputs remain `status: draft_not_applied`.

## Hardware And Tool Provenance

Remote collection host:

- SSH target: `dsp5060`
- Hostname: `dsplab5060`
- Remote date: `2026-06-13T03:07:02+08:00`
- Kernel: `Linux dsplab5060 6.17.0-29-generic`

Device and tool identity:

- GPU: `NVIDIA GeForce RTX 5060`
- UUID: `GPU-fd113d06-81ba-5c47-6fbe-fd8f1b99f80e`
- Driver: `595.71.05`
- PCI bus: `00000000:08:00.0`
- Compute capability: `12.0`
- Observed state before collection: `P8`, SM clock `225 MHz`, memory clock
  `405 MHz`, memory used `217 MiB`
- CUDA toolkit: `/usr/local/cuda-13.2`, `nvcc V13.2.78`
- Nsight Systems: `2025.6.3.541-256337736014v0`
- GNU time: `time (GNU Time) UNKNOWN`

Inputs copied to `/tmp/s7-hardware-target-provenance-20260613-030650/`:

- Native executable:
  `simulator-remodeled/gpu-app-collection/bin/13.1/release/backprop-rodinia-2.0-ft`
  - SHA256:
    `e2e4cfdf8f13f3101d97701abf0a1dfedfe225d0a8c92759e5254471bf01b038`
- Gold output:
  `simulator-remodeled/gpu-app-collection/data_dirs/cuda/rodinia/2.0-ft/backprop-rodinia-2.0-ft/data/result-4096.txt`
  - SHA256:
    `bb8a3873b36c4725b84a8efb34fd7e84040b6c29707a17350ad949c666429e3b`

The main workspace was not copied to `dsp5060`.

## Collection Commands

Native repeats used this command pattern on `dsp5060`:

```bash
cd /tmp/s7-hardware-target-provenance-20260613-030650
for i in 1 2 3 4 5; do
  LD_LIBRARY_PATH=/usr/local/cuda-13.2/targets/x86_64-linux/lib:/usr/local/cuda/targets/x86_64-linux/lib:$LD_LIBRARY_PATH \
    /usr/bin/time -f 'MGS_HW_TIME_wall_seconds=%e\nMGS_HW_TIME_user_seconds=%U\nMGS_HW_TIME_sys_seconds=%S\nMGS_HW_TIME_max_rss_kbytes=%M\nMGS_HW_TIME_exit_status=%x' \
    -o native/native-time-run${i}.txt \
    ./backprop-rodinia-2.0-ft 4096 data/result-4096.txt \
    > native/native-stdout-run${i}.txt 2> native/native-stderr-run${i}.txt
  echo $? > native/native-run${i}.exitcode
done
```

Nsight repeats used this command pattern on `dsp5060`:

```bash
cd /tmp/s7-hardware-target-provenance-20260613-030650
for i in 1 2 3 4 5; do
  LD_LIBRARY_PATH=/usr/local/cuda-13.2/targets/x86_64-linux/lib:/usr/local/cuda/targets/x86_64-linux/lib:$LD_LIBRARY_PATH \
    nsys profile --trace=cuda --sample=none --cpuctxsw=none \
    --force-overwrite=true --output nsys/backprop-nsys-run${i} \
    ./backprop-rodinia-2.0-ft 4096 data/result-4096.txt
  echo $? > nsys/nsys-profile-run${i}.exitcode
  nsys stats --report cuda_gpu_kern_sum --format csv \
    --output nsys/backprop-nsys-run${i}_cuda_gpu_kern_sum \
    --force-export true --force-overwrite true \
    nsys/backprop-nsys-run${i}.nsys-rep
  echo $? > nsys/nsys-stats-run${i}.exitcode
done
```

Each native/profiler pair was parsed locally with
`simulator-remodeled/util/tuner/collect_sm120_hardware_metrics.py`, preserving
the existing simulator-marker rejection and draft-only output policy.

## Derived Metrics

All five native runs exited `0`, printed `PASSED`, and reported checksum
`0x42b0e8add8ca`.

Repeatability summary from `repeatability-summary.draft.json`:

| Metric | Values | Mean | Median | Min | Max | CV |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `cuda_kernel_total_time_ms` | `0.011008, 0.010880, 0.010912, 0.010912, 0.010848` | `0.010912` | `0.010912` | `0.010848` | `0.011008` | `0.548630%` |
| `cuda_kernel_avg_time_ms` | `0.005504, 0.005440, 0.005456, 0.005456, 0.005424` | `0.005456` | `0.005456` | `0.005424` | `0.005504` | `0.548630%` |
| `cuda_kernel_bpnn_layerforward_cuda_total_time_ms` | `0.002368, 0.002368, 0.002400, 0.002432, 0.002336` | `0.002381` | `0.002368` | `0.002336` | `0.002432` | `1.532494%` |
| `cuda_kernel_bpnn_adjust_weights_cuda_total_time_ms` | `0.008640, 0.008512, 0.008512, 0.008480, 0.008512` | `0.008531` | `0.008512` | `0.008480` | `0.008640` | `0.731192%` |
| `native_wall_time_seconds` | `0.38, 0.28, 0.27, 0.27, 0.27` | `0.294000` | `0.270000` | `0.270000` | `0.380000` | `16.418392%` |

Only the Nsight Systems CUDA kernel elapsed-time metrics are currently
simulator-comparable calibration targets. Native wall/user/sys/RSS metrics
remain hardware characterization only and are excluded from S6 target handoff.

## Simulator-Marker Rejection

Raw native/profiler inputs were scanned for the collector's known simulator
markers:

```text
gpu_tot_sim_cycle
gpu_tot_sim_insn
gpgpu_simulation_time
GPGPU-Sim
Accel-Sim
ProcMan job
```

No marker was found in `native/`, `nsys/`, `remote-tool-versions.txt`, or
`nvidia-smi-query.csv`. The generated YAMLs include those marker strings only
inside the recorded rejection-policy list.

## Promotion Status

This is stronger RTX5060 hardware-target provenance than the earlier
single-run artifact, but it is still draft and not promotion-quality as-is.

Current blockers to promotion-quality hardware targets:

- The checked-in collector emits per-run draft target YAMLs, not an approved
  aggregate hardware-target schema with mean/median/variance fields and clear
  target selection rules.
- No reviewed acceptance threshold exists for how many repetitions are enough,
  whether to use mean or median, what CV/range is acceptable, or how to treat
  cold-start native wall time.
- No approved hardware-control protocol exists for clocks, persistence mode,
  thermal state, warmup, idle-GPU validation, or background-load rejection.
- The S6 handoff is still a template. It lacks a reviewed runnable
  supplied-metrics manifest with matching simulator candidate metrics for the
  chosen search space.
- No promotion-gate reviewer has approved using these repeated metrics as final
  targets, and no RTX5070Ti compatibility signoff has been performed for a
  proposed promoted surface.

## Next Acceptance Criteria

Before hardware targets can be called promotion-quality:

- Define and review an aggregate hardware-target schema or extend the collector
  intentionally to emit reviewed aggregate targets from repeated raw runs.
- Approve the repeat protocol: repetition count, warmups, clock/thermal/power
  logging, idle/process checks before and after collection, and acceptance
  thresholds for CUDA-kernel timing variation.
- Recollect or reprocess with that approved protocol, preserving raw logs,
  command provenance, hashes, device identity, tool versions, and explicit
  simulator-marker rejection.
- Create a reviewed S6 supplied-metrics manifest only after hardware aggregate
  targets and matching simulator candidate metrics are both accepted.
- Keep all outputs draft under ignored `artifacts/s7/` until promotion review
  explicitly accepts them.
