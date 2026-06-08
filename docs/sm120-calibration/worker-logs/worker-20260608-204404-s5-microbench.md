# Worker S5 Microbenchmark Calibration MVP

## Purpose

Implement the S5 MVP for SM120 staged microbenchmark calibration: a minimal
result schema, stage model, parser/collector draft generator, small fixtures,
documentation, and clean S4 handoff without claiming RTX 5060 calibration.

## Base Commit

- Base commit at worker start: `c0660f6a736854e81724ddbb9ffa27ce17834e13`

## Timestamp

- Start: `2026-06-08 20:44:04 CST +0800`

## Branch / Worktree Status

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch at start: `dev-5060...origin/dev-5060 [ahead 5]`
- Worktree at start: no local modifications reported by `git status --short`.

## Scope

In scope:

- Define staged microbenchmark calibration phases and provenance requirements.
- Add a machine-readable calibration-result schema/manifest contract.
- Add a lightweight parser that extracts tuner config lines from
  `GPU_Microbenchmark/run_all.sh` or single-microbenchmark output.
- Generate a YAML draft with supported keys, unsupported keys, duplicate/conflict
  reporting, source metadata, and `draft_not_applied` status.
- Add small synthetic fixtures and local verification commands.
- Document collection-only usage on `dsp5060` and local parsing handoff.

Out of scope:

- No full simulator runs.
- No large GPU benchmark runs.
- No workspace placement on `dsp5060`.
- No edits to current flat SM120 `tested-cfgs`.
- No automatic S4 generator consumption of S5 results.
- No claim that RTX 5060 microbenchmark calibration is complete.

## Actions

- Read the required supervisor, overall plan, S2 layering design, S3
  prerequisites, S4 generator docs, and S4 worker log.
- Inspected the existing S4 layered schema and generator owner model.
- Inspected tuner `run_all.sh`, legacy `tuner.py`, and sample
  `GPU_Microbenchmark/output.file` output format.
- Added `parse_sm120_microbench.py` to parse config-style lines, assign S5
  stages, apply S4 owners, record unsupported keys, and emit result YAML drafts.
- Added a calibration-result schema/manifest contract under layered SM120
  schema files.
- Added synthetic microbenchmark and system-config/config-line fixtures.
- Added a synthetic sample result draft under `calibration-results/samples/`.
- Added S5 documentation with stage boundaries, parser use, `dsp5060`
  collection-only flow, and S4 handoff.
- Added a short S5 handoff note to the S4 generator documentation.

## Changed Files

- Added `docs/sm120-calibration/s5-microbenchmark-calibration.md`.
- Added `docs/sm120-calibration/worker-logs/worker-20260608-204404-s5-microbench.md`.
- Modified `docs/sm120-calibration/s4-config-generator.md`.
- Added `simulator-remodeled/util/tuner/parse_sm120_microbench.py`.
- Added `simulator-remodeled/util/tuner/testdata/sm120_microbench_sample.txt`.
- Added `simulator-remodeled/util/tuner/testdata/sm120_system_config_sample.txt`.
- Added `simulator-remodeled/util/tuner/testdata/sm120_human_devicequery_sample.txt`
  as a negative fixture for unsupported human-readable deviceQuery text.
- Added `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema/calibration-result.schema.yaml`.
- Added `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/calibration-results/samples/RTX5060-microbench-draft.yaml`.

## Commands / Verification

- `python3 -m py_compile simulator-remodeled/util/tuner/parse_sm120_microbench.py`
  - Result: passed.
- `python3 simulator-remodeled/util/tuner/parse_sm120_microbench.py --input simulator-remodeled/util/tuner/testdata/sm120_microbench_sample.txt --output /tmp/RTX5060-microbench-draft.yaml --gpu RTX5060 --source-type microbenchmark --source-label sm120_microbench_sample --collection-host local-fixture --collection-command 'synthetic fixture, no GPU run' --calibration-id RTX5060-synthetic-sm120-microbench-draft --generated-at 2026-06-08T12:00:00Z --fixture-only`
  - Result: parsed 12 config lines, 11 supported lines, 1 unsupported line, and
    11 draft delta keys.
  - Unsupported key evidence: `-gpgpu_l1_latency` recorded under
    `unsupported_keys.gpgpusim.config` with reason
    `key_not_in_s5_supported_stage_map`.
- `python3 simulator-remodeled/util/tuner/parse_sm120_microbench.py --input simulator-remodeled/util/tuner/testdata/sm120_system_config_sample.txt --output /tmp/RTX5060-system-config-draft.yaml --gpu RTX5060 --source-type system_config --source-label sm120_system_config_sample --collection-host local-fixture --collection-command 'synthetic fixture, no GPU run' --calibration-id RTX5060-synthetic-sm120-system-config-draft --generated-at 2026-06-08T12:00:00Z --fixture-only`
  - Result: parsed 4 config lines, all supported, and generated 4 draft delta keys.
  - Result: `handoff.do_not_claim_calibrated` is `true`.
