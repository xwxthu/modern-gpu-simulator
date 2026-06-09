# S7 Hardware Target Metrics MVP

## Purpose

S7 now has a draft hardware target metrics path that is separate from local
simulator smoke metrics. The MVP collects or parses native RTX5060 application
timing and emits ignored, draft-only YAML under `artifacts/s7/`.

The parser script is:

```bash
python3 simulator-remodeled/util/tuner/collect_sm120_hardware_metrics.py --help
```

The output schema is intentionally simple and draft-only:

- `schema_id: sm120_hardware_target_metrics_v1`
- `status: draft_not_applied`
- `hardware_target_metrics: true`
- `simulator_smoke_metrics: false`
- `handoff.do_not_claim_calibrated: true`

The collector rejects input files containing known simulator smoke markers such
as `gpu_tot_sim_cycle`, `gpu_tot_sim_insn`, and `gpgpu_simulation_time`. Job
`486` metrics remain simulator validation evidence only; they are not hardware
target metrics.

## Calibration Target Selection Policy

The hardware target artifact keeps all parsed hardware characterization
metrics that are useful for provenance and run review, including native process
wall time, user/sys time, and max RSS. These metrics are not automatically S6
calibration targets.

The S6 handoff/template includes only simulator-comparable calibration targets:
currently Nsight Systems CUDA kernel elapsed-time metrics whose simulator
candidate counterpart can be derived from per-kernel simulator cycles and the
configured core clock.

Excluded/non-comparable metrics remain out of the S6 target list. In
particular, `native_wall_time_seconds` is retained in the hardware target YAML
as hardware characterization, but it is excluded from
`s6_supplied_metrics_handoff.target_metrics` and from generated S6 templates.
The simulator candidate bridge must not fabricate it.

## Supported MVP Case

The first case is:

- Job-launching selector:
  `rodinia_2.0-ft:backprop-rodinia-2.0-ft:0`
- Native case id: `backprop_4096`
- Native executable: `backprop-rodinia-2.0-ft`
- Native args: `4096 data/result-4096.txt`

The corresponding app definition is in:

```text
simulator-remodeled/util/job_launching/apps/define-all-apps.yml
```

The source is under:

```text
simulator-remodeled/gpu-app-collection/src/cuda/rodinia/2.0-ft/backprop/
```

## Native Collection Commands

Use `dsp5060` only for the GPU-dependent native run. Do not copy the main
workspace to `dsp5060`; copy only the small executable and gold file needed for
this case.

Example command sequence:

```bash
cd /home/xiewx/accel-0608/modern-gpu-simulator
RUN_ID=s7-hardware-target-$(date +%Y%m%d-%H%M%S)
ART=artifacts/s7/$RUN_ID
mkdir -p "$ART"

scp simulator-remodeled/gpu-app-collection/bin/13.1/release/backprop-rodinia-2.0-ft \
  dsp5060:/tmp/${RUN_ID}-backprop-rodinia-2.0-ft
ssh dsp5060 "rm -rf /tmp/$RUN_ID; mkdir -p /tmp/$RUN_ID/data; \
  mv /tmp/${RUN_ID}-backprop-rodinia-2.0-ft /tmp/$RUN_ID/backprop-rodinia-2.0-ft; \
  chmod +x /tmp/$RUN_ID/backprop-rodinia-2.0-ft"
scp simulator-remodeled/gpu-app-collection/data_dirs/cuda/rodinia/2.0-ft/backprop-rodinia-2.0-ft/data/result-4096.txt \
  dsp5060:/tmp/$RUN_ID/data/result-4096.txt

ssh dsp5060 "cd /tmp/$RUN_ID && {
  hostname
  date -Iseconds
  sha256sum backprop-rodinia-2.0-ft data/result-4096.txt
  ldd ./backprop-rodinia-2.0-ft
  nvidia-smi --query-gpu=name,uuid,driver_version,pci.bus_id,compute_cap,pstate,temperature.gpu,clocks.sm,clocks.mem,memory.total,memory.used --format=csv,noheader,nounits -i 0
  /usr/local/cuda-13.2/bin/nvcc --version
  nsys --version
  /usr/bin/time --version 2>&1 | head -3
}" > "$ART/remote-tool-versions.txt"

ssh dsp5060 "cd /tmp/$RUN_ID && \
  LD_LIBRARY_PATH=/usr/local/cuda-13.2/targets/x86_64-linux/lib:/usr/local/cuda/targets/x86_64-linux/lib:\$LD_LIBRARY_PATH \
  /usr/bin/time -f 'MGS_HW_TIME_wall_seconds=%e\nMGS_HW_TIME_user_seconds=%U\nMGS_HW_TIME_sys_seconds=%S\nMGS_HW_TIME_max_rss_kbytes=%M\nMGS_HW_TIME_exit_status=%x' \
  -o native-time.txt \
  ./backprop-rodinia-2.0-ft 4096 data/result-4096.txt \
  > native-stdout.txt 2> native-stderr.txt"

scp dsp5060:/tmp/$RUN_ID/native-stdout.txt "$ART/"
scp dsp5060:/tmp/$RUN_ID/native-stderr.txt "$ART/"
scp dsp5060:/tmp/$RUN_ID/native-time.txt "$ART/"
```

Optional Nsight Systems kernel timing:

