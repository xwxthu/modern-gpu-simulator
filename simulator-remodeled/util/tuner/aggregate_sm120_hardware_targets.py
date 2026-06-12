#!/usr/bin/env python3
"""Aggregate repeated draft SM120 hardware target YAMLs offline.

The output is intentionally draft-only. It can summarize repeated hardware
target runs and produce an aggregate S6 target handoff, but it must not be
treated as promotion-quality evidence until the repeat protocol is reviewed.
"""

from __future__ import annotations

import argparse
import copy
import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import sys
from typing import Any

import yaml


SIMULATOR_MARKERS = (
    "gpu_tot_sim_cycle",
    "gpu_tot_sim_insn",
    "gpgpu_simulation_time",
    "gpgpu_simulation_rate",
    "GPGPU-Sim",
    "Accel-Sim",
    "ProcMan job",
)
NATIVE_EXCLUDED_PREFIXES = ("native_",)
FORBIDDEN_OUTPUT_PARTS = (
    "/configs/tested-cfgs/",
    "/configs/generated/tested-cfgs/",
    "/configs/layered/sm120/",
    "/calibration-results/",
)
DEFAULT_CV_THRESHOLD_PERCENT = 2.0
DEFAULT_RANGE_THRESHOLD_PERCENT = 5.0


class AggregateError(RuntimeError):
    pass


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[3]


