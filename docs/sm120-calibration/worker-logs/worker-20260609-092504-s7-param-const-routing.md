# S7 Parameter Constant Routing Worker Log

## Purpose

Fix or precisely bound the PTX-mode LD/ST queue-routing blocker where a
kernel-parameter load was coalesced as `CONST_ACC_R` but aborted in
`ldst_unit_sm::cycle()` with:

```text
Error: Invalid access type
ldst_unit_sm::cycle() at ldst_unit_sm.cc:948
```

The fix must route PTX `param_space_kernel` constant reads consistently with
their access type and existing PTX constant semantics, preserve remodeled trace
mode and all existing non-constant routes, avoid hard-coded SM120/RTX5060
values, and avoid accepted config, generated bulk-output, calibration `latest`,
or fake metric edits.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Host: `dsp-ubuntu`
- Base HEAD: `5a3b6b937caa637dba7dad1864e850179291211e`
- Base subject: `fix: guard LDST trace metadata in PTX mode`
- Timestamp: `2026-06-09T09:25:04+08:00`
- Run id: `s7-param-const-routing-20260609-092504`
- Artifact root: `artifacts/s7/s7-param-const-routing-20260609-092504/`
- Initial tracked working tree: clean before this task.

## Actions

- Read the supervisor log, overall plan, immediate LD/ST trace-metadata worker
  log, prior scoreboard-reserve worker log, and prior coredump evidence.
- Inspected LD/ST queue routing in
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/ldst_unit_sm.cc`.
- Inspected PTX memory-space classification in
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/abstract_hardware_model.cc`
  and `abstract_hardware_model.h`.
- Confirmed the existing model already treats `param_space_kernel` as constant:
  `memory_space_t::is_const()` returns true for both `const_space` and
  `param_space_kernel`, and `warp_inst_t::generate_mem_accesses()` classifies
  both as `CONST_ACC_R` with constant-cache line size.
- Identified the queue-routing root cause: the remodeled LD/ST router tested
  only literal `const_space` before pushing to `m_access_queue_to_l1c`, even
  though classification and legacy constant-cycle code include
  `param_space_kernel`.
- Changed three LD/ST literal `const_space` checks to use the existing
  `memory_space_t::is_const()` predicate:
  - coalescing stats registration for constant loads;
  - queue routing to `m_access_queue_to_l1c`;
  - constant coalescing-conflict stats in PRT processing.
- Did not suppress the invalid-access abort, bypass queue routing, drop
  accesses, change configs, edit generated outputs, edit calibration `latest`,
  create fake metrics, or run simulator workloads on `dsp5060`.

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

- `artifacts/s7/s7-param-const-routing-20260609-092504/rebuild-gpgpusim.log`
- `artifacts/s7/s7-param-const-routing-20260609-092504/rebuild-gpgpusim.exitcode`,
  value `0`

### Generator And Whitespace Checks

Commands:

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
git diff --check
```

Evidence:

- `artifacts/s7/s7-param-const-routing-20260609-092504/generate-check-only.log`
  reports regenerated SM120 RTX5070 Ti and RTX5060 bootstrap profiles.
- `artifacts/s7/s7-param-const-routing-20260609-092504/generate-check-only.exitcode`,
  value `0`
- `artifacts/s7/s7-param-const-routing-20260609-092504/git-diff-check.log`
- `artifacts/s7/s7-param-const-routing-20260609-092504/git-diff-check.exitcode`,
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
  -N s7-param-const-routing-20260609-092504-smoke-plan \
  -r artifacts/s7/s7-param-const-routing-20260609-092504/sim-smoke-plan \
  -l local \
  -n
```

Evidence:

- `artifacts/s7/s7-param-const-routing-20260609-092504/procman-before-plan.log`
  reported no active jobs.
- `artifacts/s7/s7-param-const-routing-20260609-092504/procman-before-plan.exitcode`,
  value `0`
- `artifacts/s7/s7-param-const-routing-20260609-092504/local-smoke-plan.log`
- `artifacts/s7/s7-param-const-routing-20260609-092504/local-smoke-plan.exitcode`,
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
  -N s7-param-const-routing-20260609-092504-smoke \
  -r artifacts/s7/s7-param-const-routing-20260609-092504/sim-smoke \
  -l local \
  -c 1
