# SM120 Configuration Layering Design

## Purpose

Define the S2 design for making SM120 configs maintainable as:

1. A common SM120 architecture model.
2. Per-GPU hardware overlays for RTX 5070 Ti, RTX 5060, and later SM120 GPUs.
3. Calibration results with provenance.
4. Generated `tested-cfgs` outputs that remain compatible with the current simulator and job launching flow.

This is a design document only. It does not change simulator source code or the current flat SM120 configs.

## Current Shape To Preserve

The existing runnable SM120 configs are flat outputs split across two config roots:

- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/tested-cfgs/SM120_RTX5070_TI/gpgpusim.config`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/tested-cfgs/SM120_RTX5060/gpgpusim.config`
- `simulator-remodeled/gpu-simulator/configs/tested-cfgs/SM120_RTX5070_TI/trace.config`
- `simulator-remodeled/gpu-simulator/configs/tested-cfgs/SM120_RTX5060/trace.config`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/tested-cfgs/*/accelwattch_sass_sim.xml`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/tested-cfgs/*/config_ampere_islip.icnt`

The only active `gpgpusim.config` deltas between the two SM120 GPUs are currently:

- `-gpgpu_n_clusters`
- `-gpgpu_n_mem`
- `-gpgpu_clock_domains`

The two `trace.config` files are currently identical. The two `.icnt` files are identical. The RTX 5060 AccelWattch XML says it was copied from RTX 5070 Ti and is not calibrated for RTX 5060 power.

`util/job_launching` reads a `base_file` from `define-standard-cfgs.yml`. In trace mode it derives the `trace.config` path by taking the `configs.../gpgpusim.config` suffix from `base_file` and opening the matching suffix under `$ACCELSIM_ROOT`. Any generated layout must preserve that mirrored path convention unless job launching is explicitly enhanced later.

## Layer Model

The source of truth should become layered data, not flat config files:

1. `SM120_BASE`: SM120-common architecture model and stable simulator policy.
2. Per-GPU overlay: device/SKU facts and board/runtime limits.
3. Calibration result: measured or tuned parameters for one GPU, clock state, toolchain, and benchmark set.
4. Render profile: output policy such as `smoke`, `performance`, or `power`.
5. Generated tested-cfgs: disposable compatibility outputs for the existing simulator.

Precedence is:

`SM120_BASE < per-GPU overlay < calibration result < render profile`

The precedence rule is not a license for arbitrary overrides. Every logical parameter must have an owner in the schema. A layer may set a parameter only if the schema allows that owner. For example, a GPU overlay may set `gpgpu_n_clusters`, but it must not override `gpgpu_compute_capability_major`. A calibration result may set `dram_latency`, but it must not override the device name or SM count. Clock domains are split into two logical fields: nominal/reported clocks in the overlay and controlled calibration clocks in the calibration result.

Generated flat files are build artifacts. They should be reproducible from the layered inputs plus the generator version.

## Recommended File Layout

S4 should introduce a layout under simulator config directories. This S2 document only describes it.

```text
simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/
  schema/
    sm120.schema.yaml
    render-rules.yaml
    required-fields.yaml
  profiles/
    bootstrap.yaml
    smoke.yaml
    performance.yaml
    power.yaml
  base/
    SM120_BASE.yaml
  overlays/
    RTX5070_TI.yaml
    RTX5060.yaml
  calibration-results/
    RTX5070_TI/
      bootstrap-current-flat.yaml
      latest.yaml
    RTX5060/
      bootstrap-current-flat.yaml
      latest.yaml
  templates/
    gpgpusim.config.j2
    accelwattch_sass_sim.xml.j2
    config_ampere_islip.icnt.j2

simulator-remodeled/gpu-simulator/configs/layered/sm120/
  templates/
    trace.config.j2

simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated/tested-cfgs/
  SM120_RTX5070_TI/
    gpgpusim.config
    accelwattch_sass_sim.xml
    config_ampere_islip.icnt
    manifest.yaml
  SM120_RTX5060/
    gpgpusim.config
    accelwattch_sass_sim.xml
    config_ampere_islip.icnt
    manifest.yaml

simulator-remodeled/gpu-simulator/configs/generated/tested-cfgs/
  SM120_RTX5070_TI/
    trace.config
    manifest.yaml
  SM120_RTX5060/
    trace.config
    manifest.yaml
