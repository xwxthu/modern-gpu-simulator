# S7 S5 Low-Risk Stage-Map Support Worker Log

## Purpose

Add minimal S5 parser/stage-map support for exactly two low-risk active
`sm120_base` facts from the S7 unsupported-key disposition:

- `-gpgpu_ptx_force_max_capability`
- `-gpgpu_coalesce_arch`

This task keeps all parser output as `draft_not_applied`, does not run the
simulator, does not use `dsp5060`, and does not promote accepted/generated/latest
configs or calibration results.

## Base And Timestamp

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base commit: `82cd0d5`
- Timestamp: `2026-06-10T00:02:52+08:00`
- Assigned role: S7 S5 Low-Risk Stage-Map Support

## Required Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/s5-microbenchmark-calibration.md`
- `docs/sm120-calibration/s7-unsupported-s5-keys-20260609.md`
- `simulator-remodeled/util/tuner/parse_sm120_microbench.py`
- `simulator-remodeled/util/tuner/testdata/sm120_microbench_sample.txt`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/calibration-results/samples/RTX5060-microbench-draft.yaml`
- `artifacts/s7/rtx5060-s7-tuner-buildfix-20260608-233545/sm120-rtx5060-microbench.txt`
- `artifacts/s7/rtx5060-s7-tuner-buildfix-20260608-233545/RTX5060-real-microbench-draft.yaml`

Additional context read:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema/sm120.schema.yaml`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/base/SM120_BASE.yaml`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/overlays/RTX5060.yaml`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/calibration-results/RTX5060/bootstrap-current-flat.yaml`

## Actions

- Confirmed branch and head: `dev-5060` at `82cd0d5`.
- Confirmed both target keys are active `gpgpusim.config` keys owned by
  `sm120_base` in `schema/sm120.schema.yaml`.
- Added exactly those two keys to the S5 `official_device_query_facts` stage in
  `parse_sm120_microbench.py`.
- Left owner and target-layer assignment unchanged and schema-driven:
  `owner_lookup()` reads `schema/sm120.schema.yaml`, and `target_layer()` maps
  `sm120_base` to `base/SM120_BASE.yaml`.
- Updated the sample fixture to include the two keys and regenerated the golden
  sample draft with fixed `calibration_id` and `generated_at`.
- Preserved the sample unsupported-key negative path with
  `-gpgpu_l1_latency`.
- Updated S5 and S7 documentation to record the new draft-only support and the
  real parse summary drop from `13` unsupported to `11` unsupported.
- Did not support the other 11 unsupported keys:
  `-gpgpu_kernel_launch_latency`, `-gpgpu_l1_latency`,
  `-gpgpu_num_dp_units`, `-gpgpu_shmem_option`, `-gpgpu_smem_latency`,
  `-gpgpu_unified_l1d_size`, `-icnt_flit_size`, `-specialized_unit_3`,
  `-specialized_unit_4`, `-trace_opcode_latency_initiation_spec_op_3`,
  `-trace_opcode_latency_initiation_spec_op_4`.
- Did not modify accepted configs, generated configs, flat tested configs, or
  `calibration-results/<GPU>/latest.yaml`.

## Changed Files

- `simulator-remodeled/util/tuner/parse_sm120_microbench.py`
- `simulator-remodeled/util/tuner/testdata/sm120_microbench_sample.txt`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/calibration-results/samples/RTX5060-microbench-draft.yaml`
- `docs/sm120-calibration/s5-microbenchmark-calibration.md`
- `docs/sm120-calibration/s7-unsupported-s5-keys-20260609.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/worker-logs/worker-20260610-000252-s7-s5-lowrisk-keys.md`

## Validation

Passed:

- `git diff --check`
  - Exit code: `0`
- Real RTX5060 parse rerun:
  `python3 simulator-remodeled/util/tuner/parse_sm120_microbench.py --input artifacts/s7/rtx5060-s7-tuner-buildfix-20260608-233545/sm120-rtx5060-microbench.txt --output /tmp/RTX5060-real-microbench-draft-lowrisk.yaml --gpu RTX5060 --source-type microbenchmark --source-label dsp5060-run-all --collection-host dsp5060 --collection-command './run_all.sh > sm120-rtx5060-microbench.txt 2>&1'`
  - Exit code: `0`
  - Summary: `76` parsed, `65` supported, `11` unsupported, `0` duplicate
    conflicts, `65` derived-delta keys.
  - `status: draft_not_applied`, `derived_delta.status: draft_not_applied`,
    and `handoff.do_not_claim_calibrated: true`.
  - The two newly supported entries are draft deltas in
    `official_device_query_facts` with owner `sm120_base` and target
    `base/SM120_BASE.yaml`.
  - The remaining unsupported keys are the expected 11 listed above.
- Sample fixture/golden reproducibility:
  `python3 simulator-remodeled/util/tuner/parse_sm120_microbench.py --input simulator-remodeled/util/tuner/testdata/sm120_microbench_sample.txt --output /tmp/RTX5060-microbench-draft-golden-check.yaml --gpu RTX5060 --source-type microbenchmark --source-label sm120_microbench_sample --collection-host local-fixture --collection-command 'synthetic fixture, no GPU run' --calibration-id RTX5060-synthetic-sm120-microbench-draft --generated-at '2026-06-08T12:00:00Z' --fixture-only && diff -u simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/calibration-results/samples/RTX5060-microbench-draft.yaml /tmp/RTX5060-microbench-draft-golden-check.yaml`
  - Exit code: `0`
  - Summary: `14` parsed, `13` supported, `1` unsupported, `13`
    derived-delta keys.
  - The only unsupported sample key is `-gpgpu_l1_latency`.
- `python3 simulator-remodeled/util/tuner/generate_sm120_configs.py --check-only`
  - Exit code: `0`
  - Output reported generated bootstrap checks for `SM120_RTX5070_TI` and
    `SM120_RTX5060`.
- Protected config/latest scoped status check:
  `git status --short -- <SM120 layered base/overlays/calibration-results latest paths, generated tested-cfgs, and flat SM120 tested-cfgs paths>`
  - Exit code: `0`
  - Empty output.

## Reviewer Rounds

Round 1:

- Reviewer type: fresh blank-context read-only Codex reviewer.
- Artifact: `/tmp/s7-s5-lowrisk-review/reviewer-round1.txt`
- Verdict: `ACCEPT`.
- Reviewer confirmed:
  - parser stage-map support is limited to the two requested keys and both are
    under `official_device_query_facts`;
  - owner lookup remains schema-derived, with no RTX5060-only special case;
  - the other 11 unsupported keys remain unsupported in the real rerun;
  - real parse rerun matched `76` parsed, `65` supported, `11` unsupported,
    `65` derived deltas, and `handoff.do_not_claim_calibrated: true`;
  - fixture golden is reproducible and still has exactly one unsupported key;
  - docs and worker log keep S7, promotion, calibration, and correlation
    claims bounded;
  - no accepted/generated/latest config promotion was detected;
  - `git diff --check` and generator check-only passed.

## Final Status

Complete. Validation passed and fresh read-only reviewer Round 1 returned
`ACCEPT`.

Remaining S7 work: the 11 still-unsupported keys require the documented
evidence or deferral path, real hardware target metrics and any required S6
supplied-metrics/ranked reports still do not exist, and the promotion gate plus
RTX5060/RTX5070Ti signoff remain open.
