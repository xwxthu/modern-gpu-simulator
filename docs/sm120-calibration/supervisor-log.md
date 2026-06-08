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

Checkpoint:
- Commit `6c0329df63d8e789c238725dcc0bb029b7edb2f9` (`docs: record S7 local smoke prerequisites`) recorded the local smoke blocked checkpoint.

### 2026-06-09 00:42:33 CST

Action:
- Spawned S7 local build-prerequisite worker `019ea812-a2b0-77f3-896a-833eb472f711`.

Worker deliverables:
- `docs/sm120-calibration/worker-logs/worker-20260609-004233-s7-local-build.md`.
- CUDA 13 build-compatibility source changes in GPGPU-Sim and the minimal Rodinia backprop app path.
- Local build evidence under ignored `artifacts/s7/s7-local-build-20260609-003407/`.

Source fixes:
- Guarded `cudaDeviceProp::clockRate` assignment for CUDA versions before 13.
- Suppressed CUDA gencodes removed by CUDA 13 for gpu-app builds.
- Replaced Rodinia backprop `cudaThreadSynchronize()` with `cudaDeviceSynchronize()`.
- Fixed exact benchmark selectors in `util/job_launching/common.py` so `suite:exe:index` preserves the full run-parameter dictionary.

Worker validation:
- Built local GPGPU-Sim release library using real CUDA 13.1:
  `simulator-remodeled/gpu-simulator/gpgpu-sim/lib/gcc-13.3.0/cuda-13010/release/libcudart.so`.
- Built local `simulator-remodeled/gpu-simulator/bin/release/accel-sim.out`.
- Built local Rodinia backprop binary:
  `simulator-remodeled/gpu-app-collection/bin/13.1/release/backprop-rodinia-2.0-ft`.
- Confirmed CUDA 13.2 is not installed locally; `cuda-13010` is the existing setup script's directory name for CUDA 13.1.
- `run_simulations.py ... -n` setup-only passed for `rodinia_2.0-ft:backprop-rodinia-2.0-ft:0` and created run files under ignored `artifacts/s7/s7-local-build-20260609-003407/sim-smoke-plan/`.
- No actual simulator job was launched.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Accepted/generated config scoped status check was empty.

Supervisor review:
- Supervisor reviewer `019ea824-9182-7a63-9ba6-a8aa0e05182c` returned `ACCEPT`.
- Reviewer confirmed the CUDA 13 fixes are narrow, the exact-selector fix is correct, build outputs exist and are ELF files, setup-only planning succeeded without `procman.py` launch evidence, and protected config/latest paths are clean.

Follow-up:
- Pending S7 work remains: reviewed Rodinia data provisioning for `./data/result-4096.txt`, then one intentional local smoke run, followed by real supplied-metrics correlation if smoke metrics are available.

Checkpoint:
- Commit `287ead489912718dbc3b3c93c656060800107d03` (`fix: support CUDA 13 local smoke setup`) recorded the local CUDA 13 build-prerequisite fixes and setup-only smoke success.

### 2026-06-09 01:08:04 CST

Action:
- Spawned S7 actual local smoke worker `019ea829-81a4-75f0-9e54-e46328c22921`.

Worker deliverables:
- `docs/sm120-calibration/worker-logs/worker-20260609-010804-s7-actual-smoke.md`.
- Local run evidence under ignored `artifacts/s7/s7-actual-smoke-20260609-005843/`.

Worker validation:
- Provisioned Rodinia backprop `result-4096.txt` locally from a native backprop run and recorded SHA256.
- Reran local setup-only smoke planning with `run_simulations.py ... -n`; setup-only passed.
- Launched exactly one local smoke job for `rodinia_2.0-ft:backprop-rodinia-2.0-ft:0` using `RTX5060_SM120_GEN`.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Accepted/generated config scoped status check was empty.

