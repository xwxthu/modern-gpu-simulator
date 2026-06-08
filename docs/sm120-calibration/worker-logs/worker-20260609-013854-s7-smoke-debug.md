# S7 Smoke Debug Worker Log

## Purpose

Debug why the S7 actual local smoke launched through local procman but did not
produce moved logs or metrics. This worker did not run a full simulator on
`dsp5060`, did not write accepted configs, did not write
`calibration-results/*/latest.yaml`, and did not fabricate metrics.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Host: `dsp-ubuntu`
- Base HEAD: `d313077c758707d0a8951cf2b0349db4a1e76633`
- Base subject: `docs: record S7 actual smoke attempt`
- Timestamp: `2026-06-09T01:38:54+08:00`
- Run id: `s7-smoke-debug-20260609-013048`
- Artifact root: `artifacts/s7/s7-smoke-debug-20260609-013048/`

## Inputs Reviewed

- Prior worker log:
  `docs/sm120-calibration/worker-logs/worker-20260609-010804-s7-actual-smoke.md`
- Failed smoke artifacts:
  `artifacts/s7/s7-actual-smoke-20260609-005843/`
- Failed wrapper:
  `artifacts/s7/s7-actual-smoke-20260609-005843/sim-smoke/backprop-rodinia-2.0-ft/4096___data_result_4096_txt/RTX5060_SM120_GEN/slurm.sim`
- Failed `/tmp` output archived under:
  `artifacts/s7/s7-actual-smoke-20260609-005843/run-output/`
- Launcher code:
  `simulator-remodeled/util/job_launching/run_simulations.py`
  and `simulator-remodeled/util/job_launching/procman.py`

## Root Cause: Missing Moved Logs

The local procman manager was spawned as a normal child process of the launcher
command. In this execution environment, when the parent command returned and a
later command checked status, that manager and its active child could be killed
with the parent session. Procman state was left at RUNNING, while `/tmp` stdout
and stderr existed but the job never reached the wrapper's final `copy_output`.

Evidence:

- Failed smoke state:
  `artifacts/s7/s7-actual-smoke-20260609-005843/procman-status-after-stale.log`
  showed active job `procId=1576963` and manager pickle
  `procman.dsp-ubuntu.pickle.tmp.1576945`, but neither process was alive.
- Failed `/tmp` stdout ended at the target command echo and stderr was empty:
  `artifacts/s7/s7-actual-smoke-20260609-005843/run-output/*.o1`
  and `*.e1`.
- Mini repro before fix:
  `artifacts/s7/procman-mini-repro-split/status-after-7s.log`
  showed a 5-second sleep job still recorded RUNNING after 7 seconds, with
  zero-byte `/tmp/procman-mini-repro-split.*` output.
- Mini repro after fix:
  `artifacts/s7/procman-mini-repro-fixed/status-after-7s.log`
  reported `Nothing Active`, and `/tmp/procman-mini-repro-fixed.o1` contained
  the real command output.

## Fix

Changed only `simulator-remodeled/util/job_launching/procman.py`.

`ProcMan.spawnProcMan()` now starts the background manager detached from the
caller's terminal/session and with stdio redirected to `DEVNULL`:

```python
Popen(..., stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL, start_new_session=True)
```

This preserves the existing procman CLI, pickle flow, job queue semantics, and
status behavior while allowing the local manager to outlive
`run_simulations.py` after the launcher exits.

## New Setup-Only

Command:

```bash
export CUDA_INSTALL_PATH=/usr/local/cuda-13.1
export PATH="$CUDA_INSTALL_PATH/bin:$PATH"
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-smoke-debug-20260609-013048-smoke-plan \
  -r artifacts/s7/s7-smoke-debug-20260609-013048/sim-smoke-plan \
  -l local \
  -n
```

- Exit code: `0`
- Evidence: `local-smoke-plan.log`
- Generated run dir:
  `artifacts/s7/s7-smoke-debug-20260609-013048/sim-smoke-plan/backprop-rodinia-2.0-ft/4096___data_result_4096_txt/RTX5060_SM120_GEN/`
- `data/result-4096.txt` SHA256:
  `bb8a3873b36c4725b84a8efb34fd7e84040b6c29707a17350ad949c666429e3b`
- `justrun.sh` command:
  `backprop-rodinia-2.0-ft 4096 ./data/result-4096.txt`

## One Local Smoke Retry

Command:

```bash
export CUDA_INSTALL_PATH=/usr/local/cuda-13.1
export PATH="$CUDA_INSTALL_PATH/bin:$PATH"
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-smoke-debug-20260609-013048-smoke \
  -r artifacts/s7/s7-smoke-debug-20260609-013048/sim-smoke \
  -l local \
  -c 1
```

- Launcher exit code: `0`
- Exactly one local procman job queued:
  `backprop-rodinia-2.0-ft-4096___data_result_4096_txt RTX5060_SM120_GEN`
- Evidence: `local-smoke-run.log`
- Poll 1: `RUNNING`
- Poll 2: `FUNC_TEST_PASSED`
- Evidence: `job-status-poll-1.log`, `job-status-poll-2.log`,
  `procman-status-poll-1.log`, `procman-status-poll-2.log`
- Final procman state after cleanup: `Nothing Active`
- No `dsp5060` simulator launch was performed.

