# S7 Validation Evidence Ledger - 2026-06-09

## Scope

This ledger consolidates the successful local PTX smoke evidence from ProcMan
job `486` into S7 validation evidence for `RTX5060_SM120_GEN`.

This is validation evidence only. It is not calibration, not S6 correlation,
not a hardware target-metrics report, and not promotion to accepted/generated
configs or `calibration-results/latest`.

## Source Evidence

- Run id: `s7-kernel2-attribution-20260609-211410`
- Artifact root:
  `artifacts/s7/s7-kernel2-attribution-20260609-211410/`
- Worker log:
  `docs/sm120-calibration/worker-logs/worker-20260609-211410-s7-kernel2-attribution.md`
- Local validation manifest:
  `artifacts/s7/s7-kernel2-attribution-20260609-211410/validation-manifest.yaml`
- Branch/head at this consolidation start: `dev-5060` at `780719f`

`artifacts/s7/` is ignored and is not a submit location for accepted
calibration artifacts. The checked-in evidence is this ledger plus the worker
log for the consolidation task.

## Local Smoke Result

ProcMan job `486` was launched on the local simulator server for:

- Benchmark: `rodinia_2.0-ft:backprop-rodinia-2.0-ft:0`
- Config alias: `RTX5060_SM120_GEN`
- Mode: local PTX smoke, not trace-driven smoke
- Launcher evidence:
  `artifacts/s7/s7-kernel2-attribution-20260609-211410/local-smoke-run.log`
- Final stdout:
  `artifacts/s7/s7-kernel2-attribution-20260609-211410/smoke-stdout-final.o486.log`
- Final stderr:
  `artifacts/s7/s7-kernel2-attribution-20260609-211410/smoke-stderr-final.e486.log`
- Final ProcMan direct status:
  `artifacts/s7/s7-kernel2-attribution-20260609-211410/procman-status-final-direct.log`

Verdict: `PASS` as a local PTX smoke test. The stdout contains final
application `PASSED`, and the final direct ProcMan status reports
`Nothing Active`.

Recorded simulator smoke metrics:

| Kernel | Metric | Value | Evidence |
| --- | --- | ---: | --- |
| First backprop kernel | `gpu_tot_sim_cycle` | 7729 | `smoke-result-summary.log` |
| First backprop kernel | `gpu_tot_sim_insn` | 4169728 | `smoke-result-summary.log` |
| First backprop kernel | `gpgpu_simulation_time` | 390 sec | `smoke-result-summary.log` |
| Kernel 2 `_Z24bpnn_adjust_weights_cudaPfiS_iS_S_` | `gpu_tot_sim_cycle` | 45818 | `smoke-result-summary.log` |
| Kernel 2 `_Z24bpnn_adjust_weights_cudaPfiS_iS_S_` | `gpu_tot_sim_insn` | 8036672 | `smoke-result-summary.log` |
| Full application | `gpgpu_simulation_time` | 2398 sec | `smoke-result-summary.log` |

These are simulator smoke metrics. They must not be used as hardware target
metrics for S6 correlation.

## Kernel 2 Attribution Evidence

The job reached the all-CTAs-resident target window:

- Evidence:
  `artifacts/s7/s7-kernel2-attribution-20260609-211410/kernel2-target-window-summary.log`
- Target line: `smoke-stdout-final.o486.log:3068`
- `next_cta=256`
- `cta_completed_kernel=76`
- `active_cta=180`
- `not_completed_threads=43648`

The sampled target window supports the attribution recorded by the attribution
worker:

- Dominant sampled PC: `0x2890`
- CTA-barrier state:
  `active_warps=42, waiting_warps=26, active_cta=6, unreleased_ready=0, partial=5`
- Scheduler sample: no issue because sampled candidates were not ready, with
  barrier blockers dominant.
- SIMT/reconvergence mismatch was not observed in the target sample
  (`pc_mis=0`).
- Post-barrier memory-return or queue-tail evidence was not observed in the
  target sample (`mem_resp=0`, `mem_prt_active=0`, sampled memory queues zero).

This attribution remains sampled evidence. It narrows the observed slow window
but does not prove a specific incorrect barrier-bookkeeping mutation.

## Artifact Integrity

Key SHA256 values are recorded in the local validation manifest. Important
anchors:

| Artifact | SHA256 |
| --- | --- |
| `local-smoke-plan.log` | `e057a93673a59c203b6680230f9007b413825d985b347bc8b9160c0bacfabfe5` |
| `local-smoke-run.log` | `f1bda6dadcc08ec317de23707462e8e2fa4a16d27df55f1ac1ac8f537e5ad617` |
| `smoke-stdout-final.o486.log` | `9d8517c81a9b47e5cb91503de2d9d6ea604a9b3deaddcc9b101bb68bee5fc408` |
| `smoke-stderr-final.e486.log` | `4ca09bca07f422eee2dd70187aff69d31e1b881212ec9cc968db70176f1b1f30` |
| `smoke-result-summary.log` | `4196f1eada0fa2e86feee97d7b5cdff0a5675191c9bb9d4065cabf200f30f67e` |
| `kernel2-target-window-summary.log` | `5175443bf3287da238ede7d4129383db62f00a38529556a4cc2fa53d5574978d` |
| `procman-status-final-direct.log` | `d3d366a1c48b61db359687d171be3104681d16257b759ac8ea126f537e20f2c5` |

## Provenance From Earlier S7 Artifacts

Earlier S7 evidence exists and is referenced rather than copied:

- RTX5060 official facts:
  `artifacts/s7/rtx5060-s7-20260608-230140/validation-manifest.yaml`
  - Status in that manifest: official facts collected from `dsp5060`.
  - Device-info manifest hash:
    `43d58c9d9f13162fee0490cde24906bba8ebe766302670ca2dd264629b442822`.
  - Reported facts include `NVIDIA GeForce RTX 5060`, driver `595.71.05`,
    compute capability `12.0`, and UUID
    `GPU-fd113d06-81ba-5c47-6fbe-fd8f1b99f80e`.
  - This consolidation did not rerun hardware collection.

- RTX5060 tuner microbenchmark draft:
  `artifacts/s7/rtx5060-s7-tuner-buildfix-20260608-233545/validation-manifest.yaml`
  - Raw output:
    `artifacts/s7/rtx5060-s7-tuner-buildfix-20260608-233545/sm120-rtx5060-microbench.txt`
  - Raw output SHA256:
    `565a904d232f71c4b4ad6efeb524fb67a8d5b24e88644bc33b4b0d5393bbadf4`
  - S5 draft:
    `artifacts/s7/rtx5060-s7-tuner-buildfix-20260608-233545/RTX5060-real-microbench-draft.yaml`
  - S5 draft SHA256:
    `eb3d12bd2e23601a86c4e4ef9353e54c6913130ef6282880c69b824fb1caece9`
  - Status: `draft_not_applied`; `do_not_claim_calibrated` remains true.
  - Parser summary from the manifest: 76 parsed config lines, 63 supported,
    13 unsupported, 0 duplicate conflicts.

## Promotion Gate Status

The S7 promotion gate remains closed.

Available and bounded:

- Local PTX smoke for job `486`: `PASS`.
- RTX5060 official facts: prior artifact exists, provenance recorded.
- RTX5060 raw microbenchmark/S5 draft: prior artifact exists,
  `draft_not_applied`.
- No full simulator workload ran on `dsp5060`.
- No accepted/generated/latest configs were modified by this consolidation.
- No calibration-results `latest` file was written or promoted.
- Current static RTX5070Ti compatibility helper check passed with
  `--gpu RTX5070_TI --run-id rtx5070ti-compat-plan --no-command-plan`.

Still missing for promotion:

- Real hardware target metrics for correlation/validation. Job `486` simulator
  metrics are not hardware target metrics.
- S6 `supplied_metrics` manifest with real hardware target provenance.
- S6 ranked draft report generated from reviewed supplied metrics.
- Promotion-gate reviewer approval for any staged delta.
- Promotion-scope RTX5070Ti compatibility review/signoff beyond the static
  helper check, if required by the final gate reviewer.
- Review decision on whether the 13 unsupported S5 keys need S6 treatment or
  explicit deferral.

## Consolidation Validation

Required validation commands passed on the current consolidation state:

- `git diff --check`
- `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`
- `python3 simulator-remodeled/util/tuner/check_sm120_s7_validation.py --gpu RTX5060 --run-id s7-kernel2-attribution-20260609-211410 --no-command-plan`
- `python3 simulator-remodeled/util/tuner/check_sm120_s7_validation.py --gpu RTX5070_TI --run-id rtx5070ti-compat-plan --no-command-plan`

Validation logs are under
`artifacts/s7/s7-kernel2-attribution-20260609-211410/` with filenames prefixed
`consolidation-`.

## Current Verdict

S7 has a formally recorded local PTX smoke `PASS` for the RTX5060 generated
config path, with artifact paths and hashes preserved in an ignored local
manifest. This is sufficient smoke evidence for the observed job `486` run. It
is not sufficient evidence to claim calibration, correlation, or promotion.