Partial result:
- The actual local smoke job did not complete and produced no real simulator metrics.
- No `gpu_tot_sim_cycle`, simulation time, simulator exit marker, or functional PASS/FAIL was found.
- No real `supplied_metrics` manifest or S6 ranking report was created.
- Procman left stale `RUNNING` state for a dead PID; worker archived the stale state evidence and cleaned it. Post-cleanup procman status was `Nothing Active`.
- No simulator job ran on `dsp5060`.

Supervisor review:
- Supervisor reviewer `019ea83c-3eae-7810-b795-55415fad0d98` returned `ACCEPT`.
- Reviewer confirmed data provisioning is reasonable, exactly one local job was queued, no fake metrics were created, artifact hashes verify, stale procman state was cleaned, and protected config/latest paths are clean.

Follow-up:
- Pending S7 work remains: debug why the local smoke job exits without moved logs or simulator metrics, rerun one local smoke after the debug fix, then generate real supplied-metrics correlation input only if real metrics exist.

Checkpoint:
- Commit `d313077c758707d0a8951cf2b0349db4a1e76633` (`docs: record S7 actual smoke attempt`) recorded the first actual local smoke attempt and its no-metrics partial result.

### 2026-06-09 01:38:54 CST

Action:
- Spawned S7 local smoke debug worker `019ea840-b75e-7bd0-a22a-49e788506118`.

Worker deliverables:
- `simulator-remodeled/util/job_launching/procman.py`.
- `docs/sm120-calibration/worker-logs/worker-20260609-013854-s7-smoke-debug.md`.
- Local debug evidence under ignored `artifacts/s7/s7-smoke-debug-20260609-013048/`.

Root cause fixed:
- The local procman manager was started as a normal child of `run_simulations.py`; in this execution environment it could die with the parent session before the job wrapper copied output.
- `ProcMan.spawnProcMan()` now starts the manager in a new session with stdio redirected to `DEVNULL`.

Worker validation:
- Mini repro showed stale `RUNNING` state before the fix and `Nothing Active` after the detach fix.
- Setup-only local smoke planning passed.
- Exactly one local smoke job was launched on `dsp-ubuntu`, not `dsp5060`.
- The job reached `FUNC_TEST_PASSED`, moved `.o1/.e1` outputs into the run directory, and produced `result.txt` matching the provisioned gold file.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Accepted/generated config scoped status check was empty.

Remaining blocker:
- The smoke still produced no real simulator metrics.
- Evidence indicates the CUDA 13.1 app loads system `/usr/local/cuda-13.1/lib64/libcudart.so.13` instead of the GPGPU-Sim runtime.
- Current GPGPU-Sim runtime exposes only unversioned/older `libcudart.so` aliases through `libcudart.so.12.0` and lacks CUDA 13 symbol/version support such as `__cudaGetKernel@libcudart.so.13`.
- No `supplied_metrics` manifest or S6 real ranking was created.

Supervisor review:
- Supervisor reviewer `019ea856-701c-7c42-a172-a050867e406f` returned `ACCEPT`.
- Reviewer confirmed the procman fix is minimal, stale-state evidence supports the root cause, the new smoke reached `FUNC_TEST_PASSED`, no fake metrics were created, protected config/latest paths are clean, and the CUDA 13 runtime ABI blocker is supported by dynamic-link evidence.

Follow-up:
- Pending S7 work remains: add reviewed CUDA 13 `libcudart.so.13` ABI support to the GPGPU-Sim runtime, rebuild, rerun one local smoke, then generate real supplied-metrics correlation input only if real simulator metrics exist.

Checkpoint:
- Commit `3f32727a41fac904b6fa3e4edabd13df5e1ee8c7` (`fix: detach local procman manager`) recorded the procman detach fix and functional local smoke without simulator metrics.

### 2026-06-09 02:08:40 CST

Action:
- Spawned S7 CUDA 13 runtime ABI worker `019ea85b-90ae-7313-b485-1ee37ac86621`.

