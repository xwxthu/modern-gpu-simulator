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

Checkpoint:
- Commit `4fa4577d27d68f8bd4f71603ef1f56796c595dd3` (`fix: initialize remodeled SM stats`) recorded the remodeled per-SM stats initialization fix.

### 2026-06-09 05:07:49 CST

Action:
- Spawned S7 function-call-stack assertion worker `019ea90f-e471-7aa0-ac26-38cedad6107e`.

Scope:
- Resolve or precisely bound the assertion `!m_function_call_stack.empty()` in `shd_warp_t::get_current_unique_function_id_call()` called from remodeled `Subcore::fetch()`.
- Prefer a root-cause fix in warp/function metadata initialization or remodeled fetch semantics, not weakening the assertion without evidence.

### 2026-06-09 05:28:51 CST

Action:
- S7 function-call-stack assertion worker `019ea90f-e471-7aa0-ac26-38cedad6107e` completed `docs/sm120-calibration/worker-logs/worker-20260609-051136-s7-function-stack.md`.
- The worker reported one blank-context internal reviewer round with verdict `ACCEPT`.

Worker deliverables:
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/sm.cc`.
- `docs/sm120-calibration/worker-logs/worker-20260609-051136-s7-function-stack.md`.
- Local smoke evidence under ignored `artifacts/s7/s7-function-stack-20260609-051136/`.

Worker validation:
- Rebuilt the CUDA 13.1 release GPGPU-Sim runtime.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Setup-only local smoke planning passed.
- Exactly one local smoke job was launched.
- Protected config/latest/generated scoped status was empty.

Root cause:
- Remodeled fetch always used the trace-mode warp function-call stack to derive function-relative instruction-cache addresses.
- PTX/performance simulation mode uses baseline `PROGRAM_MEM_START` instruction addresses and does not seed trace-mode function-call stacks.

Partial result:
- Trace mode still uses `get_current_unique_function_id_call()` and keeps the assertion intact.
- PTX mode now uses function id `0` as the carrier value and remodeled PTX PC translation round-trips through `PROGRAM_MEM_START`.
- The previous `shd_warp_t::get_current_unique_function_id_call()` assertion is resolved for the local smoke.
- The smoke still produced no real simulator metrics.
- New blocker: segmentation fault from null `traced_instruction` in `warp_inst_t::assign_predicate_latencies_if_needed()`, called from `Subcore::single_decode()`.
- Stderr still reports `libgomp: Invalid value for environment variable OMP_NUM_THREADS:`.

Supervisor review:
- Supervisor reviewer `019ea921-525e-70b3-9320-8bcd8d26f1df` returned `ACCEPT`.
- Reviewer confirmed mode separation is clean, trace-mode stack semantics remain intact, function id `0` is a valid PTX-mode carrier value, and the new null `traced_instruction` decode blocker is properly bounded.

Follow-up:
- Pending S7 work remains: fix or precisely bound the null `traced_instruction` dereference in PTX-mode remodeled decode/predicate latency handling, rebuild, rerun one local smoke, then create real supplied-metrics correlation input only if simulator metrics exist.

Checkpoint:
- Commit `e8dd5bc16ff9e7f04f532c248506a30134292f45` (`fix: handle PTX-mode remodeled fetch PCs`) recorded the PTX-mode remodeled fetch/function-id fix.

### 2026-06-09 05:30:21 CST

Action:
- Spawned S7 predicate latency trace-metadata worker `019ea924-77b7-70a1-aa98-34b2bf31f3d7`.

Scope:
- Resolve or precisely bound the null `traced_instruction` dereference in `warp_inst_t::assign_predicate_latencies_if_needed()` called from remodeled `Subcore::single_decode()`.
- Prefer a trace-mode/trace-metadata availability guard that preserves normal PTX decode semantics.

### 2026-06-09 05:51:53 CST

Action:
- S7 predicate latency trace-metadata worker `019ea924-77b7-70a1-aa98-34b2bf31f3d7` completed `docs/sm120-calibration/worker-logs/worker-20260609-053213-s7-predicate-latency.md`.
- The worker reported one blank-context internal reviewer round with verdict `ACCEPT`.

Worker deliverables:
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/abstract_hardware_model.cc`.
- `docs/sm120-calibration/worker-logs/worker-20260609-053213-s7-predicate-latency.md`.
- Local smoke evidence under ignored `artifacts/s7/s7-predicate-latency-20260609-053213/`.

Worker validation:
- Rebuilt the CUDA 13.1 release GPGPU-Sim runtime.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Setup-only local smoke planning passed.
- Exactly one local smoke job was launched.
- Protected config/latest/generated scoped status was empty.

Root cause:
- `warp_inst_t::assign_predicate_latencies_if_needed()` unconditionally touched trace-enhanced instruction metadata during remodeled decode.
- The local smoke is PTX/performance simulation mode, so normal PTX predecode already assigns instruction latency and no trace metadata is available.

Partial result:
- PTX mode now returns before trace-enhanced predicate latency metadata is accessed.
- Trace mode still requires trace metadata and trace config before using predicate/SETP trace latency modeling.
- The previous null `traced_instruction::get_contains_setp(this=0x0)` segmentation fault is resolved for the local smoke.
- The smoke still produced no real simulator metrics.
- New blocker: assertion in `warp_inst_t::generate_mem_latencies()` at `simulator-remodeled/gpu-simulator/gpgpu-sim/src/abstract_hardware_model.cc:514`, because the trace-enhanced memory latency helper still asserts `shader_config.is_trace_mode` when called from PTX-mode remodeled decode.
- Stderr still reports `libgomp: Invalid value for environment variable OMP_NUM_THREADS:`.

Supervisor review:
- Supervisor reviewer `019ea934-fb5e-7171-8334-aae66bc9f3b0` returned `ACCEPT`.
- Reviewer confirmed the guard is narrow, PTX decode is not skipped globally, trace-mode predicate latency modeling remains strict, and the new memory-latency assertion blocker is properly bounded.

Follow-up:
- Pending S7 work remains: fix or precisely bound the PTX-mode call to trace-enhanced `generate_mem_latencies()`, rebuild, rerun one local smoke, then create real supplied-metrics correlation input only if simulator metrics exist.

Checkpoint:
- Commit `65b3f4d76dce08f2fd0cf527fd35b32f2e75f01b` (`fix: guard trace predicate latency in PTX mode`) recorded the PTX-mode predicate-latency trace metadata guard.

### 2026-06-09 05:53:32 CST

Action:
- Spawned S7 memory latency trace-metadata worker `019ea939-ad2a-7e23-94d5-2f2fe1bf4767`.

Scope:
- Resolve or precisely bound the PTX-mode assertion in `warp_inst_t::generate_mem_latencies()`.
- Prefer a trace-mode/trace-metadata availability guard that preserves normal PTX memory instruction latency semantics and trace-mode memory latency modeling.

### 2026-06-09 06:34:34 CST

Action:
- S7 memory latency trace-metadata worker `019ea939-ad2a-7e23-94d5-2f2fe1bf4767` completed `docs/sm120-calibration/worker-logs/worker-20260609-055623-s7-memory-latency.md`.
- The worker reported a blank-context internal reviewer verdict of `ACCEPT` after earlier reviewer CLI attempts failed or timed out before verdict.