- Empty input / human-readable deviceQuery negative checks:
  - `python3 simulator-remodeled/util/tuner/parse_sm120_microbench.py --input <empty-temp-file> --output /tmp/should-not-exist-empty.yaml --gpu RTX5060 --source-type microbenchmark`
  - Result: exited nonzero with `error: no config-style calibration lines found...`.
  - `python3 simulator-remodeled/util/tuner/parse_sm120_microbench.py --input simulator-remodeled/util/tuner/testdata/sm120_human_devicequery_sample.txt --output /tmp/should-not-exist-human.yaml --gpu RTX5060 --source-type system_config`
  - Result: exited nonzero with the same no-config-line error.
- `python3 simulator-remodeled/util/tuner/parse_sm120_microbench.py --input simulator-remodeled/util/tuner/testdata/sm120_microbench_sample.txt --output /tmp/RTX5060-microbench-draft.yaml --gpu RTX5060 --source-type microbenchmark --fail-on-unsupported`
  - Result: exited with status `2`, as expected for unsupported parsed keys.
- `python3 simulator-remodeled/util/tuner/parse_sm120_microbench.py --input simulator-remodeled/util/tuner/testdata/sm120_microbench_sample.txt --output /tmp/RTX5060-microbench-draft-regenerated.yaml --gpu RTX5060 --source-type microbenchmark --source-label sm120_microbench_sample --collection-host local-fixture --collection-command 'synthetic fixture, no GPU run' --calibration-id RTX5060-synthetic-sm120-microbench-draft --generated-at 2026-06-08T12:00:00Z --fixture-only && cmp /tmp/RTX5060-microbench-draft-regenerated.yaml simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/calibration-results/samples/RTX5060-microbench-draft.yaml`
  - Result: passed; checked-in sample draft is reproducible from the parser and
    fixture with fixed metadata.
- `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`
  - Result: passed for `SM120_RTX5070_TI` and `SM120_RTX5060`; S4 bootstrap
    generated outputs remain valid.
- `git diff --check`
  - Result: passed.
- Flat/generated SM120 config status check:
  - `git status --short -- simulator-remodeled/gpu-simulator/gpgpu-sim/configs/tested-cfgs/SM120_RTX5070_TI simulator-remodeled/gpu-simulator/gpgpu-sim/configs/tested-cfgs/SM120_RTX5060 simulator-remodeled/gpu-simulator/configs/tested-cfgs/SM120_RTX5070_TI simulator-remodeled/gpu-simulator/configs/tested-cfgs/SM120_RTX5060 simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated/tested-cfgs simulator-remodeled/gpu-simulator/configs/generated/tested-cfgs`
  - Result: no modifications reported.

Supervisor rework verification:

- `python3 -m py_compile simulator-remodeled/util/tuner/parse_sm120_microbench.py`
  - Result: passed; removed generated `__pycache__` afterward.
- `python3 simulator-remodeled/util/tuner/parse_sm120_microbench.py --input simulator-remodeled/util/tuner/testdata/sm120_microbench_sample.txt --output /tmp/RTX5060-microbench-draft-regenerated.yaml --gpu RTX5060 --source-type microbenchmark --source-label sm120_microbench_sample --collection-host local-fixture --collection-command 'synthetic fixture, no GPU run' --calibration-id RTX5060-synthetic-sm120-microbench-draft --generated-at 2026-06-08T12:00:00Z --fixture-only && cmp /tmp/RTX5060-microbench-draft-regenerated.yaml simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/calibration-results/samples/RTX5060-microbench-draft.yaml`
  - Result: passed; sample draft remains reproducible.
- `python3 simulator-remodeled/util/tuner/parse_sm120_microbench.py --input simulator-remodeled/util/tuner/testdata/sm120_system_config_sample.txt --output /tmp/RTX5060-system-config-draft.yaml --gpu RTX5060 --source-type system_config --source-label sm120_system_config_sample --collection-host local-fixture --collection-command 'synthetic fixture, no GPU run' --calibration-id RTX5060-synthetic-sm120-system-config-draft --generated-at 2026-06-08T12:00:00Z --fixture-only`
  - Result: parsed 4 config lines, all supported, and generated 4 draft delta
    keys with `handoff.do_not_claim_calibrated: true`.
- `python3 simulator-remodeled/util/tuner/parse_sm120_microbench.py --input simulator-remodeled/util/tuner/testdata/sm120_human_devicequery_sample.txt --output /tmp/should-not-exist-human.yaml --gpu RTX5060 --source-type system_config`
  - Result: exited with status `1` and
    `error: no config-style calibration lines found...`.
- `python3 simulator-remodeled/util/tuner/parse_sm120_microbench.py --input <empty-temp-file> --output /tmp/should-not-exist-empty.yaml --gpu RTX5060 --source-type microbenchmark`
  - Result: exited with status `1` and the same no-config-line error.
- `python3 simulator-remodeled/util/tuner/parse_sm120_microbench.py --input simulator-remodeled/util/tuner/testdata/sm120_microbench_sample.txt --output /tmp/RTX5060-microbench-draft.yaml --gpu RTX5060 --source-type microbenchmark --fail-on-unsupported`
  - Result: exited with status `2`.