Worker deliverables:
- `simulator-remodeled/gpu-simulator/gpgpu-sim/Makefile`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/linux-so-version.txt`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/libcuda/cuda_api_object.h`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/libcuda/cuda_runtime_api.cc`.
- `simulator-remodeled/util/job_launching/run_simulations.py`.
- `docs/sm120-calibration/worker-logs/worker-20260609-020840-s7-cuda13-abi.md`.
- Local ABI/smoke evidence under ignored `artifacts/s7/s7-cuda13-abi-20260609-015602/`.

Worker validation:
- Rebuilt GPGPU-Sim runtime with `SONAME libcudart.so.13`, `libcudart.so.13` symlink, and `libcudart.so.13` version node.
- Exported/bound CUDA 13 app-side runtime symbols including `cudaGetKernel`, `__cudaGetKernel`, `__cudaLaunchKernel`, and `__cudaPopCallConfiguration`.
- Updated local run-dir copying to preserve `libcudart.so.*` aliases.
- Setup-only local smoke planning passed.
- Exactly one local smoke job was launched.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Accepted/generated config scoped status check was empty.

Partial result:
- The CUDA 13 app now resolves `libcudart.so.13` from the copied GPGPU-Sim runtime rather than system CUDA.
- The smoke still produced no real simulator metrics.
- New blocker: runtime loading fails on unresolved trace-driven/remodeling symbol `_ZTV16trace_shd_warp_t` (`vtable for trace_shd_warp_t`).
- Evidence points to trace-driven/remodeling definitions under `trace-driven/` and `util/traces_enhanced/src/` not being linked into the GPGPU-Sim runtime.

Supervisor review:
- Supervisor reviewer `019ea874-9e84-71a0-8de4-38651bd90700` returned `ACCEPT`.
- Reviewer confirmed the ABI changes are narrow, the app binds GPGPU-Sim `libcudart.so.13`, no fake metrics were created, protected config/latest paths are clean, and the new trace-driven symbol blocker is supported by evidence.

Follow-up:
- Pending S7 work remains: link the required trace-driven/remodeling objects into the runtime or otherwise resolve `_ZTV16trace_shd_warp_t`, rebuild, rerun one local smoke, then create real supplied-metrics correlation input only if simulator metrics exist.

Checkpoint:
- Commit `4a32e4c9486ce807978bec5f46017d80aee3ff79` (`fix: add CUDA 13 cudart ABI support`) recorded the CUDA 13 runtime ABI fixes and bounded the next trace-driven runtime link blocker.

### 2026-06-09 02:56:03 CST

Action:
- S7 trace runtime link worker `019ea87e-4940-7961-aed7-4f436885a8b8` completed `docs/sm120-calibration/worker-logs/worker-20260609-023311-s7-trace-link.md`.
- The worker reported one blank-context internal reviewer round with verdict `ACCEPT`.

Worker deliverables:
- `simulator-remodeled/gpu-simulator/gpgpu-sim/Makefile`.
- `docs/sm120-calibration/worker-logs/worker-20260609-023311-s7-trace-link.md`.
- Local link/smoke evidence under ignored `artifacts/s7/s7-trace-link-20260609-023311/`.

Worker validation:
- Rebuilt the CUDA 13.1 release GPGPU-Sim runtime after linking existing trace-driven, trace-parser, enhanced trace, and protobuf object outputs into `libcudart.so` when `TRACE=1`.
- Rebuilt `libcudart.so.13` retained `SONAME libcudart.so.13`, emitted `DT_NEEDED` for zlib/protobuf, and passed `ldd -r`.
- Setup-only local smoke planning passed and copied runtime also passed `ldd -r`.
- Exactly one local smoke job was launched.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Accepted/generated config scoped status check was empty.

Partial result:
- The previous `_ZTV16trace_shd_warp_t` runtime loader blocker is resolved.
- The smoke reached GPGPU-Sim startup and PTX simulation mode output.
- The smoke still produced no real simulator metrics.
- New blocker: config parsing fails with `GPGPU-Sim ** ERROR: Unknown Option: '-is_extra_traces_enabled'`.
- Evidence points to the CUDA runtime entry path registering PTX, interconnect, and `gpgpu_sim_config` options but not registering trace-driven `trace_config` options before parsing `gpgpusim.config`.

Supervisor review:
- Supervisor reviewer `019ea891-0f9c-7292-9df8-e78a01b555cf` returned `ACCEPT`.
- Reviewer confirmed the Makefile change is scoped to trace runtime link inputs, link ordering is correct, the previous loader blocker is resolved by evidence, and the new option-registration blocker is properly bounded rather than hidden.

Follow-up:
- Pending S7 work remains: add a reviewed runtime initialization path for trace-driven `trace_config` option registration, rebuild, rerun one local smoke, then create real supplied-metrics correlation input only if simulator metrics exist.

Checkpoint:
- Commit `e9206095136e1d78c687d89164f0686bf69e95b1` (`fix: link trace runtime into cudart`) recorded the trace runtime link fix and bounded the next trace option registration blocker.

### 2026-06-09 02:57:26 CST

Action:
- Spawned S7 trace config option registration worker `019ea898-82de-7bb0-8614-e71c81ff1f3a`.

Scope:
- Resolve or precisely bound `GPGPU-Sim ** ERROR: Unknown Option: '-is_extra_traces_enabled'` on the CUDA runtime initialization path.
- Prefer a root-cause fix that registers trace-driven `trace_config` options before parsing `gpgpusim.config`, rather than deleting SM120 trace options from generated configs.

### 2026-06-09 03:16:02 CST

Action:
- S7 trace config option registration worker `019ea898-82de-7bb0-8614-e71c81ff1f3a` completed `docs/sm120-calibration/worker-logs/worker-20260609-025836-s7-trace-config.md`.
- The worker reported one blank-context internal reviewer round with verdict `ACCEPT`.

Worker deliverables:
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpusim_entrypoint.cc`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpusim_entrypoint.h`.
- `simulator-remodeled/gpu-simulator/main.cc`.
- `docs/sm120-calibration/worker-logs/worker-20260609-025836-s7-trace-config.md`.
- Local smoke evidence under ignored `artifacts/s7/s7-trace-config-20260609-025836/`.

Worker validation:
- Rebuilt the CUDA 13.1 release GPGPU-Sim runtime.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Setup-only local smoke planning passed.
- Exactly one local smoke job was launched.
- Protected config/latest/generated scoped status was empty.
- Final procman state was `Nothing Active`.

Partial result:
- The previous `Unknown Option: '-is_extra_traces_enabled'` blocker is resolved by registering and parsing trace-driven `trace_config` on the CUDA runtime initialization path.
- The smoke advanced through config parsing and PTX parsing.
- The smoke still produced no real simulator metrics.
- New blocker: CUDA 13.1 `ptxas` resource-output parsing fails on `ptxas info    : Used 28 registers, used 1 barriers, 400 bytes cmem[0], 8 bytes cmem[2]`.
- Stderr also reports `libgomp: Invalid value for environment variable OMP_NUM_THREADS:`.

Supervisor review:
- Supervisor reviewer `019ea8a7-c286-79b3-be3d-4d4b7c654022` returned `ACCEPT`.
- Reviewer confirmed the fix is root-cause oriented, registration order is correct, runtime-owned versus standalone non-owned `trace_config` lifetime is bounded, and the new `ptxas` parser blocker is properly recorded.

Follow-up:
- Pending S7 work remains: update the PTX/ptxas resource-output parser for CUDA 13.1 output syntax, rebuild, rerun one local smoke, then create real supplied-metrics correlation input only if simulator metrics exist.

Checkpoint:
- Commit `06fd88c053e95d5b9486612f02e557699d084ce9` (`fix: register trace config on cudart path`) recorded the runtime trace option registration fix and bounded the next CUDA 13.1 `ptxas` parser blocker.

### 2026-06-09 03:17:57 CST

Action:
- Spawned S7 CUDA 13.1 `ptxas` resource parser worker `019ea8ab-7a47-7700-a045-aaf7e101a7f3`.

Scope:
- Resolve or precisely bound parsing of `ptxas info    : Used 28 registers, used 1 barriers, 400 bytes cmem[0], 8 bytes cmem[2]`.
- Prefer a compatibility fix in the PTX/ptxas resource parser that preserves older `ptxas` output behavior and uses the existing barrier resource data model if appropriate.

### 2026-06-09 03:34:55 CST

Action:
- S7 CUDA 13.1 `ptxas` resource parser worker `019ea8ab-7a47-7700-a045-aaf7e101a7f3` completed `docs/sm120-calibration/worker-logs/worker-20260609-031826-s7-ptxas-parser.md`.
- The worker reported one blank-context internal reviewer round with verdict `ACCEPT`.

Worker deliverables:
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/ptxinfo.l`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/ptxinfo.y`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/cuda-sim.cc`.
- `docs/sm120-calibration/worker-logs/worker-20260609-031826-s7-ptxas-parser.md`.
- Local smoke evidence under ignored `artifacts/s7/s7-ptxas-parser-20260609-031826/`.

