# S7 Validation Evidence Consolidation Worker Log

## Purpose

Consolidate ProcMan job `486` into formal S7 validation evidence for the
RTX5060 generated SM120 path, while keeping the boundary clear between local
smoke evidence, hardware target metrics, correlation, calibration, and
promotion.

## Base And Timestamp

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base commit: `780719f`
- Timestamp: `2026-06-09T22:40:22+0800`
- Assigned role: S7 Validation Evidence Consolidation

## Scope

- Read the S7 planning/runbook context and job `486` attribution evidence.
- Create a checked-in S7 evidence ledger.
- Create an ignored local validation manifest under the job `486` artifact
  root.
- Explicitly mark local simulator smoke metrics as not hardware target
  metrics.
- Reference existing RTX5060 official facts and microbenchmark draft artifacts
  by provenance/status only.
- Do not modify accepted configs, generated configs, calibration result
  `latest` files, or flat tested configs.
- Do not write `calibration-results/latest`.
- Do not claim calibration, correlation, or promotion completion.

## Required Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/s7-validation-runbook.md`
- `docs/sm120-calibration/s7-validation-manifest-template.yaml`
- `docs/sm120-calibration/worker-logs/worker-20260609-211410-s7-kernel2-attribution.md`
- `artifacts/s7/s7-kernel2-attribution-20260609-211410/`

## Actions

- Confirmed branch/head: `dev-5060` at `780719f`.
- Observed pre-existing dirty supervisor-owned file:
  `docs/sm120-calibration/supervisor-log.md`; this worker did not edit it.
- Read the S7 runbook, manifest template, S6 correlation contract, and the job
  `486` attribution worker log.
- Inspected job `486` final stdout/stderr, smoke summary, target-window
  summary, ProcMan status, and artifact hashes.
- Added checked-in evidence ledger:
  `docs/sm120-calibration/s7-validation-evidence-20260609.md`.
- Added ignored validation manifest:
  `artifacts/s7/s7-kernel2-attribution-20260609-211410/validation-manifest.yaml`.
- Added this worker log.

## Evidence

Job `486` local PTX smoke:

- Benchmark: `rodinia_2.0-ft:backprop-rodinia-2.0-ft:0`
- Config alias: `RTX5060_SM120_GEN`
- Mode: local PTX smoke.
- Result: `PASSED`.
- Final ProcMan status: `Nothing Active`.
- Kernel 2 `_Z24bpnn_adjust_weights_cudaPfiS_iS_S_`:
  - `gpu_tot_sim_cycle = 45818`
  - `gpu_tot_sim_insn = 8036672`
- Full application simulation time: `2398 sec`.

The above metrics are simulator smoke metrics only. They were not recorded as
hardware target metrics and were not used to create an S6 supplied-metrics
manifest.

Existing S7 provenance referenced:

- Official RTX5060 facts:
  `artifacts/s7/rtx5060-s7-20260608-230140/validation-manifest.yaml`.
- RTX5060 microbenchmark raw output and S5 draft:
  `artifacts/s7/rtx5060-s7-tuner-buildfix-20260608-233545/validation-manifest.yaml`.

## Changed Files

Checked-in documentation:

- `docs/sm120-calibration/s7-validation-evidence-20260609.md`
- `docs/sm120-calibration/worker-logs/worker-20260609-224022-s7-validation-evidence.md`

Ignored local artifact:

- `artifacts/s7/s7-kernel2-attribution-20260609-211410/validation-manifest.yaml`

Config/generated/calibration result changes:

- None.

## Validation

All required validation commands passed:

- `git diff --check`
  - Log: `artifacts/s7/s7-kernel2-attribution-20260609-211410/consolidation-final-git-diff-check.log`
  - Exit code: `0`
- `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`
  - Log: `artifacts/s7/s7-kernel2-attribution-20260609-211410/consolidation-final-generate-sm120-check-only.log`
  - Exit code: `0`
- `python3 simulator-remodeled/util/tuner/check_sm120_s7_validation.py --gpu RTX5060 --run-id s7-kernel2-attribution-20260609-211410 --no-command-plan`
  - Log: `artifacts/s7/s7-kernel2-attribution-20260609-211410/consolidation-final-s7-check-rtx5060.log`
  - Exit code: `0`
- `python3 simulator-remodeled/util/tuner/check_sm120_s7_validation.py --gpu RTX5070_TI --run-id rtx5070ti-compat-plan --no-command-plan`
  - Log: `artifacts/s7/s7-kernel2-attribution-20260609-211410/consolidation-final-s7-check-rtx5070ti.log`
  - Exit code: `0`
- Process audit: no `run_simulations.py`, `procman.py`, or
  `/home/xiewx/accel-0608/modern-gpu-simulator` simulator job was running.
  A separate `/workspace/prefetch/.../accel-sim.out` process owned by another
  user was observed and left untouched.

## Reviewer Rounds

Round 1:

- Reviewer type: Codex CLI read-only attempt.
- Verdict: invalid/no verdict.
- Artifact root:
  `artifacts/s7/s7-kernel2-attribution-20260609-211410/reviewer/consolidation-round1/`
- Notes: the first invocation failed due CLI argument mismatch. The retry did
  not produce a verdict in a reasonable time and was terminated. This was not
  counted as a reviewer acceptance.

Round 2:

- Reviewer type: fresh blank-context read-only reviewer.
- Artifact root:
  `artifacts/s7/s7-kernel2-attribution-20260609-211410/reviewer/consolidation-round2/`
- Verdict: `ACCEPT`.
- Reviewer confirmed:
  - job `486` metrics are treated only as simulator smoke metrics, not
    hardware target metrics;
  - S6 supplied-metrics manifest and S6 ranked draft report are clearly
    missing;
  - promotion gate remains closed;
  - no accepted/generated/latest configs or calibration-results `latest` were
    promoted;
  - prior official-facts and microbenchmark artifacts are referenced by
    provenance/status only;
  - RTX5070Ti static helper check is represented as passed, with final
    promotion-scope signoff still separate;
  - artifact paths, hashes, and statuses are coherent.
- Residual risks noted by reviewer: sampled attribution coverage, 13
  unsupported S5 keys, no S6 hardware target metrics/report, RTX5070Ti final
  signoff, and supervisor review.

Supervisor review:

- Independent supervisor reviewer `019eaceb-ed55-7e20-9eec-1571d2dc3660`
  returned `CHANGES_NEEDED`.
- Blocking issue: the ignored validation manifest marked
  `microbenchmark_calibration.unsupported_keys_reviewed: true` and
  `microbenchmark_calibration.pass: true`, while the checked-in ledger
  correctly states that 13 unsupported S5 keys still need explicit S6 treatment
  or reviewed deferral.
- Rework: updated the ignored validation manifest so
  `unsupported_keys_reviewed: false`, `pass: false`, and the notes state that
  unsupported keys are identified but unresolved before promotion.

## Final Status

Complete for this consolidation task. Final verdict: local PTX smoke evidence
from ProcMan job `486` is recorded as S7 validation evidence with an ignored
manifest and a checked-in ledger. The promotion gate remains closed: no S6
supplied-metrics manifest, no S6 ranked report, no hardware target metrics,
and no config/calibration promotion were created.
