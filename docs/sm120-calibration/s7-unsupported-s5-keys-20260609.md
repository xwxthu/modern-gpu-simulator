# S7 Unsupported S5 Key Disposition - 2026-06-09

## Scope

This note dispositions the 13 `unsupported_keys` from the real RTX5060 S5
microbenchmark draft:

- Draft:
  `artifacts/s7/rtx5060-s7-tuner-buildfix-20260608-233545/RTX5060-real-microbench-draft.yaml`
- Raw output:
  `artifacts/s7/rtx5060-s7-tuner-buildfix-20260608-233545/sm120-rtx5060-microbench.txt`
- Raw output SHA256:
  `565a904d232f71c4b4ad6efeb524fb67a8d5b24e88644bc33b4b0d5393bbadf4`
- Draft SHA256:
  `eb3d12bd2e23601a86c4e4ef9353e54c6913130ef6282880c69b824fb1caece9`

The draft remains `draft_not_applied` and has
`handoff.do_not_claim_calibrated: true`. This review did not update
accepted configs, generated configs, flat tested configs, or
`calibration-results/<GPU>/latest.yaml`.

## Method

For each unsupported key, this review checked:

- the value, source benchmark, and line recorded in the real S5 draft;
- whether the key is active in
  `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema/sm120.schema.yaml`;
- the active owner and current provenance file when the key is active;
- whether the key should be added to S5 parser stage support, left for S6,
  explicitly deferred or rejected, or held for more hardware/benchmark
  evidence.

Current S6 MVP note: `search_sm120_correlation.py` only accepts active
`calibration_result` keys in the `rf_prefetch_remodeled_parameters` stage with
`correlation_search` provenance. None of the 13 keys is currently eligible for
that S6 search contract as-is.

## Summary

| Category | Count | Keys |
| --- | ---: | --- |
| Schema-active, low-risk future S5 stage-map candidates | 2 | `-gpgpu_ptx_force_max_capability`, `-gpgpu_coalesce_arch` |
| Schema-active, but needs further hardware or benchmark evidence before S5 support | 4 | `-gpgpu_kernel_launch_latency`, `-gpgpu_shmem_option`, `-gpgpu_unified_l1d_size`, `-icnt_flit_size` |
| Not schema-active; explicit legacy or inactive current-flow deferral | 7 | `-gpgpu_l1_latency`, `-gpgpu_num_dp_units`, `-gpgpu_smem_latency`, `-specialized_unit_3`, `-specialized_unit_4`, `-trace_opcode_latency_initiation_spec_op_3`, `-trace_opcode_latency_initiation_spec_op_4` |
| Current S6 MVP candidates | 0 | None |

No parser or stage-map change was made in this task. The schema-active keys are
not automatically safe to promote from this single draft because some values
come from tuner bootstrap constants or from a launch-latency benchmark that
warns the value can be higher than the real event-based latency. Keeping the
real draft's unsupported summary unchanged is the safer gate behavior until the
follow-up evidence is reviewed.

## Decision Matrix

| Key | Extend S5 stage/parser support? | Leave to S6 supplied-metrics/correlation? | Explicit deferral or rejection? | Needs more hardware/benchmark evidence? |
| --- | --- | --- | --- | --- |
| `-gpgpu_ptx_force_max_capability` | Later, yes; low-risk active `sm120_base` fact | No | No | No beyond existing compute-capability evidence |
| `-gpgpu_coalesce_arch` | Later, yes; low-risk active `sm120_base` fact | No | No | No beyond existing compute-capability evidence |
| `-gpgpu_kernel_launch_latency` | Not yet | Not current S6 MVP; possible future launch-timing search if S6 is extended | No | Yes; current raw benchmark warns the value can be high |
| `-gpgpu_shmem_option` | Not yet | No | No | Yes; separate device fact, policy, and tuner bootstrap logic first |
| `-gpgpu_unified_l1d_size` | Not yet | No | No | Yes; current value is from tuner `hw_def` bootstrap constant |
| `-icnt_flit_size` | Not yet | No | No | Yes; current value is computed from bootstrap topology constants |
| `-gpgpu_l1_latency` | No, not as this raw key | No | Yes; legacy key outside active SM120 schema | Yes only if translating to active remodeled memory keys |
| `-gpgpu_num_dp_units` | No, not without schema/generator owner | No | Yes; inactive legacy unit-count key | Yes only if a future schema adds this surface |
| `-gpgpu_smem_latency` | No, not as this raw key | No | Yes; legacy key outside active SM120 schema | Yes only if translating to active remodeled memory keys |
| `-specialized_unit_3` | No, not under current trace schema | No | Yes; inactive trace spec-unit key | Yes if SM120 trace model intentionally reintroduces tensor spec-unit 3 |
| `-trace_opcode_latency_initiation_spec_op_3` | No, not under current trace schema | No | Yes; inactive trace spec-unit key | Yes if paired spec-unit 3 is reintroduced |
| `-specialized_unit_4` | No, not under current trace schema | No | Yes; inactive UDP spec-unit key | Yes if SM120 trace model intentionally reintroduces UDP spec-unit 4 |
| `-trace_opcode_latency_initiation_spec_op_4` | No, not under current trace schema | No | Yes; inactive UDP spec-unit key | Yes if paired spec-unit 4 is reintroduced |