```

The `generated/tested-cfgs` path keeps existing flat configs untouched while preserving the `configs...` suffix expected by `util/job_launching/run_simulations.py`.

`bootstrap-current-flat.yaml` is a migration seed extracted from today's flat configs. It is not a claim of calibration. It should record inherited or placeholder provenance where values were copied from RTX 5070 Ti or lack evidence.

## Parameter Ownership Rules

### SM120_BASE

`SM120_BASE` contains values that are common to SM120 or are explicitly part of the simulator's SM120 architecture model.

GPGPU-Sim architecture and simulator mode:

- `-gpgpu_ptx_instruction_classification`
- `-gpgpu_ptx_sim_mode`
- `-gpgpu_ptx_force_max_capability 120`
- `-gpgpu_compute_capability_major 12`
- `-gpgpu_compute_capability_minor 0`
- `-gpgpu_ptx_convert_to_ptxplus`
- `-gpgpu_ptx_save_converted_ptxplus`
- `-gpgpu_coalesce_arch 120`

Common SM/subcore structure, unless later evidence proves SKU variation:

- `-gpgpu_n_cores_per_cluster`
- `-gpgpu_sub_core_model`
- `-gpgpu_num_sched_per_core`
- `-num_subcores_in_SM`
- `-gpgpu_simd_model`
- `-gpgpu_shader_core_pipeline` when used as warp-size and max-thread shape, not as SKU SM count
- `-gpgpu_pipeline_widths`
- `-gpgpu_num_sp_units`
- `-gpgpu_num_sfu_units`
- `-gpgpu_num_int_units`
- `-gpgpu_tensor_core_avail`
- `-gpgpu_num_tensor_core_units`
- `-gpgpu_num_reg_banks`
- `-gpgpu_shmem_num_banks`
- `-gpgpu_shmem_limited_broadcast`
- `-gpgpu_shmem_warp_parts`

SM120 remodeled model enablement and trace assumptions:

- `-is_fetch_and_decode_improved`
- `-is_extra_traces_enabled`
- `-is_SM_remodeling_enabled`
- `-is_ibuffer_remodeled_enabled`
- `-fetch_decode_width`
- `-is_L0I_enabled`
- `-max_request_allowed_to_L1I`
- `-max_reply_allowed_from_L1I`
- `-gpgpu_cache:il1`
- `-gpgpu_cache:il0`
- `-gpgpu_subcore_const_cache:l0`
- `-gpgpu_tex_cache:l1` for legacy texture compatibility
- `-gpgpu_const_cache:l1` shape if retained as common legacy/cache model
- `-gpgpu_perfect_inst_const_cache`
- `-perfect_constant_cache`
- `-perfect_instruction_cache`
- `-invalidate_instruction_caches_at_kernel_end`

Stable simulator policy defaults:

- Flush/stat/visualizer defaults such as `-gpgpu_flush_l1_cache`, `-gpgpu_flush_l2_cache`, `-gpgpu_runtime_stat`, `-enable_ptx_file_line_stats`, `-visualizer_enabled`.
- Kernel filters such as `-filter_first_kernel_id` and `-filter_last_kernel_id`, unless a benchmark-specific run profile overrides them.
- Power disabled by default for performance configs. `-power_simulation_enabled 0` may be rendered explicitly by performance/power-oriented generated profiles, but the bootstrap profile may rely on the simulator's implicit default to preserve golden diffs against today's flat SM120 configs.
- Enhanced trace requirements and Blackwell control-bit/operand model assumptions. These live in source today but should be represented in base metadata with `manual_arch_model` provenance.

Interconnect base:

- Current SM120 configs use `-network_mode 2`, the local xbar path. The inline `-icnt_*` options are therefore the active interconnect config and should be represented in `SM120_BASE` unless measured otherwise.
- The existing `config_ampere_islip.icnt` file is a compatibility artifact while `network_mode 2` remains active. It should be rendered or copied for directory completeness, but it is not a required active input for SM120 local-xbar runs.
- `-inter_config_file` and `.icnt` topology fields become active only if a future source change supports `network_mode 1` again.

### Per-GPU Overlay

The overlay contains physical SKU facts, board-level facts, and runtime/device limits.

RTX 5070 Ti overlay should own:

- `-gpgpu_n_clusters 70`
- `-gpgpu_n_mem 16`
- Device name and stable aliases such as `SM120_RTX5070_TI` and `RTX5070_TI`
- Nominal/reported clock domains, currently `2580:2580:2580:14000`, tagged as reported or nominal rather than controlled calibration

RTX 5060 overlay should own:

- `-gpgpu_n_clusters 30`
- `-gpgpu_n_mem 8`
- Device name and aliases such as `SM120_RTX5060` and `RTX5060`
- Nominal/reported clock domains, currently `2640:2640:2640:14000`, tagged as smoke-ready reported clocks
- The current 128-bit bus / 24 MiB L2 statement only after official-tool/device-query evidence is attached. Until then it must be tagged as inherited or placeholder, not calibrated fact.

Per-GPU resource and topology fields:

- `-gpgpu_n_sub_partition_per_mchannel` if confirmed common; otherwise overlay.
- `-gpgpu_n_mem_per_ctrlr`
- `-gpgpu_dram_buswidth`
- `-gpgpu_dram_burst_length`
- `-dram_data_command_freq_ratio`
- `-gpgpu_shader_registers`
- `-gpgpu_registers_per_block`
- `-gpgpu_shader_cta`
- `-gpgpu_shmem_size`
- `-gpgpu_shmem_sizeDefault`
- `-gpgpu_shmem_per_block`
- Runtime limits: stack, heap, sync depth, pending launch count, max concurrent kernels, if read from runtime or official tools.

`-gpgpu_occupancy_sm_number 120` should be owned by `SM120_BASE` as a compute-capability/occupancy model field, despite the misleading name. Device query should verify that the expected compute capability remains 12.0.

AccelWattch overlay fields:

- Device name and power-profile identity.
- Per-GPU static/idle constants only when calibrated for that GPU.
- RTX 5060 must not silently inherit RTX 5070 Ti XML for calibrated power. If copied for smoke compatibility, every copied XML parameter must have `inherited_from_5070ti` or `placeholder` provenance and power mode should remain disabled by default.

### Active-Key Ownership And Profile Policy

S4 must construct an active-key inventory from the current SM120 flat `gpgpusim.config`, `trace.config`, AccelWattch XML, and active interconnect settings. Every active option in that inventory must have exactly one schema owner and an allowed profile policy before the generator can emit a config. If a current active option is present in a flat SM120 config but missing from the schema, generation fails. The MVP may store the full inventory as generated/schema data rather than in this design document, but the inventory itself is required for S4 acceptance.

The following current active SM120 keys have explicit S2 ownership:

| Key | Owner | Profiles | Provenance / policy |
| --- | --- | --- | --- |
| `-gpgpu_kernel_launch_latency` | Calibration result | `bootstrap`, `smoke`, `performance`; benchmark profile may override | Current value is bootstrap timing. Treat as `placeholder` or `microbenchmark` once measured; it is not a per-GPU public fact. |
| `-gpgpu_TB_launch_latency` | Calibration result | `bootstrap`, `smoke`, `performance`; benchmark profile may override | Same policy as kernel launch latency. Current zero may be preserved in bootstrap, then measured or justified. |
| `-latency_L0_to_L1` | Calibration result | `bootstrap`, `smoke`, `performance` | L0I existence is `SM120_BASE`; L0I timing is measured/tuned. Current value is bootstrap until a microbenchmark/correlation source exists. |
| `-latency_L1_to_L0` | Calibration result | `bootstrap`, `smoke`, `performance` | Same policy as `-latency_L0_to_L1`; validate together as an L0I timing group. |
| `-is_instruction_prefetching_enabled` | `SM120_BASE` model policy, with render-profile override allowed | `bootstrap`, `smoke`, `performance`; controlled sweep profiles may override | Baseline architecture/model choice for current SM120. If swept, generated profile must record the override as a controlled experiment, not as calibrated default. |
| `-prefetch_per_stream_buffer_size` | Calibration result | `bootstrap`, `smoke`, `performance`; controlled sweep profiles may override | Queue/buffer sizing is a timing/model parameter. Bootstrap may inherit current flat value; performance requires measured/searched or manual-model justification. |
| `-prefetch_num_stream_buffers` | Calibration result | `bootstrap`, `smoke`, `performance`; controlled sweep profiles may override | Same policy as prefetch buffer size. |
| `-num_instruction_prefetches_per_cycle` | Calibration result | `bootstrap`, `smoke`, `performance`; controlled sweep profiles may override | Same policy as prefetch buffer size. |
| `-is_custom_omp_scheduler_enabled` | `SM120_BASE` model policy, with render-profile override allowed | `bootstrap`, `smoke`, `performance`; controlled sweep profiles may override | This is a simulator scheduling policy, not a GPU SKU fact. If disabled/enabled in sweeps, the manifest must mark the selected model policy. |
| `-custom_omp_scheduler_ratio_to_dynamic` | Calibration result, with `profile_override_allowed` for controlled sweeps | `bootstrap`, `smoke`, `performance`; controlled sweep profiles may override | Current value is a bootstrap model/tuning parameter. A performance config needs `manual_arch_model`, `microbenchmark`, or `correlation_search` provenance. Any sweep override must remain a manifested profile override, not a second schema owner. |

General active-key rules:

- `SM120_BASE` owns architecture identity, source-level model enablement, and stable simulator policies.
- Per-GPU overlays own device/SKU facts and runtime/device limits.
- Calibration results own timing, queue sizing, memory/cache behavior, scheduling/tuning knobs, RF/PRT/interwarp knobs, and launch latency.
- Render profiles may only override parameters whose schema explicitly marks `profile_override_allowed`.
- Controlled sweep configs must be generated through S4 or marked as unmanifested overrides in the run metadata.
- Bootstrap may use `placeholder` and `inherited_from_5070ti`; performance/power profiles must apply the stricter rules in the validation section.

### Calibration Result

Calibration results contain measured, searched, or explicitly inherited non-public model parameters. They should be narrow delta files, not full copied configs.

Instruction and trace timing:

- `-ptx_opcode_latency_int`
- `-ptx_opcode_initiation_int`
- `-ptx_opcode_latency_fp`
- `-ptx_opcode_initiation_fp`
- `-ptx_opcode_latency_dp`
- `-ptx_opcode_initiation_dp`
- `-ptx_opcode_latency_sfu`
- `-ptx_opcode_initiation_sfu`
- `-ptx_opcode_latency_tesnor` (keep the existing misspelled render key)
- `-ptx_opcode_initiation_tensor`
- `-tensor_latency`
- `-tensor_extra_latency_16816_fp32_1688_fp32`
- `-tensor_rate_per_cycle`
- Branch, half, uniform, predicate, and miscellaneous latency/initiation pairs.
- All `trace.config` latency/initiation entries.
- Specialized units such as TEX: `-specialized_unit_2` and `-trace_opcode_latency_initiation_spec_op_2`.

Memory/cache timing and geometry:

- `-gpgpu_cache:dl1`
- `-gpgpu_l1_banks`
- `-gpgpu_l1_banks_hashing_function`
- `-gpgpu_unified_l1d_size` if not proven SM120-common
- `-gpgpu_shmem_option`
- `-gpgpu_cache:dl2`
- L2 set/assoc/bank/MSHR/queue mapping and any formula from L2 size to cache config.
- `-gpgpu_l2_rop_latency`
- `-dram_latency`
- `-memory_l1d_minimum_latency`
- `-memory_l1d_max_lookups_per_cycle_per_bank`
- `-memory_shared_memory_minimum_latency`
- `-memory_shared_memory_extra_latency_ldsm_multiple_matrix`
- `-memory_global_shared_latency_for_ldgsts`
- `-constant_cache_latency_at_sm_structure`

DRAM, partitioning, and addressing:

- `-gpgpu_dram_timing_opt`
- `-gpgpu_dram_scheduler`
- `-gpgpu_frfcfs_dram_sched_queue_size`
- `-gpgpu_dram_return_queue_size`
- `-gpgpu_dram_partition_queues`
- `-gpgpu_memory_partition_indexing`
- `-gpgpu_mem_addr_mapping`
- `-gpgpu_mem_address_mask`
- `-dram_bnk_indexing_policy`
- `-dram_bnkgrp_indexing_policy`
- `-dram_dual_bus_interface`

Pipeline, RF, scoreboard, and remodeled queues:

- Operand collector counts and port counts.
- `-gpgpu_reg_file_port_throughput`
- `-gpgpu_scheduler`
- `-gpgpu_max_insn_issue_per_warp`
- `-gpgpu_dual_issue_diff_exec_units`
- `-ibuffer_remodeled_size`
- `-miscellaneous_queue_size`
- `-memory_subcore_queue_size`
- `-memory_intermidiate_stages_subcore_unit`
- `-memory_sm_prt_size`
- Per-access queue sizes for L1C/L1T/L1D/shared/bypass/misc.
- Dispatch wait cycles from subcore to shared SM pipeline.
- `-memory_maximum_coalescing_cycles`
- `-offset_latency_firts_stage_memory_subcore`
- `-memmory_max_concurrent_requests_shmem_per_sm`
- `-memmory_max_concurrent_requests_standard_per_sm`
- Scalar units, subcore-to-SM link width, load/store half-bandwidth toggles.
- DP queue/stage/latency fields.
- `-is_dp_pipeline_shared_for_subcores`
- `-is_fp32ops_allowed_in_int_pipeline`
- `-is_fp32_and_int_unified_pipeline`
- Tracking toggles if their values affect timing/correlation.
- Barrier/stall knobs.
- RF cache enablement, max operands, RF latency, read/write ports, write queue, read granularity, write-back cycles.
- Scoreboard WAR settings.

PRT/interwarp/coalescing:

- `-measure_coalescing_potential_stats`
- `-number_of_coalescers`
- `-prt_selection_policy_string`
- `-number_of_clusters_for_prt_selection`
- `-is_interwarp_coalescing_enabled`
- `-num_interwarp_coalescing_tables`
- `-interwarp_coalescing_quanta`
- `-interwarp_coalescing_quanta_warppool_policy_miss_ratio_threshold`
- `-interwarp_coalescing_selection_policy_string`
- `-max_size_interwarp_coalescing_per_table`

Power:

- AccelWattch dynamic activity factors.
- Static and idle power constants.
- McPAT/AccelWattch structural XML values if they are not direct renderings from the simulator config.
- Power calibration metadata: benchmark set, power sampling source, clock/power limit state, averaging window, and idle subtraction method.

## Provenance And Schema

Every logical parameter must have a schema entry and provenance. Generated files do not carry enough structure by themselves, so S4 should also emit `manifest.yaml` beside each generated config directory.

Recommended logical parameter shape:

```yaml
schema_version: 1
parameter_id: sm_count
owner: gpu_overlay
value: 30
type: int
unit: count
render:
  - file: gpgpusim.config
    key: "-gpgpu_n_clusters"
