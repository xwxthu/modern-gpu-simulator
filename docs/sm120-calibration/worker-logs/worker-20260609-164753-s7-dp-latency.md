# S7 DP Latency Worker Log

## Purpose

Fix or precisely bound the current S7 PTX-mode smoke blocker:

```text
traced_instruction::get_num_destination_registers(this=0x0)
warp_inst_t::generate_dp_latencies()
Subcore::single_decode()
Subcore::decode()
```

The assigned root-cause question is whether remodeled decode-latency generation
is incorrectly using trace-enhanced instruction metadata in PTX mode, where the
decoded PTX instruction has no `m_extra_trace_instruction_info`.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base commit: `6147018`
- Timestamp: `2026-06-09T16:47:53+08:00`
- Initial worktree: tracked tree clean; ignored artifacts/build outputs present
- Artifact root: `artifacts/s7/s7-dp-latency-20260609-164753/`

## Inputs Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/worker-logs/worker-20260609-160932-s7-function-call-stack.md`
- `artifacts/s7/s7-function-call-stack-20260609-160932/coredump-gdb-focused-new-blocker-1366300.log`
- `artifacts/s7/s7-function-call-stack-20260609-160932/coredump-gdb-focused-new-blocker-state-1366300.log`

## Assigned Scope

- Inspect and fix the PTX-mode crash in remodeled decode latency generation.
- Preserve trace-mode detailed trace-enhanced latency modeling.
- Keep trace mode explicit-fail behavior when trace instruction metadata is
  required but absent.
- Do not globally disable decode latency generation.
- Do not use SM120/RTX5060 magic constants.
- Do not modify config/latest/generated/calibration/result files.
- Do not run simulator workloads on `dsp5060`.
- Do not commit.

## Root Cause

The crash is a PTX/trace metadata boundary bug in remodeled decode-latency
generation.

In PTX mode, the decoded `ptx_instruction` already carries baseline
`latency`, `initiation_interval`, opcode classification, PTX operand counts,
and architectural source/destination registers from `ptx_instruction::pre_decode()`
and `set_opcode_and_latency()`. It does not carry enhanced trace metadata:

- `m_config->is_trace_mode == false`
- `pI->op == DP_OP`
- `pI->sp_op == DP___OP`
- `pI->m_decoded == true`
- `pI->m_extra_trace_instruction_info` is empty

`warp_inst_t::generate_dp_latencies()` unconditionally called
`get_extra_trace_instruction_info().get_num_destination_registers()`, so an
assertion-disabled build dereferenced a null `std::shared_ptr<traced_instruction>`.
The same boundary existed around tensor-core latency: tensor metadata parsing
was called unconditionally from `Subcore::single_decode()`, and
`generate_tensor_core_latencies()` immediately read trace-derived tensor shape
metadata.

The existing memory and predicate paths already showed the correct model:
PTX/no-trace mode must use PTX-predecode/config-backed baseline timing, while
trace mode must keep detailed trace-enhanced modeling and explicitly fail if the
metadata required for that modeling is missing.

## Actions

- Added explicit metadata checks before trace-only tensor-core metadata parsing.
- Split `generate_tensor_core_latencies()` by mode:
  - PTX mode preserves the PTX-predecoded `latency` and `initiation_interval`
    and initializes the WAR-free counter needed by the remodeled fixed-latency
    path.
  - Trace mode requires enhanced trace metadata and keeps the existing tensor
    shape/rate calculation.
- Split `generate_dp_latencies()` by mode:
  - PTX mode uses existing config parameters (`dp_shared_intermidiate_stages`
    and `memory_subcore_link_to_sm_byte_size`) plus PTX-predecoded source
    register count (`incount`) to initialize the shared-DP subcore transfer
    stages without touching trace metadata.
  - Trace mode explicitly aborts if trace instruction metadata is absent, then
    keeps the existing operand-transfer and writeback modeling.
- Added a config sanity check for zero shared-DP intermediate stages to avoid an
  unsigned underflow in both PTX and trace DP latency modeling.
- Gated `Subcore::single_decode()` tensor-core metadata extraction on trace mode
  so PTX tensor instructions do not call a trace-only parser.
- Did not:
  - globally disable decode latency generation
  - set missing metadata to a silent default trace instruction
  - default all missing metadata to one cycle
  - add RTX5060/SM120 magic constants
  - modify generated configs, latest aliases, calibration results, or metrics
  - run simulator workloads on `dsp5060`

## Changed Files

Code:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/abstract_hardware_model.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc`

Documentation:

- `docs/sm120-calibration/worker-logs/worker-20260609-164753-s7-dp-latency.md`

Ignored/local artifacts:

- `artifacts/s7/s7-dp-latency-20260609-164753/`

## Validation

Whitespace checks passed:

```bash
git diff --check
```

- Initial evidence:
  `artifacts/s7/s7-dp-latency-20260609-164753/git-diff-check.initial.log`,
  exit code `0`.
- Prebuild evidence:
  `artifacts/s7/s7-dp-latency-20260609-164753/git-diff-check-prebuild.log`,
  exit code `0`.
- Final evidence:
  `artifacts/s7/s7-dp-latency-20260609-164753/git-diff-check-final.log`,
  exit code `0`.

SM120 generated-config reproducibility check passed:

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
```

- Evidence:
  - `artifacts/s7/s7-dp-latency-20260609-164753/generate-check-only.log`
  - `artifacts/s7/s7-dp-latency-20260609-164753/generate-check-only-final.log`
- Exit codes:
  - `generate-check-only.exitcode`: `0`
  - `generate-check-only-final.exitcode`: `0`
