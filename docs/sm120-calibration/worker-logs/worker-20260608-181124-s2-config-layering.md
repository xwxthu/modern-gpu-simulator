# Worker S2 Config Layering Design

## Purpose

Design the SM120 configuration layering scheme for S2 so that later S3/S4 work has concrete inputs for implementing collection, schema, generation, validation, and migration without breaking the current SM120 configs.

This is documentation-only work.

## Base Commit

- Design base commit: `841066382f610876adf9f94ca1a0e49e579e5b11`
- Reference repo status: `/home/xiewx/accel-0608/accel-sim-framework` was used only as background from S1; it was not modified.

## Timestamp

- Start: `2026-06-08 18:06:40 CST +0800`
- Draft before reviewer: `2026-06-08 18:11:24 CST +0800`

## Branch / Worktree Status

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch at start: `dev-5060...origin/dev-5060 [ahead 2]`
- Worktree before S2 edits: clean.
- Worktree after draft: documentation-only additions under `docs/sm120-calibration/`.

## Scope

In scope:

- Read S0/S1 planning and audit documents.
- Inspect existing SM120 flat configs, trace configs, AccelWattch XML, interconnect config files, tuner templates, and job-launching config behavior as needed.
- Produce a long-lived S2 design document for SM120 config layering.
- Produce this worker log.
- Run a blank-context reviewer and revise until accepted.

Out of scope:

- No simulator source edits.
- No edits to existing SM120 `tested-cfgs`.
- No edits to `util/tuner`, `util/job_launching`, or any runtime config.
- No GPU collection, no simulator runs, no reference repo modifications.

## Actions

- Read:
  - `docs/sm120-calibration/supervisor-log.md`
  - `docs/sm120-calibration/overall-plan.md`
  - `docs/sm120-calibration/worker-logs/worker-20260608-174813-s1-audit.md`
- Inspected current SM120 runnable file layout:
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/tested-cfgs/SM120_RTX5070_TI/gpgpusim.config`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/tested-cfgs/SM120_RTX5060/gpgpusim.config`
  - `simulator-remodeled/gpu-simulator/configs/tested-cfgs/SM120_RTX5070_TI/trace.config`
  - `simulator-remodeled/gpu-simulator/configs/tested-cfgs/SM120_RTX5060/trace.config`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/tested-cfgs/SM120_RTX5070_TI/accelwattch_sass_sim.xml`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/tested-cfgs/SM120_RTX5060/accelwattch_sass_sim.xml`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/tested-cfgs/SM120_RTX5070_TI/config_ampere_islip.icnt`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/tested-cfgs/SM120_RTX5060/config_ampere_islip.icnt`
- Confirmed current SM120 active `gpgpusim.config` deltas are only cluster count, memory partition count, and clock domains.
- Confirmed current SM120 `trace.config` and `.icnt` files are identical across RTX 5070 Ti and RTX 5060.
- Confirmed RTX 5060 AccelWattch XML is copied from RTX 5070 Ti and explicitly uncalibrated.
- Inspected `util/tuner/config_template/gpgpusim.config` and `util/tuner/config_template/trace.config`; current tuner templates omit the SM120 remodeled block and therefore cannot serve as the S4 generator by simple line replacement.
- Inspected `util/job_launching/configs/define-standard-cfgs.yml`, `util/job_launching/common.py`, and `util/job_launching/run_simulations.py`; job launching reads only `base_file` and derives `trace.config` from the mirrored `configs.../gpgpusim.config` path.
- Inspected interconnect option registration in `gpgpu-sim/src/gpgpu-sim/icnt_wrapper.cc`; current SM120 uses `network_mode 2` local xbar, while Intersim `network_mode 1` aborts.
- Created `docs/sm120-calibration/config-layering-design.md`.

## Evidence Summary

- Existing current flat configs must be preserved first because `define-standard-cfgs.yml` maps `RTX5060` and `RTX5070_TI` directly to the flat `tested-cfgs` `gpgpusim.config` files.
- In trace mode, `run_simulations.py` computes the trace config path by replacing the root while preserving the `configs.../gpgpusim.config` suffix. Generated outputs must keep mirrored gpgpusim/trace paths or job launching must later gain explicit `trace_file` support.
- The generator must render both config roots:
  - `$GPGPUSIM_ROOT/configs/.../<CONFIG>/gpgpusim.config`
  - `$ACCELSIM_ROOT/configs/.../<CONFIG>/trace.config`
- `trace.config` latency categories are parsed independently from remodeled `gpgpusim.config` latency fields, so S4 needs canonical latency groups and drift validation.
- Existing `.icnt` files are compatibility files for directory completeness while current SM120 uses local xbar.
- Existing AccelWattch XML should be layered separately from performance config generation; power remains disabled by default unless a calibrated power profile is selected.

## Design Produced

The long-lived design in `docs/sm120-calibration/config-layering-design.md` specifies:

- Layer precedence: `SM120_BASE < per-GPU overlay < calibration result < render profile`.
- Recommended future file layout for layered schema, base, overlays, calibration results, render templates, and generated `tested-cfgs`.
- Parameter ownership rules for:
  - `gpgpusim.config`
  - `trace.config`
  - `accelwattch_sass_sim.xml`
  - `config_ampere_islip.icnt` / active local-xbar interconnect options
