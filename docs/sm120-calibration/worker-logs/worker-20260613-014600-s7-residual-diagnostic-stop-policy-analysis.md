# S7 Residual Diagnostic Stop-Policy Analysis Worker Log

## Purpose

Analyze why refined residual-attribution diagnostic Job `14` stopped at
dispatch cycle `201` / cycle-cost sample `200` instead of reaching the deeper
cycle `1200` or cycle `1801` pre-admission window.

This is diagnostic methodology and stop-policy analysis only. No simulator run,
ProcMan diagnostic run, source edit, generated config edit, metrics generation,
S6 report generation, or promotion action was performed.

## Scope And Base

- Repo: `/home/xiewx/accel-0608/modern-gpu-simulator`
- Branch: `dev-5060`
- Base checkpoint: `78a5bc7` (`docs: record SM120 residual attribution diagnostic`)
- Timestamp: `2026-06-13T01:46:00+08:00`
- Host: `dsp-ubuntu`
- Worker role: S7 analysis worker

Initial tracked worktree state:

```text
## dev-5060...origin/dev-5060 [ahead 70]
 M docs/sm120-calibration/supervisor-log.md
```

The supervisor-log modification was pre-existing and was not edited by this
worker.

## Mandatory Context Read

- `docs/sm120-calibration/supervisor-log.md`
- `docs/sm120-calibration/overall-plan.md`
- `docs/sm120-calibration/worker-logs/worker-20260613-012616-s7-candidate0002-residual-attribution-diagnostic.md`
- `docs/sm120-calibration/worker-logs/worker-20260612-235505-s7-candidate0002-cluster-core-detail-diagnostic.md`
- `artifacts/s7/s7-candidate0002-residual-attribution-diagnostic-20260613-011718/logs/`
- `artifacts/s7/s7-candidate0002-cluster-core-detail-diagnostic-20260612-235505/logs/`

## Question 1: Stall Or Stop Policy

Conclusion: Job `14` is stronger evidence of an overly output-driven stop
policy than of a real simulator stall or livelock before cycle `1200`.
Confidence: medium-high for stop-policy miscalibration, low for a proven
simulator livelock.

Evidence:

- Job `14` did make simulated progress after a long initial quiet interval:
  `monitor.log` stayed at `max_cycle=1` through `poll_elapsed=164`, then grew
  at `poll_elapsed=185` to `stdout_size=204742` and
  `max_cycle=201`.
- The final useful diagnostics show normal pre-admission TB-latency countdown,
  not a stuck counter:
  `select_kernel_none detail=tb_latency_pending` at dispatch cycle `201` with
  `tb_latency=1600`, and cycle-cost sample `200` with `tb_latency=1599`.
- Cycle `201` is still far before expected admission. Prior analysis established
  the TB-latency path needs the countdown to reach zero around cycle `1801`;
  stopping at cycle `201` gives no evidence about the intended cycle `1200`
  or `1801` window.
- Job `14` had CPU-heavy child evidence at manual stop:
  the benchmark/simulator child had `%CPU=931` in
  `process-poll-manual-stop.log`, and `process-tree-at-manual-stop.log`
  showed the same child at `99%` with `00:34:06` accumulated CPU time.
- The monitor's `cpu_heavy=False` lines are not reliable CPU-idleness evidence:
  they tracked ProcMan wrapper PID `3379431`, while the CPU-heavy process was
  child PID `3379432`.
- The Job `14` artifacts do not contain a monitor sequence proving a long
  post-cycle-201 no-output interval. `monitor.log` ends with the output-growth
  poll that observed cycle `201`. Manual-stop snapshots prove the child was
  still CPU-heavy and that stdout stopped at cycle `201`, but they do not prove
  several later no-growth monitor intervals after that cycle.

This does not prove the simulator was healthy. The child was CPU-heavy and the
pre-admission path remained extremely expensive. It does show that killing the
run at cycle `201` was premature for the stated diagnostic target.

## Question 2: Job 13 Versus Job 14

Both jobs used the same candidate point:

```text
-latency_L0_to_L1=37
-prefetch_per_stream_buffer_size=10
```

Both enabled startup, dispatch, progress, and cycle-cost diagnostics with
`GPGPUSIM_CYCLE_COST_INTERVAL=200`. Both stayed in pre-admission
`tb_latency_pending` state with no `select_kernel_current`, no bind/admission,
no CTA launch, no result, and no metrics.

