# SM120 S5 Staged Microbenchmark Calibration MVP

## Purpose

S5 adds the smallest runnable framework for staged SM120 microbenchmark
calibration. The MVP parses tuner `GPU_Microbenchmark/run_all.sh` output or a
single microbenchmark output file, records provenance, and emits a
calibration-result YAML draft.

This is not a completed RTX 5060 calibration. Parser output remains
`draft_not_applied` until real GPU collection is reviewed and copied into a
`latest.yaml` or staged delta file.

## Stage Model

| Stage | Input | Output | Candidate keys | Provenance |
| --- | --- | --- | --- | --- |
| `official_device_query_facts` | Tuner `system_config` output, or official facts already converted to config-style lines | Candidate `SM120_BASE` or per-GPU overlay facts | Compute capability, SM count, clock domains, register/shared-memory limits | `source_type: system_config` preferred; record host, command, input SHA256, benchmark, line |
| `system_core_config_microbench` | Tuner `core_config`, `config_int`, `config_fpu`, `config_dpu`, `config_sfu`, `config_tensor` output | Candidate SM120 common facts or calibration-result opcode deltas | Unit counts, issue widths, `-ptx_opcode_*`, tensor keys | `source_type: microbenchmark`; record input SHA256, benchmark, line |
| `memory_l2_l1_config_microbench` | Tuner L1/L2/memory/shared-memory config output | Candidate GPU overlay facts or calibration-result memory/cache deltas | `-gpgpu_cache:dl1`, `-gpgpu_cache:dl2`, banks, memory partitions, DRAM timing | `source_type: microbenchmark` or `system_config`; record input SHA256, benchmark, line |
| `trace_latency_groups` | Tuner trace latency/initiation lines or reviewed trace measurements | Candidate `trace.config` calibration-result deltas | `-trace_opcode_latency_initiation_*`, specialized trace groups | `source_type: microbenchmark`; record input SHA256, benchmark, line |
| `rf_prefetch_remodeled_parameters` | Future focused microbenchmarks or S6 targeted search | Candidate calibration-result deltas for remodeled parameters | RF, instruction prefetch, L0I timing, PRT/interwarp/scheduler knobs | S5 records the manifest shape; most keys remain future work |
| `power_placeholder` | None in S5 MVP | No delta | None | Power remains disabled or smoke-compatibility only |

The complete machine-readable stage contract lives in:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema/calibration-result.schema.yaml`

## Parser

Script:

```bash
python3 simulator-remodeled/util/tuner/parse_sm120_microbench.py --help
```

Parse a small local fixture:

```bash
python3 simulator-remodeled/util/tuner/parse_sm120_microbench.py \
  --input simulator-remodeled/util/tuner/testdata/sm120_microbench_sample.txt \
  --output /tmp/RTX5060-microbench-draft.yaml \
  --gpu RTX5060 \
  --source-type microbenchmark \
  --source-label sm120_microbench_sample \
  --collection-host local-fixture \
  --collection-command 'synthetic fixture, no GPU run' \
  --fixture-only
```

The parser:

- Extracts config lines beginning with known S4 keys or calibration-style
  prefixes such as `-gpgpu_`, `-trace_`, `-ptx_`, `-dram_`, and remodeled
  parameter prefixes.
- Assigns each supported key to an S5 stage and S4 owner using
  `schema/sm120.schema.yaml`.
- Emits `derived_delta.files.gpgpusim.config` and
  `derived_delta.files.trace.config` entries with `status: draft_not_applied`.
- Records unsupported parsed keys under `unsupported_keys` with line number and
  reason.
- Withholds conflicting duplicate keys from the derived delta and records the
  conflict in `duplicate_keys`.
- Fails instead of emitting an empty draft when no config-style lines are found.

Supported parser source types are `microbenchmark` and `system_config`.
Raw `nvidia-smi` output and human-readable CUDA `deviceQuery` text are not
parsed by this MVP; convert official facts into reviewed config-style lines
before using this parser.

## Sample Fixture

The checked-in sample output is synthetic and intentionally small:

- `simulator-remodeled/util/tuner/testdata/sm120_microbench_sample.txt`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/calibration-results/samples/RTX5060-microbench-draft.yaml`

