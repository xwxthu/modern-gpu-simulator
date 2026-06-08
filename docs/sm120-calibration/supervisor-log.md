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

Checkpoint:
- Commit `c0660f6a736854e81724ddbb9ffa27ce17834e13` (`feat: generate layered SM120 bootstrap configs`) recorded the S4 generated-bootstrap deliverable.

### 2026-06-08 20:44:04 CST

Action:
- Spawned S5 microbenchmark-calibration worker `019ea742-bc97-7632-b96e-fe6ea904735c`.

Worker deliverables:
- `simulator-remodeled/util/tuner/parse_sm120_microbench.py`
- `simulator-remodeled/util/tuner/testdata/sm120_microbench_sample.txt`
- `simulator-remodeled/util/tuner/testdata/sm120_system_config_sample.txt`
- `simulator-remodeled/util/tuner/testdata/sm120_human_devicequery_sample.txt`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema/calibration-result.schema.yaml`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/calibration-results/samples/RTX5060-microbench-draft.yaml`
- `docs/sm120-calibration/s5-microbenchmark-calibration.md`
- `docs/sm120-calibration/worker-logs/worker-20260608-204404-s5-microbench.md`
- S4 handoff note in `docs/sm120-calibration/s4-config-generator.md`

Worker validation:
- Parser Python syntax check.
- Microbenchmark fixture parse and byte-for-byte sample draft reproducibility.
- Tuner `system_config` config-line fixture parse.
- Human-readable CUDA `deviceQuery` negative fixture and empty-input negative checks.
- `--fail-on-unsupported` exits with status `2`.
- `generate_sm120_configs.py --check-only`.
- `git diff --check`.
- Flat SM120 configs, S4 generated configs, and `generate_sm120_configs.py` status remain clean.

Supervisor review:
- First supervisor reviewer `019ea762-bc92-75b1-926b-5eef8af9b38a` returned `changes-needed`.
- Required fixes:
  - The parser and docs overstated `device_query` support; the code only parsed config-style lines and should not imply raw `nvidia-smi` or human-readable CUDA `deviceQuery` parsing.
  - Raw parser drafts should keep `handoff.do_not_claim_calibrated: true`.
  - The unsupported sample-key explanation should match `key_not_in_s5_supported_stage_map`.

Follow-up:
- Worker narrowed parser source types to `microbenchmark` and `system_config`.
- Worker documented that raw `nvidia-smi` and human-readable CUDA `deviceQuery` text are unsupported by the S5 parser and must be converted to reviewed config-style lines first.
- Worker added negative empty-input and human-readable `deviceQuery` checks.
- Worker made all raw parser drafts keep `handoff.do_not_claim_calibrated: true`.
- Worker updated the unsupported-key documentation and reran blank-context reviewer rounds until Round 3 returned `ACCEPT`.
- Second supervisor reviewer `019ea776-7af5-7bc3-9446-6ac1be7d45e3` returned `ACCEPT`.
- Marked S5 complete and S6 ready to start in `overall-plan.md`.

Checkpoint:
- Commit `a517d1962eaef8b0e73172dd99c149b20ef58f39` (`feat: add staged SM120 microbenchmark parser`) recorded the S5 draft-parser deliverable.

### 2026-06-08 21:56:32 CST

Action:
- Spawned S6 targeted-correlation-search worker `019ea77d-8d3c-7791-b821-53859905f854`.

Worker deliverables:
- `simulator-remodeled/util/tuner/search_sm120_correlation.py`
- `simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/schema/correlation-search.schema.yaml`
- `simulator-remodeled/util/tuner/testdata/sm120_correlation_search_fixture.yaml`
- `simulator-remodeled/util/tuner/testdata/sm120_correlation_search_fixture_report.yaml`
- `simulator-remodeled/util/tuner/testdata/sm120_correlation_search_invalid_unknown_key.yaml`
- `simulator-remodeled/util/tuner/testdata/sm120_correlation_search_invalid_unbounded.yaml`
- `docs/sm120-calibration/s6-correlation-search.md`
- `docs/sm120-calibration/worker-logs/worker-20260608-215632-s6-correlation.md`

Worker validation:
- Correlation-search harness Python syntax check.
- Fixture report generation and byte-for-byte reproducibility against checked-in sample report.
- Dry-run planned-command mode prints plan-only commands with `-n`.
- Invalid unknown-key and unbounded-range manifests fail cleanly.
- `generate_sm120_configs.py --check-only`.
- `git diff --check`.
- Flat SM120 configs, S4 generated configs, and `generate_sm120_configs.py` status remain clean.

Supervisor review:
- First supervisor reviewer `019ea796-93fc-7662-bb9e-b40077ac871b` returned `changes-needed`.
- Required fix: `check_output_target()` protected SM120 layered subdirectories but allowed output directly under top-level `gpgpu-sim/configs/layered/sm120/`.

