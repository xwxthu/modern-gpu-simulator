# S7 Hardware Target Metrics Worker Log

## Purpose

Create an S7 MVP for real hardware target metrics, distinct from simulator
smoke metrics, and provide reusable parsing/docs for future S6
`supplied_metrics` manifests.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base commit: `bd3826fed10f35f8915da22645089b58cdcf2901`
- Timestamp: `2026-06-10T00:39:54+08:00`
- Worker role: `S7 Hardware Target Metrics MVP`
- Worktree at start:
  - `docs/sm120-calibration/supervisor-log.md` had a pre-existing
    modification not made by this worker.

## Required Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/s7-validation-runbook.md`
- `docs/sm120-calibration/s7-validation-evidence-20260609.md`
- `docs/sm120-calibration/s6-correlation-search.md`
- `simulator-remodeled/util/tuner/search_sm120_correlation.py`
- `simulator-remodeled/util/tuner/testdata/sm120_correlation_search_fixture.yaml`
- Rodinia backprop source under
  `simulator-remodeled/gpu-app-collection/src/cuda/rodinia/2.0-ft/backprop/`
- Job-launching app YAML:
  `simulator-remodeled/util/job_launching/apps/define-all-apps.yml`

## Hard Rules Observed

- Did not use job `486` simulator metrics as hardware target metrics.
- Did not create an S6 ranked report.
- Did not modify accepted/generated/latest configs.
- Did not write `calibration-results/latest`.
- Did not run simulator workloads on `dsp5060`.
- Did not copy the main workspace to `dsp5060`; only a small native executable
  and gold output were copied to `/tmp`.

## Changes

- Added reusable collector:
  `simulator-remodeled/util/tuner/collect_sm120_hardware_metrics.py`
- Added fixture inputs:
  - `simulator-remodeled/util/tuner/testdata/sm120_hardware_backprop_stdout.txt`
  - `simulator-remodeled/util/tuner/testdata/sm120_hardware_backprop_time.txt`
  - `simulator-remodeled/util/tuner/testdata/sm120_hardware_backprop_nsys_kernel_sum.txt`
  - `simulator-remodeled/util/tuner/testdata/sm120_hardware_backprop_nvidia_smi.txt`
- Added checked-in runbook:
  `docs/sm120-calibration/s7-hardware-target-metrics.md`
- Added ignored artifact root:
  `artifacts/s7/s7-hardware-target-20260610-003544/`

## Collector Behavior

The collector parses:

- Native application stdout/stderr.
- GNU `/usr/bin/time` output with `MGS_HW_TIME_*` fields.
- Optional timing JSON.
- Optional Nsight Systems `cuda_gpu_kern_sum` CSV.
- Optional `nvidia-smi` query output.

It writes draft-only hardware targets:

- `schema_id: sm120_hardware_target_metrics_v1`
- `status: draft_not_applied`
- `hardware_target_metrics: true`
- `simulator_smoke_metrics: false`
- `handoff.do_not_claim_calibrated: true`

Safety behavior:

- Rejects known simulator markers including `gpu_tot_sim_cycle`,
  `gpu_tot_sim_insn`, and `gpgpu_simulation_time`.
- Refuses output paths under tested/generated config roots and
  `configs/layered/sm120/`.
- Writes optional S6 scaffold as `status: template_not_runnable`, with no
  candidate simulator metrics.

## Real Native RTX5060 Collection

Artifact root:

```text
artifacts/s7/s7-hardware-target-20260610-003544/
```

Remote collection host:

- SSH target: `dsp5060`
- Hostname: `dsplab5060`
- User: `xiewx`
- Date recorded by remote host: `2026-06-10T00:36:25+08:00`

Tool and device evidence:

- GPU: `NVIDIA GeForce RTX 5060`
- UUID: `GPU-fd113d06-81ba-5c47-6fbe-fd8f1b99f80e`
- Driver: `595.71.05`
- Compute capability: `12.0`
- Observed state: `P8`, SM clock `225 MHz`, memory clock `405 MHz`
- CUDA toolkit ledger: `/usr/local/cuda-13.2/bin/nvcc`, `V13.2.78`
- Nsight Systems: `2025.6.3.541-256337736014v0`
- GNU time: `time (GNU Time) UNKNOWN`

