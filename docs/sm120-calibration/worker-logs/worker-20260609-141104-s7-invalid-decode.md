# S7 Invalid Decode Worker Log

## Purpose

Fix or precisely bound the remodeled PTX decode blocker reached by the previous
S7 smoke:

```text
subcore.cc:916: void Subcore::single_decode(...):
Assertion `pI->valid()' failed.
```

Prior focused evidence from
`artifacts/s7/s7-barrier-metadata-20260609-131926/` showed
`Subcore::single_decode()` received a non-null but default/invalid
`warp_inst_t`:

```text
pc = 18446744073709551615
m_decoded = false
op = NO_OP
isize = 0
```

The target was a narrow root-cause fix that prevents invalid/default PTX
instructions from becoming decode candidates while preserving the existing
`pI->valid()` assertion and trace-mode behavior.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base HEAD requested by supervisor:
  `6795932f921a003c87a8adc243bfae514245e7cc`
- Actual `git rev-parse HEAD` at task start:
  `6795932f921a003c87a8adc243bfae514245e7cc`
- Base subject: `fix: propagate PTX barrier metadata`
- Timestamp: `2026-06-09T14:11:04+08:00`
- Artifact root: `artifacts/s7/s7-invalid-decode-20260609-140131/`
- Initial tracked working tree: clean; only ignored artifacts/build outputs were
  present.

## Actions

- Read:
  - `docs/sm120-calibration/supervisor-log.md`
  - `docs/sm120-calibration/overall-plan.md`
  - `docs/sm120-calibration/worker-logs/worker-20260609-131926-s7-barrier-metadata.md`
- Inspected the remodeled PTX fetch/decode path:
  - `IBuffer_Remodeled::get_next_pc_to_fetch_request()`
  - `Subcore::fetch()`, `Subcore::decode()`, `Subcore::single_decode()`,
    and `Subcore::get_next_inst()`
  - `gpgpu_context::ptx_fetch_inst()` and `pc_to_instruction()`
  - PTX PDOM/predecode setup in `function_info::do_pdom()`
  - SIMT-stack PC update/terminal `-1` PC handling
- Confirmed the crash object was an undecoded/default timing instruction cloned
  from the PTX fetch path before `single_decode()` enforced its invariant.
- Implemented a narrow PTX-mode remodeled fix:
  - Run the existing PTX `do_pdom()` setup once during remodeled PTX
    `SM::init_warps()` before timing fetch/decode can clone instructions. This
    preserves existing reconvergence analysis and predecodes all canonical PTX
    instructions for the function.
  - Change `gpgpu_context::pc_to_instruction()` to accept `address_type` so
    64-bit invalid/null PCs such as `(address_type)-1` cannot be narrowed to an
    in-range `unsigned` instruction-table index.
  - In remodeled PTX `Subcore::get_next_inst()`, refuse to clone a PTX fetch
    result unless it is non-null, decoded, has a matching PC, and has nonzero
    instruction size.
  - If a PTX fetch response decodes to no valid instruction, roll back the
    specific IBuffer reservation instead of marking it valid.
- Did not:
  - remove or weaken `pI->valid()`
  - insert unconditional `NO_OP` instructions
  - skip valid PTX instructions
  - modify trace-mode decode/fetch behavior
  - edit accepted/generated configs, `latest`, calibration results, or metrics
  - run full simulator workloads on `dsp5060`

## Root Cause

The remodeled PTX IBuffer path reserves an entry by PC, then clones the canonical
PTX instruction returned by `gpgpu_context::ptx_fetch_inst(pc)`. The prior code
assumed that a non-null PTX lookup was already a valid timing instruction. That
assumption is false in PTX performance mode until the function's PDOM/predecode
setup has run: parsed `ptx_instruction` objects can still carry the base
`inst_t` defaults (`m_decoded=false`, `pc=-1`, `op=NO_OP`, `isize=0`).

The fetch API also narrowed `address_type` to `unsigned` inside
`pc_to_instruction()`, so terminal or otherwise invalid 64-bit PCs were not
defensively excluded by type. A non-null but invalid/default instruction could
therefore be cloned into the remodeled IBuffer and then reach
`Subcore::single_decode()`, where the correct invariant assertion fired.

The fix makes remodeled PTX timing setup use the existing function-level
PDOM/predecode path before fetch/decode, and makes remodeled decode validate the
canonical PTX instruction before cloning it into an IBuffer-owned dynamic
instruction.

## Changed Files

Code:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/libcuda/gpgpu_context.h`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/ptx_ir.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/sm.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc`

Documentation:

- `docs/sm120-calibration/worker-logs/worker-20260609-141104-s7-invalid-decode.md`

Ignored/local artifacts:

- `artifacts/s7/s7-invalid-decode-20260609-140131/`

## Validation Commands And Results

`git diff --check` passed before build and after smoke:

- `artifacts/s7/s7-invalid-decode-20260609-140131/git-diff-check-prebuild.exitcode`
  value `0`
- `artifacts/s7/s7-invalid-decode-20260609-140131/git-diff-check-final.exitcode`
  value `0`

SM120 generated-config reproducibility check passed:

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
```

