# S7 Hardware Target Provenance Worker Log

## Purpose

Prepare promotion-quality RTX5060 hardware-target provenance for
`backprop_4096`, or identify the missing collection requirements and blockers.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base checkpoint: `a565298` (`docs: package SM120 high-latency validation evidence`)
- Worker timestamp: `2026-06-13T03:06:50+08:00`
- Existing worktree state at start:
  - `docs/sm120-calibration/supervisor-log.md` was already modified.
  - This worker did not edit `supervisor-log.md`.

## Required Context Read

- `docs/sm120-calibration/supervisor-log.md` recent S7 entries
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/s7-hardware-target-metrics.md`
- `docs/sm120-calibration/s7-high-latency-validation-package.md`
- `docs/sm120-calibration/s7-simulator-candidate-metrics-bridge.md`
- Prior hardware target worker log:
  `docs/sm120-calibration/worker-logs/worker-20260610-003954-s7-hardware-target-metrics.md`
- Prior hardware target artifact root:
  `artifacts/s7/s7-hardware-target-20260610-003544/`
- Collector:
  `simulator-remodeled/util/tuner/collect_sm120_hardware_metrics.py`

## Hard Rules Observed

- Did not run local simulator or ProcMan jobs.
- Did not run the full simulator on `dsp5060`.
- Did not move the main workspace to `dsp5060`.
- Copied only the small native executable and gold file to `/tmp` on
  `dsp5060`.
- Did not modify accepted/latest/generated configs, calibration results,
  candidate metrics, S6 reports, or promotion artifacts.
- Wrote raw hardware collection artifacts only under ignored `artifacts/s7/`.
- Kept all hardware target outputs `draft_not_applied`.

## Collection Artifact

New artifact root:

```text
artifacts/s7/s7-hardware-target-provenance-20260613-030650/
```

Important files:

- `remote-tool-versions.txt`
- `nvidia-smi-query.csv`
- `native/native-stdout-run{1..5}.txt`
- `native/native-stderr-run{1..5}.txt`
- `native/native-time-run{1..5}.txt`
- `nsys/backprop-nsys-run{1..5}.nsys-rep`
- `nsys/backprop-nsys-run{1..5}.sqlite`
- `nsys/backprop-nsys-run{1..5}_cuda_gpu_kern_sum_cuda_gpu_kern_sum.csv`
- `RTX5060-backprop-4096-hardware-target-repeat-run{1..5}-draft.yaml`
- `RTX5060-backprop-4096-s6-supplied-metrics-template-run{1..5}.yaml`
- `repeatability-summary.draft.json`
- `local-inputs.sha256`
- `local-artifacts.sha256`

## Remote Provenance

Remote host and device:

- SSH target: `dsp5060`
- Hostname: `dsplab5060`
- Remote date: `2026-06-13T03:07:02+08:00`
- GPU: `NVIDIA GeForce RTX 5060`
- UUID: `GPU-fd113d06-81ba-5c47-6fbe-fd8f1b99f80e`
- Driver: `595.71.05`
- Compute capability: `12.0`
- PCI bus: `00000000:08:00.0`
- Observed pre-collection state: `P8`, SM clock `225 MHz`, memory clock
  `405 MHz`, memory used `217 MiB`
- CUDA toolkit: `/usr/local/cuda-13.2`, `nvcc V13.2.78`
- Nsight Systems: `2025.6.3.541-256337736014v0`

Input hashes:

- `backprop-rodinia-2.0-ft`:
  `e2e4cfdf8f13f3101d97701abf0a1dfedfe225d0a8c92759e5254471bf01b038`
- `data/result-4096.txt`:
  `bb8a3873b36c4725b84a8efb34fd7e84040b6c29707a17350ad949c666429e3b`

## Commands Run

Initial `dsp5060` precheck:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 dsp5060 \
  'hostname; date -Iseconds; pgrep -af "[g]pgpu|[r]un_simulations|[p]rocman|[a]ccel-sim" || true; nvidia-smi --query-gpu=name,uuid,driver_version,compute_cap --format=csv,noheader,nounits -i 0'
```

Collection used the native and Nsight repeat command patterns now recorded in:

```text
docs/sm120-calibration/s7-hardware-target-provenance.md
```

Per-run draft parsing used:

```bash
python3 simulator-remodeled/util/tuner/collect_sm120_hardware_metrics.py \
  --gpu RTX5060 \
  --stdout "$ART/native/native-stdout-run${i}.txt" \
  --stderr "$ART/native/native-stderr-run${i}.txt" \
  --time-output "$ART/native/native-time-run${i}.txt" \
  --nsys-kernel-csv "$ART/nsys/backprop-nsys-run${i}_cuda_gpu_kern_sum_cuda_gpu_kern_sum.csv" \
  --nvidia-smi-query "$ART/nvidia-smi-query.csv" \
  --tool-versions "$ART/remote-tool-versions.txt" \
  --collection-host dsp5060 \
  --source-label "backprop_4096_native_repeat_run${i}" \
  --target-id "rtx5060-backprop-4096-hardware-target-repeat-run${i}-20260613" \
  --collection-command "recorded in docs/sm120-calibration/worker-logs/worker-20260613-030650-s7-hardware-target-provenance.md" \
  --notes "S7 repeated lightweight RTX5060 hardware collection; draft/provenance only; native run${i} paired with Nsight run${i}." \
  --output "$ART/RTX5060-backprop-4096-hardware-target-repeat-run${i}-draft.yaml" \
  --s6-template-output "$ART/RTX5060-backprop-4096-s6-supplied-metrics-template-run${i}.yaml"
```

## Results

All collection and parse exit codes were `0`.