```bash
ssh dsp5060 "cd /tmp/$RUN_ID && \
  LD_LIBRARY_PATH=/usr/local/cuda-13.2/targets/x86_64-linux/lib:/usr/local/cuda/targets/x86_64-linux/lib:\$LD_LIBRARY_PATH \
  nsys profile --trace=cuda --sample=none --cpuctxsw=none \
  --force-overwrite=true --output backprop-nsys \
  ./backprop-rodinia-2.0-ft 4096 data/result-4096.txt && \
  nsys stats --report cuda_gpu_kern_sum --format csv \
  --output backprop-nsys_cuda_gpu_kern_sum \
  --force-export true --force-overwrite true backprop-nsys.nsys-rep"

scp dsp5060:/tmp/$RUN_ID/backprop-nsys_cuda_gpu_kern_sum_cuda_gpu_kern_sum.csv \
  "$ART/backprop-nsys_cuda_gpu_kern_sum.csv"
scp dsp5060:/tmp/$RUN_ID/backprop-nsys.nsys-rep "$ART/"
scp dsp5060:/tmp/$RUN_ID/backprop-nsys.sqlite "$ART/"
```

## Parse Into Draft Hardware Targets

```bash
python3 simulator-remodeled/util/tuner/collect_sm120_hardware_metrics.py \
  --gpu RTX5060 \
  --stdout "$ART/native-stdout.txt" \
  --stderr "$ART/native-stderr.txt" \
  --time-output "$ART/native-time.txt" \
  --nsys-kernel-csv "$ART/backprop-nsys_cuda_gpu_kern_sum.csv" \
  --nvidia-smi-query "$ART/nvidia-smi-query.csv" \
  --tool-versions "$ART/remote-tool-versions.txt" \
  --collection-host dsp5060 \
  --source-label backprop_4096_native \
  --collection-command "recorded in worker log" \
  --output "$ART/RTX5060-backprop-4096-hardware-target-draft.yaml" \
  --s6-template-output "$ART/RTX5060-backprop-4096-s6-supplied-metrics-template.yaml"
```

The S6 template is deliberately `status: template_not_runnable`. It contains
only simulator-comparable hardware `target_metrics`, but it still lacks
reviewed bounded search parameters and local simulator candidate metrics. Do
not generate an S6 ranked report from this template as-is.

## 2026-06-10 Draft RTX5060 Artifact

Collected artifact root:

```text
artifacts/s7/s7-hardware-target-20260610-003544/
```

Important files:

- `RTX5060-backprop-4096-hardware-target-draft.yaml`
- `RTX5060-backprop-4096-s6-supplied-metrics-template.yaml`
- `native-stdout.txt`
- `native-time.txt`
- `backprop-nsys_cuda_gpu_kern_sum.csv`
- `backprop-nsys.nsys-rep`
- `backprop-nsys.sqlite`
- `remote-tool-versions.txt`
- `local-artifacts.sha256`

Summary:

- Host: `dsplab5060`
- GPU: `NVIDIA GeForce RTX 5060`
- Driver: `595.71.05`
- Compute capability: `12.0`
- CUDA toolkit recorded: `/usr/local/cuda-13.2`, `nvcc V13.2.78`
- Nsight Systems: `2025.6.3.541-256337736014v0`
- Native run result: `PASSED`
- Native wall time: `0.38` seconds from GNU time
- Nsight kernel total time: `0.0112` ms
- Nsight per-kernel totals:
  - `bpnn_layerforward_CUDA`: `0.002496` ms
  - `bpnn_adjust_weights_cuda`: `0.008704` ms

The native executable used for this first artifact is the existing checked-in
CUDA 13.1 `backprop-rodinia-2.0-ft` binary, run with the CUDA 13.2 runtime path
available on `dsp5060`. This is a real hardware timing artifact, but it is
still a single-run draft target and not an accepted calibration.

## Validation Commands

Fixture parser smoke:

```bash
python3 simulator-remodeled/util/tuner/collect_sm120_hardware_metrics.py \
  --gpu RTX5060 \
  --stdout simulator-remodeled/util/tuner/testdata/sm120_hardware_backprop_stdout.txt \
  --time-output simulator-remodeled/util/tuner/testdata/sm120_hardware_backprop_time.txt \
  --nsys-kernel-csv simulator-remodeled/util/tuner/testdata/sm120_hardware_backprop_nsys_kernel_sum.txt \
  --nvidia-smi-query simulator-remodeled/util/tuner/testdata/sm120_hardware_backprop_nvidia_smi.txt \
  --collection-host fixture \
  --source-label fixture \
  --collection-command "fixture native command" \
  --target-id fixture-sm120-backprop-hardware-target \
  --generated-at 2026-06-09T00:00:00Z \
  --fixture-only \
  --output /tmp/sm120_hardware_backprop_target.yaml \
  --s6-template-output /tmp/sm120_hardware_backprop_s6_template.yaml
```

Simulator-marker rejection:

```bash
printf 'gpu_tot_sim_cycle = 123\n' > /tmp/sm120_sim_marker.txt
python3 simulator-remodeled/util/tuner/collect_sm120_hardware_metrics.py \
  --gpu RTX5060 \
  --stdout /tmp/sm120_sim_marker.txt \
  --time-output simulator-remodeled/util/tuner/testdata/sm120_hardware_backprop_time.txt \
  --output /tmp/should-not-exist.yaml
```

The rejection command must fail.