Follow-up:
- A focused S6 rework worker `019ea79a-c4e7-7572-a6a1-51b4619572fd` updated path protection to reject the entire SM120 layered source directory root and all child paths.
- The rework added a negative test for `gpgpu-sim/configs/layered/sm120/s6-report.yaml`.
- The worker updated the fixture report hash and S6 worker log, then reran blank-context reviewer rounds until Round 3 returned `ACCEPT`.
- Second supervisor reviewer `019ea79f-9021-77f2-a9cd-9800e16712bb` returned `ACCEPT`.
- Marked S6 complete and S7 ready to start in `overall-plan.md`.

Checkpoint:
- Commit `e37d55a8c7c77b3f3c164cbd1678e1624ed790b4` (`feat: add bounded SM120 correlation search`) recorded the S6 bounded-parameter-sweep deliverable.

### 2026-06-08 22:51:29 CST

Action:
- Spawned S7 validation-planning worker `019ea7a8-2080-7390-b229-b87ef5cbf12c`.

Worker deliverables:
- `.gitignore` update for `artifacts/s7/`.
- `docs/sm120-calibration/s7-validation-runbook.md`.
- `docs/sm120-calibration/s7-validation-manifest-template.yaml`.
- `simulator-remodeled/util/tuner/check_sm120_s7_validation.py`.
- `docs/sm120-calibration/worker-logs/worker-20260608-225129-s7-validation.md`.

Worker validation:
- S7 helper Python syntax check.
- S7 helper dry-run checks for `RTX5060` and `RTX5070_TI`.
- S7 helper command-plan mode prints commands without executing hardware collection or simulator workloads.
- `generate_sm120_configs.py --check-only`.
- S6 fixture dry-run planned-command check.
- Manifest-template YAML parsing and required-standard-term checks.
- `git diff --check`.

Worker internal review:
- Round 1 returned `CHANGES NEEDED` because the RTX5070Ti helper output could imply hardware collection on `dsp5060` by default.
- Worker added `--include-hardware-plan` and made non-RTX5060 hardware collection planning opt-in.
- Round 2 returned `ACCEPT`.

Supervisor review:
- Supervisor reviewer `019ea7ba-06d3-7e02-95ae-fdd2c83478bb` returned `ACCEPT`.
- Reviewer confirmed:
  - Standard terms are used: hardware characterization, microbenchmark calibration, parameter sweep, correlation/validation, smoke test, promotion gate.
  - `dsp5060` is collection-only and local server owns simulator smoke/correlation.
  - Fixture/sample output is not treated as real calibration evidence.
  - Draft parser/search output is not auto-applied to accepted configs or `latest.yaml`.
  - RTX5070Ti hardware collection is opt-in; default compatibility checks are config/alias/static checks.

Follow-up:
- Marked S7 `In progress` in `overall-plan.md`, not complete.
- Pending S7 work remains: real RTX5060 hardware characterization, RTX5060 tuner microbenchmark collection, local S5 parse review, local simulator smoke tests, real supplied-metrics correlation search, and promotion-gate review.

Checkpoint:
- Commit `252376a235cb984e6b7780da3b1888be021c61eb` (`docs: add SM120 S7 validation runbook`) recorded the S7 runbook and dry-run planner checkpoint.

### 2026-06-08 23:12:05 CST

Action:
- Spawned S7 RTX5060 collection worker `019ea7bf-ef86-7032-a30a-deacf3a418ee`.

Worker deliverables:
- `docs/sm120-calibration/worker-logs/worker-20260608-231205-s7-rtx5060-collection.md`.
- Local run evidence under ignored `artifacts/s7/rtx5060-s7-20260608-230140/`.
- Local dry-run evidence under ignored `artifacts/logs/`.

Worker validation:
- Local RTX5060 dry-run planner passed.
- Official-tool collector on `dsp5060` passed and recorded hardware characterization data locally.
- CUDA 13.2 was found at `/usr/local/cuda-13.2`; `nvcc --list-gpu-code` includes `sm_120`.
- Tuner build on `dsp5060` failed before `run_all.sh`.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Accepted config diff check was empty.

Hardware characterization evidence:
- GPU: `NVIDIA GeForce RTX 5060`.
- Driver: `595.71.05`.
- Compute capability: `12.0`.
- UUID: `GPU-fd113d06-81ba-5c47-6fbe-fd8f1b99f80e`.
- Observed clocks and memory state were recorded in the ignored S7 artifact manifest.

Blocker:
- Real tuner microbenchmark collection is blocked by a CUDA 13.2 build failure:
  `l1_access_grain.cu(54): error: identifier "uint32_t" is undefined`.
- `run_all.sh` was not run.
- S5 parsing was skipped because no real microbenchmark output exists.
- S6 real supplied-metrics parameter sweep and local simulator smoke remain pending.

Supervisor review:
- Supervisor reviewer `019ea7d7-45a8-7ca0-9a51-21e8d53ddcad` returned `ACCEPT`.
- Reviewer confirmed the partial/blocked conclusion is supported, no full simulator ran on `dsp5060`, no main workspace was placed on `dsp5060`, and no accepted configs or `latest.yaml` were modified.
- Low-severity reviewer finding: `artifacts/logs/` was not ignored. Added `artifacts/logs/` to `.gitignore`.

