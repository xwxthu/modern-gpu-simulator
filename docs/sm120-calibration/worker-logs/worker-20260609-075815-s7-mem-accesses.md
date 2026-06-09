# S7 Memory Accesses Worker Log

## Purpose

Resolve or precisely bound the PTX-mode memory access assertion reached by the
previous smoke:

```text
abstract_hardware_model.cc:676: void warp_inst_t::generate_mem_accesses(): Assertion `m_per_scalar_thread_valid' failed.
warp_inst_t::generate_mem_accesses()
SM::issue_warp()
Subcore::issue_warp()
Subcore::issue()
Subcore::cycle()
SM::cycle()
```

The fix must preserve normal PTX address generation and memory coalescing,
avoid fake per-thread memory state or global memory-access bypasses, preserve
trace-mode MICRO25/remodeled behavior, avoid hard-coded SM120/RTX5060 values,
and avoid accepted config, calibration `latest`, generated bulk-output, or fake
metric changes.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Host: `dsp-ubuntu`
- Base HEAD: `a9798111ba635e30f18758e90a73a6ca46a38459`
- Base subject: `fix: separate PTX scoreboarding from trace metadata`
- Timestamp: `2026-06-09T07:58:15+08:00`
- Run id: `s7-mem-accesses-20260609-074137`
- Artifact root: `artifacts/s7/s7-mem-accesses-20260609-074137/`
- Initial working tree: inherited source edit in
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/cuda-sim.cc`;
  no accepted configs, calibration `latest`, generated bulk outputs, or
  calibration metrics were dirty or modified.

## Actions

- Read the supervisor log, overall plan, prior scoreboard/PTX worker log, and
  immediate memory-latency worker log.
- Inspected the assigned coredump evidence from the previous smoke, which
  showed `generate_mem_accesses()` asserting because PTX-mode issue reached a
  memory instruction without per-lane memory request addresses.
- Traced PTX timing execution through
  `core_t::execute_warp_inst_t()` and confirmed it calls
  `ptx_thread_info::ptx_exec_inst(warp_inst_t&, unsigned)` for each active
  lane before memory access generation.
- Identified the root cause: the local
  `ptx_thread_info::ptx_exec_inst(warp_inst_t&, unsigned)` implementation in
  `cuda-sim.cc` was an empty stub, so the remodeled PTX performance path did
  not execute PTX opcode handlers and ordinary PTX loads/stores never populated
  `warp_inst_t` lane addresses via `set_addr()`.
- Restored the upstream GPGPU-Sim-style PTX dispatcher in that overload:
  PC synchronization, predicate lane masking, opcode dispatch through
  `opcodes.def`, warp-level `OP_W_DEF` handling, tensorcore gating, callbacks,
  debug/stat updates, PC updates, exit handling, and memory return-state capture
  from `last_eaddr()`, `last_space()`, and `datatype2size()`.
- Left `warp_inst_t::generate_mem_accesses()` and the coalescer intact. The
  fix feeds the existing per-lane address path instead of bypassing or faking
  memory accesses.
- Did not change trace-mode metadata-dependent paths, accepted configs,
  calibration `latest`, generated bulk outputs, or calibration metrics.
- Did not run any simulator workload on `dsp5060`.

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

- `artifacts/s7/s7-mem-accesses-20260609-074137/rebuild-gpgpusim.log`
- `artifacts/s7/s7-mem-accesses-20260609-074137/rebuild-gpgpusim.exitcode`:
  `0`

### Generator And Whitespace Checks

Commands:

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
git diff --check
```

Evidence:

- `artifacts/s7/s7-mem-accesses-20260609-074137/generate-check-only.log`
- `artifacts/s7/s7-mem-accesses-20260609-074137/generate-check-only.exitcode`:
  `0`
- `artifacts/s7/s7-mem-accesses-20260609-074137/git-diff-check.log`
- `artifacts/s7/s7-mem-accesses-20260609-074137/git-diff-check.exitcode`:
  `0`

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
  -N s7-mem-accesses-20260609-074137-smoke-plan \
  -r artifacts/s7/s7-mem-accesses-20260609-074137/sim-smoke-plan \
  -l local \
  -n
```

Evidence:

- `artifacts/s7/s7-mem-accesses-20260609-074137/local-smoke-plan.log`
- `artifacts/s7/s7-mem-accesses-20260609-074137/local-smoke-plan.exitcode`:
  `0`
- The plan log records `Nothing Active` before setup-only planning.

### One Local Smoke

Exactly one local smoke was run after the passing build/checks.

Command:

```bash
export CUDA_INSTALL_PATH=/usr/local/cuda-13.1
export PATH="$CUDA_INSTALL_PATH/bin:$PATH"
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-mem-accesses-20260609-074137-smoke \
  -r artifacts/s7/s7-mem-accesses-20260609-074137/sim-smoke \
  -l local \
  -c 1
```