Worker validation:
- Rebuilt the CUDA 13.1 release GPGPU-Sim runtime and regenerated the `ptxinfo` parser.
- Verified the existing parser conflict count was unchanged from the base.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Setup-only local smoke planning passed.
- Exactly one local smoke job was launched.
- Protected config/latest/generated scoped status was empty.
- Final procman state was `Nothing Active`.

Partial result:
- The previous CUDA 13.1 `ptxas` parser blocker on `used 1 barriers` is resolved.
- The parser consumed `ptxas info    : Used 28 registers, used 1 barriers, 400 bytes cmem[0], 8 bytes cmem[2]`.
- Smoke evidence shows `GPGPU-Sim PTX: Kernel ... : regs=28, lmem=0, smem=0, cmem=408`.
- The smoke still produced no real simulator metrics.
- New blocker: parser fails on `ptxas info    : Compile time = 2.998 ms`.
- Stderr still reports `libgomp: Invalid value for environment variable OMP_NUM_THREADS:`.

Supervisor review:
- Supervisor reviewer `019ea8b8-c615-7082-a11b-5f93a7fc88aa` returned `ACCEPT`.
- Reviewer confirmed the parser change is scoped, preserves existing register/memory/cmem-bank forms, uses the existing barrier model, resets barrier state, and properly bounds the new compile-time parser blocker.