Source inputs copied to `/tmp/s7-hardware-target-20260610-003544/`:

- Existing native binary:
  `simulator-remodeled/gpu-app-collection/bin/13.1/release/backprop-rodinia-2.0-ft`
  - SHA256:
    `e2e4cfdf8f13f3101d97701abf0a1dfedfe225d0a8c92759e5254471bf01b038`
- Gold output:
  `simulator-remodeled/gpu-app-collection/data_dirs/cuda/rodinia/2.0-ft/backprop-rodinia-2.0-ft/data/result-4096.txt`
  - SHA256:
    `bb8a3873b36c4725b84a8efb34fd7e84040b6c29707a17350ad949c666429e3b`

Native run command:

```bash
cd /tmp/s7-hardware-target-20260610-003544
LD_LIBRARY_PATH=/usr/local/cuda-13.2/targets/x86_64-linux/lib:/usr/local/cuda/targets/x86_64-linux/lib:$LD_LIBRARY_PATH \
  /usr/bin/time -f 'MGS_HW_TIME_wall_seconds=%e\nMGS_HW_TIME_user_seconds=%U\nMGS_HW_TIME_sys_seconds=%S\nMGS_HW_TIME_max_rss_kbytes=%M\nMGS_HW_TIME_exit_status=%x' \
  -o native-time.txt \
  ./backprop-rodinia-2.0-ft 4096 data/result-4096.txt \
  > native-stdout.txt 2> native-stderr.txt
```

Native run result:

- Exit code: `0`
- Application stdout contains `PASSED`
- Checksum printed by app: `0x42b0e8add8ca`
- GNU time:
  - `native_wall_time_seconds = 0.38`
  - `native_user_time_seconds = 0.05`
  - `native_sys_time_seconds = 0.31`
  - `native_max_rss_kbytes = 138420`

Nsight Systems command:

```bash
cd /tmp/s7-hardware-target-20260610-003544
LD_LIBRARY_PATH=/usr/local/cuda-13.2/targets/x86_64-linux/lib:/usr/local/cuda/targets/x86_64-linux/lib:$LD_LIBRARY_PATH \
  nsys profile --trace=cuda --sample=none --cpuctxsw=none \
  --force-overwrite=true --output backprop-nsys \
  ./backprop-rodinia-2.0-ft 4096 data/result-4096.txt
nsys stats --report cuda_gpu_kern_sum --format csv \
  --output backprop-nsys_cuda_gpu_kern_sum \
  --force-export true --force-overwrite true backprop-nsys.nsys-rep
```

Nsight result:

- `nsys profile` exit code: `0`
- `nsys stats` exit code: `0`
- Exported CSV copied locally as
  `artifacts/s7/s7-hardware-target-20260610-003544/backprop-nsys_cuda_gpu_kern_sum.csv`
- Kernel totals:
  - `bpnn_layerforward_CUDA`: `2496 ns` = `0.002496 ms`
  - `bpnn_adjust_weights_cuda`: `8704 ns` = `0.008704 ms`
  - Total kernel time: `0.0112 ms`

## Draft Hardware Target Artifact

Draft YAML:

```text
artifacts/s7/s7-hardware-target-20260610-003544/RTX5060-backprop-4096-hardware-target-draft.yaml
```

Generated S6 scaffold:

```text
artifacts/s7/s7-hardware-target-20260610-003544/RTX5060-backprop-4096-s6-supplied-metrics-template.yaml
```

Important hashes after final collector script update:

| Artifact | SHA256 |
| --- | --- |
| `collect_sm120_hardware_metrics.py` | `2a02380d14a3a3f09ddf9532e9f91ebd3840cd062b060a8c9fde9179b6677047` |
| `RTX5060-backprop-4096-hardware-target-draft.yaml` | `2f83bcd2d59d6e1a1eece262485856090b2041dc66d3b4e9c95b9524951e76ae` |
| `RTX5060-backprop-4096-s6-supplied-metrics-template.yaml` | `d14072cba3c87f2ed9f84a009ec9e917b3a736ce7e070dc67739e49445b504de` |
| `native-stdout.txt` | `daf8768fde5468c707e82d36ac7c138cc90146a6c4fdb381a4c38bc5ee669523` |
| `native-time.txt` | `822652a0e5a9278fad2139d4c0d844ac1996961e88d985bbe4b8dc68835daa84` |
| `backprop-nsys_cuda_gpu_kern_sum.csv` | `cfec0ba2892f2cb9bedd7ef74450f8269aaa8fada96530817767c71f7958779f` |
| `backprop-nsys.nsys-rep` | `1a4fd8c0687c1978d801744a915ab28deba8a9a02340a71cb4b36db5ab833973` |
| `backprop-nsys.sqlite` | `a4e5099ef1f4635823edf5ac2c90e8d4e57ce2ede44673b41a06ba90ae611d04` |
| `remote-tool-versions.txt` | `d6e9b8a8dba9b83f34d1324445440406337faedc01a86626d081e3ab97db5419` |

The draft YAML records `fixture_only: false`, `hardware_target_metrics: true`,
and `simulator_smoke_metrics: false`. The S6 handoff records
`ready_for_search_sm120_correlation: false` because no reviewed candidate
simulator metrics exist for the target metric names yet.

## Validation

Completed during implementation and final validation:

- `git diff --check`
  - Exit code: `0`
- `python3 simulator-remodeled/util/tuner/collect_sm120_hardware_metrics.py --help`
  - Exit code: `0`
- Fixture parse/generation to `/tmp/sm120_hardware_backprop_target.yaml` and
  `/tmp/sm120_hardware_backprop_s6_template.yaml`
  - Exit code: `0`
  - Summary: `sm120_hardware_target_metrics_v1`, `draft_not_applied`,
    `9` target metrics, `hardware_target_metrics: true`,
    `simulator_smoke_metrics: false`.
- Simulator-marker negative check with `gpu_tot_sim_cycle`; command failed as
  expected with a hardware-target rejection.
  - Exit code: `1`
  - Error included: `native stdout contains simulator markers`.
- `python3 -m py_compile simulator-remodeled/util/tuner/collect_sm120_hardware_metrics.py`
  - Exit code: `0`
- `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`
  - Exit code: `0`
- Protected config/latest scoped status check:
  - Command:
    `git status --short -- <SM120 tested configs, generated tested configs, layered base/overlays/calibration-results>`
  - Exit code: `0`
  - Output size: `0` bytes.
- `dsp5060` no-simulator/no-workspace check:
  - Exit code: `0`
  - `pgrep -af "[g]pgpu|[r]un_simulations|[p]rocman|[a]ccel-sim"`
    had no output between `SIM_PROCESS_CHECK_BEGIN` and
    `SIM_PROCESS_CHECK_END`.
  - `NO_MAIN_WORKSPACE_IN_TMP` and `NO_MAIN_WORKSPACE_IN_HOME` were recorded.

Validation logs are under:

```text
artifacts/s7/s7-hardware-target-20260610-003544/
```

## Reviewer Rounds

Reviewer round 1:

- Reviewer: fresh blank-context Codex read-only reviewer.
- Command output:
  `artifacts/s7/s7-hardware-target-20260610-003544/reviewer-round1-codex.txt`
- Exit code: `0`
- Verdict: `ACCEPT`
- Summary: reviewer confirmed the S7 boundary is satisfied; hardware targets are
  distinct from simulator smoke metrics, the artifact YAML is real native
  `dsp5060` provenance and draft-only, the S6 output is a non-runnable
  template with no candidate simulator metrics, validation evidence is
  adequate, and accepted/generated/latest config paths remain unmodified.

## Current Status

Real RTX5060 native hardware target metrics were collected and parsed into a
draft-only artifact. The target is a single lightweight run and is not promoted
to any accepted config or `latest` calibration result. S6 still needs reviewed
bounded parameters and candidate simulator metrics before any ranked report can
be generated.
