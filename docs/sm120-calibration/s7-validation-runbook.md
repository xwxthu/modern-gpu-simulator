# SM120 S7 RTX5060 Validation And Calibration Runbook MVP

## Purpose

S7 validates the RTX5060 path without turning the simulator into an
RTX5060-only model. The boundary remains:

- `SM120_BASE`: common SM120 architecture modeling and simulator policy.
- Per-GPU overlays: official SKU/device facts such as SM count, clocks, memory
  geometry, and limits.
- Calibration results: timing, cache, memory, scheduler, register-file,
  prefetch, PRT, trace, and correlation-tuned values.

This runbook is the first S7 MVP. It describes hardware characterization,
microbenchmark calibration, bounded parameter sweep, correlation/validation,
smoke test, RTX5070Ti compatibility checks, and the promotion gate. It does not
claim a final RTX5060 calibration.

## Hard Rules

- Use `dsp5060` only for RTX5060 hardware characterization and tuner
  microbenchmark calibration output.
- Do not run full simulator workloads on `dsp5060`.
- Do not place the main workspace on `dsp5060`; copy only the minimal tuner
  source bundle to `/tmp`.
- Do not treat fixture/sample output as real calibration evidence.
- Do not auto-apply parser or correlation-search output to flat tested configs,
  generated configs, staged deltas, or `latest.yaml`.
- Run simulator smoke tests and correlation runs only on the local strong
  server after the `-n` setup-only plan is reviewed.

## Artifact Manifest

Copy the template before starting an official run:

```bash
cd /home/xiewx/accel-0608/modern-gpu-simulator
RUN_ID=rtx5060-s7-$(date +%Y%m%d-%H%M%S)
mkdir -p artifacts/s7/$RUN_ID
cp docs/sm120-calibration/s7-validation-manifest-template.yaml \
  artifacts/s7/$RUN_ID/validation-manifest.yaml
```

`artifacts/s7/` is intentionally not an accepted config location. Keep the
manifest as the run ledger: artifact paths, SHA256 values, pass/fail fields,
review notes, and residual risks.

## Dry-Run Planner

The helper below checks that S3/S5/S6 tools, generated SM120 configs, and job
aliases exist. It prints commands but does not connect to `dsp5060`, run
microbenchmarks, launch simulator jobs, or write accepted configs.

```bash
cd /home/xiewx/accel-0608/modern-gpu-simulator
python3 simulator-remodeled/util/tuner/check_sm120_s7_validation.py \
  --gpu RTX5060 \
  --run-id $RUN_ID
```

Use its output as a checklist, not as an unattended script.

## Step 1: Local Readiness

Run these on the local strong server:

```bash
cd /home/xiewx/accel-0608/modern-gpu-simulator
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only

python3 simulator-remodeled/util/tuner/search_sm120_correlation.py \
  --manifest simulator-remodeled/util/tuner/testdata/sm120_correlation_search_fixture.yaml \
  --dry-run \
  --print-planned-commands \
  --command-candidate-limit 2
```

The S6 fixture command is only a harness check. Its metrics are synthetic and
must never be used as RTX5060 calibration data.

## Step 2: RTX5060 Hardware Characterization On dsp5060

Run from the local workspace. The collector executes lightweight official-tool
queries through ssh and stores the output locally:

```bash
cd /home/xiewx/accel-0608/modern-gpu-simulator
python3 simulator-remodeled/util/hw_stats/collect_sm120_device_info.py \
  --remote dsp5060 \
  --device 0
```

Record the output directory in the S7 manifest. Required review points:

- GPU name, UUID, driver, compute capability, clocks, memory totals, and tool
  versions are present or explicitly marked unavailable.
- Any `nvidia-smi` or Nsight query failures are recorded with return codes.
- Clock fields are observed state, not controlled calibration clocks, unless a
  separate clock-locking policy is recorded.

Optional metric discovery is allowed because it is not a benchmark:

```bash
python3 simulator-remodeled/util/hw_stats/collect_sm120_device_info.py \
  --remote dsp5060 \
  --device 0 \
  --include-metric-discovery
```