Follow-up:
- Pending S7 work remains: update the PTX/ptxas parser to accept CUDA 13.1 `Compile time = ... ms` informational lines, rebuild, rerun one local smoke, then create real supplied-metrics correlation input only if simulator metrics exist.

Checkpoint:
- Commit `f151f81d3a680d9523f0ac20b93bfdd4667f565e` (`fix: parse CUDA 13 ptxas barrier usage`) recorded the CUDA 13.1 barrier resource parser fix and bounded the next compile-time informational-line parser blocker.

### 2026-06-09 03:36:13 CST

Action:
- Spawned S7 CUDA 13.1 `ptxas` compile-time parser worker `019ea8bc-14d7-7303-a68d-9c672e184196`.

Scope:
- Resolve or precisely bound parsing of `ptxas info    : Compile time = 2.998 ms`.
- Prefer a minimal compatibility fix that accepts or ignores this informational line without suppressing resource parsing.

### 2026-06-09 03:58:37 CST

Action:
- S7 CUDA 13.1 `ptxas` compile-time parser worker `019ea8bc-14d7-7303-a68d-9c672e184196` completed `docs/sm120-calibration/worker-logs/worker-20260609-033652-s7-ptxas-compile-time.md`.
- The worker reported one blank-context internal reviewer round with verdict `ACCEPT`.

Worker deliverables:
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/ptxinfo.l`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/ptxinfo.y`.
- `docs/sm120-calibration/worker-logs/worker-20260609-033652-s7-ptxas-compile-time.md`.
- Local smoke evidence under ignored `artifacts/s7/s7-ptxas-compile-time-20260609-033652/`.