Checkpoint:
- Commit `a5d058aeff82caf55df90281a5eec88da11d9cc8` (`docs: record RTX5060 S7 collection blocker`) recorded the partial RTX5060 hardware-characterization checkpoint and tuner build blocker.

### 2026-06-08 23:51:02 CST

Action:
- Spawned S7 tuner build-fix worker `019ea7dc-28c6-7b92-892f-bf929eb1d7cb`.

Worker deliverables:
- Added `<cstdint>` to five CUDA tuner microbenchmark sources using `uint32_t` in adjacent access-grain/write-policy/memory-atom tests.
- `docs/sm120-calibration/worker-logs/worker-20260608-235102-s7-tuner-buildfix.md`.
- Local run evidence under ignored `artifacts/s7/rtx5060-s7-tuner-buildfix-20260608-233545/`.

Source fix:
- Fixed the CUDA 13.2 `uint32_t` compile blocker with standard fixed-width integer headers rather than a macro workaround.
- No broad source sweep or unrelated tuner rewrite was performed.

Worker validation:
- Local CUDA 13.1 compile smoke passed for the five changed sources.
- `dsp5060` CUDA 13.2 preflight passed and confirmed `sm_120` support.
- Tuner build on `dsp5060` passed with exit code `0` and produced `58` binaries.
- `./run_all.sh` on `dsp5060` passed with exit code `0` and produced `438` output lines.
- S5 parser produced `artifacts/s7/rtx5060-s7-tuner-buildfix-20260608-233545/RTX5060-real-microbench-draft.yaml`.
- The S5 draft has `status: draft_not_applied`, `fixture_only: false`, and `handoff.do_not_claim_calibrated: true`.
- S5 parse summary: `76` parsed config lines, `63` supported, `13` unsupported, `0` duplicate conflicts.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Accepted/generated config scoped status check was empty.

Supervisor review:
- Supervisor reviewer `019ea7f8-690f-7ed1-a4ef-2ee75c9640ae` returned `ACCEPT`.
- Reviewer confirmed the source diff only adds `#include <cstdint>` to the five target sources, artifact hashes verify, CUDA 13.2 tuner build/run evidence is sufficient, S5 draft-only semantics are preserved, and no accepted configs or `latest.yaml` were modified.
- Informational reviewer note: three originally CRLF `.cu` files now have one LF-only inserted include line; `git diff --check` passes.

Follow-up:
- Promotion gate remains closed. The real microbenchmark draft is raw single-run evidence and has not been copied into accepted configs, `latest.yaml`, or generated SM120 configs.
- Pending S7 work remains: review unsupported S5 keys, run local simulator smoke tests, construct real supplied-metrics S6 correlation manifests, run bounded local correlation if needed, and perform promotion-gate review.

Checkpoint:
- Commit `bade0d0bc4304f5aa3826b3ca572a14c3a30a22f` (`fix: restore CUDA 13 tuner microbench builds`) recorded the CUDA 13 tuner build fix and real RTX5060 microbenchmark draft collection checkpoint.

### 2026-06-09 00:08:56 CST

Action:
- Spawned S7 local smoke/correlation-prep worker `019ea7fc-9997-7000-b2e8-ed554a743f04`.

Worker deliverables:
- `docs/sm120-calibration/worker-logs/worker-20260609-000856-s7-local-smoke.md`.
- Local run evidence under ignored `artifacts/s7/rtx5060-s7-local-smoke-20260609-000856/`.

Worker validation:
- Local `generate_sm120_configs.py --check-only` passed.
- S7 helper dry-run for RTX5060 passed.
- S6 fixture dry-run and planned-command check passed.
- Local smoke setup-only command with `run_simulations.py ... -n` was attempted on the local server.
- `git diff --check` passed.
- Accepted/generated config scoped status check was empty.

Blocker:
- Local smoke setup-only failed before run-directory creation because local build prerequisites are missing:
  `gpgpu-sim/lib/gcc-13.3.0/cuda-13010/release`.
- Local inspection also found no `simulator-remodeled/gpu-app-collection/bin`.
- No local simulator job was launched.
- No full simulator ran on `dsp5060`.

Supplied-metrics status:
- Worker prepared only a template skeleton:
  `artifacts/s7/rtx5060-s7-local-smoke-20260609-000856/RTX5060-s6-supplied-metrics.TEMPLATE.yaml`.
- The template has `candidate_metrics: []` and no fabricated metrics.
- No real S6 ranking report was generated.

Supervisor review:
- Supervisor reviewer `019ea80f-7615-7363-ab8c-04bf6bbb0292` returned `ACCEPT`.
- Reviewer confirmed the partial/blocked conclusion is supported, no simulator job was launched, the supplied-metrics file is template-only, artifact hashes verify, and protected config/latest paths are clean.

Follow-up:
- Pending S7 work remains: build the local GPGPU-Sim release library and gpu-app binaries, rerun setup-only smoke planning, then intentionally run one local smoke only after setup is reviewed.