Worker deliverables:
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/abstract_hardware_model.cc`.
- `docs/sm120-calibration/worker-logs/worker-20260609-055623-s7-memory-latency.md`.
- Local smoke evidence under ignored `artifacts/s7/s7-memory-latency-20260609-055623/`.

Worker validation:
- Rebuilt the CUDA 13.1 release GPGPU-Sim runtime.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Setup-only local smoke planning passed.
- Exactly one local smoke job was launched.

Root cause:
- `warp_inst_t::generate_mem_latencies()` asserted trace mode before trace-enhanced memory operand metadata access.
- The local smoke is PTX/performance simulation mode, where normal PTX predecode already provides instruction latency and initiation interval and no enhanced trace metadata is available.

Partial result:
- PTX mode now initializes remodeled memory-latency state from existing PTX predecode values plus config-backed SM-side memory latency knobs.
- Trace mode still uses the detailed trace-enhanced memory latency path and now asserts if required trace instruction metadata is missing.
- The previous `shader_config.is_trace_mode` assertion in `generate_mem_latencies()` is resolved for the local smoke.
- The smoke still produced no real simulator metrics.
- New blocker: null trace metadata dereference in `Scoreboard::checkCollision_remodeling()`, specifically `traced_instruction::get_num_operands(this=0x0)`, reached from `Subcore::issue()`.

Supervisor review:
- Supervisor reviewer `019ea95c-adbf-7de1-b2ba-6ab40109ddb8` returned `ACCEPT`.
- Reviewer confirmed the PTX fallback is not SM120/RTX5060-specific, trace-mode detailed modeling is preserved, missing trace metadata is explicitly guarded before dereference, and the new scoreboard blocker is distinct and properly bounded.

Follow-up:
- Pending S7 work remains: fix or precisely bound the PTX-mode trace metadata dereference in `Scoreboard::checkCollision_remodeling()`, rebuild, rerun one local smoke, then create real supplied-metrics correlation input only if simulator metrics exist.

Checkpoint:
- Commit `fc68f6fa3ec89d326ecc5d6584c0e2b9daff3dc9` (`fix: handle PTX-mode remodeled memory latencies`) recorded the PTX-mode memory latency handling fix.

### 2026-06-09 06:39:09 CST

Action:
- Spawned S7 scoreboard PTX-mode trace-metadata worker `019ea961-6d87-7ee0-84fa-260333efd867`.

Scope:
- Resolve or precisely bound the PTX-mode null trace metadata crash in `Scoreboard::checkCollision_remodeling()`.
- Preserve trace-mode MICRO25/remodeled scoreboarding behavior and avoid disabling scoreboarding globally.

### 2026-06-09 07:31:12 CST

Action:
- S7 scoreboard PTX-mode worker `019ea961-6d87-7ee0-84fa-260333efd867` completed `docs/sm120-calibration/worker-logs/worker-20260609-064749-s7-scoreboard-ptx.md`.
- The worker reported a prompt-only blank-context internal reviewer verdict of `ACCEPT` after several CLI reviewer attempts failed or stalled before a usable verdict.

Worker deliverables:
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/abstract_hardware_model.cc`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/functional_unit.cc`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/register_file.cc`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/register_file.h`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/sm.cc`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/scoreboard.cc`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/scoreboard_reads.cc`.
- `docs/sm120-calibration/worker-logs/worker-20260609-064749-s7-scoreboard-ptx.md`.
- Local smoke evidence under ignored `artifacts/s7/s7-scoreboard-ptx-20260609-064749/`.

Worker validation:
- Rebuilt the CUDA 13.1 release GPGPU-Sim runtime.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Setup-only local smoke planning passed.
- Exactly one local smoke job was launched.
- Protected accepted config/latest/generated scoped status was clean.

Root cause:
- PTX/performance simulation instructions do not carry enhanced trace instruction metadata, but the remodeled issue path called metadata-dependent scoreboard, register-file, functional-unit, barrier, and retirement helpers.
- `Scoreboard::checkCollision_remodeling()` dereferenced missing trace metadata while checking operands.

Partial result:
- PTX instructions without enhanced trace metadata use classic scoreboard/register-file behavior where trace operand-use metadata is unavailable.
- Trace-mode metadata-dependent paths remain preserved or stricter: missing trace metadata now aborts explicitly rather than silently degrading in assertion-disabled builds.
- The previous `traced_instruction::get_num_operands(this=0x0)` scoreboard crash is resolved for the local smoke.
- The smoke still produced no real simulator metrics.
- New blocker: `warp_inst_t::generate_mem_accesses()` assertion `m_per_scalar_thread_valid` at `abstract_hardware_model.cc:676`, reached from the remodeled issue path.

Supervisor review:
- Supervisor reviewer `019ea98f-2329-7942-8b2d-fe1d379005b8` returned `ACCEPT`.
- Reviewer confirmed the implementation separates PTX/no-trace instructions from trace-enhanced metadata paths without disabling scoreboarding globally, preserves or tightens trace-mode contracts, avoids SM120/RTX5060-specific constants, and properly bounds the new memory-access validity blocker.

Follow-up:
- Pending S7 work remains: fix or precisely bound the PTX-mode `m_per_scalar_thread_valid` assertion in `warp_inst_t::generate_mem_accesses()`, rebuild, rerun one local smoke, then create real supplied-metrics correlation input only if simulator metrics exist.

Checkpoint:
- Commit `a9798111ba635e30f18758e90a73a6ca46a38459` (`fix: separate PTX scoreboarding from trace metadata`) recorded the PTX-mode scoreboarding/register-file trace metadata separation fix.

### 2026-06-09 07:38:22 CST

Action:
- Spawned S7 memory-access validity worker `019ea995-4b09-7e30-a224-a956af6d7cd5`.

Scope:
- Resolve or precisely bound the PTX-mode `m_per_scalar_thread_valid` assertion in `warp_inst_t::generate_mem_accesses()`.
- Preserve normal PTX address generation and memory coalescing; avoid fake per-thread memory state or global memory-access bypasses.

### 2026-06-09 08:04:26 CST

Action:
- S7 memory-access validity worker `019ea995-4b09-7e30-a224-a956af6d7cd5` completed `docs/sm120-calibration/worker-logs/worker-20260609-075815-s7-mem-accesses.md`.
- The worker reported a fresh read-only blank-context internal reviewer verdict of `ACCEPT` after one failed CLI reviewer attempt.

Worker deliverables:
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/cuda-sim.cc`.
- `docs/sm120-calibration/worker-logs/worker-20260609-075815-s7-mem-accesses.md`.
- Local smoke evidence under ignored `artifacts/s7/s7-mem-accesses-20260609-074137/`.

Worker validation:
- Rebuilt the CUDA 13.1 release GPGPU-Sim runtime.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Setup-only local smoke planning passed.
- Exactly one local smoke job was launched.

Root cause:
- `ptx_thread_info::ptx_exec_inst(warp_inst_t&, unsigned)` was an empty stub in `cuda-sim.cc`.
- PTX-mode timing execution therefore did not run PTX opcode handlers for active lanes and memory operations did not populate per-lane addresses through the normal `set_addr()` path before coalescing.

Partial result:
- Restored the normal PTX opcode-dispatch path in `ptx_exec_inst(warp_inst_t&, unsigned)`, including PC synchronization, predicate handling, opcode execution through `opcodes.def`, callbacks, PC/stat updates, and memory return-state capture from `last_eaddr()`, `last_space()`, and `datatype2size()`.
- `warp_inst_t::generate_mem_accesses()` and the coalescer remain intact.
- The previous `m_per_scalar_thread_valid` assertion is resolved for the local smoke.
- Coredump evidence for the next abort shows `m_per_scalar_thread_valid = true`, `m_mem_accesses_created = true`, and a generated `CONST_ACC_R` access queue entry.
- The smoke still produced no real simulator metrics.
- New blocker: `Scoreboard::reserveRegister()` abort at `scoreboard.cc:95`, with `Subcore::issue_warp()` issuing `sm_warp_id = 12` while the `warp_inst_t` carries `m_warp_id = 5`, `m_dynamic_warp_id = 5`, `m_is_reissued = true`, and `m_vpreg_need_to_reissue = false`.

Supervisor review:
- Supervisor reviewer `019ea9ae-b960-7d80-87fa-2902f4b542a3` returned `ACCEPT`.
- Reviewer confirmed the fix restores normal PTX execution/address setup semantics, does not fake memory addresses or bypass coalescing, does not regress trace-mode behavior, changes no config/latest/generated outputs, and bounds the next scoreboard warp-id mismatch blocker.

Follow-up:
- Pending S7 work remains: fix or precisely bound the PTX-mode `Scoreboard::reserveRegister()` abort caused by the mismatch between the issuing `sm_warp_id` and the instruction's stored warp id during reissue/scoreboard reservation.

Checkpoint:
- Commit `e02786e96e817169cc4d3bee5602e2f8b6254124` (`fix: restore PTX memory address execution`) recorded the PTX-mode memory address execution fix.

### 2026-06-09 08:08:40 CST

Action:
- Spawned S7 scoreboard reserve warp-id worker `019ea9b3-922f-7b92-b1f4-824799e201dc`.

Scope:
- Resolve or precisely bound the PTX-mode `Scoreboard::reserveRegister()` abort caused by a mismatch between the issuing `sm_warp_id` and the instruction's stored warp id.
- Preserve scoreboard correctness; do not disable reserve checks or ignore warp-id mismatches.

### 2026-06-09 08:43:19 CST

Action:
- S7 scoreboard reserve warp-id worker `019ea9b3-922f-7b92-b1f4-824799e201dc` completed `docs/sm120-calibration/worker-logs/worker-20260609-082450-s7-scoreboard-reserve.md`.
- The worker reported a prompt-only blank-context internal reviewer verdict of `ACCEPT` after one stalled read-only reviewer attempt.

Worker deliverables:
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc`.
- `docs/sm120-calibration/worker-logs/worker-20260609-082450-s7-scoreboard-reserve.md`.
- Local smoke evidence under ignored `artifacts/s7/s7-scoreboard-reserve-20260609-081120/`.

