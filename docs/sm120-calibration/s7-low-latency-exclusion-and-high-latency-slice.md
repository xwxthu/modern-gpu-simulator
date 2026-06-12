# S7 Low-Latency Exclusion And High-Latency Evidence Slice

## Scope

This note records a documentation-only S7 policy decision for the current
SM120 RTX5060 calibration pass. It does not launch simulator work, generate
candidate metrics, run S6 correlation, or promote configs.

The bounded sweep still has four designed signatures:

| Candidate | `-latency_L0_to_L1` | `-prefetch_per_stream_buffer_size` | Current promotion status |
| --- | ---: | ---: | --- |
| `candidate_0001` | `37` | `8` | excluded/deprioritized for this S7 pass |
| `candidate_0002` | `37` | `10` | excluded/deprioritized for this S7 pass |
| `candidate_0003` | `39` | `8` | actionable high-latency simulator evidence from job `486` |
| `candidate_0004` | `39` | `10` | actionable high-latency simulator evidence from job `487` |

## Policy

For the current S7 pass, low `-latency_L0_to_L1=37` candidates
`candidate_0001` and `candidate_0002` are excluded/deprioritized from
promotion unless supervisor signoff explicitly reopens them.

This is not a permanent rejection of the 37-cycle latency value. It is a
current-pass promotion policy based on incomplete completion evidence and
diagnostic-only artifacts. Reopening requires a supervisor decision plus
completion-quality evidence or a reviewed diagnostic plan that explains why the
existing low-latency risk is no longer gating.

Do not use the 37-cycle diagnostic runs as calibration-quality candidate
metrics. Do not infer a ranked S6 result from the two available 39-cycle points
as a promotion artifact.

## Evidence For Excluding 37-Cycle Candidates

`candidate_0001` (`37/8`) has no accepted simulator candidate metrics. The
post-ProcMan-fix run entered `RUNNING` and stayed CPU-active for about
`43:14`, but produced no `result.txt`, no `PASSED`, no simulator exit marker,
and no parseable simulator metrics. Static comparison found no accidental
config drift: relative to passing job `486`/`candidate_0003`, the effective
config differed only by `-latency_L0_to_L1 37` versus `39`.

Later `candidate_0001` diagnostics showed the early dispatch-to-bind path can
be normal through cycle `1806`: stream launch latency completed, TB latency
counted down, kernel selection occurred at cycle `1801`, shaders bound, CTAs
initialized, and `cta_launched_kernel=180`. That rules out an early pre-bind
deadlock in the observed window, but the original late 43-minute timeout
region remains unobserved. The candidate still has no full benchmark result
and no metrics.

`candidate_0002` (`37/10`) also has no accepted simulator candidate metrics.
Its diagnostics progressively localized earlier silent/CPU-heavy behavior and
then, with a progress-aware stop policy in job `15`, showed startup, dispatch,
TB-latency countdown, kernel selection, cluster/SM bind/admission, shader bind,
CTA issue/init, and `cta_launched_kernel=180` by cycle `1806`. This replaces
the premature job `14` stop artifact and rules out a pre-admission semantic
deadlock for that diagnostic window.

The `candidate_0002` evidence remains diagnostic-only. Job `15` intentionally
stopped at the progress gate, produced no result, no `PASSED`, no simulator
exit marker, no candidate metrics, no S6 report, no hardware target metrics,
and no promotion artifact. Post-admission behavior, full benchmark completion,
and calibration quality are still unproven.

## Actionable 39-Cycle Evidence

The current actionable validation slice is the higher-latency
`-latency_L0_to_L1=39` pair:

- `candidate_0003` is represented by ProcMan job `486` baseline evidence with
  `-latency_L0_to_L1=39` and `-prefetch_per_stream_buffer_size=8`.
  The draft simulator candidate metrics artifact is:
  `artifacts/s7/s7-target-selection-20260610-022405/RTX5060-job486-simulator-candidate-metrics-policy-draft.yaml`.
  It is `status: draft_not_applied`, `simulator_candidate_metrics: true`, and
  `hardware_target_metrics: false`. The job passed the baseline local PTX
  smoke and recorded kernel 2 `gpu_tot_sim_cycle = 45818` and
  `gpu_tot_sim_insn = 8036672`.
- `candidate_0004` is ProcMan job `487` with
  `-latency_L0_to_L1=39` and `-prefetch_per_stream_buffer_size=10`.
  The draft simulator candidate metrics artifact is:
  `artifacts/s7/s7-bounded-sweep-20260610-024829/candidate_0004-simulator-candidate-metrics.yaml`.
  It is `status: draft_not_applied`, `application_passed: true`,
  `simulator_candidate_metrics: true`, and `hardware_target_metrics: false`.
  The recovered job reported `PASSED`, simulator exit, kernel 2
  `gpu_tot_sim_cycle = 45760`, and `gpu_tot_sim_insn = 8036672`.

The existing partial bridge scaffold:

```text
artifacts/s7/s7-bounded-sweep-20260610-024829/RTX5060-backprop-4096-s7-bounded-sweep-s6-manifest.PARTIAL-2OF4.yaml
```

already records the available `39/8` and `39/10` metrics, but remains
non-runnable with `s6_manifest_runnable: false`,
`missing_candidate_signatures:2`, and
`do_not_run_search_sm120_correlation_as_is: true`.

## Limitations

- The 39-cycle evidence is simulator candidate evidence only, not hardware
  target metrics.
- The hardware target artifact for `backprop_4096` is still single-run draft
  evidence.
- The original four-candidate bounded sweep is incomplete because
  `candidate_0001` and `candidate_0002` lack completion metrics.
- The 37-cycle diagnostics are useful for root-cause work, but not for
  calibration scoring or promotion.
- No calibration-quality S6 ranked report exists for this narrowed slice.

## Recommended Next Validation

For this S7 pass, validate only the high-latency 39-cycle slice as a
non-promotion evidence package:

1. Treat `candidate_0003` and `candidate_0004` as the only actionable
   simulator-candidate evidence for immediate review.
2. Keep the current partial scaffold non-runnable, or create a clearly marked
   high-latency-only draft analysis artifact under ignored `artifacts/s7/` only
   if existing tooling can do so without schema changes and without touching
   protected outputs.
3. Defer low-latency `37` promotion work until supervisor signoff reopens it
   with explicit acceptance criteria.

Acceptance criteria for reopening `candidate_0001` or `candidate_0002`:

- A bounded run reaches full application completion with `PASSED`, simulator
  exit marker, and parseable simulator metrics, or a supervisor accepts a
  narrower diagnostic objective as sufficient for reopening.
- Effective config values match the intended candidate signature with no
  accidental drift.
- Metrics are produced through the simulator-candidate bridge as
  `draft_not_applied`, `simulator_candidate_metrics: true`, and
  `hardware_target_metrics: false`.
- A reviewer confirms no generated/accepted/latest configs, calibration
  results, hardware target metrics, S6 promotion reports, or promotion
  artifacts were modified.

Acceptance criteria for the current high-latency-only evidence slice:

- Both `39/8` and `39/10` artifacts are cited with exact paths and remain
  draft-only simulator evidence.
- Any analysis output is explicitly non-promotion and does not claim complete
  four-candidate S6 search coverage.
- The promotion gate remains closed pending supervisor review and final
  RTX5060/RTX5070Ti validation signoff.
