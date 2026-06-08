# Worker S4 Generator: SM120 Layered Bootstrap Configs

## Purpose

Implement the S4 MVP for SM120 calibration: layered bootstrap inputs, a
deterministic config generator, generated SM120 bootstrap outputs, validation
for active-key coverage/golden diff/latency drift, generated job-launch aliases,
and documentation.

## Base Commit

- Base commit at worker start: `21853fa204f1cce3bde636705edf9b8e90051974`

## Timestamp

- Start: `2026-06-08 19:54:31 CST +0800`

## Branch / Worktree Status

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch at start: `dev-5060...origin/dev-5060 [ahead 4]`
- Worktree at start: no local modifications reported by `git status --short --branch`.

## Scope

In scope:

- Add MVP layered schema/profile/base/overlay/bootstrap-current-flat inputs for
  `SM120_RTX5070_TI` and `SM120_RTX5060`.
- Add a generator script that emits generated `gpgpusim.config`, `trace.config`,
  `config_ampere_islip.icnt`, `accelwattch_sass_sim.xml`, and manifests.
- Validate active-key owner/profile coverage for current flat
  `gpgpusim.config` and `trace.config` active options.
- Validate bootstrap golden equivalence while ignoring comments/blank lines and
  not adding `-power_simulation_enabled 0`.
- Validate S2 shared latency groups across trace and gpgpusim configs.
- Add generated job-launch aliases while keeping existing aliases unchanged.
- Document generation, validation, compatibility policy, and limitations.

Out of scope:

- No edits to existing flat `tested-cfgs/SM120_*` source configs.
- No full simulator runs.
- No workspace placement or simulation work on `dsp5060`.
- No full tuner search, microbenchmark ingestion, or calibrated SM120 parameter
  replacement.

## Actions

- Read the required supervisor, overall-plan, S2 design, prerequisites, and S1/S2 worker-log documents.
- Inspected current SM120 flat gpgpusim/trace/XML/icnt files and launcher path derivation.
- Added layered MVP source files under the S2-proposed config roots.
- Added `simulator-remodeled/util/tuner/generate_sm120_configs.py`.
- Generated bootstrap outputs for both SM120 GPUs under `configs/generated/tested-cfgs`.
- Added `RTX5060_SM120_GEN` and `RTX5070_TI_SM120_GEN` aliases without changing existing aliases.
- Added `docs/sm120-calibration/s4-config-generator.md`.

## Changed Files

