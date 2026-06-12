# S7 Low-Latency Exclusion Policy Worker Log

## Purpose

Create a documentation/artifact-only S7 policy and evidence slice that
excludes or deprioritizes low `-latency_L0_to_L1=37` candidates from promotion
for the current S7 pass, and reframes actionable validation around the existing
higher-latency 39-cycle evidence.

No simulator jobs, ProcMan jobs, hardware collection, metric ingestion, S6
search/report generation, or promotion commands were run.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base checkpoint: `b72cb1e` (`docs: record SM120 progress-aware diagnostic rerun`)
- Timestamp: `2026-06-13T02:34:30+08:00`
- Worker role: S7 policy/high-latency validation worker

Initial tracked worktree state:

```text
 M docs/sm120-calibration/supervisor-log.md
```

The supervisor-log modification was pre-existing and was not edited by this
worker.

## Mandatory Context Read

- `docs/sm120-calibration/supervisor-log.md` recent S7 entries
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/s7-bounded-parameter-sweep-design.md`
- `docs/sm120-calibration/s7-simulator-candidate-metrics-bridge.md`
- `docs/sm120-calibration/s7-validation-evidence-20260609.md`
- `docs/sm120-calibration/worker-logs/worker-20260613-015927-s7-candidate0002-progress-aware-rerun.md`
- `docs/sm120-calibration/worker-logs/worker-20260613-014600-s7-residual-diagnostic-stop-policy-analysis.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-235505-s7-candidate0002-cluster-core-detail-diagnostic.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-182853-s7-candidate0001-timeout-analysis.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-201232-s7-candidate0001-final-dispatch-diagnostic.md`
- `docs/sm120-calibration/worker-logs/worker-20260611-113040-s7-single-candidate-recovery.md`

Read-only ignored artifacts inspected only to verify existing job `486` and
job `487` evidence:

- `artifacts/s7/s7-target-selection-20260610-022405/RTX5060-job486-simulator-candidate-metrics-policy-draft.yaml`
- `artifacts/s7/s7-bounded-sweep-20260610-024829/candidate_0004-simulator-candidate-metrics.yaml`
- `artifacts/s7/s7-bounded-sweep-20260610-024829/RTX5060-backprop-4096-s7-bounded-sweep-s6-manifest.PARTIAL-2OF4.yaml`

## Actions

1. Confirmed branch `dev-5060`, HEAD `b72cb1e`, and the pre-existing
   supervisor-log modification.
2. Read the required S7 plan, bridge, evidence ledger, and focused diagnostic
   worker logs.
3. Verified exact artifact names and fields for job `486`/`39,8` and job
   `487`/`39,10`.
4. Decided not to produce a high-latency-only S6/scorer artifact because the
   existing partial scaffold is explicitly non-runnable and bridge policy
   requires reviewed/full candidate coverage for runnable S6 output.
5. Added the checked-in policy note:
   `docs/sm120-calibration/s7-low-latency-exclusion-and-high-latency-slice.md`.
6. Added this worker log.

## Evidence Summary

Low-latency candidates excluded/deprioritized for this S7 pass unless
supervisor signoff reopens them:

- `candidate_0001`: `-latency_L0_to_L1=37`,
  `-prefetch_per_stream_buffer_size=8`. The timeout run entered `RUNNING` and
  stayed CPU-active for about `43:14`, but produced no `result.txt`, no
  `PASSED`, no simulator exit marker, and no parseable metrics. A later
  diagnostic showed normal early dispatch/bind/CTA launch through
  `cta_launched_kernel=180` by cycle `1806`, but the late timeout region is
  still unobserved and no metrics exist.
- `candidate_0002`: `-latency_L0_to_L1=37`,
  `-prefetch_per_stream_buffer_size=10`. Job `15` showed startup, TB-latency
  countdown, kernel selection, bind/admission, shader bind, CTA init, and
  `cta_launched_kernel=180` by cycle `1806`, but it intentionally stopped at
  the diagnostic progress gate and produced no result, no simulator exit, no
  metrics, and no S6/promotion artifact.

Higher-latency actionable slice:

- `candidate_0003`: represented by job `486` baseline simulator evidence with
  `-latency_L0_to_L1=39`, `-prefetch_per_stream_buffer_size=8`.
  Artifact:
  `artifacts/s7/s7-target-selection-20260610-022405/RTX5060-job486-simulator-candidate-metrics-policy-draft.yaml`.
  Verified fields include `status: draft_not_applied`,
  `simulator_candidate_metrics: true`, `hardware_target_metrics: false`, and
  candidate values `39/8`. Kernel 2 recorded `gpu_tot_sim_cycle = 45818` and
  `gpu_tot_sim_insn = 8036672`.
- `candidate_0004`: job `487` simulator evidence with
  `-latency_L0_to_L1=39`, `-prefetch_per_stream_buffer_size=10`.
  Artifact:
  `artifacts/s7/s7-bounded-sweep-20260610-024829/candidate_0004-simulator-candidate-metrics.yaml`.
  Verified fields include `status: draft_not_applied`,
  `application_passed: true`, `simulator_candidate_metrics: true`,
  `hardware_target_metrics: false`, and candidate values `39/10`. Kernel 2
  recorded `gpu_tot_sim_cycle = 45760` and `gpu_tot_sim_insn = 8036672`.

The existing partial bridge scaffold remains non-runnable:

```text
artifacts/s7/s7-bounded-sweep-20260610-024829/RTX5060-backprop-4096-s7-bounded-sweep-s6-manifest.PARTIAL-2OF4.yaml
s6_manifest_runnable: false
missing_candidate_signatures:2
do_not_run_search_sm120_correlation_as_is: true
```

## Changed Files

Tracked documentation added:

- `docs/sm120-calibration/s7-low-latency-exclusion-and-high-latency-slice.md`
- `docs/sm120-calibration/worker-logs/worker-20260613-023430-s7-low-latency-exclusion-policy.md`

Ignored artifacts created:

- `artifacts/s7/s7-low-latency-exclusion-policy-20260613-023430/reviewer/`
  for fallback reviewer prompt/output logs only.

Protected paths:

- No generated/accepted/latest configs modified.
- No calibration results modified.
- No hardware target metrics modified.
- No candidate metrics modified.
- No S6 reports or promotion artifacts modified.
- No supervisor-log edits by this worker.

## Validation

Validation commands:

```bash
git diff --check
git status --short
git status --short -- simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated simulator-remodeled/gpu-simulator/configs/generated simulator-remodeled/gpu-simulator/gpgpu-sim/configs/tested-cfgs simulator-remodeled/gpu-simulator/configs/tested-cfgs simulator-remodeled/gpu-simulator/gpgpu-sim/configs/accepted simulator-remodeled/gpu-simulator/configs/accepted simulator-remodeled/gpu-simulator/gpgpu-sim/configs/latest simulator-remodeled/gpu-simulator/configs/latest simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/calibration-results docs/sm120-calibration/supervisor-log.md docs/sm120-calibration/s7-low-latency-exclusion-and-high-latency-slice.md docs/sm120-calibration/worker-logs/worker-20260613-023430-s7-low-latency-exclusion-policy.md
```

Results:

- `git diff --check`: passed.
- `git status --short`: showed only the pre-existing
  `docs/sm120-calibration/supervisor-log.md` modification plus the two new
  tracked documentation files from this worker.
- Protected generated/tested/accepted/latest config and calibration-result
  paths were clean in scoped status.

## Reviewer Rounds

### Round 1

Blank-context reviewer:

- Primary multi-agent spawn failed with `agent thread limit reached`.
- Fallback reviewer was run as a separate local `codex exec` process with
  `--sandbox read-only`.
- Reviewer prompt/output artifacts:
  `artifacts/s7/s7-low-latency-exclusion-policy-20260613-023430/reviewer/`
- Exit code: `0`
- Verdict: `ACCEPT`

Reviewer findings: none.

Reviewer confirmed:

- Low-latency exclusion is explicit and supervisor-gated.
- `candidate_0001` and `candidate_0002` evidence is bounded as
  diagnostic/no-metrics evidence.
- Job `486`/`39,8` and job `487`/`39,10` evidence is correctly cited as
  draft simulator-only evidence, not hardware or promotion evidence.
- The non-runnable partial S6 caveat is present.
- Next validation and acceptance criteria are present.
- Protected-path/no-promotion claims are appropriately limited.

## Final Verdict

Policy slice complete and accepted by internal reviewer.

No simulator, ProcMan, hardware target, metric ingestion, S6 search/report, or
promotion command was run. The current S7 recommendation is to exclude or
deprioritize `candidate_0001` and `candidate_0002` for this pass unless
supervisor signoff reopens them, and to use the existing `39/8` and `39/10`
draft simulator evidence as the actionable non-promotion validation slice.