Worker validation:
- Rebuilt the CUDA 13.1 release GPGPU-Sim runtime and regenerated the `ptxinfo` parser.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Setup-only local smoke planning passed.
- Exactly one local smoke job was launched.
- Protected config/latest/generated scoped status was empty.

Partial result:
- The previous CUDA 13.1 `ptxas` parser blocker on `Compile time = ... ms` is resolved.
- The smoke parsed the `sm_120` `ptxas` output and advanced to performance-simulation launch.
- The smoke still produced no real simulator metrics.
- New blocker: segmentation fault before simulator metrics in `ptx_instruction::set_opcode_and_latency()` at `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/cuda-sim.cc:768`.
- Evidence maps the top simulator-library frame to `sscanf(gpgpu_ctx->func_sim->opcode_latency_fp, ...)`.
- Stderr still reports `libgomp: Invalid value for environment variable OMP_NUM_THREADS:`.

Supervisor review:
- Supervisor reviewer `019ea8cd-856c-76a2-a823-5daeea38b864` returned `ACCEPT`.
- Reviewer confirmed the parser change is narrow, preserves resource parsing, rebuild evidence shows no new parser conflict count, smoke evidence shows compile-time lines were consumed, and the later segfault is properly bounded.

Follow-up:
- Pending S7 work remains: debug and fix or precisely bound the `ptx_instruction::set_opcode_and_latency()` segmentation fault, rebuild, rerun one local smoke, then create real supplied-metrics correlation input only if simulator metrics exist.

Checkpoint:
- Commit `9822684d61f285337e74a6d9b431f928d26482a9` (`fix: parse CUDA 13 ptxas compile time lines`) recorded the CUDA 13.1 compile-time informational-line parser fix and bounded the next opcode-latency segmentation fault.

### 2026-06-09 04:00:32 CST

Action:
- Spawned S7 opcode latency segmentation fault worker `019ea8d2-5296-7831-8c98-2dbfab0fa91c`.

Scope:
- Resolve or precisely bound the segmentation fault in `ptx_instruction::set_opcode_and_latency()` at `cuda-sim.cc:768`.
- Verify whether the root cause is option registration/default/parse ownership, malformed/null opcode latency strings, or another initialization issue on the CUDA runtime path.

### 2026-06-09 04:40:20 CST

Action:
- S7 opcode latency segmentation fault worker `019ea8d2-5296-7831-8c98-2dbfab0fa91c` completed `docs/sm120-calibration/worker-logs/worker-20260609-040030-s7-opcode-latency.md`.
- The worker reported one blank-context internal reviewer round with verdict `ACCEPT`.