- Added `docs/sm120-calibration/s4-config-generator.md`.
- Added `docs/sm120-calibration/worker-logs/worker-20260608-195431-s4-generator.md`.
- Added layered inputs under:
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/`
  - `simulator-remodeled/gpu-simulator/configs/layered/sm120/`
- Added generated outputs under:
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated/tested-cfgs/SM120_RTX5070_TI/`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated/tested-cfgs/SM120_RTX5060/`
  - `simulator-remodeled/gpu-simulator/configs/generated/tested-cfgs/SM120_RTX5070_TI/`
  - `simulator-remodeled/gpu-simulator/configs/generated/tested-cfgs/SM120_RTX5060/`
- Added `simulator-remodeled/util/tuner/generate_sm120_configs.py`.
- Modified `simulator-remodeled/util/job_launching/configs/define-standard-cfgs.yml` only to add generated aliases.

## Commands / Verification

- Supervisor re-review finding and fix:
  - Finding: `generate_sm120_configs.py` trusted overlay `config_name` as a path component; output safety used unresolved paths/string containment; `source_file_set()` did not verify source paths were inside expected flat source roots.
  - Fix: added `config_name` validation with `^[A-Za-z0-9_][-A-Za-z0-9_]*$` plus single-component/non-absolute/non-`..` checks.
  - Fix: changed output safety to resolve output paths and require each file under the expected generated root for either gpgpu-sim configs or mirrored trace configs.
  - Fix: changed source validation to reject absolute/escaping source paths, require gpgpusim/XML/icnt sources under `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/tested-cfgs`, require trace sources under `simulator-remodeled/gpu-simulator/configs/tested-cfgs`, reject generated roots as sources, and reject unknown/missing source keys.
- `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py`
  - Result: generated both SM120 configs with `gpgpu_keys=217` and `trace_keys=13`.
- `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`
  - Result: passed validation for existing generated outputs.
- `python3 -m py_compile simulator-remodeled/util/tuner/generate_sm120_configs.py`
  - Result: passed.
- `git diff --check`
  - Result: passed.
- Flat SM120 source-config status check:
  - `git status --short -- simulator-remodeled/gpu-simulator/gpgpu-sim/configs/tested-cfgs/SM120_RTX5070_TI simulator-remodeled/gpu-simulator/gpgpu-sim/configs/tested-cfgs/SM120_RTX5060 simulator-remodeled/gpu-simulator/configs/tested-cfgs/SM120_RTX5070_TI simulator-remodeled/gpu-simulator/configs/tested-cfgs/SM120_RTX5060`
  - Result: no modifications reported.
- Generated-output reproducibility check:
  - Recorded SHA256 sums for all generated files.
  - Re-ran `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py`.
  - Recomputed SHA256 sums and diffed them.
  - Result: no differences after rerun from the same input state.
- Active golden equivalence spot check:
  - Current flat and generated `gpgpusim.config` active options match for both GPUs: `217/217`.
  - Current flat and generated `trace.config` active options match for both GPUs: `13/13`.
  - `rg -n -- "-power_simulation_enabled" simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated/tested-cfgs/SM120_RTX5070_TI simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated/tested-cfgs/SM120_RTX5060`
  - Result: no matches; bootstrap did not add `-power_simulation_enabled`.
- Manifest spot check:
  - Generated manifests record commit `21853fa204f1cce3bde636705edf9b8e90051974`.
  - Generated manifests record source files, generator script SHA256, SHA256 input hashes, provenance, active key counts, per-active-key provenance, XML inventory count `339`, XML per-param/stat provenance, and validation results.
- Post-review manifest audit hardening:
  - Added generator script SHA256 to manifest inputs.
  - Added per-active-key owner/source/confidence entries for `gpgpusim.config` and `trace.config`.
  - Added per-XML `param`/`stat` owner/source/confidence inventory entries.
  - Re-ran generation, `--check-only`, Python compile, `git diff --check`, and generated-output reproducibility hash diff.
  - Result: all passed.
- Supervisor rework validation:
  - Re-ran `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py`.
  - Re-ran `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`.
  - Re-ran `python3 -m py_compile simulator-remodeled/util/tuner/generate_sm120_configs.py`.
  - Re-ran `git diff --check`.
  - Re-ran flat SM120 source-config status check; no modifications reported.
  - Re-ran generated-output reproducibility SHA256 diff; no differences after rerun from the same input state.
  - Ran function-level negative path tests without creating temporary files:
    - `output_paths(root, "../bad")` rejected.
    - `output_paths(root, "SM120/BAD")` rejected.
    - `output_paths(root, "/tmp/SM120_BAD")` rejected.
    - `output_paths(root, "SM120\\BAD")` rejected.
    - `output_paths(root, "..")` rejected.
    - `source_file_set(...)` with an escaping `../...` source rejected.
    - `source_file_set(...)` with an absolute source path rejected.
    - `source_file_set(...)` with a generated config source rejected.
    - `source_file_set(...)` with a trace source from the gpgpu flat root rejected.
    - `source_file_set(...)` with an unknown source key rejected.
  - Result: all passed.
- Final supervisor staging finding and fix:
  - Finding: after staging, `git diff --cached --check` reported whitespace errors in generated files because the bootstrap generator copied trailing spaces/tabs/CR from existing flat XML/config/icnt sources.
  - Follow-up staging check also reported extra blank lines at EOF in generated `gpgpusim.config` files.
  - Fix: changed generated text copying to strip trailing spaces, tabs, and CR from each line, drop trailing blank lines at EOF, and write LF newlines.
  - Compatibility: byte identity with flat source files is no longer required; S4 golden checks compare normalized active config lines, XML param/stat inventory, and normalized non-comment icnt content.
  - Re-ran `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py`.
  - Re-ran `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`.
  - Re-ran `python3 -m py_compile simulator-remodeled/util/tuner/generate_sm120_configs.py`.
  - Re-ran generated-output trailing-whitespace scan; no matches reported.
  - Re-ran flat SM120 source-config status check; no modifications reported.
  - Staged S4 files and re-ran `git diff --cached --check`; result: passed.

## Reviewer Rounds

### Round 1

- Reviewer command: `codex exec -C /home/xiewx/accel-0608/modern-gpu-simulator --sandbox read-only --ephemeral ...`
- Reviewer role: blank-context S4 generated-config reviewer; read-only.
- Verdict: ACCEPT.
- Blocking findings: none.
- Reviewer rationale: `--check-only` passes, required generated artifacts are present for both SM120 configs, flat `tested-cfgs/SM120_*` paths are unmodified, and the alias diff only adds generated aliases.

### Round 2

- Reviewer command: `codex exec -C /home/xiewx/accel-0608/modern-gpu-simulator --sandbox read-only --ephemeral ...`
- Reviewer role: narrow blank-context re-review after manifest audit hardening; read-only.
- Verdict: ACCEPT.
- Blocking findings: none.
- Reviewer checks:
  - Generator syntax OK and `--check-only` runs successfully for both SM120 configs: `gpgpu_keys=217`, `trace_keys=13`.
  - All generated gpgpu and trace manifests record `generator.script_sha256`.
  - `input_hashes_sha256` includes the generator script hash, matching the current script SHA.
  - Per-key provenance counts match: 217 `gpgpusim.config`, 13 `trace.config`.
  - XML provenance count matches: 339 param/stat items.
  - Required generated outputs and mirror manifests are present.
  - Flat `tested-cfgs/SM120_*` paths show no git diff.
  - Job alias diff only adds `RTX5060_SM120_GEN` and `RTX5070_TI_SM120_GEN`.

### Round 3

- Reviewer command: `codex exec -C /home/xiewx/accel-0608/modern-gpu-simulator --sandbox read-only --ephemeral ...`
- Reviewer role: blank-context supervisor-rework reviewer for path safety; read-only.
- Verdict: ACCEPT.
- Blocking findings: none.
- Reviewer checks:
  - `config_name` is constrained to one safe path component and rejects separators, absolute paths, and `..`.
  - Output safety resolves paths and verifies every generated output stays under the expected generated gpgpu or trace root.
  - `source_file_set()` enforces repo-relative, non-escaping source paths under the expected existing flat `tested-cfgs` roots and rejects generated roots.
  - Function-level negative checks rejected bad `config_name` values, escaping/absolute/generated/wrong-root source paths, and unknown source keys.
  - `--check-only`, syntax parsing, `git diff --check`, flat SM120 source-config status, and generated manifest spot checks passed.
  - Scope remains limited to S4 docs/layered/generated files, the generator, and generated launcher aliases.

### Round 4

- Reviewer command: `codex exec -C /home/xiewx/accel-0608/modern-gpu-simulator --sandbox read-only --ephemeral ...`
- Reviewer role: blank-context final staging reviewer for generated whitespace normalization.
- Verdict: ACCEPT.
- Blocking findings: none.
- Reviewer checks:
  - `generate_sm120_configs.py --check-only` passed for both `SM120_RTX5070_TI` and `SM120_RTX5060`.
  - AST syntax check passed without writing `__pycache__`.
  - `git diff --cached --check` passed.
  - Generated trailing whitespace/CR/final-LF scan passed.
  - Existing flat `tested-cfgs/SM120_*` status is clean and not staged.
  - Generated config/XML/ICNT files match their flat sources exactly after generator normalization: trailing space/tab/CR stripping, EOF blank-line removal, and LF final newline.
  - Manifest JSON/YAML pairs match, source files point to flat `tested-cfgs` rather than generated directories, and recorded input/script hashes are current.

## Final Status

Ready for supervisor review after Round 4 ACCEPT.
