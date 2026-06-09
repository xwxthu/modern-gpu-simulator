# S7 PTX Stats Concurrency Worker Log

## Purpose

Fix or precisely bound the current S7 PTX-mode smoke blocker:

```text
SIGSEGV in ptx_file_line_stats_add_exec_count()
std::unordered_map<ptx_file_line, ptx_file_line_stats,...>::operator[](...)
```

Prior evidence from
`artifacts/s7/s7-invalid-decode-20260609-140131/coredump-gdb-focused-new-blocker-808003.log`
showed concurrent OpenMP execution reaching
`ptx_file_line_stats_tracker` insertion from
`ptx_thread_info::ptx_exec_inst()` and `SM::func_exec_inst()`.

The target was a narrow root-cause fix that keeps PTX source-line statistics
enabled and preserves trace-mode/remodeled behavior outside the stats data
structure.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Requested base HEAD:
  `77288bca89538826abcdb41b07a833efacda82f9`
- Actual `git rev-parse HEAD` at task start:
  `77288bca89538826abcdb41b07a833efacda82f9`
- Timestamp: `2026-06-09T14:41:09+08:00`
- Artifact root:
  `artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/`
- Initial tracked working tree: clean except ignored artifacts/build outputs.

## Actions

- Read the S7 supervisor context:
  - `docs/sm120-calibration/supervisor-log.md`
  - `docs/sm120-calibration/overall-plan.md`
  - `docs/sm120-calibration/worker-logs/worker-20260609-141104-s7-invalid-decode.md`
- Inspected focused evidence from the prior run:
  - `artifacts/s7/s7-invalid-decode-20260609-140131/coredump-gdb-focused-new-blocker-808003.log`
  - `artifacts/s7/s7-invalid-decode-20260609-140131/smoke-result-search-final.log`
- Located all PTX file-line stats paths:
  - Global tracker definition:
    `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/ptx-stats.cc`
  - Write/export path:
    `ptx_stats::ptx_file_line_stats_write_file()`
  - Direct global-map update paths:
    `ptx_file_line_stats_add_exec_count()`,
    `ptx_file_line_stats_add_latency()`,
    `ptx_file_line_stats_add_dram_traffic()`,
    `ptx_file_line_stats_add_smem_bank_conflict()`,
    `ptx_file_line_stats_add_uncoalesced_gmem()`,
    `ptx_inflight_memory_insn_tracker::attribute_exposed_latency()`, and
    `ptx_file_line_stats_add_warp_divergence()`
  - Inflight-memory bookkeeping paths:
    `ptx_file_line_stats_create_exposed_latency_tracker()`,
    `ptx_file_line_stats_destroy_exposed_latency_tracker()`,
    `ptx_file_line_stats_add_inflight_memory_insn()`,
    `ptx_file_line_stats_sub_inflight_memory_insn()`, and
    `ptx_file_line_stats_commit_exposed_latency()`
  - Callers:
    `ptx_thread_info::ptx_exec_inst()`,
    `warp_inst_t::completed()`, memory coalescing/stat paths in
    `abstract_hardware_model.cc`, DRAM traffic accounting in
    `mem_latency_stat.cc`, and warp-divergence accounting in
    `simt_stack::update()`.
- Confirmed concurrent execution context:
  `gpgpu_sim::cycle()` advances clusters with
  `#pragma omp parallel for schedule(runtime)` and the prior crashing stack was
  inside `_ZN9gpgpu_sim5cycleEv._omp_fn.1`.
- Implemented a narrow root-cause fix:
  - Added a static `std::mutex` guarding the global
    `ptx_file_line_stats_tracker`.
  - Replaced every direct `ptx_file_line_stats_tracker[...]` update with a
    locked update.
  - Guarded final tracker iteration in
    `ptx_file_line_stats_write_file()`.
  - Kept `-enable_ptx_file_line_stats 1` behavior unchanged; no stats call was
    disabled or skipped.
- Did not:
  - disable PTX source-line stats
  - skip `ptx_file_line_stats_add_exec_count()`
  - change trace-mode fetch/decode/remodeled paths
  - edit accepted/generated configs, `latest`, calibration results, or metrics
  - run any simulator workload on `dsp5060`

## Root Cause

`ptx_file_line_stats_tracker` is a process-global `tr1_hash_map`, which is
`std::unordered_map` in this build. Multiple OpenMP worker threads can execute
PTX instructions concurrently across clusters/SMs and call
`ptx_file_line_stats_add_exec_count()` from `ptx_thread_info::ptx_exec_inst()`.
The previous implementation used `operator[]` directly on the global map for
exec counts and every other source-line stats bucket update.

`std::unordered_map` does not support concurrent insertion or mutation without
external synchronization. The prior focused core shows the crash in
`std::_Hashtable::_M_insert_bucket_begin()` while inserting a
`ptx_file_line_stats_tracker` entry, matching unsynchronized concurrent map
mutation rather than an instruction decode or PTX metadata failure.

The fix serializes every global tracker mutation and the final tracker
iteration with one mutex. This preserves existing statistics semantics:
updates still happen at all previous call sites and aggregate into the same
global per-source-line buckets.

## Changed Files

Code:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/ptx-stats.cc`

Documentation:

- `docs/sm120-calibration/worker-logs/worker-20260609-144109-s7-ptx-stats-concurrency.md`

Ignored/local artifacts:

- `artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/`

## Validation Commands And Results

Pre-build whitespace check passed:

```bash
git diff --check
```

- Evidence:
  `artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/git-diff-check-prebuild.log`
- Exit code:
  `artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/git-diff-check-prebuild.exitcode`,
  value `0`

SM120 generated-config reproducibility check passed:

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
```

