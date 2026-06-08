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
| S5 | Not started | Add staged microbenchmark calibration | Add or adapt microbenchmarks and parsers for directly measurable parameters, with isolated tests where practical. |
| S6 | Not started | Add targeted correlation search | Implement small, staged search for parameters not directly measurable, using simulator runs on the strong local server and hardware data from `dsp5060`. |
| S7 | Not started | Validate on RTX5060 and preserve RTX5070Ti compatibility | Run smoke, calibration, and correlation checks; produce final configs/reports. |
| S8 | Not started | Documentation and release checkpoint | Document workflow, limitations, reproduction commands, and checkpoint commits. |

## Current Active Stage

S5: Add staged microbenchmark calibration.

S0 through S4 are complete. S5 is ready to start.

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
