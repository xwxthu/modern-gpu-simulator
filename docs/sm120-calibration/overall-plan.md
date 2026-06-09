# SM120 Calibration Overall Plan

Base repo: `/home/xiewx/accel-0608/modern-gpu-simulator`

Initial branch: `dev-5060`

Initial base commit: `b52920c838b752fcfd6ca9e1557ae924cdc36cb1`

Initial timestamp: `2026-06-08 17:41:35 CST`

## Objective

Make the modern simulator maintainable as:

1. A common SM120/Blackwell architecture model.
2. GPU-specific hardware parameter definitions.
3. A runnable calibration flow that can produce and validate per-GPU configs for SM120-series GPUs.

## Stage Plan

| Stage | Status | Goal | Acceptance Criteria |
| --- | --- | --- | --- |
| S0 | Complete | Establish documentation and governance | Supervisor log, overall plan, and worker log rules exist and are committed or ready for checkpoint. |
| S1 | Complete | Audit current parameter/config/calibration surface | Produce a parameter taxonomy for SM120 configs and remodeled source constants; identify config-driven, hardcoded, measurable, and search-only parameters. |
| S2 | Complete | Design SM120 configuration layering | Define `SM120_BASE` plus per-GPU overlay strategy; specify file layout and generation rules without breaking existing configs. |
| S3 | Complete | Modernize calibration prerequisites | Plan and implement CUDA 13.2 / SM120 microbenchmark build support, `.venv`, and hardware collection interface using official tools. |
| S4 | Complete | Extend tuner/config generation | Update tuner templates and parsing so it can generate complete modern SM120 configs, including remodeled parameters. |
| S5 | Complete | Add staged microbenchmark calibration | Add or adapt microbenchmarks and parsers for directly measurable parameters, with isolated tests where practical. |
| S6 | Complete | Add targeted correlation search | Implement small, staged search for parameters not directly measurable, using simulator runs on the strong local server and hardware data from `dsp5060`. |
| S7 | In progress | Validate on RTX5060 and preserve RTX5070Ti compatibility | Run smoke, calibration, and correlation checks; produce final configs/reports. |
| S8 | Not started | Documentation and release checkpoint | Document workflow, limitations, reproduction commands, and checkpoint commits. |

## Current Active Stage

S7: Validate on RTX5060 and preserve RTX5070Ti compatibility.

S0 through S6 are complete. S7 smoke bring-up is in progress. CUDA 13 runtime ABI, trace-driven runtime linking, runtime trace option registration, CUDA 13.1 `ptxas` parsing, runtime opcode-latency option lifetime, remodeled per-SM stats initialization, PTX-mode remodeled fetch PC/function-id handling, PTX-mode predicate-latency trace metadata guarding, PTX-mode memory-latency handling, PTX-mode scoreboarding/register-file trace metadata separation, PTX-mode memory access address setup, PTX-mode IBuffer instruction ownership, PTX-mode LD/ST trace metadata separation, PTX-mode parameter constant routing, PTX-mode post-execution memory-latency regeneration, PTX-mode variable-size IBuffer fetch/decode, PTX scalar ALU pipeline classification, and PTX functional PC/SIMT-stack synchronization have been fixed for the observed local smoke. The current precise blocker is a PTX barrier metadata assertion in `barrier_set_t::warp_reaches_barrier()`: `bar_id != (unsigned)-1` fails at `shader.cc:3867` after the smoke reaches the `bar.sync 0` reconvergence region; focused evidence shows `bar_type = SYNC` and timing-side `bar_id = 4294967295`, likely because PTX `bar.sync` id/count metadata is not propagated back into the dynamic timing `warp_inst_t`. Real simulator metrics and real supplied-metrics correlation are still pending.

## Checkpoint Policy

Commit at stable points:
- After S0 documentation setup.
- After S1 audit deliverables.
- After S2 configuration layering design or implementation.
- After each working calibration pipeline milestone.

Do not commit generated bulk data unless it is intentionally small, stable, and needed for reproducibility.

## Known Constraints

- No RTX5060 on the local simulator server.
- Use `ssh dsp5060` only for GPU-dependent hardware collection.
- Avoid running full simulator workloads on `dsp5060`.
- Prefer CUDA 13.2-compatible tooling.
- Avoid large destructive restructures when a hard blocker should instead be discussed.
