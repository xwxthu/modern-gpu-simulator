# S7 Cycle-Cost Diagnostics Worker Log

## Purpose

Add default-off, low-volume host-time diagnostics around
`gpgpu_sim::cycle()` sections so the next bounded `candidate_0002`
diagnostic can measure host-time distribution in the pre-admission
TB-latency window.

This was instrumentation only. It was not a simulator metrics run, not an S6
correlation run, and not a calibration promotion.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base checkpoint: `3611fc2` (`docs: analyze SM120 pre-admission latency path`)
- Timestamp: `2026-06-12T22:21:08+08:00`
- Host: `dsp-ubuntu`
- ProcMan jobs launched by this worker: none

Pre-existing tracked modification observed and not edited:

- `docs/sm120-calibration/supervisor-log.md`

## Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-220119-s7-candidate0002-preadmission-codepath.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-214628-s7-candidate0002-deeper-dispatch-diagnostic.md`
- Existing dispatch/progress diagnostics in:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-sim.cc`
  and
  `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-sim.h`

## Code Paths Changed

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-sim.cc`
  - Added local `std::chrono::steady_clock` timing helpers.
  - Added `GPGPUSIM_CYCLE_COST_DEBUG` gate with:
    - `GPGPUSIM_CYCLE_COST_INTERVAL` default `200`,
    - `GPGPUSIM_CYCLE_COST_LIMIT` default `32`, where `0` means unlimited.
  - Added compact `GPGPUSIM-CYCLE-COST` output with simulated cycle,
    clock mask, running-kernel count, TB-latency-pending count, CTA/SM state,
    running-kernel launch/TB-latency details, and section costs in
    microseconds.
  - Timed named coarse sections in `gpgpu_sim::cycle()`:
    `clock_domain`, `interconnect_memory`, `cluster_core`,
    `stats_bookkeeping`, `issue_block2core`,
    `decrement_kernel_latency`, and `diagnostic_emission`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-sim.h`
  - Added private helper declarations and cached env/interval/limit state.

## Design Notes

- Disabled behavior remains semantic no-op. The default-off path performs the
  same style of cached env check used by existing diagnostics and does not
  build strings, scan kernels/clusters, or read timing clocks unless an
  emission is due.
- Output is generated only after the existing `maybe_print_kernel_progress_debug()`
  call, so `diagnostic_emission` includes existing progress-debug cost when it
  is enabled.
- Kernel and cluster summaries are computed only after the interval/limit gate
  decides a line will be printed.
- The instrumentation uses standard C++ `std::chrono::steady_clock`.
- No simulator scheduling, admission, latency, CTA, cache, memory, or stats
  semantics were changed.

## Validation

Commands run:

```bash
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
make -C simulator-remodeled/gpu-simulator/gpgpu-sim -j"$(nproc)"
git diff --check
python3 simulator-remodeled/util/job_launching/procman.py -p
test ! -e simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml
git status --short -- \
  simulator-remodeled/gpu-simulator/gpgpu-sim/configs \
  simulator-remodeled/gpu-simulator/configs \
  simulator-remodeled/util/job_launching/configs \
  simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/calibration-results
```

Results:

- Final release GPGPU-Sim rebuild passed, exit code `0`.
- `gpu-sim.cc` compiled successfully with the new diagnostics after reviewer
  fixes. An intermediate rebuild exposed two new diagnostic `printf` format
  warnings; these were fixed and the final rebuild did not repeat them. The
  build still reports existing warning classes such as RapidJSON deprecated
  iterator, remodeled hidden-virtual warnings, and the pre-existing
  shader maybe-uninitialized warning.
- `git diff --check` passed.
- ProcMan final state: `Nothing Active`.
- Temporary S7 bounded-sweep alias:
  `simulator-remodeled/util/job_launching/configs/define-s7-bounded-sweep-temp.yml`
  is absent.
- Protected generated/tested/job-alias/calibration-result paths checked above
  had no tracked changes.
- No ProcMan diagnostic run was launched.

## Changed Files

- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-sim.cc`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-sim.h`
- `docs/sm120-calibration/worker-logs/worker-20260612-222108-s7-cycle-cost-diagnostics.md`

Pre-existing tracked modification still present and not edited:

- `docs/sm120-calibration/supervisor-log.md`

## Reviewer Rounds

- Round 1: Hooke (`019ebc37-9127-7aa2-ae48-15a85a7cdfcc`) returned
  `CHANGES_NEEDED`.
  - Finding: emitted `cycle=` used the post-increment simulated cycle.
  - Finding: sampled cycles used heap allocation.
  - Finding: samples could arm before clock-mask gating and then allocate on
    non-CORE cycles that would not emit.
  - Fixes: saved and emitted the pre-increment simulated cycle, removed heap
    allocation, gated emission to CORE cycles after `next_clock_domain()`, and
    used stack-local `std::optional` so non-due cycles do not construct the
    timing snapshot.
- Round 2: Noether (`019ebc3c-0169-7530-8fa8-598089aa272b`) returned
  `CHANGES_NEEDED`.
  - Finding: the `clock_domain` timing bucket started after
    `next_clock_domain()`.
  - Fix: moved candidate timing start before `next_clock_domain()` so the
    bucket includes clock-domain selection.
- Round 3: Lovelace (`019ebc40-c7a9-78e1-93dc-76f88304c98c`) returned
  `CHANGES_NEEDED`.
  - Finding: sampled cycle-cost emission still used `std::ostringstream`,
    which can allocate on the sampled path.
  - Fix: replaced the cycle-cost emission streams with direct `printf`
    emission. The first rebuild after this change exposed two new format
    warnings for `m_total_cta_launched` and `kernel->num_blocks()`; those
    specifiers were fixed and the release rebuild was rerun successfully.
- Round 4: Laplace (`019ebc49-fbca-79b1-8d5d-9e76448e33b1`) returned
  `ACCEPT`.
  - Key checks: disabled path caches the env check and avoids timers, string
    work, kernel/cluster scans, and sampled-state allocation when disabled.
    Sampled path uses stack-local `std::optional`, `std::chrono::steady_clock`,
    direct `printf`, bounded interval/limit controls, and safe format
    specifiers.
  - Key checks: timing starts before `next_clock_domain()`, emission is gated
    to CORE cycles after the clock mask, and emitted `cycle` is the saved
    pre-increment simulated cycle.
  - Hygiene checked where allowed: `git diff --check` passed, temp alias was
    absent, and protected config/result paths were clean. Laplace did not
    independently rerun ProcMan or the release rebuild; this worker did.

Final reviewer status: accepted after fixes.

## No-Promotion Confirmation

- No accepted config was modified.
- No generated config was modified.
- No latest config was modified.
- No calibration result was modified.
- No job alias was modified.
- No S6 search/report was run.
- No candidate metrics were generated.
- No hardware target metrics were generated.
- No runtime artifact directory was created for this instrumentation task.

## Recommendation

Do not promote `candidate_0002`.

Recommended next supervisor action: spawn an independent reviewer for this
instrumentation is complete. Run one bounded `candidate_0002` diagnostic with
startup, dispatch/progress, and cycle-cost diagnostics enabled until cycle
`1801`, first bind/first CTA launch, or a strict wall cap. Suggested env
additions:

```text
GPGPUSIM_CYCLE_COST_DEBUG=1
GPGPUSIM_CYCLE_COST_INTERVAL=200
GPGPUSIM_CYCLE_COST_LIMIT=16
```

Keep artifacts under ignored `artifacts/s7/`, do not generate/promote metrics,
and keep the temporary alias removed at cleanup.
