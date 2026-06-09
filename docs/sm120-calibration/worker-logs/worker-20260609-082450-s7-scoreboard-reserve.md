# S7 Scoreboard Reserve Worker Log

## Purpose

Resolve or precisely bound the PTX-mode scoreboard reserve warp-id mismatch
abort reached by the previous smoke:

```text
Scoreboard::reserveRegister() at scoreboard.cc:95
Subcore::issue_warp() is issuing sm_warp_id = 12
warp_inst_t carries m_warp_id = 5, m_dynamic_warp_id = 5,
m_is_reissued = true, m_vpreg_need_to_reissue = false
```

The fix must preserve scoreboard correctness, avoid ignoring warp-id mismatch
checks, preserve trace-mode MICRO25/remodeled behavior, avoid hard-coded
SM120/RTX5060 values, and avoid accepted config, calibration `latest`,
generated bulk-output, or fake metric changes.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Host: `dsp-ubuntu`
- Base HEAD: `e02786e96e817169cc4d3bee5602e2f8b6254124`
- Base subject: `fix: restore PTX memory address execution`
- Timestamp: `2026-06-09T08:24:50+08:00`
- Run id: `s7-scoreboard-reserve-20260609-081120`
- Artifact root: `artifacts/s7/s7-scoreboard-reserve-20260609-081120/`
- Working tree note: this task's source diff is limited to
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc`.
  On resume, that file already contained the in-progress worker edit for this
  task; no unrelated tracked source, accepted config, calibration `latest`, or
  generated bulk-output edits were present.

## Actions

- Read the supervisor log, overall plan, immediate memory-access worker log,
  prior scoreboard/PTX worker log, and prior coredump evidence.
- Inspected the failing state in
  `artifacts/s7/s7-mem-accesses-20260609-074137/`, especially the
  scoreboard and warp-mismatch GDB logs.
- Traced remodeled PTX fetch/decode/issue ownership through
  `Subcore::decode()`, `Subcore::get_next_inst()`,
  `IBuffer_Remodeled::issued()/flush()`, and `SM::issue_warp()`.
- Identified the root cause: in PTX mode, remodeled decode stored the
  canonical `ptx_fetch_inst(pc)` pointer in each per-warp IBuffer entry. With
  IBuffer coalescing, multiple warps at the same PC could share the same
  mutable static instruction object. Later decodes overwrote that shared
  instruction's warp fields, so an entry owned by one warp could be issued
  while carrying another warp id. Scoreboard reserve then saw a real ownership
  mismatch instead of a register-scoreboard bug.
- Changed PTX-mode `Subcore::get_next_inst()` to clone the canonical PTX
  timing instruction into a heap-owned `warp_inst_t` for each remodeled IBuffer
  entry. The remodeled IBuffer/pipe path already owns these instruction
  objects and deletes/moves them through `unique_ptr`.
- Added an issue-path invariant
  `assert(pI->warp_id() == sm_warp_id)` so any future decoded-instruction
  ownership mismatch fails at issue before scoreboard state can be corrupted.
- Left trace-mode `trace_shd_warp_t::get_next_trace_inst(pc)` untouched.
- Did not disable scoreboarding, bypass reserve checks, ignore mismatches,
  edit accepted configs, edit calibration `latest`, edit generated bulk
  outputs, create fake metrics, or run simulator workloads on `dsp5060`.

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

- Initial post-fix build:
  `artifacts/s7/s7-scoreboard-reserve-20260609-081120/rebuild-gpgpusim.log`
- Final build after final source cleanup:
  `artifacts/s7/s7-scoreboard-reserve-20260609-081120/rebuild-gpgpusim-final2.log`
- Final build exit:
  `artifacts/s7/s7-scoreboard-reserve-20260609-081120/rebuild-gpgpusim-final2.exitcode`,
  value `0`

### Generator And Whitespace Checks

Commands:

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
git diff --check
```

Evidence:

- `artifacts/s7/s7-scoreboard-reserve-20260609-081120/generate-check-only-final2.log`
- `artifacts/s7/s7-scoreboard-reserve-20260609-081120/generate-check-only-final2.exitcode`,
  value `0`
- `artifacts/s7/s7-scoreboard-reserve-20260609-081120/git-diff-check-final2.log`
- `artifacts/s7/s7-scoreboard-reserve-20260609-081120/git-diff-check-final2.exitcode`,
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
  -N s7-scoreboard-reserve-20260609-081120-smoke-plan-final \
  -r artifacts/s7/s7-scoreboard-reserve-20260609-081120/sim-smoke-plan-final \
  -l local \
  -n
