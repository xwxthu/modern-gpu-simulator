# S7 Unsupported S5 Keys Worker Log

## Purpose

Disposition the 13 unsupported keys in the real RTX5060 S5 microbenchmark
draft before any promotion-gate decision. This task is documentation-only and
does not apply parser output to accepted configs, generated configs, or
`calibration-results/latest`.

## Base And Timestamp

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base commit: `fd23be9`
- Timestamp: `2026-06-09T23:28:27+0800`
- Assigned role: S7 Unsupported S5 Key Disposition

## Scope

- Inspect all 13 `unsupported_keys` from the real RTX5060 S5 draft.
- For each key, record key, value, benchmark, raw line, schema active-key
  status, owner/provenance, and disposition.
- Decide whether any key is safe to add to the S5 stage map in this task.
- Produce a checked-in disposition document.
- Do not modify accepted configs, generated configs, flat tested configs, or
  `calibration-results/latest`.
- Do not run the simulator.
- Do not use `ssh dsp5060`.

## Required Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/s5-microbenchmark-calibration.md`
- `docs/sm120-calibration/s6-correlation-search.md`
- `docs/sm120-calibration/s7-validation-evidence-20260609.md`
- `simulator-remodeled/util/tuner/parse_sm120_microbench.py`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema/sm120.schema.yaml`
- `artifacts/s7/rtx5060-s7-tuner-buildfix-20260608-233545/RTX5060-real-microbench-draft.yaml`
- `artifacts/s7/rtx5060-s7-tuner-buildfix-20260608-233545/sm120-rtx5060-microbench.txt`

Additional context read:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema/calibration-result.schema.yaml`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema/correlation-search.schema.yaml`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/base/SM120_BASE.yaml`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/calibration-results/RTX5060/bootstrap-current-flat.yaml`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/overlays/RTX5060.yaml`
- Relevant tuner sources for `core_config`, `l1_config`, `l2_config`, tensor,
  UDP, legacy L1/shared latency, and `kernel_lat` output ownership.

## Actions

- Confirmed branch and head: `dev-5060` at `fd23be9`.
- Observed a pre-existing dirty supervisor-owned file:
  `docs/sm120-calibration/supervisor-log.md`. This worker did not edit it.
- Extracted the 13 unsupported keys from the real draft and cross-checked their
  raw benchmark line numbers.
- Compared each key against active owners in `sm120.schema.yaml`.
- Checked existing layered provenance for active owners:
  - `sm120_base`: `manual_arch_model` in `base/SM120_BASE.yaml`.
  - `calibration_result`: `inherited_from_5070ti` for RTX5060 bootstrap in
    `calibration-results/RTX5060/bootstrap-current-flat.yaml`.
  - no active owner/provenance for the 7 inactive legacy or trace spec-unit keys.
- Checked the current S6 correlation contract and confirmed none of the 13 keys
  is eligible for the S6 MVP as-is.
- Decided not to modify the parser or S5 stage map in this task. Two keys are
  low-risk future S5 stage-map candidates, but changing support now would alter
  the reviewed real draft summary before the promotion gate has accepted the
  disposition.
- Added checked-in disposition document:
  `docs/sm120-calibration/s7-unsupported-s5-keys-20260609.md`.
- Added this worker log.

## Unsupported Key Summary

- Schema-active, low-risk future S5 stage-map candidates:
  `-gpgpu_ptx_force_max_capability`, `-gpgpu_coalesce_arch`.
- Schema-active, but needing more evidence before S5 support:
  `-gpgpu_kernel_launch_latency`, `-gpgpu_shmem_option`,
  `-gpgpu_unified_l1d_size`, `-icnt_flit_size`.
- Not schema-active; explicitly deferred or rejected as raw keys for current
  SM120 flow:
  `-gpgpu_l1_latency`, `-gpgpu_num_dp_units`, `-gpgpu_smem_latency`,
  `-specialized_unit_3`, `-specialized_unit_4`,
  `-trace_opcode_latency_initiation_spec_op_3`,
  `-trace_opcode_latency_initiation_spec_op_4`.