## Step 3: RTX5060 Tuner Microbenchmark Collection On dsp5060

Create and copy only a compact tuner source bundle:

```bash
cd /home/xiewx/accel-0608/modern-gpu-simulator
tar --exclude 'bin' --exclude '*.o' -czf /tmp/sm120-tuner-src.tgz \
  -C simulator-remodeled/util/tuner GPU_Microbenchmark
scp /tmp/sm120-tuner-src.tgz dsp5060:/tmp/
```

Build and run the tuner in `/tmp` on `dsp5060`:

```bash
ssh dsp5060 '
  set -e
  rm -rf /tmp/sm120-tuner-collection
  mkdir -p /tmp/sm120-tuner-collection
  tar -xzf /tmp/sm120-tuner-src.tgz -C /tmp/sm120-tuner-collection
  cd /tmp/sm120-tuner-collection/GPU_Microbenchmark
  make CUDA_PATH=/usr/local/cuda-13.2 CUDA_ARCH=sm_120 HW_DEF=SM120_RTX5060
  ./run_all.sh > sm120-rtx5060-microbench.txt 2>&1
'
```

If CUDA 13.2 is not installed on `dsp5060`, first verify that the selected CUDA
toolkit supports `sm_120` with `nvcc --list-gpu-code`; record the actual CUDA
path and version in the manifest. Do not silently fall back to a toolkit that
cannot compile SM120.

Copy back only the text result:

```bash
mkdir -p artifacts/s7/$RUN_ID
scp dsp5060:/tmp/sm120-tuner-collection/GPU_Microbenchmark/sm120-rtx5060-microbench.txt \
  artifacts/s7/$RUN_ID/
```

## Step 4: Local S5 Parsing Into Draft YAML

Parse locally:

```bash
python3 simulator-remodeled/util/tuner/parse_sm120_microbench.py \
  --input artifacts/s7/$RUN_ID/sm120-rtx5060-microbench.txt \
  --output artifacts/s7/$RUN_ID/RTX5060-real-microbench-draft.yaml \
  --gpu RTX5060 \
  --source-type microbenchmark \
  --source-label dsp5060-run-all \
  --collection-host dsp5060 \
  --collection-command './run_all.sh > sm120-rtx5060-microbench.txt 2>&1'
```

Review before any promotion discussion:

- `status` is `draft_not_applied`.
- `handoff.do_not_claim_calibrated` is `true`.
- Unsupported keys are either intentionally out of S5 scope or assigned to a
  future S6 parameter sweep.
- Duplicate conflicts are withheld and explained.
- Owner assignments preserve `SM120_BASE` vs per-GPU overlay vs calibration
  result boundaries.

Raw `nvidia-smi` and human-readable CUDA `deviceQuery` text are not accepted by
the S5 parser. Convert reviewed official facts to config-style lines only when
the owner and source are clear.

## Step 5: Local Bounded Correlation Search

Use S6 only for parameters that remain after official facts and microbenchmark
calibration. A real S7 manifest must use `evaluation.mode: supplied_metrics`
with local simulator metrics; fixture metrics are not calibration evidence.

Dry-run a reviewed supplied-metrics manifest:

```bash
python3 simulator-remodeled/util/tuner/search_sm120_correlation.py \
  --manifest artifacts/s7/$RUN_ID/RTX5060-s6-supplied-metrics.yaml \
  --dry-run \
  --print-planned-commands \
  --command-candidate-limit 4
```

If planned commands contain only `gpgpusim.config` deltas, add reviewed
temporary `extra_params` aliases outside accepted calibration artifacts, then
launch only on the local strong server. Keep `-n` until setup directories are
reviewed. Remove `-n` only for the intentional local parameter sweep.

For `trace.config` candidate deltas, create reviewed temporary trace configs
instead of relying on `extra_params`; S6 command planning intentionally rejects
trace deltas because the launcher appends `trace.config` after `extra_params`.

Generate the ranked draft report after supplied metrics exist:

```bash
python3 simulator-remodeled/util/tuner/search_sm120_correlation.py \
  --manifest artifacts/s7/$RUN_ID/RTX5060-s6-supplied-metrics.yaml \
  --output artifacts/s7/$RUN_ID/RTX5060-s6-ranked-report.yaml \
  --emit-planned-commands \
  --command-candidate-limit 4
```

The report is still `draft_not_applied`; it is not an accepted calibration.

## Step 6: Local Smoke Test Commands

First create a setup-only plan on the local strong server:

```bash
cd /home/xiewx/accel-0608/modern-gpu-simulator
export CUDA_INSTALL_PATH=${CUDA_INSTALL_PATH:-/usr/local/cuda-13.2}
source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release
source simulator-remodeled/gpu-app-collection/src/setup_environment

python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N $RUN_ID-smoke-plan \
  -r artifacts/s7/$RUN_ID/sim-smoke-plan \
  -l local \
  -n
```

After the setup-only plan is reviewed, run a short local smoke test by removing
`-n`. This is the only command in this section that launches simulator work, and
it must never run on `dsp5060`:

```bash
python3 simulator-remodeled/util/job_launching/run_simulations.py \
  -B rodinia_2.0-ft:backprop-rodinia-2.0-ft:0 \
  -C RTX5060_SM120_GEN \
  -N $RUN_ID-smoke \
  -r artifacts/s7/$RUN_ID/sim-smoke \
  -l local \
  -c 4
```

For trace-driven smoke, add `-T <reviewed-trace-root>` and keep the generated
config alias. Record whether the smoke test is PTX-mode or trace-mode.

## Step 7: RTX5070Ti Compatibility

These checks do not require RTX5070Ti hardware:

```bash
python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only
python3 simulator-remodeled/util/tuner/check_sm120_s7_validation.py \
  --gpu RTX5070_TI \
  --run-id rtx5070ti-compat-plan \
  --no-command-plan
```

Review that:

- `RTX5070_TI_SM120_GEN` still points to generated SM120 RTX5070Ti configs.
- RTX5070Ti overlay and bootstrap-current-flat calibration inputs are not
  modified by RTX5060 calibration drafts.
- Any common `SM120_BASE` change is justified as architecture-wide and is
  compatible with both RTX5060 and RTX5070Ti generated configs.

If RTX5070Ti hardware is explicitly available, repeat the hardware
characterization and microbenchmark calibration steps on that host with
`--gpu RTX5070_TI`, `--include-hardware-plan`, the real RTX5070Ti host name, and
`HW_DEF=SM120_RTX5070_TI`; otherwise leave hardware fields as "not run".

## Promotion Gate

Promotion is manual and reviewed:

1. Keep S5 parser output and S6 ranked reports as drafts under
   `artifacts/s7/<run_id>/`.
2. Create a small reviewed staged delta file only after artifact hashes,
   provenance, owner assignment, smoke test, and correlation/validation results
   are accepted.
3. Copy only owner-matched entries:
   - official hardware characterization facts to the per-GPU overlay;
   - architecture-wide evidence to `SM120_BASE`;
   - timing/correlation values to calibration-result staged delta/latest.
4. Do not update `calibration-results/RTX5060/latest.yaml` in this MVP unless a
   separate reviewer explicitly approves promotion.
5. Never update flat `configs/tested-cfgs/SM120_*` or generated
   `configs/generated/tested-cfgs/SM120_*` by hand. Regenerate with S4 tooling
   after accepted inputs change.

Minimum promotion evidence:

- S7 manifest completed with pass/fail fields.
- Official facts collected from `dsp5060`.
- Real tuner microbenchmark output collected from `dsp5060`, not a fixture.
- S5 draft reviewed for unsupported and duplicate keys.
- S6 supplied-metrics report reviewed when a parameter sweep is used.
- Local smoke test passes on the strong server.
- RTX5070Ti compatibility check passes without requiring RTX5070Ti hardware.
- `generate_sm120_configs.py --check-only` and `git diff --check` pass.
