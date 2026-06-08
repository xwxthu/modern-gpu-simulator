# S7 Actual Local Smoke Worker Log

## Purpose

Prepare Rodinia backprop smoke data and run one actual local simulator smoke for
`rodinia_2.0-ft:backprop-rodinia-2.0-ft:0` with `RTX5060_SM120_GEN`. This worker
did not run a full simulator workload on `dsp5060`, did not write accepted
configs, and did not write `calibration-results/*/latest.yaml`.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Host: `dsp-ubuntu`
- Base HEAD: `287ead489912718dbc3b3c93c656060800107d03`
- Base subject: `fix: support CUDA 13 local smoke setup`
- Timestamp: `2026-06-09T01:08:04+08:00`
- Run id: `s7-actual-smoke-20260609-005843`
- Artifact root: `artifacts/s7/s7-actual-smoke-20260609-005843/`

## Data Provisioning

Rodinia 2.0-ft backprop uses the second argument as a functional-test gold file:
the app writes `result.txt` and compares it against `./data/result-4096.txt`.
It is not an input network file.

Provisioning command:

```bash
mkdir -p artifacts/s7/s7-actual-smoke-20260609-005843/gold-generation-native
cd artifacts/s7/s7-actual-smoke-20260609-005843/gold-generation-native
env LD_LIBRARY_PATH=/usr/local/cuda-13.1/lib64 PATH=/usr/local/cuda-13.1/bin:$PATH \
  /home/xiewx/accel-0608/modern-gpu-simulator/simulator-remodeled/gpu-app-collection/bin/13.1/release/backprop-rodinia-2.0-ft 4096
```

Installed data path:

```text
simulator-remodeled/gpu-app-collection/data_dirs/cuda/rodinia/2.0-ft/backprop-rodinia-2.0-ft/data/result-4096.txt
```

Evidence:

- Generation log:
  `artifacts/s7/s7-actual-smoke-20260609-005843/gold-generation-native.log`
- Native stdout checksum: `0x42b0e8add8ca`
- SHA256:
  `bb8a3873b36c4725b84a8efb34fd7e84040b6c29707a17350ad949c666429e3b`
- Line count: `69649`

## Setup-Only Plan

The first setup-only attempt used an outer `set -u` wrapper and failed before
launch because the simulator setup script references unset
`OPENCL_REMOTE_GPU_HOST`. Evidence:
`local-smoke-plan-attempt1-nounset.log`.

Successful setup-only command:

```bash
export CUDA_INSTALL_PATH=/usr/local/cuda-13.1
export PATH="$CUDA_INSTALL_PATH/bin:$PATH"
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-actual-smoke-20260609-005843-smoke-plan \
  -r artifacts/s7/s7-actual-smoke-20260609-005843/sim-smoke-plan \
  -l local \
  -n
```

- Exit code: `0`
- Evidence: `local-smoke-plan.log`
- Generated run dir:
  `artifacts/s7/s7-actual-smoke-20260609-005843/sim-smoke-plan/backprop-rodinia-2.0-ft/4096___data_result_4096_txt/RTX5060_SM120_GEN/`
- `data` symlink points to the provisioned gpu-app collection data directory.
- `justrun.sh` command:
  `backprop-rodinia-2.0-ft 4096 ./data/result-4096.txt`

## Actual Local Smoke

Command:

```bash
export CUDA_INSTALL_PATH=/usr/local/cuda-13.1
export PATH="$CUDA_INSTALL_PATH/bin:$PATH"
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-actual-smoke-20260609-005843-smoke \
  -r artifacts/s7/s7-actual-smoke-20260609-005843/sim-smoke \
  -l local \
  -c 2
```

- Launcher exit code: `0`
- Exactly one job queued:
  `backprop-rodinia-2.0-ft-4096___data_result_4096_txt RTX5060_SM120_GEN`
- Evidence: `local-smoke-run.log`
- Local procman only; no `dsp5060` simulator launch.