- Current S6 MVP candidates: none.

## Changed Files

Checked-in documentation:

- `docs/sm120-calibration/s7-unsupported-s5-keys-20260609.md`
- `docs/sm120-calibration/worker-logs/worker-20260609-232827-s7-unsupported-s5-keys.md`

Code, parser, schema, fixture, config, generated, latest changes:

- None.

## Validation

Passed:

- `git diff --check`
  - Exit code: `0`
- `python3 simulator-remodeled/util/tuner/parse_sm120_microbench.py --input artifacts/s7/rtx5060-s7-tuner-buildfix-20260608-233545/sm120-rtx5060-microbench.txt --output /tmp/RTX5060-real-microbench-draft-check.yaml --gpu RTX5060 --source-type microbenchmark --source-label dsp5060-run-all --collection-host dsp5060 --collection-command './run_all.sh > sm120-rtx5060-microbench.txt 2>&1'`
  - Exit code: `0`
  - Output summary remained `76` parsed, `63` supported, `13` unsupported,
    `0` duplicate conflicts, and `63` derived-delta keys.
  - `handoff.do_not_claim_calibrated` remained `true`.
- `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`
  - Exit code: `0`
  - Output reported generated bootstrap checks for `SM120_RTX5070_TI` and
    `SM120_RTX5060`.
- Protected config/latest scoped status check:
  `git status --short -- <SM120 layered calibration-results/base/overlays, generated tested-cfgs, and flat SM120 tested-cfgs paths>`
  - Exit code: `0`
  - Empty output.

No fixture reproducibility or negative parser check was required because no
parser, stage-map, or fixture code changed.

## Reviewer Rounds

Round 1:

- Reviewer type: fresh blank-context read-only Codex reviewer.
- Artifact:
  `/tmp/s7-unsupported-s5-review/reviewer-round1.txt`
- Verdict: `CHANGES_NEEDED`.
- Blocking finding: the log recorded passed validation but still ended with
  `Pending validation and reviewer acceptance`, which contradicted the
  validation section.
- Reviewer also confirmed:
  - the 13 keys match the draft and raw lines;
  - active owners match `sm120.schema.yaml` plus base/bootstrap provenance;
  - none of the 13 keys is a current S6 MVP candidate;
  - current status shows no accepted/generated/latest config changes.
- Rework: updated final status to reflect that validation passed and that
  reviewer acceptance is pending only until the next fresh reviewer round.

Round 2:

- Reviewer type: new fresh blank-context read-only Codex reviewer.
- Artifact:
  `/tmp/s7-unsupported-s5-review/reviewer-round2.txt`
- Verdict: `ACCEPT`.
- Reviewer confirmed:
  - the disposition table covers all 13 unsupported keys exactly once with
    value, benchmark/line, schema-active status, owner/provenance, and
    disposition;
  - active-owner claims match `sm120.schema.yaml`, `SM120_BASE.yaml`, and the
    RTX5060 bootstrap provenance;
  - S5/S6 decisions are consistent with the parser stage map and S6 MVP
    contract;
  - the document does not claim calibration, S6 completion, validation
    promotion, or `latest.yaml` writes;
  - protected config status is clean for SM120 layered base/overlays,
    calibration-results, generated tested configs, and flat tested configs;
  - current dirty state is limited to the pre-existing modified supervisor log
    plus this task's new disposition doc and worker log.

## Final Status

Complete. Validation passed and fresh read-only reviewer Round 2 returned
`ACCEPT`.

Remaining risk: this disposition is documentation-only. No parser/stage-map
changes were made, no S5 values were promoted, and the S7 promotion gate remains
closed pending real hardware target metrics, any required S6 supplied-metrics
report, and promotion-gate review.