Worker validation:
- Rebuilt the CUDA 13.1 release GPGPU-Sim runtime.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Setup-only local smoke planning passed.
- Exactly one local smoke job was launched.

Root cause:
- In PTX mode, remodeled decode stored the canonical `ptx_fetch_inst(pc)` pointer in each per-warp IBuffer entry.
- Multiple warps at the same PC could share the same mutable static instruction object, and later decodes could overwrite the shared instruction's warp fields before an earlier IBuffer entry was issued.

Partial result:
- PTX-mode `Subcore::get_next_inst()` now clones the canonical PTX timing instruction into a heap-owned `warp_inst_t` for each remodeled IBuffer entry.
- The issue path now asserts `pI->warp_id() == sm_warp_id` before forwarding to `SM::issue_warp()`.
- Trace-mode fetch remains unchanged.
- The previous `Scoreboard::reserveRegister()` warp-id mismatch abort is resolved for the local smoke.
- The smoke still produced no real simulator metrics.
- New blocker: `PendingRequestTable::get_next_processed_access()` in `ldst_unit_sm.cc` unconditionally dereferences enhanced trace metadata through `traced_instruction::get_control_bits(this=0x0)` on a PTX-mode memory instruction.

Supervisor review:
- Supervisor reviewer `019ea9d2-2007-7501-8ede-55274166a0c2` returned `ACCEPT`.
- Reviewer confirmed the change is a real decoded-instruction ownership fix, preserves scoreboard correctness, leaves trace-mode fetch unchanged, changes no config/latest/generated outputs, and properly bounds the new LD/ST memory-pipeline trace metadata blocker.

Follow-up:
- Pending S7 work remains: fix or precisely bound the PTX-mode trace metadata null dereference in `PendingRequestTable::get_next_processed_access()` / `ldst_unit_sm.cc`.

Checkpoint:
- Commit `4f07eeffdfa2406cd669bc7d8a60005ff2ace2ff` (`fix: clone PTX instructions for remodeled ibuffer`) recorded the PTX-mode IBuffer instruction ownership fix.

### 2026-06-09 08:48:41 CST

Action:
- Spawned S7 LD/ST trace-metadata worker `019ea9d7-8d2a-7c31-a07c-178e2a95c227`.

Scope:
- Resolve or precisely bound the PTX-mode trace metadata null dereference in `PendingRequestTable::get_next_processed_access()` / `ldst_unit_sm.cc`.
- Preserve LD/ST pipeline and pending request processing; do not fabricate control bits or drop accesses.

### 2026-06-09 09:20:15 CST

Action:
- S7 LD/ST trace-metadata worker `019ea9d7-8d2a-7c31-a07c-178e2a95c227` completed `docs/sm120-calibration/worker-logs/worker-20260609-090538-s7-ldst-trace-metadata.md`.
- The worker reported a fresh read-only blank-context internal reviewer verdict of `ACCEPT`.

Worker deliverables:
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/ldst_unit_sm.cc`.
- `docs/sm120-calibration/worker-logs/worker-20260609-090538-s7-ldst-trace-metadata.md`.
- Local smoke evidence under ignored `artifacts/s7/s7-ldst-trace-metadata-20260609-085111/`.

Worker validation:
- Rebuilt the CUDA 13.1 release GPGPU-Sim runtime.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Setup-only local smoke planning passed.
- Exactly one local smoke job was launched.

Root cause:
- `PendingRequestTable::get_next_processed_access()` and related LD/ST metadata paths unconditionally read enhanced trace control bits from `warp_inst_t::get_extra_trace_instruction_info()`.
- PTX/performance-mode memory instructions have no enhanced trace metadata, so the dereference was invalid.

Partial result:
- Added a mode-gated LD/ST control-bit helper: PTX/performance mode returns no trace control bits before touching metadata; trace mode aborts explicitly if required metadata is missing.
- Applied the helper to PRT access dependency metadata, PRT dependency-counter selection, and inter-warp coalescing dependency metadata.
- Guarded LD/ST pending-write ID logic so PTX mode uses decoded `inst->out[idx]`, while trace mode keeps trace destination metadata behavior.
- The previous `traced_instruction::get_control_bits(this=0x0)` null dereference is resolved for the local smoke.
- The smoke still produced no real simulator metrics.
- New blocker: `Error: Invalid access type` at `ldst_unit_sm.cc:948` for a PTX-mode `param_space_kernel` load coalesced as `CONST_ACC_R`.

Supervisor review:
- First supervisor reviewer `019ea9ec-4833-7753-9259-f9393a766ff2` returned `CHANGES_NEEDED`.
- Required fix: make LD/ST control-bit and pending-write ID logic mode-gated rather than metadata-presence gated, so PTX mode never dereferences enhanced trace metadata even if metadata happens to be present.
- Worker completed the targeted rework and a new internal reviewer round.
- Second supervisor reviewer `019ea9f5-9377-7f30-8d37-d6025c091c7c` returned `ACCEPT`.
- Reviewer confirmed PTX mode now returns before any enhanced metadata access, trace mode still requires metadata explicitly, LD/ST/PRT processing remains present, and the new `param_space_kernel` / `CONST_ACC_R` routing blocker is separate.

Follow-up:
- Pending S7 work remains: fix or precisely bound the PTX-mode LD/ST queue-routing `Invalid access type` abort for `param_space_kernel` accesses classified as `CONST_ACC_R`.

Checkpoint:
- Commit `5a3b6b937caa637dba7dad1864e850179291211e` (`fix: guard LDST trace metadata in PTX mode`) recorded the PTX-mode LD/ST trace metadata separation fix.

### 2026-06-09 09:23:10 CST

Action:
- Spawned S7 parameter constant routing worker `019ea9f9-36ca-77f3-acb4-57ea898f18d1`.

Scope:
- Resolve or precisely bound the PTX-mode LD/ST queue-routing `Invalid access type` abort for `param_space_kernel` accesses classified as `CONST_ACC_R`.
- Route parameter constant reads consistently with existing constant-read semantics; do not suppress invalid-access errors blindly.

### 2026-06-09 09:46:36 CST

Action:
- S7 parameter constant routing worker `019ea9f9-36ca-77f3-acb4-57ea898f18d1` completed `docs/sm120-calibration/worker-logs/worker-20260609-092504-s7-param-const-routing.md`.
- The worker reported a bounded fresh blank-context internal reviewer verdict of `ACCEPT` after one stalled read-only reviewer attempt.

Worker deliverables:
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/ldst_unit_sm.cc`.
- `docs/sm120-calibration/worker-logs/worker-20260609-092504-s7-param-const-routing.md`.
- Local smoke evidence under ignored `artifacts/s7/s7-param-const-routing-20260609-092504/`.

Worker validation:
- Rebuilt the CUDA 13.1 release GPGPU-Sim runtime.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Setup-only local smoke planning passed.
- Exactly one local smoke job was launched.

Root cause:
- PTX memory coalescing classifies both `const_space` and `param_space_kernel` as `CONST_ACC_R`, and `memory_space_t::is_const()` includes both.
- Remodeled LD/ST queue routing only tested literal `const_space`, so `param_space_kernel` constant reads fell through to the invalid-access abort.

Partial result:
- Replaced literal `const_space` checks with `space.is_const()` for constant coalescing stats, L1C queue routing, and constant coalescing-conflict stats.
- The invalid-access abort remains intact for genuinely unsupported spaces.
- The previous `Error: Invalid access type` abort is resolved for the local smoke.
- The `param_space_kernel` / `CONST_ACC_R` access now reaches `ldst_unit_sm::dispatch_to_memory_access_queue_l1Ccache()`.
- The smoke still produced no real simulator metrics.
- New blocker: SIGSEGV in L1C dispatch because `inst->m_latency_of_mem_operation_at_sm_structure == 0`, causing `constant_cache_l1_latency_queue[inst_latency - 1]` to underflow to index `4294967295`.