def iso_utc_now() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_git(root: Path, args: list[str]) -> str | None:
    import subprocess

    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def resolve_path(path_text: str | Path, root: Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path.resolve()
    return (root / path).resolve()


def display_path(path: Path, root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def check_output_target(path: Path, root: Path) -> None:
    rel = "/" + display_path(path, root)
    for part in FORBIDDEN_OUTPUT_PARTS:
        if part in rel:
            raise AggregateError(f"refusing to write aggregate hardware target into protected path: {path}")


def load_yaml(path: Path, label: str) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise AggregateError(f"{label} is not valid YAML: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise AggregateError(f"{label} must be a YAML mapping: {path}")
    return data


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AggregateError(f"{label} is not valid JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise AggregateError(f"{label} must be a JSON mapping: {path}")
    return data


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AggregateError(message)


def parse_run_number(path: Path, fallback: int) -> int:
    match = re.search(r"run(\d+)", path.name)
    if match:
        return int(match.group(1))
    return fallback


def metric_key(item: dict[str, Any]) -> tuple[str, str]:
    benchmark = item.get("benchmark")
    metric = item.get("metric")
    if not isinstance(benchmark, str) or not benchmark:
        raise AggregateError(f"target metric lacks benchmark: {item!r}")
    if not isinstance(metric, str) or not metric:
        raise AggregateError(f"target metric lacks metric name: {item!r}")
    return benchmark, metric


def numeric(value: Any, label: str) -> float:
    if isinstance(value, bool) or value is None:
        raise AggregateError(f"{label} must be numeric")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise AggregateError(f"{label} must be numeric, got {value!r}") from exc


def computed_stats(values: list[float]) -> dict[str, Any]:
    require(values, "cannot compute statistics for an empty value list")
    mean = statistics.fmean(values)
    stdev = statistics.stdev(values) if len(values) > 1 else 0.0
    range_value = max(values) - min(values)
    cv_percent = (stdev / mean * 100.0) if mean else 0.0
    range_percent = (range_value / mean * 100.0) if mean else 0.0
    return {
        "n": len(values),
        "values": values,
        "mean": mean,
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
        "stdev": stdev,
        "cv_percent": cv_percent,
        "range_percent_of_mean": range_percent,
    }


def rounded(value: float) -> float:
    if math.isfinite(value):
        return round(float(value), 9)
    return value


def stats_with_rounded_values(values: list[float]) -> dict[str, Any]:
    stats = computed_stats(values)
    return {
        "n": stats["n"],
        "values": [rounded(v) for v in stats["values"]],
        "mean": rounded(stats["mean"]),
        "median": rounded(stats["median"]),
        "min": rounded(stats["min"]),
        "max": rounded(stats["max"]),
        "stdev": rounded(stats["stdev"]),
        "cv_percent": round(float(stats["cv_percent"]), 6),
        "range_percent_of_mean": round(float(stats["range_percent_of_mean"]), 6),
    }


def values_close(left: list[float], right: list[float], tolerance: float = 1.0e-12) -> bool:
    if len(left) != len(right):
        return False
    return all(abs(a - b) <= tolerance for a, b in zip(left, right))


def stats_close(left: float, right: float, tolerance: float = 1.0e-9) -> bool:
    return abs(left - right) <= tolerance


def validate_source_run(data: dict[str, Any], path: Path, run_number: int) -> None:
    require(data.get("status") == "draft_not_applied", f"{path} must have status: draft_not_applied")
    require(data.get("hardware_target_metrics") is True, f"{path} must mark hardware_target_metrics: true")
    require(data.get("simulator_smoke_metrics") is False, f"{path} must mark simulator_smoke_metrics: false")
    require(data.get("fixture_only") is False, f"{path} must not be fixture_only")
    require(isinstance(data.get("target_metrics"), list) and data["target_metrics"], f"{path} lacks target_metrics")

    observations = data.get("run_observations")
    require(isinstance(observations, dict), f"{path} lacks run_observations")
    stdout = observations.get("native_stdout")
    require(isinstance(stdout, dict), f"{path} lacks native_stdout observations")
    require(stdout.get("application_passed") is True, f"{path} run {run_number} did not pass application")
    time_metrics = observations.get("gnu_time")
    require(isinstance(time_metrics, dict), f"{path} lacks gnu_time observations")
    require(time_metrics.get("exit_status") == 0, f"{path} run {run_number} native exit_status is not zero")
    source_safety = data.get("source_safety")
    require(isinstance(source_safety, dict), f"{path} lacks source_safety")
    require(
        source_safety.get("simulator_marker_policy") == "reject_inputs_containing_known_simulator_smoke_metric_markers",
        f"{path} lacks the expected simulator-marker rejection policy",
    )
    rejected_markers = source_safety.get("rejected_markers")
    require(isinstance(rejected_markers, list), f"{path} lacks source_safety.rejected_markers")
    missing_markers = [marker for marker in SIMULATOR_MARKERS if marker not in rejected_markers]
    require(not missing_markers, f"{path} source_safety.rejected_markers missing: {', '.join(missing_markers)}")


def validate_summary(summary: dict[str, Any], source_count: int) -> None:
    require(summary.get("promotion_quality") is False, "repeatability summary must keep promotion_quality: false")
    require(summary.get("all_application_passed") is True, "repeatability summary requires all_application_passed: true")
    require(summary.get("all_native_exit_zero") is True, "repeatability summary requires all_native_exit_zero: true")
    require(int(summary.get("run_count_native", -1)) == source_count, "repeatability summary native run count mismatch")
    require(int(summary.get("run_count_nsys", -1)) == source_count, "repeatability summary Nsight run count mismatch")
    require(isinstance(summary.get("metric_stats"), dict), "repeatability summary lacks metric_stats")


def metric_selection_value(stats: dict[str, Any], policy: str) -> float:
    return numeric(stats[policy], f"metric selection policy {policy}")


def build_aggregate(args: argparse.Namespace) -> dict[str, Any]:
    root = args.repo_root.resolve()
    source_paths = [resolve_path(item, root) for item in args.source_yaml]
    require(source_paths, "at least one --source-yaml is required")
    summary_path = resolve_path(args.repeatability_summary, root)
    summary = load_json(summary_path, "repeatability summary")
    validate_summary(summary, len(source_paths))

    runs: list[dict[str, Any]] = []
    metric_records: dict[tuple[str, str], list[dict[str, Any]]] = {}
    source_file_hashes: list[dict[str, Any]] = []
    device_observations: list[dict[str, Any]] = []
    tool_identity_files: dict[str, dict[str, Any]] = {}
    native_statuses: list[dict[str, Any]] = []
    benchmark_cases: list[dict[str, Any]] | None = None
    gpu = architecture = ""

    for index, path in enumerate(source_paths, start=1):
        data = load_yaml(path, "source target YAML")
        run_number = parse_run_number(path, index)
        validate_source_run(data, path, run_number)
        if index == 1:
            gpu = str(data.get("gpu", ""))
            architecture = str(data.get("architecture", ""))
            benchmark_cases = data.get("benchmark_cases")
        else:
            require(data.get("gpu") == gpu, f"{path} GPU differs from first source")
            require(data.get("architecture") == architecture, f"{path} architecture differs from first source")
            require(data.get("benchmark_cases") == benchmark_cases, f"{path} benchmark_cases differs from first source")

        observations = data["run_observations"]
        native_stdout = observations["native_stdout"]
        gnu_time = observations["gnu_time"]
        native_statuses.append(
            {
                "run": run_number,
                "application_passed": True,
                "exit_status": 0,
                "checksum": native_stdout.get("checksum"),
            }
        )
        source_file_hashes.append(
            {
                "run": run_number,
                "path": display_path(path, root),
                "sha256": sha256_file(path),
                "source_files": data.get("source_files", []),
            }
        )
        collection = data.get("collection", {})
        if isinstance(collection, dict):
            device_observations.append(
                {
                    "run": run_number,
                    "host": collection.get("host"),
                    "source_label": collection.get("source_label"),
                    "device_observation": collection.get("device_observation", {}),
                }
            )

        for source_file in data.get("source_files", []):
            if isinstance(source_file, dict) and source_file.get("kind") in {"tool_versions", "nvidia_smi_query"}:
                tool_identity_files[str(source_file["kind"])] = {
                    "path": source_file.get("path"),
                    "sha256": source_file.get("sha256"),
                    "bytes": source_file.get("bytes"),
                }

        run_entry: dict[str, Any] = {"run": run_number}
        run_entry["application_passed"] = True
        run_entry["exit_status"] = 0
        if native_stdout.get("checksum"):
            run_entry["checksum"] = native_stdout.get("checksum")
        for metric in data["target_metrics"]:
            key = metric_key(metric)
            value = numeric(metric.get("target"), f"{path} target {key}")
            copied = dict(metric)
            copied["target"] = value
            copied["run"] = run_number
            metric_records.setdefault(key, []).append(copied)
            run_entry[key[1]] = value
        for name, value in gnu_time.items():
            if name == "exit_status":
                continue
            metric_name = f"native_{name}" if not str(name).startswith("native_") else str(name)
            run_entry.setdefault(metric_name, value)
        runs.append(run_entry)

    metric_stats = summary["metric_stats"]
    aggregate_metrics: list[dict[str, Any]] = []
    excluded_native_wall_metrics: list[dict[str, Any]] = []
    metric_thresholds: list[dict[str, Any]] = []
    selection_policy = args.metric_selection_policy

    for key in sorted(metric_records):
        benchmark, metric_name = key
        records = sorted(metric_records[key], key=lambda item: item["run"])
        values = [numeric(item["target"], f"{metric_name} run target") for item in records]
        require(
            len(values) == len(source_paths),
            f"{metric_name} appears in {len(values)} source runs, expected {len(source_paths)}",
        )
        stats = computed_stats(values)
        source_stats = metric_stats.get(metric_name)
        if isinstance(source_stats, dict):
            summary_stats = {
                "n": int(source_stats["n"]),
                "values": [numeric(v, f"{metric_name} summary value") for v in source_stats["values"]],
                "mean": numeric(source_stats["mean"], f"{metric_name} summary mean"),
                "median": numeric(source_stats["median"], f"{metric_name} summary median"),
                "min": numeric(source_stats["min"], f"{metric_name} summary min"),
                "max": numeric(source_stats["max"], f"{metric_name} summary max"),
                "stdev": numeric(source_stats["stdev"], f"{metric_name} summary stdev"),
                "cv_percent": numeric(source_stats["cv_percent"], f"{metric_name} summary CV"),
                "range_percent_of_mean": numeric(
                    source_stats["range_percent_of_mean"], f"{metric_name} summary range"
                ),
            }
            require(summary_stats["n"] == len(values), f"{metric_name} summary n does not match source runs")
            require(
                values_close(summary_stats["values"], values),
                f"{metric_name} summary values do not match source run targets",
            )
            for stat_name in ("mean", "median", "min", "max", "stdev", "cv_percent", "range_percent_of_mean"):
                require(
                    stats_close(summary_stats[stat_name], numeric(stats[stat_name], stat_name)),
                    f"{metric_name} summary {stat_name} does not match recomputed source-run statistic",
                )

        first = records[0]
        threshold = {
            "benchmark": benchmark,
            "metric": metric_name,
            "repeat_count": len(values),
            "cv_percent": round(float(stats["cv_percent"]), 6),
            "cv_threshold_percent": args.cv_threshold_percent,
            "cv_within_threshold": stats["cv_percent"] <= args.cv_threshold_percent,
            "range_percent_of_mean": round(float(stats["range_percent_of_mean"]), 6),
            "range_threshold_percent": args.range_threshold_percent,
            "range_within_threshold": stats["range_percent_of_mean"] <= args.range_threshold_percent,
        }
        metric_thresholds.append(threshold)

        item = {
            "benchmark": benchmark,
            "metric": metric_name,
            "target": rounded(metric_selection_value(stats, selection_policy)),
            "selected_statistic": selection_policy,
            "unit": first.get("unit"),
            "source": "aggregate_repeated_draft_hardware_targets",
            "source_metric_source": first.get("source"),
            "metric_role": first.get("metric_role"),
            "weight": first.get("weight", 1.0),
            "epsilon": first.get("epsilon"),
            "normalization": first.get("normalization"),
            "include_in_s6_template": bool(first.get("include_in_s6_template")),
            "repeatability": stats_with_rounded_values(values),
            "threshold_evaluation": threshold,
            "policy_reason": first.get("policy_reason"),
        }
        if metric_name.startswith(NATIVE_EXCLUDED_PREFIXES):
            item["include_in_s6_template"] = False
            item["metric_role"] = first.get("metric_role", "hardware_characterization")
            excluded_native_wall_metrics.append(copy.deepcopy(item))
        aggregate_metrics.append(item)

    comparable_targets = [
        item
        for item in aggregate_metrics
        if item.get("include_in_s6_template") is True
        and str(item.get("source_metric_source", "")).startswith("nsight_systems")
        and str(item.get("metric", "")).endswith("_time_ms")
    ]
    blocked_thresholds = [
        item
        for item in metric_thresholds
        if not item["cv_within_threshold"] or not item["range_within_threshold"]
    ]
    blocker_text = (
        "Aggregate target is draft-only: repeat count and variation thresholds are documented, "
        "but the hardware-control protocol, warmup/clock/thermal policy, S6 supplied-metrics "
        "manifest, promotion-gate review, and RTX5070Ti signoff are not approved."
    )

    return {
        "schema_version": 1,
        "schema_id": "sm120_aggregate_hardware_target_metrics_v1",
        "target_id": args.target_id,
        "gpu": gpu,
        "architecture": architecture,
        "status": "draft_not_applied",
        "aggregate_draft": True,
        "non_promotion": True,
        "promotion_quality": False,
        "hardware_target_metrics": True,
        "simulator_smoke_metrics": False,
        "generated_at": args.generated_at or iso_utc_now(),
        "fixture_only": False,
        "aggregator": {
            "script": "simulator-remodeled/util/tuner/aggregate_sm120_hardware_targets.py",
            "script_sha256": sha256_file(Path(__file__).resolve()),
        },
        "repository": {
            "root": str(root),
            "git_commit": run_git(root, ["rev-parse", "HEAD"]) or "unknown",
            "git_branch": run_git(root, ["rev-parse", "--abbrev-ref", "HEAD"]) or "unknown",
        },
        "source_artifacts": {
            "repeatability_summary": {
                "path": display_path(summary_path, root),
                "sha256": sha256_file(summary_path),
            },
            "per_run_hardware_target_yamls": source_file_hashes,
            "raw_provenance_hashes": {
                "per_run_hardware_target_yamls": [
                    {"path": item["path"], "sha256": item["sha256"]} for item in source_file_hashes
                ],
                "tool_identity_files": tool_identity_files,
            },
        },
        "device_and_tool_identity": {
            "device_observations": device_observations,
            "tool_identity_files": copy.deepcopy(tool_identity_files),
        },
        "benchmark_cases": benchmark_cases or [],
        "repeat_protocol": {
            "source_protocol_status": "retrospective_draft_from_repeated_runs",
            "repeat_count": len(source_paths),
            "native_run_count": int(summary.get("run_count_native")),
            "nsight_run_count": int(summary.get("run_count_nsys")),
            "metric_selection_policy": selection_policy,
            "cv_threshold_percent": args.cv_threshold_percent,
            "range_threshold_percent": args.range_threshold_percent,
            "required_source_status": "draft_not_applied",
            "required_source_flags": {
                "hardware_target_metrics": True,
                "simulator_smoke_metrics": False,
            },
            "required_native_outcome": {
                "application_passed": True,
                "exit_status": 0,
            },
            "warmup_clock_thermal_policy": "not_approved_for_promotion_in_source_collection",
        },
        "source_validation": {
            "all_source_runs_draft": True,
            "all_hardware_target_metrics": True,
            "all_simulator_smoke_metrics_false": True,
            "all_native_exit_zero": True,
            "all_application_passed": True,
            "native_statuses": native_statuses,
        },
        "simulator_marker_rejection_summary": {
            "policy": "source collector rejected raw inputs containing known simulator smoke metric markers",
            "rejected_markers": list(SIMULATOR_MARKERS),
            "aggregate_script_did_not_rescan_raw_inputs": True,
            "source_yaml_policy_checked": True,
        },
        "target_metrics": aggregate_metrics,
        "s6_supplied_metrics_handoff": {
            "target_metrics": [
                {
                    "benchmark": item["benchmark"],
                    "metric": item["metric"],
                    "target": item["target"],
                    "weight": item["weight"],
                    "epsilon": item["epsilon"],
                    "normalization": item["normalization"],
                    "selected_statistic": item["selected_statistic"],
                }
                for item in comparable_targets
            ],
            "candidate_simulator_metrics_present": False,
            "ready_for_search_sm120_correlation": False,
            "reason": (
                "Aggregate hardware targets are available for review, but S6 still needs a reviewed "
                "supplied_metrics manifest with matching simulator candidate metrics."
            ),
        },
        "excluded_native_wall_metrics": excluded_native_wall_metrics,
        "threshold_summary": {
            "all_metrics_within_thresholds": not blocked_thresholds,
            "blocked_metrics": copy.deepcopy(blocked_thresholds),
            "thresholds_are_promotion_gate": False,
            "reason": "Thresholds are draft review aids only until the repeat protocol is approved.",
        },
        "blockers": [
            blocker_text,
            "No approved hardware-control protocol for clocks, warmup, thermal state, idle GPU state, or background load.",
            "No reviewed runnable S6 supplied_metrics manifest with matching simulator candidate metrics.",
            "No promotion-gate reviewer approval and no RTX5070Ti compatibility signoff.",
        ],
        "handoff": {
            "result_policy": "draft_not_applied",
            "do_not_claim_calibrated": True,
            "do_not_apply_automatically": [
                "flat tested configs",
                "generated tested-cfgs outputs",
                "calibration-results/latest",
                "S6 ranked reports without candidate simulator metrics",
            ],
        },
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=repo_root_from_script(), help="Repository root.")
    parser.add_argument("--repeatability-summary", required=True, help="repeatability-summary.draft.json path.")
    parser.add_argument("--source-yaml", action="append", required=True, help="Per-run draft hardware target YAML.")
    parser.add_argument("--output", required=True, help="Aggregate draft YAML output path, or '-' for stdout.")
    parser.add_argument("--target-id", required=True, help="Stable aggregate target id.")
    parser.add_argument("--generated-at", default="", help="Deterministic generated_at timestamp.")
    parser.add_argument(
        "--metric-selection-policy",
        choices=("mean", "median"),
        default="mean",
        help="Statistic copied into aggregate target values.",
    )
    parser.add_argument("--cv-threshold-percent", type=float, default=DEFAULT_CV_THRESHOLD_PERCENT)
    parser.add_argument("--range-threshold-percent", type=float, default=DEFAULT_RANGE_THRESHOLD_PERCENT)
    return parser.parse_args(argv)


def write_yaml(path_text: str, data: dict[str, Any], root: Path) -> None:
    if path_text == "-":
        sys.stdout.write(yaml.safe_dump(data, sort_keys=False, width=120))
        return
    path = resolve_path(path_text, root)
    check_output_target(path, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, width=120), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        root = args.repo_root.resolve()
        result = build_aggregate(args)
        write_yaml(args.output, result, root)
    except AggregateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