```

Evidence:

- `artifacts/s7/s7-param-const-routing-20260609-092504/local-smoke-run.log`,
  launcher exit `0`
- Exactly one ProcMan job was queued: `Job 471`.
- `artifacts/s7/s7-param-const-routing-20260609-092504/procman-after-smoke-final.log`
  reports one completed job and no active jobs.
- Smoke stdout/stderr copies:
  - `artifacts/s7/s7-param-const-routing-20260609-092504/smoke-stdout.o471`
  - `artifacts/s7/s7-param-const-routing-20260609-092504/smoke-stderr.e471`

Smoke result:

- The assigned `Error: Invalid access type` abort did not recur. The blocker
  search found no old invalid-access abort and recorded only the new
  segmentation fault:
  `artifacts/s7/s7-param-const-routing-20260609-092504/smoke-blocker-search.log`.
- The smoke again advanced through PTX parsing, PTXInfo loading, argument
  setup, reconvergence analysis, predecode, and kernel push.
- The routed access advanced to the L1C dispatch path, then hit a distinct
  downstream blocker:

```text
SIGSEGV
std::deque<mem_fetch *>::operator[](4294967295)
ldst_unit_sm::dispatch_to_memory_access_queue_l1Ccache()
ldst_unit_sm::execute_cache_dispatch()
ldst_unit_sm::cycle()
SM::cycle()
```

Bounded new blocker:

- Core metadata:
  `artifacts/s7/s7-param-const-routing-20260609-092504/coredump-info-3664318.log`
- Core dump:
  `artifacts/s7/s7-param-const-routing-20260609-092504/core.3664318`
- Backtrace:
  `artifacts/s7/s7-param-const-routing-20260609-092504/coredump-gdb-bt-3664318.log`
- Focused state:
  `artifacts/s7/s7-param-const-routing-20260609-092504/coredump-gdb-focused-l1c-latency-3664318.log`
- The same PTX kernel-parameter load now reaches
  `ldst_unit_sm::dispatch_to_memory_access_queue_l1Ccache()`:
  - `mem_access_t::m_space = param_space_kernel`
  - `mem_access_t::m_type = CONST_ACC_R`
  - instruction `pc = 9216` (`0x2400`)
  - instruction `op = LOAD_OP`
  - instruction `memory_op = memory_load`
  - instruction `space = param_space_kernel`
  - instruction `warp_id = 4`
  - `m_access_coal_info.m_prts_requesting = {0}`
  - `m_dep_counters_id_requesting` is empty, as expected for PTX mode
  - `m_config->constant_cache_latency_at_sm_structure = 11`
  - `constant_cache_l1_latency_queue.size() = 11`
  - `inst->m_latency_of_mem_operation_at_sm_structure = 0`
  - `inst->m_num_cycles_per_intermediate_stage = {1, 0, 0, 0, 0, 0}`
- Failure mechanism: L1C dispatch uses
  `constant_cache_l1_latency_queue[inst_latency - 1]`. With
  `inst_latency == 0`, the unsigned index underflows to `4294967295`.
- This is downstream of the queue-routing decision. The assigned route no
  longer aborts as invalid; the next blocker is missing/cleared PTX-mode
  constant-memory SM-structure latency before L1C dispatch.
- No real simulator metrics were produced before the new segmentation fault.

## Changed Files

Code:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/ldst_unit_sm.cc`

Documentation:

- `docs/sm120-calibration/worker-logs/worker-20260609-092504-s7-param-const-routing.md`

Ignored/local artifacts:

- `artifacts/s7/s7-param-const-routing-20260609-092504/`

## Reviewer Rounds

- Round 1 fresh blank-context read-only reviewer attempt: terminated after
  stalling during repository inspection.
  - Prompt: `artifacts/s7/s7-param-const-routing-20260609-092504/reviewer-round1.prompt.txt`
  - Stdout: `artifacts/s7/s7-param-const-routing-20260609-092504/reviewer-round1-codex.stdout.txt`
  - Stderr/tool transcript:
    `artifacts/s7/s7-param-const-routing-20260609-092504/reviewer-round1-codex.stderr.txt`
  - Exit code:
    `artifacts/s7/s7-param-const-routing-20260609-092504/reviewer-round1-codex.exitcode`,
    value `124`
- Round 2 fresh blank-context bounded read-only reviewer: `ACCEPT`.
  - Prompt: `artifacts/s7/s7-param-const-routing-20260609-092504/reviewer-round2.prompt.txt`
  - Final message:
    `artifacts/s7/s7-param-const-routing-20260609-092504/reviewer-round2-final-message.txt`
  - Stdout:
    `artifacts/s7/s7-param-const-routing-20260609-092504/reviewer-round2-codex.stdout.txt`
  - Stderr/tool transcript:
    `artifacts/s7/s7-param-const-routing-20260609-092504/reviewer-round2-codex.stderr.txt`
  - Exit code:
    `artifacts/s7/s7-param-const-routing-20260609-092504/reviewer-round2-codex.exitcode`,
    value `0`
  - Reviewer summary: no findings. The reviewer verified that the three
    `is_const()` substitutions match the existing classification where both
    `const_space` and `param_space_kernel` become `CONST_ACC_R`, and that the
    new L1C latency underflow is downstream of the routing decision rather
    than evidence of an incomplete routing fix.

## Final Status

Accepted by the worker's fresh bounded blank-context reviewer. The assigned
PTX-mode LD/ST queue-routing blocker is fixed: `param_space_kernel`
`CONST_ACC_R` accesses route to the constant-read/L1C queue instead of aborting
as an invalid access type. The one local smoke advanced to a separate bounded
PTX-mode constant-memory latency blocker in L1C dispatch: the routed access has
`m_latency_of_mem_operation_at_sm_structure == 0`, which underflows
`constant_cache_l1_latency_queue[inst_latency - 1]`. Real simulator metrics
remain blocked by that downstream latency initialization/lifetime issue.