Supervisor review:
- Supervisor reviewer `019eaa0c-d96f-78c0-8f24-5035fd36b2c0` returned `ACCEPT`.
- Reviewer confirmed `is_const()` covers exactly `const_space` and `param_space_kernel`, matches `CONST_ACC_R` classification, does not misroute global/local/shared/texture/surface paths, changes no config/latest/generated outputs, and properly bounds the new L1C latency underflow blocker.

Follow-up:
- Pending S7 work remains: fix or precisely bound the PTX-mode constant-memory latency underflow in `ldst_unit_sm::dispatch_to_memory_access_queue_l1Ccache()`.

Checkpoint:
- Commit `fbcca5b04017ed640dc7b5915d1f077cf3698c00` (`fix: route PTX parameter constants to L1C`) recorded the PTX-mode parameter constant routing fix.

### 2026-06-09 09:50:16 CST

Action:
- Spawned S7 L1C latency worker `019eaa11-093a-7d93-82ed-8fe2879dedf1`.

Scope:
- Resolve or precisely bound the PTX-mode L1C dispatch latency underflow for parameter constant accesses.
- Preserve config-backed latency semantics; do not add a dispatch fallback or hard-coded latency.

### 2026-06-09 10:32:09 CST

Action:
- S7 L1C latency worker `019eaa11-093a-7d93-82ed-8fe2879dedf1` completed `docs/sm120-calibration/worker-logs/worker-20260609-100045-s7-l1c-latency.md`.
- The worker reported a bounded blank-context internal reviewer verdict of `ACCEPT` after two timed-out reviewer attempts.

Worker deliverables:
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/sm.cc`.
- `docs/sm120-calibration/worker-logs/worker-20260609-100045-s7-l1c-latency.md`.
- Local smoke evidence under ignored `artifacts/s7/s7-l1c-latency-20260609-100045/`.

Worker validation:
- Rebuilt the CUDA 13.1 release GPGPU-Sim runtime.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Setup-only local smoke planning passed.
- Exactly one local smoke job was launched.

Root cause:
- Remodeled PTX decode generated memory latency metadata before functional PTX execution resolved `.param` / generic memory spaces.
- Functional execution and access generation later produced `param_space_kernel` / `CONST_ACC_R`, but the SM-structure latency field remained at decode-time zero.

Partial result:
- PTX/non-trace memory operations now regenerate memory latency metadata after `execute_warp_inst_t(inst)` and before `inst.generate_mem_accesses()`.
- This preserves the existing config-backed `space.is_const()` path for `param_space_kernel`.
- Trace mode remains unchanged.
- The previous `constant_cache_l1_latency_queue[inst_latency - 1]` underflow is resolved for the local smoke.
- The smoke still produced no real simulator metrics.
- New blocker: `Subcore::single_decode()` asserts `ibuffer_entry.m_inst->pc == ibuffer_entry.m_pc` at `subcore.cc:934`; focused evidence records `sm_warp_id = 32`, `ibuffer_entry.m_pc = 48`, and `ibuffer_entry.m_valid = true`.

Supervisor review:
- Supervisor reviewer `019eaa34-65dc-7640-a2cd-67e18b72183f` returned `ACCEPT`.
- Reviewer confirmed the fix is a root-cause PTX timing update after memory-space resolution, preserves trace-mode behavior, adds no dispatch fallback or config change, changes no config/latest/generated outputs, and properly bounds the new IBuffer PC mismatch blocker.

Follow-up:
- Pending S7 work remains: fix or precisely bound the PTX-mode IBuffer PC mismatch assertion in `Subcore::single_decode()`.

Checkpoint:
- Commit `d75fb941c33f60c9b26451fa12a19d7daf3fae96` (`fix: regenerate PTX memory latency after execution`) recorded the PTX-mode post-execution memory latency regeneration fix.

### 2026-06-09 10:37:01 CST

Action:
- Spawned S7 IBuffer PC worker `019eaa3b-bc3e-7422-8c6e-0248775bce1d`.

Scope:
- Resolve or precisely bound the PTX-mode IBuffer PC mismatch assertion in `Subcore::single_decode()`.
- Preserve the PC/instruction invariant; do not remove or weaken the assertion.

### 2026-06-09 11:27:21 CST

Action:
- S7 IBuffer PC worker `019eaa3b-bc3e-7422-8c6e-0248775bce1d` completed `docs/sm120-calibration/worker-logs/worker-20260609-110231-s7-ibuffer-pc.md`.
- The worker reported a bounded blank-context internal reviewer verdict of `ACCEPT` after one CLI invocation error and one timeout.

Worker deliverables:
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/ibuffer_remodeled.cc`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/ibuffer_remodeled.h`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc`.
- `docs/sm120-calibration/worker-logs/worker-20260609-110231-s7-ibuffer-pc.md`.
- Local smoke evidence under ignored `artifacts/s7/s7-ibuffer-pc-20260609-104918/`.

Worker validation:
- Rebuilt the CUDA 13.1 release GPGPU-Sim runtime.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Setup-only local smoke planning passed.
- Exactly one local smoke job was launched.

Root cause:
- PTX-mode `IBuffer_Remodeled` reused the trace/SASS fixed-width fetch reservation model.
- It reserved `fetch_decode_width` entries and advanced by fixed 16-byte strides before PTX decode knew the instruction size, but PTX instruction size comes from decoded `pI->isize`.

Partial result:
- PTX mode now reserves one unresolved entry per fetch request and refuses another fetch while unresolved invalid entries exist.
- After successful PTX decode, the IBuffer cursor advances to `decoded_pc + inst_size`.
- Trace mode still uses `fetch_decode_width` and fixed 16-byte reservation behavior.
- The original `ibuffer_entry.m_inst->pc == ibuffer_entry.m_pc` assertion is preserved, with an added earlier decode-time PC assertion.
- The previous IBuffer PC mismatch assertion is resolved for the local smoke.
- The smoke still produced no real simulator metrics.
- New blocker: `Subcore::get_fu()` aborts with `ERROR. EXECUTION PIPELINE FOR THIS INSTRUCTION NOT IMPLEMENTED` for decoded PTX instruction `pc=0x2420`, `isize=8`, `op=ALU_OP`, `sp_op=INT__OP`, `op_pipe=UNKOWN_OP`, `oprnd_type=INT_OP`, and `memory_op=no_memory_op`.

Supervisor review:
- Supervisor reviewer `019eaa69-2cae-7812-a98c-790b4572bb71` returned `ACCEPT`.
- Reviewer confirmed the fix removes fixed-width PTX fetch assumptions, preserves trace-mode reservation behavior, preserves the PC assertion, disables no scoreboard/fetch/decode checks, changes no config/latest/generated outputs, and properly bounds the new PTX ALU pipeline-classification blocker.

Follow-up:
- Pending S7 work remains: fix or precisely bound the PTX `ALU_OP` / `INT__OP` instruction whose `op_pipe` remains `UNKOWN_OP` and therefore has no implemented execution pipeline in `Subcore::get_fu()`.

Checkpoint:
- Commit `a103a0ebd4d084ca55b378d99d9566878ca05b9a` (`fix: handle variable PTX instruction fetch PCs`) recorded the PTX-mode variable-size IBuffer fetch/decode fix.

### 2026-06-09 11:30:29 CST

Action:
- Spawned S7 PTX ALU pipeline worker `019eaa6e-10d3-7bb2-ae5d-f9e11c5d234e`.

Scope:
- Resolve or precisely bound the PTX `ALU_OP` / `INT__OP` instruction whose `op_pipe` remained `UNKOWN_OP` and therefore had no implemented execution pipeline in `Subcore::get_fu()`.
- Classify PTX scalar ALU operations before FU selection; do not map all unknown operations to a default pipeline.

### 2026-06-09 12:14:19 CST

Action:
- S7 PTX ALU pipeline worker `019eaa6e-10d3-7bb2-ae5d-f9e11c5d234e` completed `docs/sm120-calibration/worker-logs/worker-20260609-120712-s7-ptx-alu-pipeline.md`.
- The worker reported a bounded read-only internal reviewer verdict of `ACCEPT` after two CLI invocation errors and one timeout.

Worker deliverables:
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/cuda-sim.cc`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/ptx_ir.h`.
- `docs/sm120-calibration/worker-logs/worker-20260609-120712-s7-ptx-alu-pipeline.md`.
- Local smoke evidence under ignored `artifacts/s7/s7-ptx-alu-pipeline-20260609-113915/`.