- Evidence:
  `artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/generate-check-only.log`
- Exit code:
  `artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/generate-check-only.exitcode`,
  value `0`

Release GPGPU-Sim rebuild passed with local CUDA 13.1:

```bash
export CUDA_INSTALL_PATH=${CUDA_INSTALL_PATH:-/usr/local/cuda-13.1}
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment
make -C simulator-remodeled/gpu-simulator/gpgpu-sim -j"$(nproc)"
```

- Evidence:
  `artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/rebuild-gpgpusim.log`
- Exit code:
  `artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/rebuild-gpgpusim.exitcode`,
  value `0`

Setup-only smoke plan passed:

```bash
export CUDA_INSTALL_PATH=${CUDA_INSTALL_PATH:-/usr/local/cuda-13.1}
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-ptx-stats-concurrency-20260609-144109-smoke-plan \
  -r artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/sim-smoke-plan \
  -l local \
  -n
```

- Evidence:
  `artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/local-smoke-plan.log`
- Exit code:
  `artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/local-smoke-plan.exitcode`,
  value `0`

One post-fix local PTX smoke was launched and allowed to run to its next
blocker:

```bash
export CUDA_INSTALL_PATH=${CUDA_INSTALL_PATH:-/usr/local/cuda-13.1}
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-ptx-stats-concurrency-20260609-144109-smoke \
  -r artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/sim-smoke \
  -l local \
  -c 4
```

- Launch log:
  `artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/local-smoke-run.log`
- `run_simulations.py` exit code:
  `artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/local-smoke-run.exitcode`,
  value `0`
- Job id: `478`
- Final procman state:
  `artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/procman-status-final.log`,
  `Nothing Active`
- Result search:
  `artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/smoke-result-search-final.log`

The assigned old blocker disappeared:

- no `Segmentation fault`
- no `_Hashtable::_M_insert_bucket_begin` crash
- no `std::unordered_map<ptx_file_line,...>::operator[]` crash
- no crash in `ptx_file_line_stats_add_exec_count()`
- no `Subcore::single_decode(): Assertion 'pI->valid()' failed`
- no `bar_id != -1` regression
- no `pc == inst.pc` regression

The smoke advanced to a new downstream blocker:

```text
backprop-rodinia-2.0-ft: ../shader.h:221:
void shd_warp_t::pop_function_call(active_mask_t):
Assertion `!m_function_call_stack.empty()' failed.
```

Focused evidence:

- `artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/coredump-info-1032513.log`
- `artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/core.1032513`
- `artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/coredump-gdb-focused-new-blocker-1032513.log`

GDB shows the new abort path:

```text
__assert_fail(... "!m_function_call_stack.empty()" ...)
shd_warp_t::pop_function_call(active_mask_t)
shd_warp_t::set_done_exit()
SM::check_if_warp_has_finished_executing_and_can_be_reclaim(...)
Subcore::fetch(...)
SM::cycle()
simt_core_cluster::core_cycle()
gpgpu_sim::cycle() [OpenMP worker]
```

Other threads in the abort core are observed waiting on
`ptx_file_line_stats_tracker_mutex`, which is expected after one OpenMP worker
aborts while peers are still executing. The fatal thread and assertion are not
inside `ptx_file_line_stats_tracker`, `_Hashtable`, or
`ptx_file_line_stats_add_exec_count()`.

No calibration or correlation metrics were produced, and no config was
promoted.

Post-review final checks:

- `git diff --check` passed:
  `artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/git-diff-check-after-review.exitcode`
  value `0`
- Protected config/latest scoped status was empty:
  `artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/protected-config-status-after-review.log`
- Final tracked status contained only:
  - modified code file
    `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/ptx-stats.cc`
  - new worker log
    `docs/sm120-calibration/worker-logs/worker-20260609-144109-s7-ptx-stats-concurrency.md`

## Reviewer Rounds

- Round 1 fresh blank-context read-only reviewer:
  - Prompt:
    `artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/reviewer/reviewer-round1-prompt.txt`
  - First CLI attempt did not start a model because `codex exec` does not
    accept `--ask-for-approval`; evidence kept in
    `artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/reviewer/reviewer-round1.stderr.txt`.
  - Rerun command used `codex exec -s read-only --ephemeral`.
  - Output:
    `artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/reviewer/reviewer-round1.last.txt`
  - Verdict: `ACCEPT`
  - Findings: no blocking findings.
  - Reviewer confirmed:
    - all direct tracker mutation/iteration paths are guarded by the new mutex
    - this is a root-cause concurrency repair, not a stats skip
    - `ptx_thread_info::ptx_exec_inst()` still calls
      `ptx_file_line_stats_add_exec_count(pI)` outside functional simulation
    - the old `_Hashtable`/`unordered_map` stats SIGSEGV disappeared
    - the new blocker is the `shd_warp_t::pop_function_call()` empty-stack
      assertion
    - trace-mode/remodeled behavior outside stats is unaffected by the diff
    - no protected configs, generated configs, `latest`, calibration results,
      or metrics were promoted
  - Reviewer residual risk: the global mutex is coarse and may add contention
    when PTX line stats are enabled, but it is materially safer than a larger
    per-thread aggregation rewrite for this narrow S7 smoke bring-up.

## Final Status

Accepted by reviewer. The code builds and the local PTX smoke no longer hits
the assigned concurrent `ptx_file_line_stats_tracker` insertion SIGSEGV. The
smoke continues to a new PTX/remodeled function-call-stack assertion in
`shd_warp_t::pop_function_call()`. S7 smoke bring-up remains in progress; no
calibration/correlation result is claimed.