```

Evidence:

- `artifacts/s7/s7-scoreboard-reserve-20260609-081120/procman-before-plan-final.log`
  reports `Nothing Active`.
- `artifacts/s7/s7-scoreboard-reserve-20260609-081120/procman-before-plan-final.exitcode`,
  value `0`
- `artifacts/s7/s7-scoreboard-reserve-20260609-081120/local-smoke-plan-final.log`
- `artifacts/s7/s7-scoreboard-reserve-20260609-081120/local-smoke-plan-final.exitcode`,
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
  -N s7-scoreboard-reserve-20260609-081120-smoke \
  -r artifacts/s7/s7-scoreboard-reserve-20260609-081120/sim-smoke \
  -l local \
  -c 1
```

Evidence:

- `artifacts/s7/s7-scoreboard-reserve-20260609-081120/local-smoke-run.log`,
  launcher exit `0`
- Exactly one ProcMan job was queued: `Job 469`.
- `artifacts/s7/s7-scoreboard-reserve-20260609-081120/procman-after-smoke.log`
  reports one completed job and no active jobs.
- `artifacts/s7/s7-scoreboard-reserve-20260609-081120/smoke-blocker-metrics-search.log`
  contains no old `Scoreboard::reserveRegister()` abort evidence from this
  run and records the new segmentation fault.

Smoke result:

- The assigned scoreboard reserve warp-id mismatch abort did not recur.
- The smoke advanced through PTX parsing, PTXInfo loading, argument setup,
  reconvergence analysis, predecode, and kernel push:

```text
GPGPU-Sim PTX: ... done pre-decoding instructions for '_Z22bpnn_layerforward_CUDAPfS_S_S_ii'.
GPGPU-Sim PTX: pushing kernel '_Z22bpnn_layerforward_CUDAPfS_S_S_ii' to stream 0, gridDim= (1,256,1) blockDim = (16,16,1)
```

- The smoke advanced to a distinct new blocker:

```text
Segmentation fault (core dumped), pid 3373419
traced_instruction::get_control_bits(this=0x0)
PendingRequestTable::get_next_processed_access()
PendingRequestTable::get_access_to_next_stage()
ldst_unit_sm::cycle()
SM::cycle()
```

Bounded new blocker:

- Core metadata:
  `artifacts/s7/s7-scoreboard-reserve-20260609-081120/coredump-info-3373419.log`
- Backtrace:
  `artifacts/s7/s7-scoreboard-reserve-20260609-081120/coredump-gdb-bt-3373419.log`
- Focused state:
  `artifacts/s7/s7-scoreboard-reserve-20260609-081120/coredump-gdb-focused-3373419.log`
- The faulting path is `ldst_unit_sm.cc:1786`, where
  `PendingRequestTable::get_next_processed_access()` unconditionally reads
  `res_acc->get_inst()->get_extra_trace_instruction_info().get_control_bits()`
  after setting the access's instruction pointer. In PTX mode these memory
  instructions do not carry enhanced trace metadata.
- This is a separate PTX-mode memory-pipeline trace-metadata dereference, not
  the assigned scoreboard reserve warp-id mismatch. No real simulator metrics
  were produced before this new fault.

## Changed Files

Code:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc`

Documentation:

- `docs/sm120-calibration/worker-logs/worker-20260609-082450-s7-scoreboard-reserve.md`

Ignored/local artifacts:

- `artifacts/s7/s7-scoreboard-reserve-20260609-081120/`

## Reviewer Rounds

- Round 1 read-only blank-context reviewer attempt: stalled during repository
  inspection and was terminated.
  - Prompt: `reviewer-round1.prompt.txt`
  - Stdout: `reviewer-round1-codex.stdout.txt`
  - Stderr/tool transcript: `reviewer-round1-codex.stderr.txt`
  - Final note: `reviewer-round1-final-message.txt`
  - Exit code: `reviewer-round1-codex.exitcode`, value `124`
- Round 2 fresh blank-context prompt-only reviewer: `ACCEPT`.
  - Prompt: `reviewer-round2.prompt.txt`
  - Final message: `reviewer-round2-final-message.txt`
  - Stdout/verdict: `reviewer-round2-codex.stdout.txt`
  - Stderr transcript: `reviewer-round2-codex.stderr.txt`
  - Exit code: `reviewer-round2-codex.exitcode`, value `0`
  - Reviewer summary: the fix is appropriately scoped because PTX-mode now
    gets per-IBuffer instruction ownership by cloning, trace-mode fetch remains
    unchanged, and the new issue-path assert preserves the warp-id invariant
    instead of weakening scoreboard checks. The reviewer found no blocking
    issues and confirmed validation followed the build/check/setup-only/one
    smoke constraints.

## Final Status

Accepted by the worker's fresh blank-context reviewer. The assigned PTX-mode
scoreboard reserve warp-id mismatch is resolved in the one local smoke. Real
simulator metrics remain blocked by the new PTX-mode memory-pipeline
trace-metadata null dereference in
`PendingRequestTable::get_next_processed_access()` / `ldst_unit_sm.cc:1786`.