Worker validation:
- Rebuilt the CUDA 13.1 release GPGPU-Sim runtime.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Setup-only local smoke planning passed.
- Exactly one local smoke job was launched.

Root cause:
- PTX `set_opcode_and_latency()` initialized some scalar instructions as generic `ALU_OP`.
- Existing helpers classified many but not all scalar ALU instructions to concrete architectural op classes; remaining operations such as `mov`, shifts, converts, bitwise ops, set/select, and predicate set could remain `ALU_OP`.
- Remodeled `Subcore::get_fu()` dispatches by `pI->op` and intentionally aborts on unimplemented generic `ALU_OP`.

Partial result:
- Added a PTX predecode helper that runs only while `op == ALU_OP` and maps explicit scalar ALU leftovers through existing `sp_op` metadata to concrete architectural classes: `INTP_OP`, `SP_OP`, `DP_OP`, `SFU_OP`, `TENSOR_CORE_OP`, or `PREDICATE_OP` for `SETP_OP`.
- The fix does not modify `op_pipe` as a fallback and does not suppress `Subcore::get_fu()`'s abort.
- The previous `ERROR. EXECUTION PIPELINE FOR THIS INSTRUCTION NOT IMPLEMENTED` abort is resolved for the local smoke.
- The smoke still produced no real simulator metrics.
- New blocker: `ptx_thread_info::ptx_exec_inst()` asserts `pc == inst.pc` at `cuda-sim.cc:1968`; focused evidence shows issued instruction `pc = 0x2460`, `op = INTP_OP`, `sp_op = INT__OP`, and lane 1 functional PC `0x24a0`.

Supervisor review:
- Supervisor reviewer `019eaa92-b149-74b3-afff-ea912a0a6cb1` returned `ACCEPT`.
- Reviewer confirmed the classifier is targeted, runs only for remaining generic `ALU_OP`, uses existing `sp_op` metadata, does not alter `op_pipe` or suppress FU aborts, changes no config/latest/generated outputs, and properly bounds the new PTX functional PC mismatch blocker.

Follow-up:
- Pending S7 work remains: fix or precisely bound the PTX functional PC mismatch assertion in `ptx_thread_info::ptx_exec_inst()`.

### 2026-06-09 13:12:59 CST

Action:
- S7 PTX functional PC worker `019eaa98-80ee-7a92-8865-b9041f03be36` completed `docs/sm120-calibration/worker-logs/worker-20260609-123740-s7-ptx-functional-pc.md`.
- The worker reported a fresh read-only internal reviewer verdict of `ACCEPT` after an initial CLI invocation error and one `CHANGES_NEEDED` round.

Worker deliverables:
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/abstract_hardware_model.cc`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/ibuffer_remodeled.cc`.
- `docs/sm120-calibration/overall-plan.md`.
- `docs/sm120-calibration/worker-logs/worker-20260609-123740-s7-ptx-functional-pc.md`.
- Local smoke evidence under ignored `artifacts/s7/s7-ptx-functional-pc-20260609-122555/`.

Worker validation:
- Rebuilt the CUDA 13.1 release GPGPU-Sim runtime.
- `generate_sm120_configs.py --check-only` passed, including the final rerun.
- `git diff --check` passed.
- Setup-only local smoke planning passed.
- Exactly one local smoke job was launched.

Root cause:
- Remodeled `simt_stack::update()` was an empty imported stub while PTX-mode `SM::issue_warp()` still called `updateSIMTStack()` after functional execution.
- After a divergent branch at PTX PC `0x2458`, functional lanes advanced to the immediate postdominator at `0x24a0`, but the timing model still fetched and issued stale fall-through PC `0x2460` with the old active mask.

Partial result:
- Restored the standard post-dominator SIMT-stack update logic so PTX mode consumes per-lane functional next PCs and updates divergence/reconvergence state.
- Added a PTX-only stale IBuffer head check before remodeled issue: if the decoded head PC no longer matches the SIMT-stack top PC, the warp next PC is reset to the SIMT top and that warp's IBuffer is flushed.
- Fixed `IBuffer_Remodeled::flush(false)` so PTX mode no longer unconditionally casts the warp to `trace_shd_warp_t`.
- Trace mode remains guarded by the existing `is_trace_mode` checks.
- The previous `ptx_thread_info::ptx_exec_inst()` `pc == inst.pc` assertion is resolved for the local smoke.
- The smoke still produced no real simulator metrics.
- New blocker: `barrier_set_t::warp_reaches_barrier()` asserts `bar_id != (unsigned)-1` at `shader.cc:3867`; focused evidence shows `bar_type = SYNC` and timing-side `bar_id = 4294967295` after reaching a `bar.sync 0` reconvergence region.

Supervisor review:
- Supervisor reviewer `019eaac6-9c27-7183-a68f-7ab03ffdd89e` returned `ACCEPT`.
- Reviewer confirmed the SIMT-stack update has the standard GPGPU-Sim pdom update shape, stale IBuffer flushing is PTX-scoped, `flush(false)` avoids the trace-only cast in PTX mode, no config/latest/generated outputs or metrics were changed, and the barrier metadata assertion is a separate downstream blocker.

Follow-up:
- Pending S7 work remains: fix or precisely bound PTX `bar.sync` barrier id/count metadata propagation into the dynamic timing `warp_inst_t` before remodeled barrier handling.

### 2026-06-09 13:48:32 CST

Action:
- S7 PTX barrier metadata worker `019eaacf-589d-71e1-8967-5d0b55e97995` completed `docs/sm120-calibration/worker-logs/worker-20260609-131926-s7-barrier-metadata.md`.
- The worker reported a fresh blank-context read-only internal reviewer verdict of `ACCEPT` after one CLI invocation error.

Worker deliverables:
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/cuda-sim.cc`.
- `docs/sm120-calibration/overall-plan.md`.
- `docs/sm120-calibration/worker-logs/worker-20260609-131926-s7-barrier-metadata.md`.
- Local smoke evidence under ignored `artifacts/s7/s7-barrier-metadata-20260609-131926/`.

Worker validation:
- Rebuilt the CUDA 13.1 release GPGPU-Sim runtime.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Setup-only local smoke planning passed.
- Exactly one local PTX smoke job was launched.

Root cause:
- In PTX mode, remodeled IBuffer clones the canonical PTX instruction into a mutable dynamic `warp_inst_t`.
- PTX `bar_impl()` resolved `bar.sync` runtime operands and wrote `bar_id` and `bar_count` onto the functional `ptx_instruction`.
- `ptx_thread_info::ptx_exec_inst()` did not copy that barrier metadata back into the dynamic timing `warp_inst_t`, so `SM::issue_warp()` passed stale default barrier metadata into `barrier_set_t::warp_reaches_barrier()`.

Partial result:
- `ptx_thread_info::ptx_exec_inst()` now copies `bar_type`, `red_type`, `bar_id`, and `bar_count` from the functional PTX instruction into the dynamic timing instruction after functional barrier execution.
- The fix does not synthesize a default barrier id, remove or weaken `bar_id != (unsigned)-1`, or skip barrier handling.
- Trace mode remains outside this PTX functional execution path.
- The previous `bar_id != (unsigned)-1` assertion is resolved for the local smoke, and the prior `pc == inst.pc` assertion did not regress.
- The smoke still produced no real simulator metrics.
- New blocker: `Subcore::single_decode()` asserts `pI->valid()` at `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc:916`; focused evidence shows `pI` is non-null but default/invalid decoded with `pc = 18446744073709551615`, `m_decoded = false`, `op = NO_OP`, and `isize = 0`.

Supervisor review:
- Supervisor reviewer `019eaae5-fa33-7d41-a3c7-1bd2cadf1723` returned `ACCEPT`.
- Reviewer confirmed this is a root-cause metadata propagation fix rather than a default-id workaround, propagation happens before remodeled barrier handling, the barrier assertion and handling are preserved, trace mode is not touched, no config/latest/calibration-result/metrics outputs were changed, and the new invalid-decode assertion is separately bounded.

Follow-up:
- Pending S7 work remains: fix or precisely bound the remodeled PTX decode path that yields a non-null but invalid/default `warp_inst_t` at `Subcore::single_decode()`.

### 2026-06-09 14:35:32 CST

Action:
- S7 invalid decode worker `019eaaee-d36c-7641-9a8c-a9783e3beb01` completed `docs/sm120-calibration/worker-logs/worker-20260609-141104-s7-invalid-decode.md`.
- The worker reported a fresh blank-context read-only internal reviewer verdict of `ACCEPT`.

Worker deliverables:
- `simulator-remodeled/gpu-simulator/gpgpu-sim/libcuda/gpgpu_context.h`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/ptx_ir.cc`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/sm.cc`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc`.
- `docs/sm120-calibration/worker-logs/worker-20260609-141104-s7-invalid-decode.md`.
- Local smoke evidence under ignored `artifacts/s7/s7-invalid-decode-20260609-140131/`.