- Output:
  generated `SM120_RTX5070_TI` and `SM120_RTX5060` bootstrap profiles with
  `gpgpu_keys=217` and `trace_keys=13`.

Release GPGPU-Sim rebuild passed with local CUDA 13.1:

```bash
export CUDA_INSTALL_PATH=${CUDA_INSTALL_PATH:-/usr/local/cuda-13.1}
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment
make -C simulator-remodeled/gpu-simulator/gpgpu-sim -j"$(nproc)"
```

- Evidence:
  `artifacts/s7/s7-dp-latency-20260609-164753/rebuild-gpgpusim.log`
- Exit code:
  `artifacts/s7/s7-dp-latency-20260609-164753/rebuild-gpgpusim.exitcode`,
  value `0`.
- Build notes:
  only existing rapidjson `std::iterator` deprecation warnings were observed.

Setup-only PTX smoke planning passed:

```bash
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-dp-latency-20260609-164753-smoke-plan \
  -r artifacts/s7/s7-dp-latency-20260609-164753/sim-smoke-plan \
  -l local \
  -n
```

- Procman before plan:
  `artifacts/s7/s7-dp-latency-20260609-164753/procman-status-before-plan.log`,
  `Nothing Active`.
- Evidence:
  `artifacts/s7/s7-dp-latency-20260609-164753/local-smoke-plan.log`
- Exit code:
  `artifacts/s7/s7-dp-latency-20260609-164753/local-smoke-plan.exitcode`,
  value `0`.

Exactly one local PTX smoke was launched after rebuild:

```bash
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-dp-latency-20260609-164753-smoke \
  -r artifacts/s7/s7-dp-latency-20260609-164753/sim-smoke \
  -l local \
  -c 4
```

- Launcher evidence:
  `artifacts/s7/s7-dp-latency-20260609-164753/local-smoke-run.log`
- Launcher exit code:
  `artifacts/s7/s7-dp-latency-20260609-164753/local-smoke-run.exitcode`,
  value `0`.
- Procman job:
  Job `481`.
- Output evidence before stop:
  - `artifacts/s7/s7-dp-latency-20260609-164753/smoke-stdout-before-stop.o481.log`
  - `artifacts/s7/s7-dp-latency-20260609-164753/smoke-stderr-before-stop.e481.log`
  - `artifacts/s7/s7-dp-latency-20260609-164753/procman-pstree-before-stop.log`
- The smoke reached first-kernel performance simulation and bound SMs through:
  `GPGPU-Sim uArch: Shader 29 bind to kernel 1
  '_Z22bpnn_layerforward_CUDAPfS_S_S_ii'`.
- The old blocker did not appear in the captured output:
  no `traced_instruction::get_num_destination_registers(this=0x0)`, no
  `Trace DP latency modeling requires trace instruction metadata`, no
  segmentation fault, and no assertion were found.
- The smoke had not produced first-kernel metrics after about eight minutes, so
  it was stopped with ProcMan rather than allowed to run indefinitely:
  `artifacts/s7/s7-dp-latency-20260609-164753/procman-kill-smoke.log`,
  exit code `0`.
- Final procman status:
  `artifacts/s7/s7-dp-latency-20260609-164753/procman-status-after-kill.log`,
  active jobs `0`, complete jobs `1`.

Smoke caveat:

- This smoke run is sufficient to show the assigned DP null-metadata crash was
  not reproduced before the run was stopped, but it is not a full successful
  PTX smoke. The current bounded next issue is a long-running/stalled local
  smoke in first-kernel execution before metrics, requiring separate S7 triage
  if the supervisor wants the smoke to run to completion.

## Reviewer Rounds

Round 1:

- Fresh read-only reviewer was launched with output under
  `artifacts/s7/s7-dp-latency-20260609-164753/reviewer/reviewer-round1.log`.
- The process ran for about 6.5 minutes and did not produce a formal `VERDICT`
  or exit-code file, so it was terminated and recorded in
  `artifacts/s7/s7-dp-latency-20260609-164753/reviewer/reviewer-round1-stop.log`.
- No code changes were made from this non-verdict attempt.

Round 2:

- Fresh blank-context read-only reviewer was launched with separated artifacts:
  - `artifacts/s7/s7-dp-latency-20260609-164753/reviewer/reviewer-round2.stdout.log`
  - `artifacts/s7/s7-dp-latency-20260609-164753/reviewer/reviewer-round2.stderr.log`
  - `artifacts/s7/s7-dp-latency-20260609-164753/reviewer/reviewer-round2.exitcode`
  - `artifacts/s7/s7-dp-latency-20260609-164753/reviewer/reviewer-round2.final.md`
- Exit code: `0`.
- Final reviewer verdict: `ACCEPT`.
- Reviewer findings: none.
- Reviewer notes:
  - the fix is scoped to the PTX/trace metadata boundary;
  - trace mode still aborts explicitly when required metadata is absent;
  - PTX DP fallback uses PTX `incount` plus existing config link/stage
    parameters;
  - no generated/config/latest/calibration/metrics files are modified.

## Final Status

Final status: `READY_FOR_SUPERVISOR_REVIEW`.

The assigned PTX-mode DP decode-latency null-metadata crash is fixed at the
root-cause boundary: PTX mode no longer dereferences enhanced trace instruction
metadata in DP/tensor decode-latency setup, while trace mode keeps explicit
metadata requirements and fails before null dereference if metadata is absent.

The old blocker was not reproduced in the bounded local smoke output before the
run was intentionally stopped. The remaining issue is not a reproduced
null-metadata crash; it is that the local PTX smoke still did not complete to
first-kernel metrics within the bounded wait and should be tracked as a separate
S7 long-running/stalled first-kernel smoke issue if completion is required.

No git commit was made.