The sample draft includes one unsupported key, `-gpgpu_l1_latency`, because the
S5 MVP stage map intentionally does not support that legacy tuner key yet. This
proves the unsupported-key path without claiming any real RTX 5060 measurement.

## dsp5060 Collection-Only Workflow

Do not place the main workspace on `dsp5060`. Use the GPU host only to build or
run the microbenchmarks and bring back a compact output file.

One conservative flow is:

```bash
# From local machine, copy only the tuner subtree or a minimal tarball.
cd /home/xiewx/accel-0608/modern-gpu-simulator
tar --exclude 'bin' --exclude '*.o' -czf /tmp/sm120-tuner-src.tgz \
  -C simulator-remodeled/util/tuner GPU_Microbenchmark
scp /tmp/sm120-tuner-src.tgz dsp5060:/tmp/

# On dsp5060, use a temporary directory and run only tuner collection.
ssh dsp5060 '
  set -e
  rm -rf /tmp/sm120-tuner-collection
  mkdir -p /tmp/sm120-tuner-collection
  tar -xzf /tmp/sm120-tuner-src.tgz -C /tmp/sm120-tuner-collection
  cd /tmp/sm120-tuner-collection/GPU_Microbenchmark
  make CUDA_PATH=/usr/local/cuda-13.2 CUDA_ARCH=sm_120 HW_DEF=SM120_RTX5060
  ./run_all.sh > sm120-rtx5060-microbench.txt 2>&1
'

# Bring back only the compact text output, then parse locally.
scp dsp5060:/tmp/sm120-tuner-collection/GPU_Microbenchmark/sm120-rtx5060-microbench.txt \
  /home/xiewx/accel-0608/modern-gpu-simulator/simulator-remodeled/util/tuner/

python3 simulator-remodeled/util/tuner/parse_sm120_microbench.py \
  --input simulator-remodeled/util/tuner/sm120-rtx5060-microbench.txt \
  --output /tmp/RTX5060-real-microbench-draft.yaml \
  --gpu RTX5060 \
  --source-type microbenchmark \
  --source-label dsp5060-run-all \
  --collection-host dsp5060 \
  --collection-command './run_all.sh > sm120-rtx5060-microbench.txt 2>&1'
```

If CUDA 13.2 is not installed on `dsp5060`, select the installed CUDA path only
after checking that it supports `sm_120`. S5 did not run this full collection.

To collect only system facts in config-line form, run the tuner `system_config`
binary on the GPU host and parse that output as `--source-type system_config`.
Do not feed raw `nvidia-smi` or human-readable `deviceQuery` text to this parser;
zero config-line inputs fail intentionally.

## S4 Handoff

S4 remains `bootstrap-current-flat`. Its generator emits configs from layered
bootstrap inputs and does not automatically consume S5 parser output.

Clean handoff for future work:

1. Collect real microbenchmark output or tuner `system_config` config-line output
   on the GPU host. Reviewed official facts must be converted to config-style
   lines before parsing.
2. Parse locally into a draft YAML with this S5 script.
3. Review unsupported keys, duplicate conflicts, owner assignments, and stage
   provenance.
4. Copy only accepted owner-matched `calibration_result` entries into
   `calibration-results/<GPU>/latest.yaml` or a staged delta file.
5. Copy accepted `gpu_overlay` or `sm120_base` facts only when their ownership
   matches `schema/sm120.schema.yaml`.
6. Extend the S4 generator later with an explicit `--calibration-result` input
   after the accepted result-file contract stabilizes.

Do not overwrite existing flat SM120 configs or generated S4 outputs with raw
parser output.