## Per-Key Disposition

| Key | Value | File | Source | Schema active key | Current owner/provenance | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| `-gpgpu_ptx_force_max_capability` | `120` | `gpgpusim.config` | `core_config`, line 103 | Yes | `sm120_base`; current base provenance is `manual_arch_model` in `base/SM120_BASE.yaml` | Future S5 stage-map candidate under `official_device_query_facts`. It is derived from compute capability 12.0, which is also emitted by `system_config` lines 409-410. Do not use S6. No code change in this task to avoid changing the reviewed draft summary. |
| `-gpgpu_coalesce_arch` | `120` | `gpgpusim.config` | `core_config`, line 107 | Yes | `sm120_base`; current base provenance is `manual_arch_model` in `base/SM120_BASE.yaml` | Future S5 stage-map candidate under `official_device_query_facts`. It is derived from the same device capability as the supported compute-capability keys. Do not use S6. No code change in this task. |
| `-gpgpu_kernel_launch_latency` | `168622` | `gpgpusim.config` | `kernel_lat`, line 148 | Yes | `calibration_result`; current RTX5060 bootstrap provenance is `inherited_from_5070ti` with replacement stage `S5` in `calibration-results/RTX5060/bootstrap-current-flat.yaml` | Needs further hardware or benchmark evidence before S5 support. The raw benchmark itself says the reported latency can be higher than real and points to event-based measurement. Current S6 MVP cannot search it because it is not in the RF/prefetch remodeled stage. Future work should use a reviewed modern CUDA/Nsight timing method or extend S6 with a launch-timing search contract. |
| `-gpgpu_shmem_option` | `0,8,16,32,64,100` | `gpgpusim.config` | `l1_config`, line 194 | Yes | `calibration_result`; current RTX5060 bootstrap provenance is `inherited_from_5070ti` with replacement stage `S5` | Needs further review before S5 support. The value includes the real shared-memory-per-SM size, but the tuner constructs the option from fixed `SHMEM_ADAPTIVE_OPTION` logic plus device properties. It should be promoted only after cross-checking official shared-memory facts and deciding whether this remains `calibration_result` or should be split from architecture policy. Not a current S6 MVP key. |
| `-gpgpu_unified_l1d_size` | `128` | `gpgpusim.config` | `l1_config`, line 195 | Yes | `sm120_base`; current base provenance is `manual_arch_model` | Needs further L1 hardware or benchmark evidence before S5 support. The tuner value is seeded from `L1_SIZE` in the SM120 `hw_def`, and the raw `l1_associativity` run only reports CSV output, not a parsed reviewed value in the S5 draft. Do not promote from this line alone. Not a current S6 MVP key. |
| `-icnt_flit_size` | `40` | `gpgpusim.config` | `l2_config`, line 261 | Yes | `sm120_base`; current base provenance is `manual_arch_model`; `icnt_provenance` is also `manual_arch_model` | Needs further architecture or benchmark evidence before S5 support. The tuner computes it from bootstrap `L2_BANK_WIDTH_in_BYTE + ACCELSIM_ICNT_CONTROL`, and the SM120 `hw_def` labels the topology as bootstrap. Do not promote from this line alone. Not a current S6 MVP key. |
| `-gpgpu_l1_latency` | `38` | `gpgpusim.config` | `l1_lat`, line 206 | No | No active SM120 schema owner or accepted provenance | Explicitly defer or reject as a raw key for the current SM120 flow. S1 already identified legacy `-gpgpu_l1_latency` while current SM120 configs use remodeled memory-latency knobs such as `-memory_l1d_minimum_latency`. Future S5 work may translate `l1_lat` evidence into active remodeled keys after review, but should not add this legacy key directly. |
| `-gpgpu_num_dp_units` | `4` | `gpgpusim.config` | `config_dpu`, line 36 | No | No active SM120 schema owner or accepted provenance | Explicitly defer or reject for current SM120 S5 output. Current active schema covers DP behavior through supported pipeline-width and opcode latency/initiation keys, not this legacy unit-count key. A future schema change would need an owner and generator surface first. |
| `-gpgpu_smem_latency` | `33` | `gpgpusim.config` | `shared_lat`, line 390 | No | No active SM120 schema owner or accepted provenance | Explicitly defer or reject as a raw key for the current SM120 flow. Future S5 work may map `shared_lat` evidence to active remodeled keys such as `-memory_shared_memory_minimum_latency`, but the legacy key should not be promoted directly. |
| `-specialized_unit_3` | `1,4,8,4,4,TENSOR` | `trace.config` | `config_tensor`, line 92 | No | No active SM120 schema owner or accepted provenance | Explicitly defer for current trace flow. Current SM120 trace configs own `-specialized_unit_2` and the generic tensor trace latency key, but do not include tensor spec-unit 3. Reintroducing this key needs a schema, generator, and trace-model review first. |
| `-trace_opcode_latency_initiation_spec_op_3` | `8,8` | `trace.config` | `config_tensor`, line 93 | No | No active SM120 schema owner or accepted provenance | Explicitly defer with `-specialized_unit_3`. The supported tensor trace evidence is already captured by `-trace_opcode_latency_initiation_tensor` at line 91. Do not add this raw key directly without trace-model review. |
| `-specialized_unit_4` | `1,4,4,4,4,UDP` | `trace.config` | `config_udp`, line 96 | No | No active SM120 schema owner or accepted provenance | Explicitly defer for current trace flow. Current SM120 active trace schema does not model UDP spec-unit 4. Reintroduction needs a schema owner, generator support, and benchmark evidence that this unit is part of the intended SM120 trace flow. |
| `-trace_opcode_latency_initiation_spec_op_4` | `4,1` | `trace.config` | `config_udp`, line 97 | No | No active SM120 schema owner or accepted provenance | Explicitly defer with `-specialized_unit_4`. Not a current S5 or S6 promotion candidate. |