required_for_profiles: [smoke, performance]
provenance:
  source_type: device_query
  source_detail: cudaDeviceProp.multiProcessorCount
  device: RTX5060
  collected_at: null
  tool_versions: {}
  evidence: null
  confidence: medium
  notes: "Current value was seeded from the flat SM120_RTX5060 config until S3 collection is attached."
```

Allowed `source_type` values:

- `official_tool`: NVIDIA official tools such as `nvidia-smi`, CUDA runtime attributes, Nsight Compute metric discovery, or documented device attributes.
- `device_query`: CUDA device query or a project device-property collector.
- `microbenchmark`: isolated timing or bandwidth benchmark.
- `correlation_search`: targeted search over a small candidate set with recorded benchmark subset and score.
- `manual_arch_model`: source-level architecture/modeling assumption deliberately retained as part of the SM120 model.
- `placeholder`: required to render a smoke config but not backed by evidence.
- `inherited_from_5070ti`: copied from RTX 5070 Ti as a temporary bootstrap value.

`placeholder` and `inherited_from_5070ti` require extra fields:

```yaml
provenance:
  source_type: inherited_from_5070ti
  source_device: RTX5070_TI
  reason: "No RTX5060 measurement available during bootstrap."
  allowed_profiles: [smoke]
  replacement_stage: S5
  replacement_plan: "Measure with shared/L1 latency microbenchmarks on dsp5060."