- `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`
  - Result: passed for both SM120 generated bootstrap configs.
- `git diff --check`
  - Result: passed.
- Flat/generated SM120 config status check:
  - Result: no modifications reported.

## Reviewer Rounds

### Round 1

- Reviewer command: `codex exec -C /home/xiewx/accel-0608/modern-gpu-simulator --sandbox read-only --ephemeral ...`
- Reviewer role: blank-context S5 MVP reviewer; read-only.
- Verdict: ACCEPT.
- Blocking findings: none.
- Reviewer checks:
  - Reviewed uncommitted file set with `git status`, `git diff --stat`, and
    targeted `git diff`.
  - Confirmed no uncommitted edits to flat SM120 tested configs, layered
    base/overlay/profile/bootstrap calibration configs, or
    `generate_sm120_configs.py`.
  - Read the S5 docs, worker log, parser, schema, fixtures, and sample draft.
  - Regenerated the sample draft to stdout and diffed it against the checked-in
    sample; exact match.
  - Parsed YAML for the schema and sample result successfully.
  - Syntax-checked the parser via `ast.parse`.
  - Searched for calibration-complete or real RTX5060 claims and found explicit
    `draft_not_applied`, `fixture_only`, and not-completed-calibration language.
- Nonblocking risks:
  - The schema is a manifest contract, not an enforcing JSON Schema-style validator.
  - The parser stage map is static and MVP-sized; future real outputs may need
    more key coverage and source-type/stage validation.

### Supervisor Review Rework

- Supervisor reviewer verdict: CHANGES_NEEDED.
- Finding 1, High: `device_query` scope was overstated. The parser only handles
  config-style lines, while CLI/docs/fixture naming implied support for raw
  `nvidia-smi` or human-readable CUDA runtime/deviceQuery output.
  - Fix: narrowed parser source types to `microbenchmark` and `system_config`.
  - Fix: renamed the config-line fixture to
    `sm120_system_config_sample.txt`.
  - Fix: added `sm120_human_devicequery_sample.txt` as a negative fixture and
    made zero config-line parses fail with a clear error.
  - Fix: updated docs/schema to state raw `nvidia-smi` and human-readable
    CUDA `deviceQuery` text are unsupported by the S5 MVP parser.
- Finding 2, Medium: non-fixture `device_query` drafts could set
  `handoff.do_not_claim_calibrated: false`.
  - Fix: `handoff.do_not_claim_calibrated` is now always `true` for raw parser
    output regardless of source type.
- Finding 3, Low: docs said the sample unsupported key was unsupported because
  S4 did not own it, while the actual reason was the S5 stage map.
  - Fix: docs now say `-gpgpu_l1_latency` is unsupported because the S5 MVP
    stage map intentionally does not support that legacy tuner key yet.

### Round 2

- Reviewer command: `codex exec -C /home/xiewx/accel-0608/modern-gpu-simulator --sandbox read-only --ephemeral ...`
- Reviewer role: blank-context S5 supervisor-rework reviewer; read-only.
- Verdict: CHANGES-NEEDED.
- Blocking finding:
  - `docs/sm120-calibration/s5-microbenchmark-calibration.md` S4 handoff step 1
    still said to collect "device-query output" and then parse locally, which
    could imply raw CUDA `deviceQuery` support.
- Fix:
  - Changed the handoff to say "microbenchmark output or tuner `system_config`
    config-line output"; reviewed official facts must be converted to
    config-style lines before parsing.
- Reviewer also confirmed:
  - Parser source types are only `microbenchmark` and `system_config`.
  - Empty stdin and human-readable deviceQuery fixture both exit nonzero with no
    YAML draft.
  - Raw parser drafts keep `handoff.do_not_claim_calibrated: true`.
  - Unsupported sample reason is `key_not_in_s5_supported_stage_map`.
  - No flat SM120 tested configs, S4 generated configs, or
    `generate_sm120_configs.py` consumption logic are modified.

### Round 3

- Reviewer command: `codex exec -C /home/xiewx/accel-0608/modern-gpu-simulator --sandbox read-only --ephemeral ...`
- Reviewer role: blank-context S5 supervisor-rework Round 3 reviewer; read-only.
- Verdict: ACCEPT.
- Blocking findings: none.
- Reviewer verified:
  - Round 2 wording is fixed: S4 handoff now says real microbenchmark output or
    tuner `system_config` config-line output, with official facts converted to
    config-style lines before parsing.
  - Parser source types are limited to `microbenchmark` and `system_config`.
  - Raw human-readable `deviceQuery` and empty input exit nonzero before YAML output.
  - Raw parser drafts always set `handoff.do_not_claim_calibrated: true`.
  - Unsupported sample reason is `key_not_in_s5_supported_stage_map`.
  - No uncommitted changes are reported for flat SM120 tested configs, S4
    generated configs, or `generate_sm120_configs.py`; generator diff is empty.

## Final Status

Ready for supervisor review after Round 3 ACCEPT.