Worker validation:
- Rebuilt the CUDA 13.1 release GPGPU-Sim runtime.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Setup-only local smoke planning passed after sourcing the simulator environment.
- Exactly one local PTX smoke job was launched.

Root cause:
- Remodeled PTX fetch/decode could clone a non-null canonical PTX instruction before the function's PDOM/predecode setup had populated decoded instruction metadata such as `pc`, `isize`, and `m_decoded`.
- `pc_to_instruction()` also accepted an `unsigned` PC, so terminal or invalid 64-bit PCs such as `(address_type)-1` were not defensively represented at the lookup boundary.
- The cloned dynamic instruction could therefore reach `Subcore::single_decode()` as a default/invalid instruction, where the correct `pI->valid()` assertion fired.

Partial result:
- PTX-mode `SM::init_warps()` now runs the existing function PDOM/predecode setup once before remodeled PTX timing fetch/decode can clone instructions.
- `gpgpu_context::pc_to_instruction()` now accepts `address_type`.
- Remodeled PTX `Subcore::get_next_inst()` now validates fetched canonical PTX instructions before cloning them: non-null, valid, matching PC, and nonzero instruction size.
- If PTX fetch returns no valid instruction, the specific unresolved IBuffer reservation is rolled back rather than being marked as a valid decoded entry.
- The `pI->valid()` assertion is preserved; the fix does not synthesize `NO_OP` instructions or skip validated PTX instructions.
- Trace mode remains on the existing trace instruction source path.
- The previous invalid/default decode assertion is resolved for the local smoke. The prior `bar_id != (unsigned)-1` and `pc == inst.pc` blockers did not regress.
- The smoke still produced no real simulator metrics.
- New blocker: SIGSEGV in `ptx_file_line_stats_add_exec_count()` during concurrent `ptx_file_line_stats_tracker` insertion; focused evidence reaches `std::unordered_map<ptx_file_line, ptx_file_line_stats,...>::operator[](...)` from `ptx_thread_info::ptx_exec_inst()`.

Supervisor review:
- Supervisor reviewer `019eab11-2bff-7ba2-9ddd-990cb6a05f60` returned `ACCEPT`.
- Reviewer confirmed `Subcore::single_decode()`'s invariant is preserved, invalid/default PTX fetch results are rejected before cloning, no `NO_OP` workaround is introduced, PTX PDOM/predecode setup is trace-mode gated and `is_pdom_set()` protected, the `address_type` lookup change is a reasonable defensive fix, rollback is scoped by the IBuffer reservation model, no config/latest/calibration-result/metrics outputs were changed, and the new stats crash is separately bounded.

Follow-up:
- Pending S7 work remains: fix or precisely bound the PTX file-line stats concurrency crash in `ptx_file_line_stats_add_exec_count()`.

### 2026-06-09 15:09:55 CST

Action:
- S7 PTX stats concurrency worker `019eab1a-1a77-7f91-8323-833e38080eeb` completed `docs/sm120-calibration/worker-logs/worker-20260609-144109-s7-ptx-stats-concurrency.md`.
- The worker reported a fresh blank-context read-only internal reviewer verdict of `ACCEPT` after one CLI invocation error and a rerun.

Worker deliverables:
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/cuda-sim/ptx-stats.cc`.
- `docs/sm120-calibration/worker-logs/worker-20260609-144109-s7-ptx-stats-concurrency.md`.
- Local smoke evidence under ignored `artifacts/s7/s7-ptx-stats-concurrency-20260609-144109/`.

Worker validation:
- Rebuilt the CUDA 13.1 release GPGPU-Sim runtime.
- `generate_sm120_configs.py --check-only` passed.
- `git diff --check` passed.
- Setup-only local smoke planning passed.
- Exactly one local PTX smoke job was launched.

Root cause:
- `ptx_file_line_stats_tracker` is a process-global unordered-map-like tracker.
- Multiple OpenMP worker threads can execute PTX instructions concurrently and call source-line stats update paths, including `ptx_file_line_stats_add_exec_count()` from `ptx_thread_info::ptx_exec_inst()`.
- The previous implementation inserted and mutated the global tracker without external synchronization, matching the focused SIGSEGV in `_Hashtable::_M_insert_bucket_begin()`.

Partial result:
- Added a mutex around the global `ptx_file_line_stats_tracker`.
- Guarded all direct tracker mutation paths for exec count, latency, DRAM traffic, shared/global memory stats, exposed latency, and warp divergence.
- Guarded final tracker iteration in `ptx_file_line_stats_write_file()`.
- PTX source-line stats remain enabled; no stats call was skipped or disabled.
- The previous `ptx_file_line_stats_add_exec_count()` / unordered-map insertion SIGSEGV is resolved for the local smoke.
- Prior `Subcore::single_decode()` `pI->valid()`, `bar_id != (unsigned)-1`, and `pc == inst.pc` blockers did not regress.
- The smoke still produced no real simulator metrics.
- New blocker: `shd_warp_t::pop_function_call(active_mask_t)` asserts `!m_function_call_stack.empty()` at `shader.h:221`; focused stack reaches `set_done_exit()`, `SM::check_if_warp_has_finished_executing_and_can_be_reclaim()`, and `Subcore::fetch()`.

Supervisor review:
- Supervisor reviewer `019eab34-e380-7c20-958e-40f283e4d81f` returned `ACCEPT`.
- Reviewer confirmed all direct tracker mutation and iteration paths are guarded, this is a root-cause concurrency repair rather than a stats skip, PTX file-line stats remain enabled and called, no recursive lock or obvious deadlock path was introduced by the diff, trace/remodeled behavior outside the stats tracker is unaffected, no config/latest/calibration-result/metrics outputs were changed, and the new call-stack assertion is separately bounded.

Follow-up:
- Pending S7 work remains: fix or precisely bound the PTX/remodeled function-call-stack assertion in `shd_warp_t::pop_function_call()`.

### 2026-06-09 16:42:45 CST

Action:
- Replacement S7 function-call-stack worker `019eab77-40cf-7e43-9f39-9b826fcef9dc` completed `docs/sm120-calibration/worker-logs/worker-20260609-160932-s7-function-call-stack.md`.
- The worker took over the dirty worktree left by interrupted replacement workers and verified the inherited two-file code change.
- The worker reported a fresh blank-context read-only reviewer verdict of `ACCEPT` in reviewer round 4. Earlier reviewer attempts were recorded as invalid or unusable and were not counted.

Worker deliverables:
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/sm.cc`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader.h`.
- `docs/sm120-calibration/worker-logs/worker-20260609-160932-s7-function-call-stack.md`.
- Reused and replacement evidence under ignored `artifacts/s7/s7-function-call-stack-20260609-160932/`.

Worker validation:
- `git diff --check` passed.
- `generate_sm120_configs.py --check-only` passed.
- The post-fix smoke evidence was reused rather than relaunched because the behavioral code state was unchanged except for an explanatory comment and worker/reviewer documentation.
- The reused smoke evidence no longer shows the old `pop_function_call()` empty-stack assertion and advanced to first-kernel metrics before hitting a downstream SIGSEGV.

Root cause:
- PTX/performance mode does not seed or maintain the remodeled trace/SASS function-call stack.
- The remodeled PTX warp-reclaim path was still calling `shd_warp_t::set_done_exit()`, which is the trace/SASS done-exit path and pops that stack.
- The original core showed `m_config->is_trace_mode == false`, an empty function-call stack, and the abort path through `SM::check_if_warp_has_finished_executing_and_can_be_reclaim()`.

Partial result:
- Trace mode still calls `warp->set_done_exit()` and therefore keeps the original function-call-stack pop path.
- PTX mode now calls `warp->set_done_exit_for_ptx_reclaim()`, which asserts `m_function_call_stack.empty()` and marks the warp done without weakening `pop_function_call()`.
- Warp reclaim cleanup is still executed; the fix does not skip reclaim, convert empty pop into a no-op, or remove the existing assertion.
- The previous `shd_warp_t::pop_function_call(active_mask_t)` assertion is resolved for the reused local smoke.
- The smoke still did not complete the full workload. It produced first-kernel metric lines, then hit a new downstream PTX/remodeled decode-latency SIGSEGV in kernel 2.

New blocker:
- `traced_instruction::get_num_destination_registers(this=0x0)` is reached from `warp_inst_t::generate_dp_latencies()` and `Subcore::single_decode()`.
- Focused state shows `m_config->is_trace_mode == false`, `pI->pc == 10120`, `pI->isize == 8`, `pI->op == DP_OP`, `pI->sp_op == DP___OP`, `pI->m_decoded == true`, and an empty `m_extra_trace_instruction_info`.

Supervisor review:
- Independent supervisor reviewer `019eab87-db56-7051-9679-11be52b50816` returned `ACCEPT`.
- Reviewer confirmed the root cause is supported by code and old core evidence, trace mode remains on the original call-stack path, PTX mode preserves a useful empty-stack invariant, validation evidence is honest, and no config/latest/generated/calibration-result/metrics promotion was present.

Follow-up:
- Pending S7 work remains: fix or precisely bound the PTX-mode DP decode-latency path that dereferences missing trace-enhanced instruction metadata in `warp_inst_t::generate_dp_latencies()`.

### 2026-06-09 17:29:08 CST

Action:
- S7 DP latency worker `019eab8f-a2cd-7301-a392-c457e3fe89fb` completed `docs/sm120-calibration/worker-logs/worker-20260609-164753-s7-dp-latency.md`.
- The worker reported a fresh blank-context read-only reviewer verdict of `ACCEPT` in reviewer round 2. Round 1 did not produce a formal verdict and was not counted.

Worker deliverables:
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/abstract_hardware_model.cc`.
- `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc`.
- `docs/sm120-calibration/worker-logs/worker-20260609-164753-s7-dp-latency.md`.
- Local evidence under ignored `artifacts/s7/s7-dp-latency-20260609-164753/`.