- Evidence:
  `artifacts/s7/s7-invalid-decode-20260609-140131/generate-check-only.log`
- Exit code:
  `artifacts/s7/s7-invalid-decode-20260609-140131/generate-check-only.exitcode`,
  value `0`

Release GPGPU-Sim rebuild passed with local CUDA 13.1:

```bash
export CUDA_INSTALL_PATH=${CUDA_INSTALL_PATH:-/usr/local/cuda-13.1}
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment
make -C simulator-remodeled/gpu-simulator/gpgpu-sim -j"$(nproc)"
```

- Evidence:
  `artifacts/s7/s7-invalid-decode-20260609-140131/rebuild-gpgpusim.log`
- Exit code:
  `artifacts/s7/s7-invalid-decode-20260609-140131/rebuild-gpgpusim.exitcode`,
  value `0`

Setup-only smoke plan:

- First attempt failed with exit code `1` because the shell had not sourced the
  simulator environment:
  `ERROR - Please run setup_environment before running this script`
- Rerun with the same environment setup used for the build passed:

```bash
export CUDA_INSTALL_PATH=${CUDA_INSTALL_PATH:-/usr/local/cuda-13.1}
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-invalid-decode-20260609-140131-smoke-plan \
  -r artifacts/s7/s7-invalid-decode-20260609-140131/sim-smoke-plan \
  -l local \
  -n
```

- Evidence:
  `artifacts/s7/s7-invalid-decode-20260609-140131/local-smoke-plan-rerun.log`
- Exit code:
  `artifacts/s7/s7-invalid-decode-20260609-140131/local-smoke-plan-rerun.exitcode`,
  value `0`

One post-fix local PTX smoke was launched and allowed to run to its next crash:

```bash
export CUDA_INSTALL_PATH=${CUDA_INSTALL_PATH:-/usr/local/cuda-13.1}
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N s7-invalid-decode-20260609-140131-smoke \
  -r artifacts/s7/s7-invalid-decode-20260609-140131/sim-smoke \
  -l local \
  -c 4
```

- Launch log:
  `artifacts/s7/s7-invalid-decode-20260609-140131/local-smoke-run.log`
- Job id: `477`
- Final procman state:
  `artifacts/s7/s7-invalid-decode-20260609-140131/procman-status-210s.log`
- Result search:
  `artifacts/s7/s7-invalid-decode-20260609-140131/smoke-result-search-final.log`

The assigned old blocker disappeared:

- no `Subcore::single_decode(): Assertion 'pI->valid()' failed`
- no `bar_id != (unsigned)-1` regression
- no `pc == inst.pc` regression
- smoke progressed past PDOM/predecode and shader binding

The smoke advanced to a new downstream blocker:

```text
Segmentation fault (core dumped)
```

Focused evidence:

- `artifacts/s7/s7-invalid-decode-20260609-140131/coredump-info-808003.log`
- `artifacts/s7/s7-invalid-decode-20260609-140131/core.808003`
- `artifacts/s7/s7-invalid-decode-20260609-140131/coredump-gdb-focused-new-blocker-808003.log`

GDB shows the new crash occurs in concurrent PTX file-line stats insertion:

```text
std::_Hashtable<ptx_file_line,...>::_M_insert_bucket_begin(...)
std::unordered_map<ptx_file_line, ptx_file_line_stats,...>::operator[](...)
ptx_file_line_stats_add_exec_count(pInsn=...)
ptx_thread_info::ptx_exec_inst(...)
core_t::execute_warp_inst_t(...)
SM::func_exec_inst(...)
```

This is a downstream PTX stats data-structure/concurrency blocker, not the
assigned invalid/default decode candidate.

No calibration or correlation metrics were produced, and no config was
promoted.

## Reviewer Rounds

- Round 1 fresh blank-context read-only reviewer:
  - Prompt:
    `artifacts/s7/s7-invalid-decode-20260609-140131/reviewer/reviewer-round1-prompt.txt`
  - Output:
    `artifacts/s7/s7-invalid-decode-20260609-140131/reviewer/reviewer-round1.last.txt`
  - Verdict: `ACCEPT`
  - Findings: no blocking findings.
  - Reviewer confirmed the fix preserves `pI->valid()`, rejects invalid PTX
    fetch results before cloning into the remodeled IBuffer, rolls back invalid
    PTX reservations, leaves trace-mode decode source unaffected by inspection,
    does not promote configs/metrics/latest, and documents the downstream PTX
    stats segfault as the new precise blocker.
  - Reviewer noted optional future cleanup: revisit whether the extra
    `SM::init_warps()` PDOM call is redundant. It was not a rejection because
    the call is PTX-mode gated and uses existing PDOM/predecode semantics.

## Final Status

Accepted by reviewer. The code fix builds and the local PTX smoke no longer
hits the assigned invalid/default decode assertion. The old barrier metadata
blocker and `pc == inst.pc` assertion did not regress. The current precise
blocker is now a segmentation fault in concurrent
`ptx_file_line_stats_tracker` insertion from
`ptx_file_line_stats_add_exec_count()` during PTX execution. No
calibration/correlation execution was completed and no metrics/configs were
promoted. No commit was made.
