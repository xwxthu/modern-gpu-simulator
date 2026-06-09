# S7 LD/ST Trace Metadata Worker Log

## Purpose

Fix or precisely bound the PTX-mode LD/ST memory-pipeline trace-metadata null
dereference reached by the previous S7 smoke:

```text
traced_instruction::get_control_bits(this=0x0)
PendingRequestTable::get_next_processed_access()
PendingRequestTable::get_access_to_next_stage()
ldst_unit_sm::cycle()
SM::cycle()
```

The fix must separate PTX/performance mode from enhanced trace metadata use,
preserve trace-mode MICRO25/remodeled control-bit behavior, fail explicitly in
trace mode if required metadata is missing, and avoid skipped LD/ST stages,
dropped accesses, fabricated control bits, hard-coded SM120/RTX5060 values,
accepted config edits, calibration `latest` edits, generated bulk-output edits,
or fake metrics.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Host: `dsp-ubuntu`
- Base HEAD: `4f07eeffdfa2406cd669bc7d8a60005ff2ace2ff`
- Base subject: `fix: clone PTX instructions for remodeled ibuffer`
- Timestamp: `2026-06-09T09:05:38+08:00`
- Run id: `s7-ldst-trace-metadata-20260609-085111`
- Artifact root: `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/`
- Initial working tree: clean before this task.

## Actions

- Read the supervisor log, overall plan, immediate scoreboard-reserve worker
  log, and prior S7 memory/scoreboard worker logs.
- Inspected prior artifact evidence under
  `artifacts/s7/s7-scoreboard-reserve-20260609-081120/`.
- Traced the failing path in
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/ldst_unit_sm.cc`.
- Identified the root cause: `PendingRequestTable::get_next_processed_access()`
  unconditionally read write-barrier control bits from
  `warp_inst_t::get_extra_trace_instruction_info()`. In PTX/performance mode,
  memory instructions have no enhanced trace metadata, so the dereference was
  invalid.
- Added a local LD/ST helper that returns trace control bits only when metadata
  exists. In trace mode it aborts with an explicit metadata error; in PTX mode
  it returns `nullptr`.
- Used that helper for PRT access dependency metadata,
  PRT dependency-counter selection, and inter-warp coalescing dependency
  metadata. PTX-mode accesses keep normal PC/warp/PRT metadata and simply have
  no trace write-barrier dependency-counter IDs.
- Guarded `ldst_unit_sm::get_instruction_id()` so PTX-mode pending-write
  tracking uses decoded PTX output registers (`inst->out[idx]`) instead of
  trace destination metadata. Trace mode still requires metadata and uses the
  existing unique trace-instruction behavior.
- Did not skip LD/ST pipeline stages, drop memory accesses, fabricate control
  bits, disable PRT processing, edit accepted configs, edit calibration
  `latest`, edit generated bulk outputs, create fake metrics, or run simulator
  workloads on `dsp5060`.

## Evidence

### Rebuild

Command:

```bash
export CUDA_INSTALL_PATH=/usr/local/cuda-13.1
export PATH="$CUDA_INSTALL_PATH/bin:$PATH"
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
make -C simulator-remodeled/gpu-simulator/gpgpu-sim -j"$(nproc)"
```

Evidence:

- `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/rebuild-gpgpusim.log`
- `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/rebuild-gpgpusim.exitcode`,
  value `0`

### Generator And Whitespace Checks

Commands:

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
git diff --check
```

Evidence:

- `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/generate-check-only.log`
- `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/generate-check-only.exitcode`,
  value `0`
- `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/git-diff-check.log`
- `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/git-diff-check.exitcode`,
  value `0`
- Final post-log whitespace check:
  `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/git-diff-check-final.exitcode`,
  value `0`

### Setup-Only Smoke Planning

Command:

```bash
export CUDA_INSTALL_PATH=/usr/local/cuda-13.1
export PATH="$CUDA_INSTALL_PATH/bin:$PATH"
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment
python3 simulator-remodeled/util/job_launching/procman.py -p
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-ldst-trace-metadata-20260609-085111-smoke-plan \
  -r artifacts/s7/s7-ldst-trace-metadata-20260609-085111/sim-smoke-plan \
  -l local \
  -n
```

Evidence:

- `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/procman-before-plan.log`
  reports `Nothing Active`.
- `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/procman-before-plan.exitcode`,
  value `0`
- `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/local-smoke-plan.log`
- `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/local-smoke-plan.exitcode`,
  value `0`

### One Local Smoke

Exactly one local smoke was run after the passing build/checks. No second
simulator smoke was run.

Command:

```bash
export CUDA_INSTALL_PATH=/usr/local/cuda-13.1
export PATH="$CUDA_INSTALL_PATH/bin:$PATH"
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-ldst-trace-metadata-20260609-085111-smoke \
  -r artifacts/s7/s7-ldst-trace-metadata-20260609-085111/sim-smoke \
  -l local \
  -c 1
```

Evidence:

- `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/local-smoke-run.log`,
  launcher exit `0`
- Exactly one ProcMan job was queued: `Job 470`.
- `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/procman-after-smoke.log`
  reports `Nothing Active`.

Smoke result:

- The assigned null dereference did not recur. The old-blocker search found no
  `traced_instruction::get_control_bits`,
  `PendingRequestTable::get_next_processed_access`, trace metadata abort, or
  segmentation fault evidence in the smoke stdout/stderr:
  `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/smoke-old-blocker-search.log`
  is empty and its exit code is `1`, the expected `rg` no-match status.