```

A parameter may have multiple sources if it is derived. For example, L2 cache rendering may use `official_tool` for total L2 size and `manual_arch_model` for the simulator's mapping from size/partitions to `-gpgpu_cache:dl2`.

Schema entries should include:

- Logical ID.
- Owner.
- Type and unit.
- Allowed values or validation regex for encoded config strings.
- Render target file and key or XML XPath.
- Required profiles.
- Whether `placeholder` or `inherited_from_5070ti` is allowed.
- Whether the parameter participates in a cross-file consistency rule.
- Deprecation/render notes, especially for misspelled existing options such as `-ptx_opcode_latency_tesnor`.

## Generator Design For S4

The S4 generator should be a deterministic renderer with validation. It should not be a line replacer over the legacy `util/tuner/config_template/gpgpusim.config`, because that template omits the SM120 remodeled block.

Inputs:

- `SM120_BASE.yaml`
- `overlays/<gpu>.yaml`
- `calibration-results/<gpu>/<profile-or-run>.yaml`
- `profiles/<profile>.yaml`
- `schema/*.yaml`
- Render templates for `gpgpusim.config`, `trace.config`, AccelWattch XML, and `.icnt`.

Outputs:

- Mirrored generated config directories under both config roots.
- `gpgpusim.config`, `trace.config`, `accelwattch_sass_sim.xml`, and `config_ampere_islip.icnt`.
- `manifest.yaml` containing input file hashes, generator command, generator version, layer names, selected profile, validation result, and per-parameter provenance summaries.

Merge and validation flow:

1. Load schema and render rules.
2. Load base, overlay, calibration result, and render profile.
3. Validate that each parameter is set only by an allowed owner.
4. Deep-merge layers by logical parameter ID.
5. Expand derived parameters such as clock-domain strings or L2 config strings.
6. Run required-field validation for the selected profile.
7. Run cross-file consistency validation.
8. Render all files.
9. Re-parse rendered config files and compare against the merged logical parameter table.
10. Emit manifest and fail on any validation error.

Active-key validation is mandatory for every profile. The generator must parse or otherwise inventory all active keys in the selected rendered files and verify that each key has a schema entry, owner, provenance policy, and profile policy. Missing ownership is an error even when the rendered value matches a legacy flat config.

Required-field validation:

- `smoke` profile: all active simulator options needed by current flat SM120 configs must render. `placeholder` and `inherited_from_5070ti` are allowed only with warnings and replacement metadata.
- `performance` profile: no timing, cache, memory, scheduler, RF, PRT/interwarp, or address-mapping parameter may use `placeholder`. `inherited_from_5070ti` is allowed only for parameters explicitly tagged as SM120-common architecture model, not for SKU calibration.
- `power` profile: power XML parameters must be calibrated for the target GPU or explicitly run in a documented non-calibrated exploratory mode. Default performance configs keep power disabled.
- `bootstrap` profile: values and omitted explicit defaults are allowed to mirror today's flat files for golden diff purposes. If a simulator default is intentionally implicit in current flat configs, such as absent `-power_simulation_enabled 0`, bootstrap output should omit it unless the diff allowlist names it. Performance and power profiles may render explicit defaults, but those outputs are profile-specific and are not required to be byte-equivalent to bootstrap flat configs.

Validation must fail if:

- A required render key is missing.
- A parameter renders to an unknown file/key.
- A logical parameter has conflicting owners.
- A calibration result attempts to override immutable architecture identity.
- `trace.config` is not generated from the same latency groups as `gpgpusim.config`.
- The generated `trace.config` path does not mirror the `gpgpusim.config` suffix expected by job launching.
- `network_mode 2` is selected but required inline `-icnt_*` fields are missing.
- `network_mode 1` is selected while the current simulator still aborts Intersim runs, unless the profile is explicitly marked non-runnable.
- Power is enabled but the selected XML file or required XML params are missing.
- A profile renders a key through an implicit default that is not represented in schema metadata. Implicit defaults are allowed only when the schema records the default source and the selected profile allows omission from the flat output.

### Avoiding `trace.config` And `gpgpusim.config` Latency Drift

S4 should define canonical latency groups in the schema. Rendered keys must consume these canonical groups instead of carrying independent flat literals.

Example:

```yaml
latency_groups:
  branch:
    latency: 2
    initiation: 1
    provenance: {source_type: microbenchmark}
    renders_to:
      - {file: gpgpusim.config, key: "-branch_latency", field: latency}
      - {file: gpgpusim.config, key: "-branch_initiation", field: initiation}
      - {file: trace.config, key: "-trace_opcode_latency_initiation_branch", format: "{latency},{initiation}"}
    drift_policy: same_value
```

Use `same_value` for categories that are semantically the same in both files:

- branch
- half
- uniform
- predicate
- miscellaneous queue
- miscellaneous no queue

Use explicit `derived` or `independent_with_reason` policies for categories where the current files are not one-to-one:

- int
- sp/fp
- dp
- sfu
- tensor
- TEX specialized unit

For these categories, validation should still require a shared source run or a documented derivation. It should not allow hand-edited `trace.config` values to drift silently from the calibration result used by `gpgpusim.config`.

The generator should preserve existing render keys exactly, including the misspelled `-ptx_opcode_latency_tesnor`, while using clean logical IDs internally.

## Compatibility Strategy

Do not replace the current flat configs first.

Phase 1 compatibility:

- Keep `SM120_RTX5070_TI` and `SM120_RTX5060` directories unchanged.
- Generate parallel outputs under `configs/generated/tested-cfgs/SM120_RTX5070_TI` and `configs/generated/tested-cfgs/SM120_RTX5060`.
- Add new job-launch aliases later, for example `RTX5070_TI_SM120_GEN` and `RTX5060_SM120_GEN`, whose `base_file` points to the generated `gpgpusim.config`.
- Ensure the matching generated `trace.config` exists under `$ACCELSIM_ROOT/configs/generated/tested-cfgs/<CONFIG>/trace.config`, because `run_simulations.py` derives it from the gpgpusim path.

Phase 2 compatibility:

- After generated outputs match today's flat configs for the bootstrap profile, use generated aliases for smoke and calibration runs.
- Keep old aliases as stable compatibility names until generated configs pass smoke tests and at least one performance/correlation checkpoint.

Phase 3 migration:

- Switch existing `RTX5060` and `RTX5070_TI` aliases to generated paths only after review.
- Optionally replace the old flat `tested-cfgs` files with generated outputs in a dedicated checkpoint, but only if the manifest and generation command are documented.

Job launching can use generated results without source changes if the generated paths follow the mirrored `configs...` convention. A later cleanup may add explicit `trace_file` support to `define-standard-cfgs.yml`, but that is not required for the MVP.

Existing `define-standard-cfgs.yml` `extra_params` combinations are still useful for legacy experiments, but they bypass the generated manifest because `run_simulations.py` appends them after reading the base config. Therefore:

- The manifest covers the generated base files and profile-selected parameters only.
- A job launched with legacy `extra_params` must be marked in run metadata as `unmanifested_override` unless S4 generated that sweep as a first-class layered profile/config.
- `unmanifested_override` runs must not be reported as validated calibration configs.
- Preferred S4 behavior for calibration sweeps is to generate controlled sweep configs from layered inputs, with each override represented in schema/provenance and captured in the manifest.

## Migration Plan

### MVP

1. Add layered data files and schema for the current SM120 flat configs.
2. Extract today's `SM120_RTX5070_TI` flat values into `SM120_BASE`, `RTX5070_TI.yaml`, and `bootstrap-current-flat.yaml`.
3. Extract today's `SM120_RTX5060` differences into `RTX5060.yaml`; tag inherited timing/memory/power values as `inherited_from_5070ti` or `placeholder`.
4. Implement generator rendering complete SM120 `gpgpusim.config` and `trace.config`; copy or render XML and `.icnt` compatibility files.
5. Validate active option key coverage against current flat configs.
6. Validate generated `trace.config` latency groups against canonical latency data.
7. Run a golden bootstrap diff check: generated flat files should compare equal to today's flat files except allowed generated headers, comments, whitespace, and manifest files.
8. Add generated job-launch aliases but keep existing aliases unchanged.
9. Run no-launch job setup or smoke generation checks locally. GPU-dependent collection remains on `dsp5060` in later stages.

MVP acceptance:

- Generated bootstrap configs for RTX 5070 Ti and RTX 5060 contain all active options present in today's flat configs.
- The S4 MVP schema has an owner/profile/provenance policy for every active option in the current SM120 `gpgpusim.config` and `trace.config`, every active XML parameter rendered or copied, and the active local-xbar interconnect fields. Generation fails on any missing owner.
- Bootstrap values match today's flat configs except comments/generated headers.
- Golden bootstrap diff checks pass for `gpgpusim.config`, `trace.config`, active XML values, and `.icnt` compatibility files, with only documented comment/header/manifest differences and any profile-specific explicit-default allowlist. In particular, bootstrap may omit `-power_simulation_enabled 0` to match current flat configs, while performance/power profiles may render it explicitly.
- Generated `trace.config` files are present in the mirrored `$ACCELSIM_ROOT` path.
- Manifest records every parameter source, including all placeholders and RTX 5070 Ti inheritance.
- Runs that append legacy job-launching `extra_params` are marked as `unmanifested_override`, unless S4 generated the sweep as a controlled manifested config.
- No existing SM120 flat config is modified.

### After MVP

S3:

- Add CUDA 13.2-compatible device collection and microbenchmark build prerequisites.
- Collect official/device-query facts for RTX 5060 on `dsp5060`: SM count, compute capability, resource limits, clock state, memory bus width, L2 size, memory clock, supported shared-memory modes, and tool versions.

S4:

- Connect tuner output to the layered calibration-result schema instead of directly replacing template lines.
- Add parser adapters for official-tool, device-query, microbenchmark, and correlation-search outputs.
- Add validation for unknown or stale tuner keys.

S5:

- Populate calibration results from staged microbenchmarks: instruction latency/initiation, L1/shared/constant/L2/DRAM timing, RF behavior, queue sizing where practical, tensor timing, and address/cache behavior.

S6:

- Run targeted correlation searches only for parameters not isolated by direct measurement: scheduling, memory scheduler, L2 hashing/interleaving, selected remodeled policy choices.

S7:

- Validate RTX 5060 and preserve RTX 5070 Ti compatibility.
- Decide whether generated aliases become default aliases.

## Risks And Open Questions

Hardcoded model assumptions to keep as `manual_arch_model` for now:

- RF/read-stage timing macros in remodeled SM headers.
- Reserved register IDs and global register ID layout for RZ/URZ/predicate registers.
- Tensor latency formula and special cases in `abstract_hardware_model.cc`.
- Hardcoded memory pipeline offsets and special cases for load/store/constant/shared/LDSM/LDGSTS paths.
- RF cache bank-slack and multi-register operand classification.
- L0I construction dependency on improved fetch/decode.
- Blackwell control-bit masks and operand-use classification in enhanced trace tooling.
- Source-level selection of remodeled SM implementation through `-is_SM_remodeling_enabled`.

These should not become calibration knobs merely because they are hardcoded. They should move to config/calibration only when a microbenchmark or correlation result demonstrates a value that must vary by SKU or architecture revision, or when the hardcoded assumption blocks a clean validation story.

High-priority open questions:

- Whether RTX 5060 and RTX 5070 Ti truly share all current timing, cache, DRAM, queue, RF, and PRT/interwarp values.
- Whether `-gpgpu_cache:dl2 S:128:128:24,...` should be derived from official L2 size and memory partitions, and what formula is correct for each SKU.
- Whether `-gpgpu_n_sub_partition_per_mchannel 8` is SM120-common or SKU-specific.
- Whether address mapping and partition indexing are common across SM120 SKUs.
- How to normalize clocks: nominal clocks are not enough for calibrated latency/cycle results. Calibration results should record locked or observed clocks per run.
- Whether AccelWattch can provide useful SM120 power without a broader XML/model audit. Until then, performance configs should keep power disabled.
- Whether PRT policy values other than the currently disabled/interwarp-off defaults can trigger unsafe behavior. Search profiles should avoid enabling risky policies until the source-level assumptions are audited.
- Whether current Nsight Compute metrics and units in plotting/correlation need new SM120 mappings before they can validate remodeled stats.

## Design Decision Summary

- `SM120_BASE` is the architecture/model layer, not a runnable config.
- Per-GPU overlays own SKU facts and reported device limits.
- Calibration result files own measured/searched timing, memory, scheduler, RF, PRT/interwarp, and power values.
- Generated `tested-cfgs` are compatibility outputs with manifests.
- Existing flat `SM120_RTX5070_TI` and `SM120_RTX5060` configs should remain unchanged until generated outputs have passed review and smoke/correlation checkpoints.
- The S4 generator must validate required fields and cross-file latency consistency; the legacy tuner line-replacement template is not sufficient for SM120.
