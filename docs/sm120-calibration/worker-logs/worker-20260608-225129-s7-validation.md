# S7 Validation Runbook Worker Log

## Purpose

Design and implement the S7 first-step RTX5060 validation/calibration runbook
MVP for the SM120 calibration flow.

## Base

- Repository: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Base commit: `e37d55a8c7c7` (`feat: add bounded SM120 correlation search`)
- Timestamp: `2026-06-08 22:51:29 CST`
- Working tree at start: clean relative to S7 files; S7 worker added new
  documentation and one lightweight helper. `git add -N` was used only so
  `git diff --check` included newly added files.

## Assigned Scope

- Add a concrete S7 RTX5060 validation/calibration runbook.
- Add a lightweight manifest/checklist template if useful.
- Optionally add a dry-run helper that verifies S3/S5/S6 tools and prints
  commands without running hardware collection or simulator workloads.
- Do not run full simulation.
- Do not run work on `dsp5060`.
- Do not put the main workspace on `dsp5060`.
- Do not write accepted configs or `latest.yaml`.

## Actions

- Read S0-S6 supervisor and stage documents, including S5 parser and S6
  correlation-search handoff constraints.
- Read S3 official-tool collector, S5 parser, S6 search harness, S4 generator,
  SM120 generated aliases, tuner makefiles, and job-launching command behavior.
- Added a runbook that separates:
  - `dsp5060` hardware characterization and tuner microbenchmark calibration
    output;
  - local S5 draft parsing;
  - local bounded S6 parameter sweep and correlation/validation;
  - local strong-server smoke test planning and launch commands;
  - RTX5070Ti compatibility checks that do not require RTX5070Ti hardware;
  - manual promotion gate from draft to reviewed staged delta/latest.
- Added a manifest template with required artifacts and pass/fail fields.
- Added a dry-run checker/command planner that validates S3/S5/S6/S4 files and
  generated SM120 aliases, then prints host-separated command plans.
- Updated `.gitignore` so `artifacts/s7/` raw evidence and logs are not
  accidentally committed.

## Changed Files

- `.gitignore`
- `docs/sm120-calibration/s7-validation-runbook.md`
- `docs/sm120-calibration/s7-validation-manifest-template.yaml`
- `simulator-remodeled/util/tuner/check_sm120_s7_validation.py`
- `docs/sm120-calibration/worker-logs/worker-20260608-225129-s7-validation.md`

## Verification

Commands run from `/home/xiewx/accel-0608/modern-gpu-simulator`:

```bash
python3 -m py_compile simulator-remodeled/util/tuner/check_sm120_s7_validation.py
```

Result: pass.

```bash
python3 simulator-remodeled/util/tuner/check_sm120_s7_validation.py \
  --gpu RTX5060 \
  --run-id test-run \
  --no-command-plan
```

Result: pass. Verified RTX5060 generated alias and generated config/trace
directories.

```bash
python3 simulator-remodeled/util/tuner/check_sm120_s7_validation.py \
  --gpu RTX5070_TI \
  --run-id test-compat \
  --no-command-plan
```

Result: pass. Verified RTX5070Ti generated alias and generated config/trace
directories without requiring hardware.

```bash
python3 simulator-remodeled/util/tuner/check_sm120_s7_validation.py \
  --gpu RTX5060 \
  --run-id test-run
```

Result: pass. Printed plan-only commands, including `dsp5060` collection-only
commands and local smoke setup/run commands. No commands from the printed plan
were executed.

```bash
python3 simulator-remodeled/util/tuner/check_sm120_s7_validation.py \
  --gpu RTX5070_TI \
  --run-id test-compat
```

Result: pass after rework. Default RTX5070Ti output prints config/alias
compatibility and does not print hardware collection commands unless
`--include-hardware-plan` is explicitly provided.

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
```

Result: pass. Output:

```text
generated SM120_RTX5070_TI profile=bootstrap gpgpu_keys=217 trace_keys=13
generated SM120_RTX5060 profile=bootstrap gpgpu_keys=217 trace_keys=13
```

```bash
python3 simulator-remodeled/util/tuner/search_sm120_correlation.py \
  --manifest simulator-remodeled/util/tuner/testdata/sm120_correlation_search_fixture.yaml \
  --dry-run \
  --print-planned-commands \
  --command-candidate-limit 2
```

Result: pass. Fixture dry-run validated four synthetic candidates and printed
plan-only `run_simulations.py ... -n` commands. The fixture is documented as not
real calibration evidence.

```bash
python3 - <<'PY'
from pathlib import Path
import yaml
path = Path('docs/sm120-calibration/s7-validation-manifest-template.yaml')
data = yaml.safe_load(path.read_text())
assert isinstance(data, dict)
assert data['schema_id'] == 'sm120_s7_validation_manifest_template_v1'
print('manifest template parsed')
PY
```

Result: pass.

```bash
python3 - <<'PY'
from pathlib import Path
text = Path('docs/sm120-calibration/s7-validation-runbook.md').read_text()
terms = [
    'hardware characterization',
    'microbenchmark calibration',
    'parameter sweep',
    'correlation/validation',
    'smoke test',
    'promotion gate',
]
missing = [term for term in terms if term not in text]
if missing:
    raise SystemExit('missing terms: ' + ', '.join(missing))
print('standard terms present')
PY
```

Result: pass.

```bash
git add -N docs/sm120-calibration/s7-validation-runbook.md \
  docs/sm120-calibration/s7-validation-manifest-template.yaml \
  simulator-remodeled/util/tuner/check_sm120_s7_validation.py
git diff --check
```

Result: pass. `git add -N` was used only to include new files in the whitespace
check.

## Reviewer Rounds

### Round 1

Reviewer stance: blank-context S7 validation reviewer.

Verdict: CHANGES NEEDED.

Finding:
- `check_sm120_s7_validation.py --gpu RTX5070_TI` printed hardware collection
  and S5 parse plans by default, using the default `dsp5060` host. That blurred
  the runbook requirement that RTX5070Ti compatibility checks do not require
  RTX5070Ti hardware unless explicitly available.

Fix:
- Added `--include-hardware-plan`.
- Changed non-RTX5060 default planning to print config/alias compatibility and
  an explicit note that hardware collection is skipped unless matching hardware
  is available.
- Updated the runbook to mention `--include-hardware-plan` for optional
  RTX5070Ti hardware runs.

### Round 2

Reviewer stance: fresh blank-context S7 validation reviewer.

Verdict: ACCEPT.

Acceptance rationale:
- Runbook uses required terms and gives concrete commands.
- Host boundaries are explicit: `dsp5060` is collection-only; local strong
  server owns smoke/correlation simulator work.
- Fixture/sample outputs are repeatedly excluded from real calibration.
- Promotion gate is manual and forbids auto-applying draft output or accepted
  config writes.
- SM120 common model vs per-GPU parameter boundary is preserved.
- Helper script is dry-run by design and passed syntax/dry-run tests.
- Required `generate_sm120_configs.py --check-only` and `git diff --check`
  passed.

## Final Status

ACCEPT.

No hardware collection, full simulator runs, or accepted config writes were
performed.