Worker deliverables:
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/cuda-sim.cc`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/cuda-sim.h`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader.cc`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpusim_entrypoint.cc`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpusim_entrypoint.h`.
- `docs/sm120-calibration/worker-logs/worker-20260609-040030-s7-opcode-latency.md`.
- Local smoke evidence under ignored `artifacts/s7/s7-opcode-latency-20260609-040030/`.

Worker validation:
- Rebuilt the CUDA 13.1 release GPGPU-Sim runtime.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Setup-only local smoke planning passed.
- Exactly one local smoke job was launched.
- Protected config/latest/generated scoped status was empty.

Root cause:
- The CUDA runtime path destroyed its temporary `option_parser_t` after parsing `gpgpusim.config`.
- `OPT_CSTR` option values were owned by that parser, so opcode latency/initiation pointers later became null and `set_opcode_and_latency()` called `sscanf(NULL, ...)`.

Partial result:
- The runtime now keeps the parser alive for `GPGPUsim_ctx` lifetime, and opcode latency/initiation/CDP latency parsing uses shared validated helpers.
- The previous `ptx_instruction::set_opcode_and_latency()` crash is resolved for the local smoke.
- The smoke advanced through PTX predecode and kernel stream push.
- The smoke still produced no real simulator metrics.
- New blocker: segmentation fault in `Subcore::issue(SM*)` at `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc:514`.
- Evidence shows `m_sm_stats.m_stats_map["total_num_cycles_issue_stage_stall_no_valid_instruction"]` exists as an empty/null `shared_ptr`.
- Stderr still reports `libgomp: Invalid value for environment variable OMP_NUM_THREADS:`.

Supervisor review:
- Supervisor reviewer `019ea8f3-4ad6-7c81-ab80-27987948832c` returned `ACCEPT`.
- Reviewer confirmed parser lifetime ownership is clean, standalone trace path behavior remains compatible, shared parsing helpers preserve existing semantics and legacy integer latency/initiation support, and the new stats-map blocker is properly bounded.

Follow-up:
- Pending S7 work remains: fix or precisely bound the remodeled issue-stage stats registration/null-counter blocker in `Subcore::issue(SM*)`, rebuild, rerun one local smoke, then create real supplied-metrics correlation input only if simulator metrics exist.

Checkpoint:
- Commit `494dfd72db4d717ee008a2b2e4a23af915ec7fc9` (`fix: preserve runtime opcode latency options`) recorded the runtime option lifetime and validated opcode latency parsing fix.

### 2026-06-09 04:42:08 CST

Action:
- Spawned S7 remodeled subcore stats worker `019ea8f8-56dd-74d3-ac6c-234029393f2a`.

Scope:
- Resolve or precisely bound the `Subcore::issue(SM*)` segmentation fault caused by an empty/null stats map entry for `total_num_cycles_issue_stage_stall_no_valid_instruction`.
- Prefer a root-cause stats registration/initialization fix rather than a local null check that silently drops stats.

### 2026-06-09 05:06:22 CST

Action:
- S7 remodeled subcore stats worker `019ea8f8-56dd-74d3-ac6c-234029393f2a` completed `docs/sm120-calibration/worker-logs/worker-20260609-044203-s7-subcore-stats.md`.
- The worker reported one blank-context internal reviewer round with verdict `ACCEPT`.

Worker deliverables:
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader.cc`.
- `docs/sm120-calibration/worker-logs/worker-20260609-044203-s7-subcore-stats.md`.
- Local smoke evidence under ignored `artifacts/s7/s7-subcore-stats-20260609-044203/`.

Worker validation:
- Rebuilt the CUDA 13.1 release GPGPU-Sim runtime.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Setup-only local smoke planning passed.
- Exactly one local smoke job was launched.
- Protected config/latest/generated scoped status was empty.

Root cause:
- Remodeled `SM` objects were constructed and initialized without calling the existing per-SM stats copy hook.
- `Subcore::issue()` then accessed the stat key through `operator[]`, inserting an empty/null `shared_ptr` for `total_num_cycles_issue_stage_stall_no_valid_instruction`.

Partial result:
- The remodeled SM construction path now calls `create_gpu_per_sm_stats(m_gpu->m_gpu_per_sm_stats)` before `init()`.
- The previous `Subcore::issue(SM*)` null stats shared-pointer crash is resolved for the local smoke.
- The smoke still produced no real simulator metrics.
- New blocker: assertion in `shd_warp_t::get_current_unique_function_id_call()` at `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader.h:229`, called from `Subcore::fetch()` at `remodeling/subcore.cc:981`.
- Stderr still reports `libgomp: Invalid value for environment variable OMP_NUM_THREADS:`.

Supervisor review:
- Supervisor reviewer `019ea90c-e335-7e11-aa65-a13284dfa67d` returned `ACCEPT`.
- Reviewer confirmed the fix uses the existing global per-SM stat registration, does not mask missing stats with null checks, has low duplicate-registration risk, and cleanly bounds the new function-call-stack assertion blocker.

Follow-up:
- Pending S7 work remains: fix or precisely bound the `shd_warp_t::get_current_unique_function_id_call()` assertion on the remodeled fetch path, rebuild, rerun one local smoke, then create real supplied-metrics correlation input only if simulator metrics exist.