The smoke did not complete. `job_status.py` reported RUNNING from procman state,
but the recorded job PID `1576963` and procman manager PID `1576945` were not
alive after waiting beyond a procman tick interval. The `/tmp` stdout contained
only wrapper script echo lines through the target command; stderr was empty.
The run directory did not receive moved `.o1`/`.e1` files, `result.txt`, a
functional PASS/FAIL, or simulator stats.

Captured evidence:

- `local-smoke-job-status.log`
- `run-output/backprop-rodinia-2.0-ft-4096___data_result_4096_txt.gpgpu-sim_git-commit-6c0329df63d8e789c238725dcc0bb029b7edb2f9_modified_1.0.o1`
- `run-output/backprop-rodinia-2.0-ft-4096___data_result_4096_txt.gpgpu-sim_git-commit-6c0329df63d8e789c238725dcc0bb029b7edb2f9_modified_1.0.e1`
- `procman-status-after-stale.log`
- `process-check-after-stale.log`
- `tmp-output-files.log`

The stale procman tmp pickle was archived under `procman-state/` and then
removed from `simulator-remodeled/util/job_launching/procman/` so later local
jobs are not polluted. Post-cleanup procman status: `Nothing Active`.

## Metrics And S6

No real simulator metrics were available. `metrics-grep.log` found no
`gpu_tot_sim_cycle`, `gpu_tot_sim_insn`, `gpu_tot_ipc`,
`gpgpu_simulation_time`, simulator exit marker, or functional PASS/FAIL.

No `RTX5060-s6-supplied-metrics.yaml` was created because the actual smoke did
not produce real metrics for a bounded S6 supplied-metrics manifest.

## Artifact Summary

- Manifest:
  `artifacts/s7/s7-actual-smoke-20260609-005843/validation-manifest.yaml`
- Smoke metrics note:
  `artifacts/s7/s7-actual-smoke-20260609-005843/smoke-metrics-note.md`
- Artifact hashes:
  `artifacts/s7/s7-actual-smoke-20260609-005843/artifact-files.sha256`
- Data hashes:
  `artifacts/s7/s7-actual-smoke-20260609-005843/data-provisioning.sha256`

## Reviewer Rounds

- Round 1 blank-context reviewer: ACCEPT.
  - Reviewer runner: `codex exec -s read-only`.
  - Exit code: `0`.
  - Evidence:
    `artifacts/s7/s7-actual-smoke-20260609-005843/reviewer-round1-codex.txt`.
  - Reviewer summary: evidence supports an honest partial/failed local smoke;
    data provisioning, setup-only, exactly one local queued job, no `dsp5060`
    simulator run, no `latest.yaml` promotion, and no fabricated metrics.

## Final Checks

- `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`
  - Exit code: `0`.
  - Evidence:
    `artifacts/s7/s7-actual-smoke-20260609-005843/final-generate-check-only.log`.
  - Output generated `SM120_RTX5070_TI` and `SM120_RTX5060` bootstrap
    profiles with `gpgpu_keys=217` and `trace_keys=13`.
- `git diff --check`
  - Exit code: `0`.
  - Evidence:
    `artifacts/s7/s7-actual-smoke-20260609-005843/final-git-diff-check.log`.
- Accepted/generated config scoped status:
  - Exit code: `0`.
  - Evidence:
    `artifacts/s7/s7-actual-smoke-20260609-005843/final-accepted-generated-config-scoped-status.log`.
  - Output was empty. No accepted config, generated tested config,
    calibration result, or `latest.yaml` path was modified.
- Final git status:
  - Evidence:
    `artifacts/s7/s7-actual-smoke-20260609-005843/final-git-status.log`.
  - Only tracked change from this worker is this worker log. Run artifacts and
    gpu-app `data_dirs/` are ignored by repo policy.

## Status

Partial. Data provisioning and setup-only are complete. One actual local smoke
job was launched, but it did not complete and produced no real simulator
metrics. S6 real supplied-metrics correlation remains pending.