Worker validation:
- `git diff --check` passed.
- `generate_sm120_configs.py --check-only` passed.
- Local CUDA 13.1 release GPGPU-Sim runtime rebuild passed.
- Setup-only local PTX smoke planning passed.
- Exactly one local PTX smoke was launched after rebuild. It reached first-kernel performance simulation and SM binding, and the previous `traced_instruction::get_num_destination_registers(this=0x0)` DP-latency crash was not reproduced before the bounded run was stopped.

Root cause:
- Remodeled decode-latency generation unconditionally used enhanced trace instruction metadata in `warp_inst_t::generate_dp_latencies()`.
- The same PTX/trace boundary also existed around tensor-core trace metadata preparation and tensor latency generation.
- PTX/performance-mode instructions have PTX predecode timing and operand metadata but no enhanced trace instruction metadata, so an assertion-disabled build dereferenced an empty trace-metadata pointer.

Partial result:
- PTX mode now avoids enhanced trace metadata in DP/tensor decode-latency setup.
- PTX DP latency setup uses PTX-predecoded source-register count plus existing config-backed shared-DP stage and subcore-to-SM link parameters.
- PTX tensor latency setup preserves existing PTX predecode latency/initiation values for the remodeled fixed-latency path.
- Trace mode still requires enhanced trace metadata for detailed DP/tensor latency modeling and fails explicitly if the required metadata is absent.
- `Subcore::single_decode()` prepares tensor-core trace metadata only in trace mode.
- No generated configs, latest aliases, accepted calibration results, or metrics artifacts were promoted.

Remaining issue:
- The bounded local PTX smoke is not a full smoke pass. It reached first-kernel execution and SM binding but did not produce first-kernel metrics within the worker's bounded wait.
- The remaining S7 issue is now a long-running or stalled first-kernel local PTX smoke before metrics, not a reproduced DP trace-metadata SIGSEGV.

Supervisor review:
- Independent supervisor reviewer `019eabb2-d577-7610-89b1-79fc066f9b8a` returned `ACCEPT`.
- Reviewer confirmed the root cause is supported, the fix is scoped to the PTX/trace metadata boundary, PTX fallback uses existing PTX/config information rather than device-specific constants, trace mode remains strict, and the bounded smoke evidence is not overstated as calibration/correlation.

Follow-up:
- Pending S7 work remains: triage why the local PTX smoke reaches first-kernel performance simulation but does not produce first-kernel metrics within a bounded wait.

### 2026-06-09 18:17:28 CST

Action:
- S7 smoke-stall triage worker `019eabb8-b3d6-79f0-89e9-573b3e26ac3e` completed `docs/sm120-calibration/worker-logs/worker-20260609-173154-s7-smoke-stall.md`.
- The worker reported a fresh read-only reviewer verdict of `ACCEPT` in reviewer round 3 after correcting earlier reviewer findings about log placement and pending reviewer/final-status sections.

Worker deliverables:
- `docs/sm120-calibration/worker-logs/worker-20260609-173154-s7-smoke-stall.md`.
- Local evidence under ignored `artifacts/s7/s7-smoke-stall-20260609-173154/`.

Worker validation:
- `git diff --check` passed.
- `generate_sm120_configs.py --check-only` passed.
- Local CUDA 13.1 release GPGPU-Sim runtime rebuild passed.
- Setup-only local PTX smoke planning passed.
- Exactly one fresh local PTX smoke was launched after rebuild as ProcMan job `482`.

Triage result:
- The earlier first-kernel no-metrics/stall hypothesis is not supported.
- Fresh job `482` produced first-kernel metrics:
  - `gpu_tot_sim_cycle = 7729`
  - `gpu_tot_sim_insn = 4169728`
  - `gpgpu_simulation_time = 0 days, 0 hrs, 7 min, 21 sec (441 sec)`
- The fresh run then launched and bound the second kernel `_Z24bpnn_adjust_weights_cudaPfiS_iS_S_`.
- No first-kernel pipeline/accounting no-progress root cause was reproduced, so no code change was justified for this specific triage task.

Caveat:
- This is not a full PTX smoke pass. The fresh run was manually stopped after first-kernel metrics and second-kernel bind were captured.
- No generated configs, latest aliases, accepted calibration results, or metrics artifacts were promoted.

Supervisor review:
- Independent supervisor reviewer `019eabde-61b7-7943-a8c8-7771658d6b3a` returned `ACCEPT`.
- Reviewer confirmed the worker conclusion is supported, no full-pass/calibration/correlation overclaim was made, no code change is acceptable for this triage-only result, and the next blocker is precise.

Follow-up:
- Pending S7 work remains: run a bounded local PTX smoke past the observed second-kernel bind, either to second-kernel/full application completion or to a later captured crash/stall point.

### 2026-06-09 19:08:44 CST

Action:
- S7 full-smoke boundary worker `019eabe4-ac2a-7f82-92f7-1d7d291bd1d3` completed `docs/sm120-calibration/worker-logs/worker-20260609-181955-s7-full-smoke.md`.
- The worker reported a fresh read-only reviewer verdict of `ACCEPT` after an earlier invalid reviewer CLI invocation.

Worker deliverables:
- `docs/sm120-calibration/worker-logs/worker-20260609-181955-s7-full-smoke.md`.
- Local evidence under ignored `artifacts/s7/s7-full-smoke-20260609-181955/`.

Worker validation:
- `git diff --check` passed.
- `generate_sm120_configs.py --check-only` passed.
- Setup-only local PTX smoke planning passed after sourcing the simulator environment.
- Exactly one bounded local PTX smoke was launched as ProcMan job `483`.
- Final ProcMan status showed `Nothing Active` after the timeout kill.

Triage result:
- The bounded full-smoke run did not complete.
- It produced first-kernel metrics:
  - `gpu_tot_sim_cycle = 7729`
  - `gpu_tot_sim_insn = 4169728`
  - `gpgpu_simulation_time = 0 days, 0 hrs, 7 min, 2 sec (422 sec)`
- It launched and bound the second kernel `_Z24bpnn_adjust_weights_cudaPfiS_iS_S_`.
- After second-kernel SM binding, it remained CPU-bound until the 30-minute wall-clock timeout.
- No second-kernel metrics, functional result output, `PASSED`/`FAILED` line, crash, assertion, or stderr growth was captured.
- GDB attach at timeout was blocked by ptrace/Yama policy, and `coredumpctl` found no visible coredumps.