Comparison:

| Dimension | Job 13 | Job 14 |
| --- | --- | --- |
| Instrumentation | Enhanced `cluster_core_detail` | Refined residual-attribution fields |
| Stop reason | `no-output-growth-cpu-heavy` | `no-output-growth-child-cpu-heavy-repeated-early-pre-admission-state` |
| Monitor entries | 24 | 11 |
| Max dispatch/progress cycle | `1201` | `201` |
| Max cycle-cost sample | `1200` | `200` |
| Cycle-cost samples | 8 sampled records (`0`, `1`, `200`, `400`, `600`, `800`, `1000`, `1200`) | 3 sampled records (`0`, `1`, `200`) |
| Output-growth cadence | stdout grew at elapsed `0`, `81`, `182`, `243`, `303`, `384` seconds, then stayed flat through `465` seconds | stdout stayed flat through `164` seconds, then grew at `185` seconds to cycle `201`; no later monitor growth sequence is recorded |
| CPU evidence | child CPU-heavy throughout monitor, around `2109` to `2557` percent | wrapper CPU looked idle in monitor, but child CPU-heavy evidence exists at manual stop (`%CPU=931`) |
| Stop gate quality | Stopped after one additional no-growth span after reaching cycle `1201` | Stopped at or immediately after first useful growth to cycle `201`; did not wait for the next expected cycle-cost interval |

Job `13` demonstrates that low-frequency output is normal for this diagnostic:
with 20-second polling and 200-cycle emission intervals, stdout growth arrived
roughly every `60` to `101` seconds once underway. It also tolerated long
no-growth stretches before later output appeared.

Job `14` was slower or delayed earlier: it needed about `185` seconds of monitor
time to reach the first `200`-cycle interval. That first interval was not a
stall; it was exactly the kind of low-frequency progress the diagnostic was
configured to emit. Killing before observing whether cycle `400`, `600`,
`1200`, or `1801` would arrive makes Job `14` an early-stop artifact.

## Question 3: Safest Next Diagnostic Policy

Safest next policy: rerun only if the supervisor wants more evidence, and make
the stop gate progress-aware rather than output-size-only.

Recommended policy for a next bounded diagnostic:

1. Keep a strict wall cap, for example `20` to `25` minutes.
2. Do not kill solely on no stdout/stderr growth before the target cycle when
   the process tree shows a CPU-heavy simulator child.
3. Track the child benchmark/simulator PID or process tree CPU time, not only
   the ProcMan wrapper PID.
4. Set the no-output-growth threshold above the observed cadence. A conservative
   threshold is at least `5` minutes after the last output growth, and only after
   confirming child CPU time is not increasing or the same simulated cycle/state
   is repeated by an independent heartbeat.
5. Prefer more frequent low-volume cycle-cost output for this pre-admission
   window, for example `GPGPUSIM_CYCLE_COST_INTERVAL=50` or `100` with a bounded
   limit. This reduces wall time between progress observations without changing
   simulator semantics.
6. Add or use an explicit heartbeat only if rerun policy alone is not enough.
   The heartbeat should be default-off, low-volume, and emitted from the
   simulator loop or cycle-cost path with simulated cycle and TB-latency state.

The lowest-risk immediate rerun policy is:

```text
stop at first of:
- cycle-cost sample >= 1800, dispatch cycle >= 1801, select_kernel_current, bind, or CTA launch;
- strict wall cap;
- child CPU time stops increasing for a sustained interval;
- explicit heartbeat shows repeated same simulated cycle/TB-latency state.

do not stop solely because stdout size is unchanged for a short interval while
child CPU remains high and the target cycle has not been reached.
```

## Question 4: Next Action

Recommended next action: rerun with changed worker stop policy and possibly a
more frequent cycle-cost interval. Do not make a source-code instrumentation
change first.

Rationale:

- The existing refined residual-attribution instrumentation already answered
  the early-cycle attribution question for cycles `0`, `1`, and `200`.
- The missing evidence is methodological: Job `14` did not stay alive long
  enough to sample the deeper requested window.
- Job `13` already proved the same candidate can reach cycle `1200` under a
  similar diagnostic setup, so a rerun policy change is safer and more directly
  targeted than new code.