Evidence:

- `artifacts/s7/s7-mem-accesses-20260609-074137/local-smoke-run.log`,
  launcher exit `0`.
- Exactly one ProcMan job was queued: `Job 468`.
- `artifacts/s7/s7-mem-accesses-20260609-074137/procman-poll-smoke-*.log`
  records the single local job while active, then complete, then inactive.
- `artifacts/s7/s7-mem-accesses-20260609-074137/procman-after-smoke.log`
  reports `Nothing Active`.

Smoke result:

- The assigned `m_per_scalar_thread_valid` assertion did not recur.
- GDB state for the new abort shows the instruction that reached the next
  blocker has:
  - `pc = 9216`
  - `op = LOAD_OP`
  - `memory_op = memory_load`
  - `space = param_space_kernel`
  - `out = {83, ...}`
  - `outcount = 1`
  - `m_per_scalar_thread_valid = true`
  - `m_mem_accesses_created = true`
  - a generated `CONST_ACC_R` access queue entry
- Evidence:
  - `artifacts/s7/s7-mem-accesses-20260609-074137/coredump-gdb-scoreboard-state-3261409.log`
  - `artifacts/s7/s7-mem-accesses-20260609-074137/smoke-blocker-search.log`
  - `artifacts/s7/s7-mem-accesses-20260609-074137/smoke-error-search.log`
- The smoke advanced to a distinct new blocker:

```text
Scoreboard::reserveRegister() at scoreboard.cc:95
Scoreboard::reserveRegisters()
SM::issue_warp()
Subcore::issue_warp()
Subcore::issue()
Subcore::cycle()
SM::cycle()
```

- Boundary details:
  - `Subcore::issue_warp()` is issuing `sm_warp_id = 12`.
  - The `warp_inst_t` being reserved has `m_warp_id = 5`,
    `m_dynamic_warp_id = 5`, and `m_is_reissued = true`.
  - `m_vpreg_need_to_reissue = false`.
  - This points at the next PTX-mode IBuffer/reissue/decoded-instruction
    ownership path rather than memory address generation.
- Evidence:
  - `artifacts/s7/s7-mem-accesses-20260609-074137/coredump-info-3261409.log`
  - `artifacts/s7/s7-mem-accesses-20260609-074137/coredump-gdb-bt-3261409.log`
  - `artifacts/s7/s7-mem-accesses-20260609-074137/coredump-gdb-warp-mismatch-3261409.log`
- No real simulator metrics were produced before the new abort:
  `artifacts/s7/s7-mem-accesses-20260609-074137/smoke-metrics-search.log`
  is empty.

## Changed Files

Code:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/cuda-sim.cc`

Documentation:

- `docs/sm120-calibration/worker-logs/worker-20260609-075815-s7-mem-accesses.md`

Ignored/local artifacts:

- `artifacts/s7/s7-mem-accesses-20260609-074137/`

## Reviewer Rounds

- Round 1 blank-context reviewer attempt: failed before review because the
  local `codex exec` command rejected the unsupported `-a` option.
  - Prompt: `reviewer-round1.prompt.txt`
  - Stdout: `reviewer-round1-codex.stdout.txt`
  - Stderr: `reviewer-round1-codex.stderr.txt`
  - Exit code: `reviewer-round1-codex.exitcode`, value `2`
- Round 2 fresh blank-context reviewer: `ACCEPT`.
  - Runner: `codex exec -C /home/xiewx/accel-0608/modern-gpu-simulator -s read-only --ephemeral`
  - Prompt: `reviewer-round1.prompt.txt`
  - Final message: `reviewer-round2-final-message.txt`
  - Stdout/verdict: `reviewer-round2-codex.stdout.txt`
  - Stderr/tool transcript: `reviewer-round2-codex.stderr.txt`
  - Exit code: `reviewer-round2-codex.exitcode`, value `0`
  - Reviewer summary: restoring `ptx_exec_inst()` fixes the root cause because
    PTX-mode lanes now execute functional opcode handlers and populate
    per-thread addresses through the existing `set_addr()`/coalescing path.
    The reviewer found no hard-coded SM120 values, fake memory state, skipped
    accesses, or trace-mode metadata regression, and confirmed the remaining
    abort is a distinct scoreboard warp-id mismatch after memory access
    generation succeeded.

## Final Status

Accepted by the worker's blank-context reviewer. The assigned PTX-mode
`m_per_scalar_thread_valid` memory-access assertion is resolved for the one
local smoke. Real simulator metrics remain blocked by the new
`Scoreboard::reserveRegister()` abort caused by a mismatch between
`sm_warp_id = 12` and an instruction carrying `m_warp_id = 5` during PTX-mode
reissue/scoreboard reservation, so no calibration outputs were promoted.