Moved run-dir outputs now exist:

- `.o1`:
  `artifacts/s7/s7-smoke-debug-20260609-013048/sim-smoke/backprop-rodinia-2.0-ft/4096___data_result_4096_txt/RTX5060_SM120_GEN/backprop-rodinia-2.0-ft-4096___data_result_4096_txt.gpgpu-sim_git-commit-6c0329df63d8e789c238725dcc0bb029b7edb2f9_modified_1.0.o1`
- `.e1`:
  same directory, `.e1`, size `0`
- `result.txt` SHA256:
  `bb8a3873b36c4725b84a8efb34fd7e84040b6c29707a17350ad949c666429e3b`
- The stdout contains checksum `0x42b0e8add8ca` and `PASSED`.

## Metrics Result

No real simulator metrics were produced by this one smoke. `metrics-grep.log`
contains only the functional `PASSED` marker and no `gpu_tot_sim_cycle`,
`gpu_tot_sim_insn`, `gpu_tot_ipc`, or `gpgpu_simulation_time`.

Root cause for missing simulator metrics is separate from the moved-log issue:
the CUDA 13.1 app binary is dynamically linked against `libcudart.so.13`, while
the GPGPU-Sim copied runtime is only `libcudart.so`. `app-ldd.log` shows that
even with the run wrapper's simulator `LD_LIBRARY_PATH`, the app loaded
`/usr/local/cuda-13.1/lib64/libcudart.so.13`.

Additional ABI evidence:

- `app-dynamic-inspection.log`: app NEEDED is `libcudart.so.13`.
- `sim-lib-inspection.log`: GPGPU-Sim build has symlinks only through
  `libcudart.so.12.0`, and copied run dirs only copied unversioned
  `libcudart.so`.
- `version-info.log`: app requires symbol version `libcudart.so.13`; current
  GPGPU-Sim version script defines only through `libcudart.so.12.0`.
- `cuda-symbols.log`: app has undefined
  `__cudaGetKernel@libcudart.so.13` and
  `__cudaLaunchKernel@libcudart.so.13`; current GPGPU-Sim runtime does not
  define `__cudaGetKernel`.
- `ldd-symlink-test-abs.log`: an absolute `libcudart.so.13` symlink to the
  GPGPU-Sim runtime is found by the dynamic linker, but still fails symbol
  versioning and `__cudaGetKernel` resolution.

Because the user allowed exactly one local smoke retry, this worker did not run
a second simulator attempt after identifying the CUDA 13 runtime ABI blocker.
No supplied-metrics manifest was created.

## Artifact Summary

- Artifact list: `artifact-files.list`
- Artifact hashes: `artifact-files.sha256`
- Procman mini repro summary: `procman-mini-repro-summary.log`
- Dynamic-link evidence: `app-ldd.log`, `version-info.log`,
  `ldd-symlink-test-abs.log`, `cuda-symbols.log`
- Final git status: `final-git-status.log`

## Final Checks

- `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`
  - Exit code: `0`
  - Evidence: `final-generate-check-only.log`
  - Output generated `SM120_RTX5070_TI` and `SM120_RTX5060` bootstrap
    profiles with `gpgpu_keys=217` and `trace_keys=13`.
- `git diff --check`
  - Exit code: `0`
  - Evidence: `final-git-diff-check.log`
- Accepted/generated config scoped status:
  - Exit code: `0`
  - Evidence:
    `final-accepted-generated-config-scoped-status.log`
  - Output was empty. No accepted config, generated tested config,
    calibration result, or `latest.yaml` path was modified.
- `python3 -m py_compile simulator-remodeled/util/job_launching/procman.py`
  - Exit code: `0`
  - Evidence: `final-procman-py-compile.log`
  - Existing SyntaxWarnings remain for unrelated invalid escape sequences in
    later `re.sub("\%j", ...)` lines.

## Changed Files

- `simulator-remodeled/util/job_launching/procman.py`
- `docs/sm120-calibration/worker-logs/worker-20260609-013854-s7-smoke-debug.md`

Ignored/local artifacts:

- `artifacts/s7/s7-smoke-debug-20260609-013048/`
- `artifacts/s7/procman-mini-repro*/`

## Reviewer Rounds

- Round 1 reviewer runner attempt:
  - `codex exec -s read-only -a never` rejected the unsupported `-a`
    argument before review.
  - Exit code: `2`
  - Evidence: `reviewer-round1-codex.txt`
- Round 2 blank-context reviewer: ACCEPT.
  - Reviewer runner: `codex exec -s read-only`
  - Exit code: `0`
  - Evidence: `reviewer-round2-codex.txt`
  - Reviewer summary: evidence supports the stale procman/no moved log root
    cause, the minimal detach fix, exactly one local smoke with moved outputs
    and `FUNC_TEST_PASSED`, honest absence of simulator metrics, documented
    CUDA 13 `libcudart.so.13` ABI blocker, and clean protected config/latest
    paths.

## Status

Partial. The original "job dies/stale without moved `.o1/.e1`" issue is root
caused and fixed, and the one allowed local smoke now reaches
`FUNC_TEST_PASSED` with moved `.o1/.e1` and matching `result.txt`. Real
simulator metrics remain blocked by CUDA 13 `libcudart.so.13` ABI support in
the GPGPU-Sim runtime, not by procman log handling.
