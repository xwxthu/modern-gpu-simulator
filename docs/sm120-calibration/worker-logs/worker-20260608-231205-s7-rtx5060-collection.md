# S7 RTX5060 Hardware Collection Worker Log

## Purpose

Run the first real S7 RTX5060 collection round for hardware characterization
and tuner microbenchmark collection only. This worker did not run a full
simulator on `dsp5060`, did not place the main workspace on `dsp5060`, and did
not write accepted calibration configs or `latest.yaml`.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base commit: `252376a235cb984e6b7780da3b1888be021c61eb`
- Timestamp: `2026-06-08T23:12:05+08:00`
- Run id: `rtx5060-s7-20260608-230140`
- Artifact root: `artifacts/s7/rtx5060-s7-20260608-230140/`
- Top-level dry-run copy: `artifacts/logs/rtx5060-s7-20260608-230140-local-dry-run-planner.stdout.txt`

## Commands And Results

- Created `artifacts/s7/rtx5060-s7-20260608-230140/` and copied
  `docs/sm120-calibration/s7-validation-manifest-template.yaml` to
  `validation-manifest.yaml`.
- Ran local dry-run planner:
  `python3 simulator-remodeled/util/tuner/check_sm120_s7_validation.py --gpu RTX5060 --run-id rtx5060-s7-20260608-230140`
  - Exit code: `0`
  - Evidence: `artifacts/s7/rtx5060-s7-20260608-230140/logs/local-dry-run-planner.stdout.txt`
  - The output states dry-run mode with no ssh, no hardware command, and no simulator launch.
- Ran local generator check:
  `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`
  - Exit code: `0`
  - Evidence: `artifacts/s7/rtx5060-s7-20260608-230140/logs/generate-sm120-check-only.stdout.txt`
- Checked `dsp5060` availability and lightweight CUDA/toolchain facts:
  - Exit code: `0`
  - Evidence: `artifacts/s7/rtx5060-s7-20260608-230140/logs/dsp5060-lightweight-toolchain.stdout.txt`
  - Found `/usr/local/cuda-13.2`; `/usr/local/cuda-13.2/bin/nvcc --list-gpu-code` contains `sm_120`.
  - Default remote `nvcc` is CUDA 12.8, so the tuner build explicitly used `CUDA_PATH=/usr/local/cuda-13.2`.
- Ran official-tool collector from local workspace:
  `python3 simulator-remodeled/util/hw_stats/collect_sm120_device_info.py --remote dsp5060 --device 0 --output-dir artifacts/s7/rtx5060-s7-20260608-230140/device-info`
  - Exit code: `0`
  - Collector output: `artifacts/s7/rtx5060-s7-20260608-230140/device-info/20260608-230436-dsp5060-device0/`
  - All collector subcommands returned `0`.
  - Metric discovery was skipped; collector manifest records `include_metric_discovery: false`.
- Created minimal tuner bundle:
  `tar --exclude 'bin' --exclude '*.o' --exclude 'sm120-rtx5060-microbench.txt' -czf /tmp/sm120-tuner-src-rtx5060-s7-20260608-230140.tgz -C simulator-remodeled/util/tuner GPU_Microbenchmark`
  - Exit code: `0`
- Copied tuner bundle to `dsp5060:/tmp/`.
  - Exit code: `0`
- Built tuner on `dsp5060` under `/tmp/sm120-tuner-collection-rtx5060-s7-20260608-230140/GPU_Microbenchmark`:
  `make CUDA_PATH=/usr/local/cuda-13.2 CUDA_ARCH=sm_120 HW_DEF=SM120_RTX5060`
  - Exit code: `2`
  - Evidence:
    `artifacts/s7/rtx5060-s7-20260608-230140/tuner-build-dsp5060.stdout.txt`,
    `artifacts/s7/rtx5060-s7-20260608-230140/tuner-build-dsp5060.stderr.txt`,
    `artifacts/s7/rtx5060-s7-20260608-230140/tuner-build-dsp5060.exitcode`
  - Root cause in stderr:
    `l1_access_grain.cu(54): error: identifier "uint32_t" is undefined`.
  - Build had already produced 23 partial binaries, but no `sm120-rtx5060-microbench.txt`.
- Did not run `./run_all.sh` because the tuner build failed.
  - Skip note: `artifacts/s7/rtx5060-s7-20260608-230140/sm120-rtx5060-microbench.SKIPPED.txt`
- Skipped local S5 parsing because real raw microbenchmark output was not produced.
  - Skip note: `artifacts/s7/rtx5060-s7-20260608-230140/RTX5060-real-microbench-draft.SKIPPED.txt`