Caveat:
- This is not a full PTX smoke pass.
- No simulator code, generated configs, latest aliases, accepted calibration results, or metrics artifacts were promoted.
- No code change was made because the worker did not prove a narrow root cause.

Supervisor review:
- Independent supervisor reviewer `019eac0f-58ab-7cd0-b94c-de01923bab03` returned `ACCEPT`.
- Reviewer confirmed the conclusion is supported, exactly one real smoke job was used, no full-pass/calibration/correlation overclaim was made, and no speculative code change is required before committing the evidence.

Follow-up:
- Pending S7 work remains: focused triage of kernel-2 PTX performance-simulation internal progress after SM bind, using reviewable temporary instrumentation or debug-attach permissions to capture active CTA counts, completed CTA counts, per-SM active warp/barrier state, scheduler issue state, and selected warp PCs.

### 2026-06-09 20:15:10 CST

Action:
- S7 kernel-2 progress diagnostic worker `019eac14-6327-7dd0-aed4-698de69e8480` completed `docs/sm120-calibration/worker-logs/worker-20260609-191215-s7-kernel2-progress.md`.
- The worker reported a fresh read-only reviewer verdict of `ACCEPT`.

Worker deliverables:
- Default-off diagnostic instrumentation in:
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-sim.cc`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/gpu-sim.h`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader.cc`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader.h`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader_core_wrapper.h`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/sm.cc`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/sm.h`
- `docs/sm120-calibration/worker-logs/worker-20260609-191215-s7-kernel2-progress.md`.
- Local evidence under ignored `artifacts/s7/s7-kernel2-progress-20260609-191215/`.

Instrumentation:
- Default off.
- Enabled only with `GPGPUSIM_KERNEL_PROGRESS_DEBUG=1`.
- Optional controls:
  - `GPGPUSIM_KERNEL_PROGRESS_INTERVAL`
  - `GPGPUSIM_KERNEL_PROGRESS_SM_LIMIT`
- Grep prefix: `GPGPUSIM-K2-PROGRESS`.
- Captures kernel uid/name/CTA progress, grid barrier aggregate state, aggregate active CTA/SM counts, sampled SM active CTA/warp/barrier/membar/gridbar/imiss/atomic state, selected warp PC/active lanes, and remodeled LD/ST public occupancy counters.

Worker validation:
- `git diff --check` passed.
- `generate_sm120_configs.py --check-only` passed.
- Local GPGPU-Sim rebuild passed.
- Setup-only local PTX smoke planning passed.
- Exactly one bounded diagnostic local PTX smoke was launched as ProcMan job `484`.
- Final ProcMan status showed `Nothing Active`.

Triage result:
- Kernel 2 is not stuck at launch or bind, and it is not a no-progress hang.
- `_Z24bpnn_adjust_weights_cudaPfiS_iS_S_` launches all 256 CTAs and completes 76 CTAs in the bounded diagnostic run.
- The smoke still does not complete.
- Sampled state near timeout shows extremely slow progress with many CTA-barrier/near-barrier warps around PC `0x2890`, pipeline activity, and small or zero normal-memory occupancy depending on sample.
- No sampled membar, gridbar, instruction miss, or atomic-pending blocker was observed.
- No second-kernel metrics, functional result output, full smoke pass, crash, assertion, or coredump was produced.

Caveat:
- This is not a root-cause fix and not a full PTX smoke pass.
- No generated configs, latest aliases, accepted calibration results, metrics artifacts, calibration, or correlation outputs were promoted.
- The `GPGPUSIM-K2-PROGRESS` prefix is acceptable for the current S7 diagnostic checkpoint; a future long-term cleanup may rename it if it becomes a general kernel-progress facility.

Supervisor review:
- Independent supervisor reviewer `019eac49-e872-70c2-97f3-7a69db91a51a` returned `ACCEPT`.
- Reviewer confirmed the instrumentation is default-off, scoped, read-only against sampled simulator state, and sufficient to support the kernel-2 progress conclusion. The reviewer found no blocking rework before commit.

Follow-up:
- Pending S7 work remains: determine why kernel 2 makes extremely slow progress after all CTAs are resident, focusing on barrier-release bookkeeping, SIMT/reconvergence behavior near PC `0x2890`, scheduler issue/no-issue conditions, or memory-return/scoreboard latency in the post-barrier global load/store tail.

### 2026-06-09 20:20:29 CST

Action:
- Resumed after an unexpected interruption.
- Re-read `supervisor-log.md`, `overall-plan.md`, and the latest S7 kernel-progress worker log per the recovery rule.
- Confirmed the current stage using standard terminology: S7 System Integration and Validation, specifically PTX-mode kernel-2 bottleneck attribution during local smoke bring-up.
- Spawned fresh blank-context S7 attribution worker `019eac54-3a0e-77b0-8ddc-32e839eb078b`.

Scope:
- Determine why backprop kernel 2 makes extremely slow progress after all CTAs are resident.
- Distinguish barrier-release bookkeeping, SIMT/reconvergence around PC `0x2890`, scheduler issue/no-issue state, and memory-return/scoreboard latency.
- Keep diagnostics default-off and avoid config/latest/calibration promotion.

### 2026-06-09 22:55:00 CST

Action:
- S7 kernel-2 attribution worker `019eac54-3a0e-77b0-8ddc-32e839eb078b` completed `docs/sm120-calibration/worker-logs/worker-20260609-211410-s7-kernel2-attribution.md`.
- The worker reported an internal fresh blank-context read-only reviewer Round 2 verdict of `ACCEPT` after a Round 1 `CHANGES_NEEDED` rework.
- Spawned independent supervisor reviewer `019eacc4-d611-7132-8ade-039c79de811f`.

Worker deliverables:
- Default-off kernel-progress attribution diagnostics in:
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/ldst_unit_sm.cc`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/ldst_unit_sm.h`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/sm.cc`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/sm.h`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.cc`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/remodeling/subcore.h`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/scoreboard.cc`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/scoreboard.h`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/scoreboard_reads.cc`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/scoreboard_reads.h`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader.cc`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader.h`
  - `simulator-remodeled/gpu-simulator/gpgpu-sim/src/gpgpu-sim/shader_core_wrapper.h`
- Worker log:
  `docs/sm120-calibration/worker-logs/worker-20260609-211410-s7-kernel2-attribution.md`.
- Local evidence under ignored `artifacts/s7/s7-kernel2-attribution-20260609-211410/`.

Validation:
- `git diff --check` passed.
- `generate_sm120_configs.py --check-only` passed.
- Local GPGPU-Sim rebuild passed.
- Setup-only local PTX smoke planning passed.
- Supervisor-authorized second bounded local PTX smoke ran as ProcMan job `486`, reached the all-CTAs-resident target window, completed kernel 2, and reported `PASSED`.
- Final ProcMan direct status reported `Nothing Active`.

Attribution result:
- Kernel 2 target window reached `next_cta=256`, `cta_completed_kernel=76`, `active_cta=180`.
- Kernel 2 completed with `gpu_tot_sim_cycle = 45818` and `gpu_tot_sim_insn = 8036672`.
- The sampled all-CTAs-resident slow window is dominated by CTA-barrier waiting / partial-barrier state around PC `0x2890`.
- Scheduler state is no-issue because sampled candidates are not ready, with barrier blockers dominant.
- Sampled evidence does not support a SIMT/reconvergence mismatch at PC `0x2890` (`pc_mis=0`).
- Sampled evidence does not support a post-barrier memory-return/queue tail (`mem_resp=0`, `mem_prt_active=0`, sampled queues zero).
- No speculative root-cause fix was made.

Supervisor review:
- Independent supervisor reviewer `019eacc4-d611-7132-8ade-039c79de811f` returned `ACCEPT`.
- Reviewer confirmed the worker satisfied the attribution goal, the `Subcore::issue()` diagnostic state is env-gated, the global print path remains default-off through `GPGPUSIM_KERNEL_PROGRESS_DEBUG`, smoke evidence is honest, and no config/latest/calibration/correlation promotion was made.
- Residual nonblocking risk: attribution is sampled with `SM_LIMIT=1`, so it narrows the bottleneck but does not prove a specific incorrect barrier-bookkeeping mutation.

Follow-up:
- S7 remains in progress.
- Pending S7 work remains: turn the successful local PTX smoke into reviewed S7 validation evidence, prepare real supplied-metrics correlation inputs only from real metrics, run bounded correlation/promotion-gate review if appropriate, and preserve RTX5070Ti compatibility.