- Provenance schema with required source types:
  - `official_tool`
  - `device_query`
  - `microbenchmark`
  - `correlation_search`
  - `manual_arch_model`
  - `placeholder`
  - `inherited_from_5070ti`
- S4 generator flow:
  - layer merge
  - owner validation
  - required-field validation
  - derived parameter expansion
  - cross-file consistency validation
  - rendering
  - re-parse validation
  - manifest emission
- Drift prevention for `trace.config` and `gpgpusim.config` latencies through canonical latency groups.
- Compatibility strategy:
  - keep existing flat SM120 configs unchanged
  - generate parallel outputs first under `configs/generated/tested-cfgs`
  - add generated job-launch aliases later
  - switch default aliases only after review and validation
- Migration plan:
  - MVP bootstrap from current flat configs
  - S3 official/device-query collection
  - S4 generator/tuner integration
  - S5 microbenchmark calibration
  - S6 targeted correlation search
  - S7 validation and alias migration
- Risks and open questions, including hardcoded model assumptions that should remain `manual_arch_model` until evidence justifies converting them to config/calibration knobs.

## Changed Files

- Added `docs/sm120-calibration/config-layering-design.md`.
- Added `docs/sm120-calibration/worker-logs/worker-20260608-181124-s2-config-layering.md`.

## Reviewer Rounds

### Round 1

- Reviewer command: `codex exec -C /home/xiewx/accel-0608/modern-gpu-simulator --sandbox read-only --ephemeral ...`
- Reviewer role: blank-context S2 design reviewer; read-only.
- Verdict: ACCEPT.
- Blocking findings: none.
- Reviewer rationale: the design covers the required layered model, ownership rules, provenance source types, S4 generator validation, latency drift prevention, compatibility strategy, migration plan, and open risks. The job-launching strategy matches current launcher behavior and preserves existing flat SM120 configs.
- Non-blocking suggestions:
  - Update this worker log from pending/blocked.
  - Add explicit `profiles/` files to the proposed layout.
  - Add a golden bootstrap diff check to S4/MVP.
- Follow-up revisions:
  - Updated this worker log with the reviewer result.
  - Added `profiles/smoke.yaml`, `profiles/performance.yaml`, and `profiles/power.yaml` to the recommended layered layout.
  - Added `profiles/<profile>.yaml` to generator inputs.
  - Added a golden bootstrap diff check to the MVP steps and acceptance criteria.

### Supervisor Review

- Reviewer: supervisor reviewer after Round 1.
- Verdict: changes-needed.
- Required fixes:
  - Add a more closed active-key ownership/profile policy, explicitly covering launch timing, L0I timing, instruction prefetch controls, and custom OMP scheduler controls.
  - State that S4 schema must assign an owner to every active option or generation fails.
  - Clarify bootstrap golden diff behavior when current flat configs rely on implicit defaults, specifically absent `-power_simulation_enabled 0`.
  - Clarify that job-launching `extra_params` appended outside generated files bypass manifest provenance and must be marked `unmanifested_override` or generated as controlled sweep configs.
  - Update this worker log and run a fresh blank-context reviewer after rework.
- Rework performed:
  - Added `Active-Key Ownership And Profile Policy` to `docs/sm120-calibration/config-layering-design.md`.
  - Explicitly assigned ownership/profile policy for `-gpgpu_kernel_launch_latency`, `-gpgpu_TB_launch_latency`, `-latency_L0_to_L1`, `-latency_L1_to_L0`, instruction prefetch controls, and custom OMP scheduler controls.
  - Added the rule that S4 active-key inventory must cover every active option from current SM120 `gpgpusim.config`, `trace.config`, rendered/copied XML parameters, and active local-xbar interconnect fields; missing owner is a generator error.
  - Added `bootstrap.yaml` to the proposed `profiles/` layout and clarified `bootstrap` required-field behavior.
  - Clarified that bootstrap output may omit explicit defaults such as `-power_simulation_enabled 0` to preserve golden diffs, while performance/power profiles may render explicit defaults in profile-specific outputs or diff allowlists.
  - Added the `unmanifested_override` policy for legacy `define-standard-cfgs.yml` `extra_params`, and stated calibration sweeps should be generated as controlled manifested configs.

### Round 2

- Reviewer command: `codex exec -C /home/xiewx/accel-0608/modern-gpu-simulator --sandbox read-only --ephemeral ...`
- Reviewer role: fresh blank-context S2 rework reviewer; read-only.
- Verdict: ACCEPT.
- Blocking findings: none.
- Reviewer rationale: the reworked design explicitly covers the required active SM120 keys, requires S4 active-key owner/profile/provenance validation, handles bootstrap golden diff behavior and implicit `-power_simulation_enabled 0`, handles `extra_params` provenance bypass, and preserves the original S2 layering/generator/migration/compatibility coverage.
- Non-blocking suggestions:
  - Clarify `-custom_omp_scheduler_ratio_to_dynamic` as one schema owner plus `profile_override_allowed`.
  - Update Round 2 and Final Status in this worker log.
- Follow-up revisions:
  - Changed `-custom_omp_scheduler_ratio_to_dynamic` ownership to `Calibration result, with profile_override_allowed for controlled sweeps`, and clarified that sweep overrides are manifested profile overrides rather than a second schema owner.
  - Updated this worker log with Round 2 result and final status.

## Final Status

Final Status: ready-for-review
