# SM120 S4 Bootstrap Config Generator

## Purpose

S4 adds a minimal layered-input generator for SM120 bootstrap configs. It keeps
the existing flat `tested-cfgs/SM120_*` directories unchanged and emits
parallel generated outputs under `configs/generated/tested-cfgs`.

The MVP is intentionally conservative: it copies today's flat SM120 config
content, validates active-key owner coverage and cross-file latency groups, and
records provenance in manifests. It does not run the simulator and does not
claim new calibration results.

## Generate

From the repository root:

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py
```

This generates both:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated/tested-cfgs/SM120_RTX5070_TI/`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated/tested-cfgs/SM120_RTX5060/`
- `simulator-remodeled/gpu-simulator/configs/generated/tested-cfgs/SM120_RTX5070_TI/`
- `simulator-remodeled/gpu-simulator/configs/generated/tested-cfgs/SM120_RTX5060/`

Each generated GPGPU-Sim directory contains:

- `gpgpusim.config`
- `config_ampere_islip.icnt`
- `accelwattch_sass_sim.xml`
- `manifest.yaml`
- `manifest.json`

Each mirrored trace directory contains:

- `trace.config`
- `manifest.yaml`
- `manifest.json`

Generate a single GPU if needed:

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --gpu RTX5060
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --gpu RTX5070_TI
```

## Validate

Validate existing generated outputs without rewriting them:

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
```

The generator fails if:

- A current active `gpgpusim.config` or `trace.config` option lacks exactly one
  schema owner.
- An owner is not allowed for the selected profile.
- Generated active `gpgpusim.config` or `trace.config` lines differ from the
  current flat bootstrap source after ignoring comments and blank lines.
- Generated AccelWattch `param`/`stat` inventories differ from the current flat
  XML.
- Generated `.icnt` non-comment content differs from the current flat `.icnt`.
- The branch, half, uniform, predicate, miscellaneous queue, or miscellaneous
  no-queue latency/initiation groups drift between `gpgpusim.config` and
  `trace.config`.
- The bootstrap profile adds `-power_simulation_enabled`.

## Layered Inputs

MVP layered input files live under:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema/`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/profiles/`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/base/`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/overlays/`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/calibration-results/`
- `simulator-remodeled/gpu-simulator/configs/layered/sm120/`

`schema/sm120.schema.yaml` owns the active-key coverage table and the canonical
latency groups. Per-GPU overlays point at the current flat bootstrap source
files. `bootstrap-current-flat.yaml` records that copied values are placeholder
or inherited bootstrap data, not calibrated values.

## Job Launching

Generated aliases are available without changing the existing aliases:

- `RTX5060_SM120_GEN`
- `RTX5070_TI_SM120_GEN`

The existing `RTX5060` and `RTX5070_TI` aliases still point to the flat
`configs/tested-cfgs` paths. Job-launching `extra_params` appended on top of
generated configs are outside the generated manifest and must be treated as
`unmanifested_override` runs.

## Limitations

- The MVP is bootstrap-equivalence only. It does not implement full tuner
  parsing, microbenchmark ingestion, or correlation search.
- RTX5060 timing, memory, trace, and power values are still inherited or
  placeholder values until later calibration stages replace them.
- AccelWattch XML is copied for compatibility. Do not treat RTX5060 power as
  calibrated.
- The `.icnt` file is copied for directory completeness. Current SM120
  bootstrap configs use `-network_mode 2` local xbar, so inline `-icnt_*`
  options are the active interconnect settings.
