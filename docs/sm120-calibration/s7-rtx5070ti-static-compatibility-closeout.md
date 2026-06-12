# S7 RTX5070Ti Static Compatibility Closeout

## Scope

This closeout records a read-only/static RTX5070Ti compatibility check for
checkpoint `c4496000439f2af1e9e3937952071a02581e37f8` before S8.

This is not RTX5070Ti hardware validation, not a simulator validation run, not
RTX5060 promotion approval, and not approval to update accepted/latest configs
or calibration results.

## Alias And Generated Paths

The generated launch alias remains defined in:

```text
simulator-remodeled/util/job_launching/configs/define-standard-cfgs.yml
```

Observed static mapping:

```yaml
RTX5070_TI_SM120_GEN:
    base_file: "$GPGPUSIM_ROOT/configs/generated/tested-cfgs/SM120_RTX5070_TI/gpgpusim.config"
```

The expected generated RTX5070Ti files still exist:

```text
simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated/tested-cfgs/SM120_RTX5070_TI/gpgpusim.config
simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated/tested-cfgs/SM120_RTX5070_TI/config_ampere_islip.icnt
simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated/tested-cfgs/SM120_RTX5070_TI/accelwattch_sass_sim.xml
simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated/tested-cfgs/SM120_RTX5070_TI/manifest.yaml
simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated/tested-cfgs/SM120_RTX5070_TI/manifest.json
simulator-remodeled/gpu-simulator/configs/generated/tested-cfgs/SM120_RTX5070_TI/trace.config
simulator-remodeled/gpu-simulator/configs/generated/tested-cfgs/SM120_RTX5070_TI/manifest.yaml
simulator-remodeled/gpu-simulator/configs/generated/tested-cfgs/SM120_RTX5070_TI/manifest.json
```

The RTX5070Ti generated manifests still select `gpu: RTX5070_TI`,
`config_name: SM120_RTX5070_TI`, `SM120_BASE`, `RTX5070_TI`, and
`calibration-results/RTX5070_TI/bootstrap-current-flat.yaml`.

## Protected Outputs

Static diff/status checks found no S7 changes after checkpoint `c449600` in:

- generated tested-cfgs roots;
- flat SM120 tested-cfgs roots;
- layered SM120 calibration-result roots;
- accepted/latest calibration-result paths;
- tracked promotion artifacts.

The current worktree had an existing uncommitted `supervisor-log.md` change
before this worker started. This closeout did not edit that file.

## Shared-Code Review

Static review covered the S4 generator, layered SM120 base/overlays, generated
manifests, S7 aggregate hardware-target schema/builder, supplied-metrics
manifest builder, and S6 search/report path.

Findings:

- `generate_sm120_configs.py` remains explicitly GPU-parameterized for
  `RTX5070_TI` and `RTX5060`. Reviewer found and this worker fixed one
  metadata-only stale limitation string that previously named RTX5060
  unconditionally in the shared manifest builder.
- `search_sm120_correlation.py` accepts both `RTX5060` and `RTX5070_TI` in
  `GPU_CHOICES` and validates generated base paths from the manifest instead
  of hardcoding an RTX5060 generated path.
- `SM120_BASE.yaml` is common architecture/model metadata and does not embed
  RTX5060-only source paths.
- Per-GPU source paths remain isolated in `overlays/RTX5070_TI.yaml` and
  `overlays/RTX5060.yaml`.
- The new S7 aggregate and supplied-metrics builders are RTX5060 evidence
  builders by invocation and artifact naming, but they write only draft
  non-promotion outputs under ignored `artifacts/s7/` and refuse protected
  config/calibration output paths.
- S7 docs and generated draft artifacts correctly keep
  `rtx5070ti_compatibility_signoff: false` until this static closeout and do
  not claim RTX5070Ti hardware validation.

RTX5060-specific S7 docs/artifacts are acceptable for this stage because they
remain draft/non-promotion evidence and are not wired into shared SM120 base,
generated RTX5070Ti config paths, latest calibration results, or promotion
artifacts.

The checked-in RTX5070Ti generated manifests still contain the older
metadata-only RTX5060 limitation text because this closeout did not regenerate
or edit generated configs. The shared generator has been corrected so the next
allowed generation will emit GPU-specific limitation text. This stale manifest
text is not a behavior redirect and does not change launch alias, config path,
active key inventory, or generated config contents.

## Validation Commands

Read-only/static commands run:

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
git diff --check
git status --short -- simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated simulator-remodeled/gpu-simulator/configs/generated simulator-remodeled/gpu-simulator/gpgpu-sim/configs/tested-cfgs/SM120_RTX5070_TI simulator-remodeled/gpu-simulator/configs/tested-cfgs/SM120_RTX5070_TI simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/calibration-results artifacts
git diff --name-status c449600..HEAD -- simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated simulator-remodeled/gpu-simulator/configs/generated simulator-remodeled/gpu-simulator/gpgpu-sim/configs/tested-cfgs simulator-remodeled/gpu-simulator/configs/tested-cfgs simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/calibration-results artifacts
git diff --name-status c449600..HEAD -- simulator-remodeled/util/tuner simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/base simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/overlays simulator-remodeled/util/job_launching/configs/define-standard-cfgs.yml
python3 -m py_compile simulator-remodeled/util/tuner/generate_sm120_configs.py
```

Results:

- `generate_sm120_configs.py --check-only` passed for
  `SM120_RTX5070_TI` and `SM120_RTX5060`, each with `217` generated
  `gpgpusim.config` keys and `13` generated `trace.config` keys.
- `git diff --check` passed.
- Scoped protected-path status was clean.
- Scoped post-`c449600` protected-path diffs were empty.
- Scoped post-`c449600` shared schema/base/overlay/alias diffs were empty.
- Scoped post-`c449600` shared generator diff is limited to the metadata-only
  limitation-string parameterization noted above.
- `py_compile` passed for the generator after that metadata fix.

No simulator, ProcMan workload, hardware collection, config promotion, or
accepted/latest update command was run.

## Signoff

Static/no-hardware/no-simulator compatibility signoff: accepted.

Boundary:

- RTX5070Ti generated alias and config paths still exist and are not redirected
  by S7 work.
- No S7 accepted/latest/generated config, calibration-result latest, or
  promotion artifact changed RTX5070Ti behavior.
- No RTX5060-only assumption was found in shared `SM120_BASE`, generated
  config selection, schemas, or tuner/report paths used by RTX5070Ti after the
  shared generator metadata fix.

Residual limitations:

- No RTX5070Ti hardware was queried or run.
- No simulator validation was run for RTX5070Ti.
- Existing generated manifests were not regenerated, so they retain a
  metadata-only stale RTX5060 limitation string until a future allowed
  generation/update.
- This does not approve promotion of the narrowed RTX5060 S7 draft ranking.
