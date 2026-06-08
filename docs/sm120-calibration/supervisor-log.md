# SM120 Calibration Supervisor Log

## Restated User Requirements

Purpose: evolve `modern-gpu-simulator` into a simulator organized as "SM120 architecture modeling is common across the architecture, while GPU-specific hardware parameters have a runnable calibration flow".

Repository scope:
- Develop in `/home/xiewx/accel-0608/modern-gpu-simulator`.
- Use `/home/xiewx/accel-0608/accel-sim-framework` only as a reference.
- `ref-docs/` contains the Accel-Sim paper and the MICRO25 NVIDIA reverse-engineering paper and should be used as reference material.

Background:
- The MICRO25 paper substantially remodeled Accel-Sim and claims Blackwell support.
- The artifact appears to have been tested only on RTX 5070 Ti.
- It does not yet provide an Accel-Sim-style calibration flow for SM120-series GPUs.
- The local `dev-5060` branch has adapted the artifact enough to run on RTX 5060, but the desired end state is not a 5060-specific simulator. It should be an SM120-common model plus per-GPU calibrated parameter sets.

Hardware and execution constraints:
- This server is suitable for building and running the simulator, but it does not have an RTX 5060.
- The RTX 5060 is available through `ssh dsp5060`.
- The GPU server should be used only for GPU-dependent collection work. Do not run full simulator workloads there, and do not place the main workspace there.
- Create and manage a local Python `.venv` as needed.
- Target the modern toolchain, including CUDA 13.2 rather than the old Accel-Sim-era CUDA/nvprof flow.

Obstacle policy:
- For hardware parameters readable through NVIDIA official tools, read them directly.
- For parameters that cannot be read directly, design microbenchmarks that isolate one parameter as much as practical.
- Avoid brute-force search over a large parameter space. Use staged microbenchmark measurement first, then small targeted correlation searches.
- If a very difficult obstacle appears, pause for discussion rather than using a complex workaround that heavily damages code structure.
- The framework should remain useful even if future Blackwell/SM120 architecture modeling changes.

Required workflow:
- The supervisor sets stage goals, manages logs/plans, delegates implementation to subagent workers, and records key actions.
- Workers may create their own scoped plans/logs but must follow the documentation scheme.
- Each worker must review its own work by spawning a secondary reviewer. The worker should address worthwhile reviewer feedback and repeat with a fresh reviewer until the reviewer accepts the result.
- After a worker reports completion, the supervisor spawns an independent reviewer. If needed, the supervisor returns the task for rework.
- At stable checkpoints, the supervisor updates the overall plan and creates git commits with reasonably detailed commit messages.
- Prefer blank-context subagents. Each subagent must understand its own role and mission.
- The supervisor should avoid doing the worker's implementation work directly.
- If context compaction occurs, first reread this log section and `overall-plan.md`, then continue.

## Documentation Scheme

Directory: `docs/sm120-calibration/`

Required files:
- `supervisor-log.md`: top-level chronological log owned by the supervisor.
- `overall-plan.md`: stage plan, acceptance criteria, current status, and checkpoint history.
- `worker-logs/`: worker/reviewer-created logs. A worker log must include purpose, base commit, branch/worktree state, timestamp, assigned scope, actions, evidence, changed files, reviewer rounds, and final status.
- `handoffs/`: optional worker handoff summaries when useful.

Naming:
- Worker logs: `worker-YYYYMMDD-HHMMSS-<short-topic>.md`.
- Reviewer notes inside worker logs are preferred. If a separate reviewer note is needed: `reviewer-YYYYMMDD-HHMMSS-<short-topic>.md`.

Log rules:
- Use precise repository paths.
- Record commit hash and timestamp for every stage start and completion.
- Mark whether changes are documentation-only, code, scripts, experiments, or generated outputs.
- Record commands and results only when they are important evidence.

## Chronological Log

### 2026-06-08 17:41:35 CST

Base repository state:
- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base commit: `b52920c838b752fcfd6ca9e1557ae924cdc36cb1`
- Working tree: clean at initial supervisor setup

Action:
- Started a fresh documentation scheme for the SM120 calibration effort.
- Created the top-level restatement and governance log for the requested supervisor/worker/reviewer workflow.

### 2026-06-08 17:43:47 CST

Action:
- Spawned S1 audit worker `019ea69c-fe3c-7a02-a71e-93ff5d7a96f8`.
- Spawned S0 documentation reviewer `019ea69d-4575-7911-a5e6-1dcdb1d15945`.

Reviewer result:
- Recommendation: accept.
- Finding: S0 status in `overall-plan.md` was still `Not started` despite S0 being established.

Follow-up:
- Updated S0 status to `Complete`.
- Marked S1 as the current active stage.

### 2026-06-08 18:02:34 CST

Action:
- S1 audit worker `019ea69c-fe3c-7a02-a71e-93ff5d7a96f8` completed `docs/sm120-calibration/worker-logs/worker-20260608-174813-s1-audit.md`.
- The worker reported one internal blank-context reviewer round with verdict `ACCEPT`.
- Spawned independent supervisor reviewer `019ea6a8-1149-7112-8bf4-fcb34fe9a723`.

Supervisor reviewer result:
- Recommendation: accept.
- Findings were low severity only:
  - Add explicit `Actions` and `Changed Files` sections.
  - Clarify actual `trace.config` path.
  - Clarify compute capability ownership as `SM120_BASE` rather than per-GPU overlay.