## Follow-Up Actions

1. If S5 parser support is extended, start with
   `-gpgpu_ptx_force_max_capability` and `-gpgpu_coalesce_arch`, because they
   are active `sm120_base` keys derived from reviewed compute capability facts.
   Add focused fixture reproducibility and a negative or unsupported-key check
   when doing that patch.
2. For `-gpgpu_kernel_launch_latency`, collect a modern event-based or otherwise
   reviewed launch-latency measurement before mapping the raw `kernel_lat`
   output into `calibration_result`.
3. For `-gpgpu_shmem_option`, `-gpgpu_unified_l1d_size`, and `-icnt_flit_size`,
   separate device facts from tuner bootstrap constants before adding S5 support.
4. For legacy latency keys, add explicit translation from benchmark evidence to
   active remodeled SM120 keys if the measurements are used.
5. For trace spec-unit 3 and 4 keys, do not add parser support until the active
   trace schema and generated trace configs intentionally include those units.

## Promotion Gate Impact

This disposition closes the unsupported-key review gap at the documentation
level only. It does not calibrate RTX5060, does not complete S6 correlation,
and does not promote any S5 draft values. The S7 promotion gate remains closed
until real hardware target metrics, any required S6 supplied-metrics reports,
and promotion-scope RTX5060/RTX5070Ti review are complete.