- Ran RTX5070Ti compatibility dry-run:
  `python3 simulator-remodeled/util/tuner/check_sm120_s7_validation.py --gpu RTX5070_TI --run-id rtx5070ti-compat-plan --no-command-plan`
  - Exit code: `0`
  - Evidence: `artifacts/s7/rtx5060-s7-20260608-230140/logs/rtx5070ti-compatibility.stdout.txt`
- Ran final required checks:
  - `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`: exit code `0`
  - `git diff --check`: exit code `0`
  - Accepted config diff check for `latest.yaml` and generated tested config roots: exit code `0`, empty stdout/stderr.

## Hardware Evidence Summary

- GPU: `NVIDIA GeForce RTX 5060`
- UUID: `GPU-fd113d06-81ba-5c47-6fbe-fd8f1b99f80e`
- PCI bus id: `00000000:08:00.0`
- Driver: `595.71.05`
- Compute capability: `12.0`
- Observed state from `nvidia-smi` query:
  `P8`, graphics/SM/memory clocks `225/225/405`, max graphics/SM/memory clocks `3135/3135/14001`, memory total/free/used `8151/7458/217`.
- Tool versions captured:
  default remote `nvcc` CUDA 12.8 V12.8.93, selected build `nvcc` CUDA 13.2 V13.2.78, Nsight Compute `2026.1.1.0`, Nsight Systems `2024.6.2.225`.

## Artifact Hashes

- Manifest: `50bd2e9dc649730b1f2d4b7fcdabd038466454a27367d9e28beaba2ca285f11b`
  `artifacts/s7/rtx5060-s7-20260608-230140/validation-manifest.yaml`
- Device-info SHA256 manifest: `43d58c9d9f13162fee0490cde24906bba8ebe766302670ca2dd264629b442822`
  `artifacts/s7/rtx5060-s7-20260608-230140/device-info.sha256`
- Non-device artifact SHA256 manifest: `71463bcca281a0564d247c4e1d1c3173eacf605f8f3a84090e308c34c4475cd5`
  `artifacts/s7/rtx5060-s7-20260608-230140/artifact-files.sha256`
- Tuner build stdout: `691840c418dafc9512b1b15b051533d511bff3fb3f2582bb821ecb80bc8c3bb6`
- Tuner build stderr: `1551e700be7d12494df0a59c7cafa18c12ed215d2638e69dc740f67b49a4e343`
- Microbench skip note: `77f03306a89f36546a594598f5f4c5fd9b8d934ca80147467d388549e22ce34d`
- S5 parser skip note: `538450c1f72bf682882f0c82f9a66ddc98019187c7a92738be2805a419e6fab2`

The aggregate non-device artifact hash manifest excludes itself to keep the
hash stable.

## Failures And Skips

- Tuner build failed on `dsp5060` with exit code `2`.
- `run_all.sh` was skipped because the build did not complete.
- `RTX5060-real-microbench-draft.yaml` was not generated because there was no
  real raw microbenchmark output. No fixture or empty input was parsed.
- Unsupported keys, duplicate conflicts, and derived delta status could not be
  summarized because S5 parser output does not exist.
- S6 parameter sweep, correlation validation, and local simulator smoke were
  out of scope for this first collection round and were not run.
- No full simulator workload was run on `dsp5060`.
- No accepted config or `latest.yaml` was changed.

## Changed Files

- Tracked:
  - `docs/sm120-calibration/worker-logs/worker-20260608-231205-s7-rtx5060-collection.md`
- Local artifact evidence:
  - `artifacts/s7/rtx5060-s7-20260608-230140/`
  - `artifacts/logs/rtx5060-s7-20260608-230140-local-dry-run-planner.*`

## Reviewer Rounds

- Codex CLI reviewer attempt: started in read-only mode but hung before
  producing a verdict; the process was terminated and the failed attempt was
  not used as a review result. Evidence:
  `artifacts/s7/rtx5060-s7-20260608-230140/logs/reviewer-round1.stderr.txt`.
- Round 1 blank-context reviewer: ACCEPT.
  - Reviewer runner: Claude CLI fallback with read-only review instructions.
  - Output:
    `artifacts/s7/rtx5060-s7-20260608-230140/reviewer-round1.txt`
  - Output SHA256:
    `0fbd611ee06bffedc08f6245e2e131586d93840186a82eb911c771a28d6d8d86`
  - Non-blocking observations: some manifest entries initially lacked
    per-entry SHA256 fields, run-id-scoped remote `/tmp` path differed from the
    runbook example but did not violate hard rules, and reviewer artifacts were
    generated after the first aggregate hash. The manifest was updated with the
    reviewer verdict and extra SHA256 fields before final reporting.

## Final Status

Partial/blocked. Hardware characterization passed. Tuner collection is blocked
by a CUDA 13.2 build failure in the tuner source, so microbenchmark raw output
and S5 parser draft were not produced. Promotion gate remains closed.