All five native runs:

- exited `0`;
- printed `PASSED`;
- reported checksum `0x42b0e8add8ca`.

Repeatability summary:

| Metric | Mean | Median | Min | Max | CV |
| --- | ---: | ---: | ---: | ---: | ---: |
| `cuda_kernel_total_time_ms` | `0.010912` | `0.010912` | `0.010848` | `0.011008` | `0.548630%` |
| `cuda_kernel_avg_time_ms` | `0.005456` | `0.005456` | `0.005424` | `0.005504` | `0.548630%` |
| `cuda_kernel_bpnn_layerforward_cuda_total_time_ms` | `0.002381` | `0.002368` | `0.002336` | `0.002432` | `1.532494%` |
| `cuda_kernel_bpnn_adjust_weights_cuda_total_time_ms` | `0.008531` | `0.008512` | `0.008480` | `0.008640` | `0.731192%` |
| `native_wall_time_seconds` | `0.294000` | `0.270000` | `0.270000` | `0.380000` | `16.418392%` |

The Nsight CUDA-kernel metrics are the only simulator-comparable hardware
targets from this set. Native wall/user/sys/RSS metrics remain hardware
characterization only.

## Promotion Assessment

This worker produced stronger hardware-target provenance than the prior
single-run artifact, but it did not produce promotion-quality hardware targets.

Blockers:

- No reviewed aggregate hardware-target schema exists for repeated runs.
- No approved rule exists for mean versus median target selection, minimum
  repetition count, CV/range thresholds, or cold-start handling.
- No approved hardware-control protocol exists for clocks, warmup, thermal
  state, idle-GPU validation, and background-load rejection.
- The checked-in collector emits per-run draft YAMLs and non-runnable S6
  templates only.
- S6 still lacks a reviewed runnable supplied-metrics manifest with matching
  simulator candidate metrics for the selected search space.
- Promotion-gate review and RTX5070Ti compatibility signoff remain pending.

## Validation

- `dsp5060` reachability/device precheck succeeded and showed the expected RTX
  5060.
- Pre-collection simulator-process check on `dsp5060` returned no matching
  process.
- All native repeat, Nsight profile, Nsight stats, `scp`, and collector exit
  code files recorded `0`.
- Raw native/profiler/device/tool inputs were scanned for simulator markers and
  none were found. The per-run generated YAMLs record those marker strings in
  their rejection-policy lists; later reviewer prompt/log artifacts may also
  quote the marker strings as review criteria.
- Five draft hardware target YAMLs were loaded and asserted as:
  `schema_id: sm120_hardware_target_metrics_v1`,
  `status: draft_not_applied`,
  `hardware_target_metrics: true`, and
  `simulator_smoke_metrics: false`.
- Five S6 templates were loaded and asserted as `status: template_not_runnable`.
- `repeatability-summary.draft.json` was loaded and asserted as
  `promotion_quality: false`, with all native exits zero and all applications
  passed.

## Reviewer

Multi-agent blank-context reviewer spawn was attempted first, but the agent
thread limit was reached. A read-only local `codex exec` reviewer fallback was
used and recorded under the artifact root.

Reviewer round 1:

- Artifact files:
  - `reviewer-round1.prompt.txt`
  - `reviewer-round1-codex.stdout.txt`
  - `reviewer-round1-codex.stderr.txt`
  - `reviewer-round1-codex.exitcode`
- Result: terminated and retried after producing no output.
- Exit code recorded as `124`.
- This nonzero exit code is a reviewer-process artifact, not a hardware
  collection, Nsight, transfer, or collector failure.

Reviewer round 2:

- Artifact files:
  - `reviewer-round2.prompt.txt`
  - `reviewer-round2-codex.txt`
  - `reviewer-round2-codex.stdout.txt`
  - `reviewer-round2-codex.stderr.txt`
  - `reviewer-round2-codex.exitcode`
- Verdict: `NEEDS_WORK`.
- Finding: the artifact root contains `reviewer-round1-codex.exitcode = 124`,
  so broad wording that all exit-code files are zero would be inaccurate after
  reviewer artifacts are added.
- Response: this log now scopes zero-exit claims to collection, native, Nsight,
  transfer, device/tool, and collector commands, and explicitly records the
  reviewer-round1 timeout as a reviewer fallback artifact.

Reviewer round 3 will be run after this clarification.

Reviewer round 3:

- Verdict: `NEEDS_WORK`.
- Finding: the worker log still used broad artifact-root wording for simulator
  marker strings, while reviewer prompt/stderr artifacts can also quote those
  strings.
- Response: this validation section now scopes marker-clean claims to raw
  native/profiler/device/tool inputs and explicitly excludes generated YAML
  policy lists plus reviewer prompt/log quotes from that raw-input claim.

Reviewer round 4 will be run after this clarification.

Reviewer rounds 4 and 5:

- Result: both timed out after starting read-only checks and produced no final
  verdict.
- These are reviewer-process artifacts, not collection failures.

Reviewer round 6:

- Artifact files:
  - `reviewer-round6.prompt.txt`
  - `reviewer-round6-codex.txt`
  - `reviewer-round6-codex.stdout.txt`
  - `reviewer-round6-codex.stderr.txt`
  - `reviewer-round6-codex.exitcode`
- Verdict: `ACCEPT`.
- Reviewer accepted that the prior `NEEDS_WORK` issues were addressed by
  narrowing zero-exit claims to collection/native/Nsight/transfer/device/tool
  and collector commands, and by scoping marker-clean claims to raw inputs only.
- Reviewer found the remaining blockers are documented as non-promotion-quality
  limitations rather than validation failures, with no new issue evident in
  the supplied evidence.