- The smoke advanced through PTX parsing, PTXInfo loading, argument setup,
  reconvergence analysis, predecode, kernel push, and shader binding.
- The smoke advanced to a distinct new blocker:

```text
Error: Invalid access type
ldst_unit_sm::cycle() at ldst_unit_sm.cc:948
SM::cycle()
simt_core_cluster::core_cycle()
```

Bounded new blocker:

- Core metadata:
  `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/coredump-info-3516712.log`
- Core dump:
  `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/core.3516712`
- Backtrace:
  `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/coredump-gdb-bt-3516712.log`
- Focused state:
  `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/coredump-gdb-invalid-access-3516712.log`
- The failing access is a PTX-mode parameter-memory load:
  - `mem_access_t::m_space = param_space_kernel`
  - `mem_access_t::m_type = CONST_ACC_R`
  - `mem_access_t::m_addr = 0`
  - `mem_access_t::m_req_size = 64`
  - `mem_access_t::m_is_last_access = true`
  - instruction `pc = 9216` (`0x2400`)
  - instruction `op = LOAD_OP`
  - instruction `memory_op = memory_load`
  - instruction `space = param_space_kernel`
  - instruction `warp_id = 4`
  - `m_extra_trace_instruction_info` is empty as expected for PTX mode
  - access coalescing metadata has `m_prts_requesting = {0}` and no trace
    dependency counter IDs
- This is a separate LD/ST queue-routing blocker: the queue-routing logic at
  `ldst_unit_sm.cc:905-915` routes `const_space` to L1C but does not route
  `param_space_kernel`, even though PTX memory coalescing classifies it as
  `CONST_ACC_R`.
- No real simulator metrics were produced before the new abort:
  `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/smoke-metrics-search.log`
  is empty and its exit code is `1`.

## Changed Files

Code:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/ldst_unit_sm.cc`

Documentation:

- `docs/sm120-calibration/worker-logs/worker-20260609-090538-s7-ldst-trace-metadata.md`

Ignored/local artifacts:

- `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/`

## Reviewer Rounds

- Round 1 fresh blank-context read-only reviewer: `ACCEPT`.
  - Prompt/output: `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/reviewer-round1-codex.stdout.txt`
  - Stderr/tool transcript: `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/reviewer-round1-codex.stderr.txt`
  - Exit code: `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/reviewer-round1-codex.exitcode`,
    value `0`
  - Reviewer summary: the change cleanly bounds LD/ST enhanced-trace metadata
    access, uses one guard for control-bit access, aborts explicitly in trace
    mode when metadata is missing, preserves PTX mode by returning no
    write-barrier dependency metadata, and the smoke advanced to a separate
    bounded `param_space_kernel` routing abort. The reviewer found no findings.
- Supervisor independent review: `CHANGES_NEEDED`.
  - Finding 1: `get_ldst_trace_control_bits()` was metadata-presence gated
    rather than mode gated. PTX/performance mode could still dereference
    enhanced trace metadata if metadata happened to be present. Required
    behavior: key on `config->is_trace_mode`; PTX mode returns `nullptr`
    regardless of metadata presence, while trace mode requires metadata and
    returns control bits or aborts explicitly.
  - Finding 2: `ldst_unit_sm::get_instruction_id()` had the same issue. PTX
    mode must use decoded `inst->out[idx]` regardless of metadata presence;
    trace mode must preserve trace destination metadata behavior and abort
    explicitly if metadata is missing.
- Rework action:
  - Changed `get_ldst_trace_control_bits()` to return `nullptr` before any
    metadata access when `!config->is_trace_mode`.
  - Changed `get_instruction_id()` to return `inst->out[idx]` before any
    metadata access when `!m_config->is_trace_mode`.
  - Trace mode still emits explicit metadata-required errors before any
    missing-metadata dereference.
- Rework validation:
  - Rebuild:
    `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/rework-20260609-091300/rebuild-gpgpusim.exitcode`,
    value `0`
  - Generator check:
    `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/rework-20260609-091300/generate-check-only.exitcode`,
    value `0`
  - Whitespace check:
    `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/rework-20260609-091300/git-diff-check.exitcode`,
    value `0`
  - No second local smoke was run. The rework only changes PTX mode to ignore
    metadata earlier when metadata happens to be present; it does not alter the
    observed PTX no-metadata smoke path or the previously bounded
    `param_space_kernel` / `CONST_ACC_R` next blocker.
- Round 2 fresh blank-context read-only reviewer after supervisor rework:
  `ACCEPT`.
  - Prompt/output:
    `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/rework-20260609-091300/reviewer-round2-codex.stdout.txt`
  - Stderr/tool transcript:
    `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/rework-20260609-091300/reviewer-round2-codex.stderr.txt`
  - Exit code:
    `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/rework-20260609-091300/reviewer-round2-codex.exitcode`,
    value `0`
  - Reviewer summary: no findings. The reviewer verified that PTX/performance
    mode returns before metadata access in both supervisor-flagged functions,
    trace mode keeps explicit metadata requirements, no forbidden files were
    edited, and rework validation exit codes were all `0`.

## Final Status

The assigned PTX-mode LD/ST trace-metadata null dereference is resolved and the
supervisor mode-gating findings were addressed. Validation passed through
build, config generation check, whitespace check, setup-only planning, exactly
one local smoke, and rework rebuild/checks. The previously bounded next blocker
remains a separate PTX-mode LD/ST routing issue for `param_space_kernel`
`CONST_ACC_R` accesses in `ldst_unit_sm::cycle()`.