Follow-up:
- Returned low-severity fixes to the worker.
- Worker updated the S1 log accordingly.
- Marked S1 complete and S2 ready to start in `overall-plan.md`.

Checkpoint:
- Commit `841066382f610876adf9f94ca1a0e49e579e5b11` (`docs: audit SM120 calibration surface`) recorded the S1 audit deliverable.

### 2026-06-08 18:06:40 CST

Action:
- Spawned S2 config-layering worker `019ea6b0-6f02-71e0-aad3-78aca1febf69`.

Worker deliverables:
- `docs/sm120-calibration/config-layering-design.md`
- `docs/sm120-calibration/worker-logs/worker-20260608-181124-s2-config-layering.md`

Worker internal review:
- Round 1 blank-context reviewer verdict: accept.
- After supervisor rework request, Round 2 blank-context reviewer verdict: accept.

Supervisor review:
- First supervisor reviewer `019ea6bc-d888-7871-86c6-1cb03239d7a8` returned `changes-needed`.
- Required fixes:
  - Active-key ownership/profile policy for launch timing, L0I timing, instruction prefetch, and custom OMP scheduler controls.
  - Generator failure if an active option lacks schema owner/profile/provenance policy.
  - Bootstrap golden-diff behavior for implicit defaults such as omitted `-power_simulation_enabled 0`.
  - `extra_params` provenance bypass handling.

Follow-up:
- Worker completed rework and second internal review.
- Second supervisor reviewer `019ea6c6-010c-7521-8642-96a709309b32` returned `accept`.
- Marked S2 complete and S3 ready to start in `overall-plan.md`.

Checkpoint:
- Commit `43b69223a07c0d66cfd1a3111cff2b9aec93787a` (`docs: design SM120 config layering`) recorded the S2 design deliverable.

### 2026-06-08 18:40:42 CST

Action:
- Spawned S3 prerequisites worker `019ea6c9-1891-7640-880a-0a601e60fa28`.

Worker deliverables:
- `.gitignore`
- `docs/sm120-calibration/calibration-prereqs.md`
- `docs/sm120-calibration/worker-logs/worker-20260608-185309-s3-prereqs.md`
- `simulator-remodeled/util/hw_stats/collect_sm120_device_info.py`
- SM120 tuner build and draft `hw_def` changes under `simulator-remodeled/util/tuner/GPU_Microbenchmark/`
- CUDA 13.x compatibility updates for selected tuner microbenchmarks.

Worker validation:
- Python syntax check for `collect_sm120_device_info.py`.
- Dry-run and remote lightweight official-tool collection against `dsp5060`.
- `make -n` checks for CUDA path, `CUDA_ARCH=sm_120`, and `HW_DEF` behavior.
- Local CUDA 13.1 compile checks for selected tuner microbenchmarks.
- `git diff --check`.

Supervisor review:
- First supervisor reviewer `019ea6f5-1dcd-7ff3-89b1-ba1a24dd18f7` returned `changes-needed`.
- Required fix: avoid printing `CUDA Cores per multiprocessor : 0` for SM120/unknown architectures in tuner `system/deviceQuery`.

Follow-up:
- Worker changed unknown SM core-count output to `unknown for sm_XY` rather than inventing a value.
- Worker documented the behavior and ran an additional blank-context reviewer round.
- Second supervisor reviewer `019ea701-f1aa-73e2-9f43-07f97fd0d478` returned `accept`.
- Marked S3 complete and S4 ready to start in `overall-plan.md`.

Checkpoint:
- Commit `21853fa204f1cce3bde636705edf9b8e90051974` (`feat: add SM120 calibration prerequisites`) recorded the S3 prerequisite deliverable.

### 2026-06-08 19:54:31 CST

Action:
- Spawned S4 generator worker `019ea706-5791-75d3-b320-c881bd8cdbc1`.

Worker deliverables:
- Layered SM120 bootstrap inputs under `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/`.
- Trace render rules under `simulator-remodeled/gpu-simulator/configs/layered/sm120/`.
- Generator script `simulator-remodeled/util/tuner/generate_sm120_configs.py`.
- Generated bootstrap configs under mirrored `configs/generated/tested-cfgs/SM120_*` roots.
- Generated job-launch aliases `RTX5060_SM120_GEN` and `RTX5070_TI_SM120_GEN`.
- `docs/sm120-calibration/s4-config-generator.md`.
- `docs/sm120-calibration/worker-logs/worker-20260608-195431-s4-generator.md`.

Worker validation:
- `generate_sm120_configs.py` generation and `--check-only`.
- Python syntax check.
- `git diff --check`.
- Generated-output reproducibility hash diff.
- Active golden equivalence checks for `gpgpusim.config` and `trace.config`.
- Manifest spot checks for script/input hashes and provenance inventory.

Supervisor review:
- First supervisor reviewer `019ea723-fde3-79c0-a8db-c1a6def9dbb2` returned `changes-needed`.
- Required fix: enforce path safety for overlay `config_name`, generated output roots, and flat source roots.

Follow-up:
- Worker added safe `config_name` validation, resolved-root output checks, and source-root validation for flat bootstrap files.
- Worker added negative path tests and a third blank-context reviewer round.
- Second supervisor reviewer `019ea733-bd29-7031-bd73-1a373a1fc693` returned `accept`.
- Marked S4 complete and S5 ready to start in `overall-plan.md`.