- A source change is justified only if a progress-aware rerun still cannot
  distinguish CPU-heavy progress from true no-progress. In that case, add a
  minimal default-off heartbeat rather than a semantic fast path.

Pause/exclusion policy:

- Keep low `-latency_L0_to_L1=37` points excluded from promotion and bounded
  sweep metrics.
- Do not spend more sweep execution on low-latency promotion candidates until
  this pre-admission cost and stop-policy issue is resolved.
- If diagnostic budget is constrained, pausing low-latency points is safer than
  promoting or interpreting Job `14` as a deep-window residual result.

## Evidence Details

Job `14` monitor excerpt:

```text
poll_elapsed=0   stdout_size=195740 max_cycle=1   no_growth_polls=0
poll_elapsed=164 stdout_size=195740 max_cycle=1   no_growth_polls=8
poll_elapsed=185 stdout_size=204742 max_cycle=201 no_growth_polls=0
```

Job `14` stop summary:

```text
stop_reason=no-output-growth-child-cpu-heavy-repeated-early-pre-admission-state
max_observed_dispatch_cycle=201
max_cycle_cost_sample=200
select_kernel_current=False
bind_or_admission=False
cta_launch=False
cycle_cost_samples=3
result_files_present=False
```

Job `14` refined cycle-cost aggregate:

```text
sample_count=3
max_cycle=200
cluster_core=625762 us
non_core_cycle_residual_us=625736 us
loop_accounted_us=26 us
eligibility_us=17 us
inactive_core_cycle_us=9 us
```

Job `13` monitor cadence:

```text
elapsed=0   max_cycle=201
elapsed=81  max_cycle=401
elapsed=182 max_cycle=601
elapsed=243 max_cycle=801
elapsed=303 max_cycle=1001
elapsed=384 max_cycle=1201
elapsed=465 max_cycle=1201
```

Job `13` cycle-cost aggregate:

```text
sample_count=8
max_cycle=1200
cluster_core=496430 us, 96.380513% of sampled total
core_cycle_us=256 us
non_core_cycle_residual_us=496174 us
```

## Limitations

- No new simulator run was performed, by scope.
- The Job `14` raw monitor does not include a post-cycle-201 no-growth series.
  The analysis therefore treats the stop as premature rather than as proven
  long silent execution after cycle `201`.
- The artifacts do not establish whether the refined attribution fields caused
  extra overhead versus Job `13`; they only show Job `14` had slower or delayed
  output and was stopped before comparable depth.
- CPU-heavy evidence for Job `14` comes from process-tree/manual-stop snapshots,
  not from the monitor's `cpu_heavy` field.

## Changed Files

Tracked documentation added by this worker:

- `docs/sm120-calibration/worker-logs/worker-20260613-014600-s7-residual-diagnostic-stop-policy-analysis.md`

No other tracked files were intentionally modified.

## Validation And Cleanup

Validation commands:

```bash
git diff --check
python3 simulator-remodeled/util/job_launching/procman.py -p
find /home/xiewx/accel-0608 -name 'define-s7-bounded-sweep-temp.yml' -print
```

Results:

- `git diff --check`: passed.
- ProcMan final state: `Nothing Active`.
- Temporary S7 bounded-sweep alias scan: no output.
- No generated/accepted/latest config, calibration-result, S6 report, metrics,
  or promotion artifact touched.

## Reviewer Rounds

### Round 1

Blank-context reviewer agent:

- Agent: `019ebcf3-b33e-7252-9dfd-9f4d15179ab8`
- Verdict: `ACCEPT`

Reviewer summary:

- The log answers all four requested questions with artifact-backed evidence.
- Job `14` progress to cycle `201`, lack of a post-cycle-201 monitor
  no-growth sequence, child CPU-heavy manual-stop evidence, and cycle-cost
  evidence only through cycle `200` are correctly represented.
- Job `13` comparison is supported for same candidate point, diagnostic
  interval, cycle progression through `1201`, CPU-heavy monitor values, and no
  bind/CTA/result.
- Conclusions are appropriately bounded: the log does not claim a healthy
  simulator, does not treat Job `14` as deep-window evidence, recommends a
  stop-policy-adjusted rerun before new instrumentation, and keeps low-latency
  points excluded from promotion.
- No scope violation or artifact misreading was found.

## Final Status

Final status: documentation-only analysis complete and accepted by internal
reviewer.
