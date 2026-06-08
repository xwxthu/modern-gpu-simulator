# Worker Log: S6 Targeted Correlation Search

## Purpose

Implement the S6 MVP targeted correlation-search framework for SM120 parameters
that remain after S5 microbenchmark/system-config parsing.

## Base State

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base commit: `a517d19b45148290e1aa711c576e27e00a9a7f0e`
- Timestamp: `2026-06-08 21:56:32 CST`
- Initial working tree: clean

## Assigned Scope

- Add a small search harness under `simulator-remodeled/util/tuner/`.
- Consume a bounded manifest with GPU/base config, benchmark cases, target
  metrics, and explicitly listed candidate parameters.
- Validate owner/stage/provenance against the existing SM120 schema and S5
  staged key map.
- Support fixture/dry-run evaluation and plan-only simulator commands without
  launching workloads.
- Emit draft-only ranked reports.
- Add synthetic fixture data and documentation.
- Do not modify flat SM120 tested configs, S4 generated configs, accepted
  calibration results, or S4 generator consumption logic.

## Actions

- Read supervisor and stage documents:
  - `docs/sm120-calibration/supervisor-log.md`
  - `docs/sm120-calibration/overall-plan.md`
  - `docs/sm120-calibration/config-layering-design.md`
  - `docs/sm120-calibration/s4-config-generator.md`
  - `docs/sm120-calibration/s5-microbenchmark-calibration.md`
- Read S4/S5 scripts and layered SM120 schema:
  - `simulator-remodeled/util/tuner/generate_sm120_configs.py`
  - `simulator-remodeled/util/tuner/parse_sm120_microbench.py`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema/sm120.schema.yaml`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema/calibration-result.schema.yaml`
- Checked original Accel-Sim tuner/correlation references enough to confirm
  that the existing plotting/launcher stack is not directly reusable for the
  S6 manifest-ranking MVP.
- Implemented a standalone S6 harness that reads generated base configs but
  writes only reports.
- Added a S6 contract, synthetic fixture manifest, negative fixtures, and a
  reproducible synthetic report.
- Documented S6 workflow and constraints.
- Supervisor rework at `2026-06-08 22:22:29 CST`: tightened
  `check_output_target()` so report outputs are refused anywhere under the
  whole layered SM120 source directory, including its root.

## Changed Files

- `docs/sm120-calibration/s6-correlation-search.md`
- `docs/sm120-calibration/worker-logs/worker-20260608-215632-s6-correlation.md`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema/correlation-search.schema.yaml`
- `simulator-remodeled/util/tuner/search_sm120_correlation.py`
- `simulator-remodeled/util/tuner/testdata/sm120_correlation_search_fixture.yaml`
- `simulator-remodeled/util/tuner/testdata/sm120_correlation_search_fixture_report.yaml`
- `simulator-remodeled/util/tuner/testdata/sm120_correlation_search_invalid_unknown_key.yaml`
- `simulator-remodeled/util/tuner/testdata/sm120_correlation_search_invalid_unbounded.yaml`

## Evidence Commands

Validation completed:

```bash
python3 -m py_compile simulator-remodeled/util/tuner/search_sm120_correlation.py

python3 simulator-remodeled/util/tuner/search_sm120_correlation.py \
  --manifest simulator-remodeled/util/tuner/testdata/sm120_correlation_search_fixture.yaml \
  --output /tmp/sm120_correlation_search_fixture_report.yaml \
  --generated-at 2026-06-08T13:56:32Z \
  --fixture-only \
  --emit-planned-commands \
  --command-candidate-limit 2

diff -u \
  simulator-remodeled/util/tuner/testdata/sm120_correlation_search_fixture_report.yaml \
  /tmp/sm120_correlation_search_fixture_report.yaml

python3 simulator-remodeled/util/tuner/search_sm120_correlation.py \
  --manifest simulator-remodeled/util/tuner/testdata/sm120_correlation_search_fixture.yaml \
  --dry-run \
  --print-planned-commands \
  --command-candidate-limit 2

python3 simulator-remodeled/util/tuner/search_sm120_correlation.py \
  --manifest simulator-remodeled/util/tuner/testdata/sm120_correlation_search_fixture.yaml \
  --output simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/s6-report.yaml \
  --generated-at 2026-06-08T13:56:32Z \
  --fixture-only \
  --emit-planned-commands \
  --command-candidate-limit 2

python3 simulator-remodeled/util/tuner/search_sm120_correlation.py \
  --manifest simulator-remodeled/util/tuner/testdata/sm120_correlation_search_invalid_unknown_key.yaml \
  --dry-run

python3 simulator-remodeled/util/tuner/search_sm120_correlation.py \
  --manifest simulator-remodeled/util/tuner/testdata/sm120_correlation_search_invalid_unbounded.yaml \
  --dry-run

python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only

git diff --check
```

Results:

- Python syntax check passed.
- Synthetic fixture report reproduced byte-for-byte.
- Dry-run and planned-command mode passed; printed plan-only commands with
  `-n`.
- Top-level layered SM120 output negative test failed as expected with
  `refusing to write S6 report into protected config/calibration path`; no
  `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/s6-report.yaml`
  file was created.
- Invalid unknown-key manifest failed with
  `unknown to schema active_option_key_owners`.
- Invalid unbounded-range manifest failed with `range is unbounded; missing stop`.
- `generate_sm120_configs.py --check-only` passed for both generated SM120
  configs.
- `git diff --check` passed.
- `git status --short` showed only new S6 docs, harness, schema contract, and
  testdata files; flat tested configs, S4 generated configs, and
  `generate_sm120_configs.py` were not modified.

## Reviewer Rounds

- Round 1 blank-context reviewer: changes requested.
  - Finding: `--output` protection should cover the whole layered SM120 source
    directory, not only tested-config paths and `latest.yaml`.
  - Finding: malformed/non-mapping `base` manifests should fail with a clean
    `SearchError` rather than a Python attribute error.
  - Rework: expanded protected output fragments to SM120 layered base,
    overlays, profiles, schema, and calibration-results directories; added a
    clean `manifest base must be a mapping` check.
- Round 2 blank-context reviewer: ACCEPT.
  - Verified draft-only report status and `do_not_claim_calibrated: true`.
  - Verified fixture-only sample and synthetic metric wording.
  - Verified bounded candidate count, explicit parameter values, owner/stage
    checks, and negative unknown/unbounded fixtures.
  - Verified no simulator launch path in the harness; planned commands are
    report text only and include `-n`.
  - Verified sample report hashes match the current harness, contract, and
    fixture manifest.
- Supervisor reviewer after Round 2: CHANGES_NEEDED.
  - Finding: Medium. `check_output_target()` still missed the top-level layered
    SM120 source directory; it rejected `.../layered/sm120/schema/s6-report.yaml`
    but allowed `.../layered/sm120/s6-report.yaml`, violating the source-dir
    write ban.
  - Rework: added a protected directory check using normalized paths and
    `Path.relative_to()` for
    `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120`, covering
    the directory root and every child path.
  - Verification: confirmed
    `--output simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/s6-report.yaml`
    exits nonzero with the protected-path error and creates no file.
- Round 3 blank-context reviewer: ACCEPT.
  - Verified the output guard now rejects the entire layered SM120 source tree.
  - Verified the rework touched only the S6 harness and reproducibility report
    hash plus this worker log; flat tested configs, S4 generated configs, and
    `generate_sm120_configs.py` remained untouched.

## Final Status

Complete. Ready for supervisor review.
