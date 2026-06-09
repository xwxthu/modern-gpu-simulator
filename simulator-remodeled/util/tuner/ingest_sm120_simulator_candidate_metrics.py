#!/usr/bin/env python3
"""Ingest SM120 simulator run artifacts into draft S6 supplied metrics.

This bridge is intentionally draft-only. It parses local simulator stdout and
generated run config files into simulator candidate metrics. It does not parse
hardware target data, does not run the simulator, and does not write accepted
configs or calibration-results/latest.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

import yaml

from collect_sm120_hardware_metrics import normalize_metric_name
import search_sm120_correlation as s6_search


GPU_CHOICES = ("RTX5060", "RTX5070_TI")
DEFAULT_ARCHITECTURE = "SM120"
DEFAULT_BENCHMARK_SELECTOR = "rodinia_2.0-ft:backprop-rodinia-2.0-ft:0"
DEFAULT_BENCHMARK_ID = "backprop_4096"
DEFAULT_BENCHMARK_SUITE = "rodinia_2.0-ft"
DEFAULT_BENCHMARK_NAME = "backprop-rodinia-2.0-ft"
DEFAULT_ARGS = "4096 ./data/result-4096.txt"
DEFAULT_SOURCE_KIND = "local_simulator_run"
TIME_FROM_CYCLES_METHOD = (
    "gpu_sim_cycle_to_cuda_kernel_time_ms_using_gpgpu_clock_domains_core_mhz"
)
FORBIDDEN_OUTPUT_PARTS = (
    "/configs/tested-cfgs/",
    "/configs/generated/tested-cfgs/",
    "/configs/layered/sm120/",
    "/calibration-results/",
)
KEY_VALUE_RE = re.compile(r"^(-[A-Za-z0-9_][A-Za-z0-9_:.-]*)=(.+)$")
GPGPU_CLOCK_RE = re.compile(r"^\s*-gpgpu_clock_domains\s+([^#\s]+)")
KERNEL_NAME_RE = re.compile(r"^\s*kernel_name\s*=\s*(\S+)")
KERNEL_UID_RE = re.compile(r"^\s*kernel_launch_uid\s*=\s*(\d+)")
STAT_RE = re.compile(r"^\s*(gpu_(?:tot_)?(?:sim_cycle|sim_insn|ipc|tot_ipc|occupancy|tot_occupancy|tot_sms_occupancy))\s*=\s*(.+?)\s*$")
SIM_TIME_RE = re.compile(r"gpgpu_simulation_time\s*=.*\((\d+(?:\.\d+)?)\s+sec\)")


class IngestError(RuntimeError):
    pass


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[3]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def display_path(path: Path, root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def resolve_path(path_text: str | Path, root: Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path.resolve()
    return (root / path).resolve()


def iso_utc_now() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_git(root: Path, args: list[str]) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def read_text_file(path: Path) -> str:
    if not path.is_file():
        raise IngestError(f"input file does not exist: {path}")
    return path.read_text(encoding="utf-8", errors="replace")


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise IngestError(f"{path} did not load as a YAML mapping")
    return data


def parse_decimal(value: Any, label: str) -> float:
    text = str(value).strip().rstrip("%").replace(",", "")
    try:
        return float(text)
    except ValueError as exc:
        raise IngestError(f"{label} must be numeric, got {value!r}") from exc


def parse_int(value: Any, label: str) -> int:
    try:
        return int(Decimal(str(value).strip().replace(",", "")))
    except (InvalidOperation, ValueError) as exc:
        raise IngestError(f"{label} must be integer-compatible, got {value!r}") from exc


def parse_key_values(items: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for item in items:
        match = KEY_VALUE_RE.match(item)
        if not match:
            raise IngestError(f"candidate values must be KEY=VALUE with a config key, got {item!r}")
        key, value = match.groups()
        if key in values:
            raise IngestError(f"duplicate candidate value for {key}")
        values[key] = value.strip()
        if not values[key]:
            raise IngestError(f"candidate value for {key} is empty")
    return values


def parse_stub_map(items: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise IngestError(f"kernel stub mappings must be RAW_NAME=metric_stub, got {item!r}")
        raw, stub = item.split("=", 1)
        raw = raw.strip()
        stub = normalize_metric_name(stub)
        if not raw:
            raise IngestError("kernel stub mapping raw name is empty")
        if raw in mapping:
            raise IngestError(f"duplicate kernel stub mapping for {raw}")
        mapping[raw] = stub
    return mapping


def core_clock_mhz_from_config(text: str) -> float:
    for line in text.splitlines():
        match = GPGPU_CLOCK_RE.match(line)
        if not match:
            continue
        fields = match.group(1).split(":")
        if not fields:
            raise IngestError("-gpgpu_clock_domains is empty")
        core_mhz = parse_decimal(fields[0], "-gpgpu_clock_domains core clock")
        if core_mhz <= 0:
            raise IngestError("-gpgpu_clock_domains core clock must be positive")
        return core_mhz
    raise IngestError("gpgpusim config lacks -gpgpu_clock_domains")


def demangle_name(raw_name: str) -> str:
    try:
        return subprocess.check_output(["c++filt", raw_name], text=True, stderr=subprocess.DEVNULL).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return raw_name


def metric_stub_for_kernel(raw_name: str, explicit_map: dict[str, str]) -> tuple[str, str, str]:
    if raw_name in explicit_map:
        stub = explicit_map[raw_name]
        return raw_name, stub, "explicit_kernel_stub_map"
    display_name = demangle_name(raw_name)
    function_name = re.sub(r"\(.*", "", display_name)
    stub = normalize_metric_name(function_name)
    return display_name, stub, "demangle_then_collect_style_normalize"


def parse_stat_value(key: str, value: str) -> int | float:
    if key.endswith("_cycle") or key.endswith("_insn"):
        return parse_int(value, key)
    return parse_decimal(value, key)


def parse_simulator_stdout(text: str, explicit_stub_map: dict[str, str], core_mhz: float) -> dict[str, Any]:
    kernels: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    simulation_times_sec: list[float] = []
    application_passed: bool | None = None

    for line in text.splitlines():
        name_match = KERNEL_NAME_RE.match(line)
        if name_match:
            current = {"kernel_name": name_match.group(1), "raw_stats": {}}
            kernels.append(current)
            continue
        if current is not None:
            uid_match = KERNEL_UID_RE.match(line)
            if uid_match:
                current["kernel_launch_uid"] = int(uid_match.group(1))
                continue
            stat_match = STAT_RE.match(line)
            if stat_match:
                key, value = stat_match.groups()
                current["raw_stats"][key] = parse_stat_value(key, value)
                continue
        time_match = SIM_TIME_RE.search(line)
        if time_match:
            simulation_times_sec.append(parse_decimal(time_match.group(1), "gpgpu_simulation_time seconds"))
        if re.match(r"^\s*PASSED\s*$", line):
            application_passed = True
        elif re.match(r"^\s*FAILED\s*$", line):
            application_passed = False

    if not kernels:
        raise IngestError("simulator stdout contains no kernel_name metric blocks")

    previous_total_cycles = 0
    previous_total_insn = 0
    mapped_kernels: list[dict[str, Any]] = []
    for index, kernel in enumerate(kernels, 1):
        raw_stats = kernel.get("raw_stats")
        if not isinstance(raw_stats, dict):
            raise IngestError(f"kernel block {index} lacks raw_stats")
        if "gpu_sim_cycle" in raw_stats:
            kernel_cycles = parse_int(raw_stats["gpu_sim_cycle"], f"kernel {index} gpu_sim_cycle")
        elif "gpu_tot_sim_cycle" in raw_stats:
            cumulative = parse_int(raw_stats["gpu_tot_sim_cycle"], f"kernel {index} gpu_tot_sim_cycle")
            kernel_cycles = cumulative - previous_total_cycles
            if kernel_cycles < 0:
                raise IngestError(f"kernel {index} cumulative gpu_tot_sim_cycle went backwards")
        else:
            raise IngestError(f"kernel {index} lacks gpu_sim_cycle or gpu_tot_sim_cycle")

        if "gpu_sim_insn" in raw_stats:
            kernel_insn = parse_int(raw_stats["gpu_sim_insn"], f"kernel {index} gpu_sim_insn")
        elif "gpu_tot_sim_insn" in raw_stats:
            cumulative_insn = parse_int(raw_stats["gpu_tot_sim_insn"], f"kernel {index} gpu_tot_sim_insn")
            kernel_insn = cumulative_insn - previous_total_insn
            if kernel_insn < 0:
                raise IngestError(f"kernel {index} cumulative gpu_tot_sim_insn went backwards")
        else:
            kernel_insn = None

        if "gpu_tot_sim_cycle" in raw_stats:
            previous_total_cycles = parse_int(raw_stats["gpu_tot_sim_cycle"], f"kernel {index} gpu_tot_sim_cycle")
        else:
            previous_total_cycles += kernel_cycles
        if "gpu_tot_sim_insn" in raw_stats:
            previous_total_insn = parse_int(raw_stats["gpu_tot_sim_insn"], f"kernel {index} gpu_tot_sim_insn")
        elif kernel_insn is not None:
            previous_total_insn += kernel_insn

        raw_name = str(kernel["kernel_name"])
        display_name, metric_stub, mapping_source = metric_stub_for_kernel(raw_name, explicit_stub_map)
        total_time_ms = kernel_cycles / (core_mhz * 1000.0)
        mapped = {
            "launch_index": index,
            "kernel_launch_uid": kernel.get("kernel_launch_uid"),
            "raw_kernel_name": raw_name,
            "display_name": display_name,
            "metric_stub": metric_stub,
            "metric_mapping_source": mapping_source,
            "gpu_sim_cycle": kernel_cycles,
            "gpu_sim_insn": kernel_insn,
            "gpu_tot_sim_cycle": previous_total_cycles,
            "gpu_tot_sim_insn": previous_total_insn if previous_total_insn else None,
            "derived_total_time_ms": round(total_time_ms, 9),
            "raw_stats": raw_stats,
        }
        mapped_kernels.append(mapped)

    metrics: dict[str, float] = {}
    total_time_ms = sum(float(kernel["derived_total_time_ms"]) for kernel in mapped_kernels)
    metrics["cuda_kernel_total_time_ms"] = round(total_time_ms, 9)
    metrics["cuda_kernel_invocations"] = float(len(mapped_kernels))
    metrics["cuda_kernel_avg_time_ms"] = round(total_time_ms / len(mapped_kernels), 9)
    for kernel in mapped_kernels:
        metric_name = f"cuda_kernel_{kernel['metric_stub']}_total_time_ms"
        if metric_name in metrics:
            metrics[metric_name] = round(float(metrics[metric_name]) + float(kernel["derived_total_time_ms"]), 9)
        else:
            metrics[metric_name] = float(kernel["derived_total_time_ms"])

    return {
        "application_passed": application_passed,
        "simulation_times_sec": simulation_times_sec,
        "kernels": mapped_kernels,
        "metrics": metrics,
    }


def source_file_record(path: Path, root: Path, kind: str) -> dict[str, Any]:
    if not path.exists():
        raise IngestError(f"source file does not exist: {path}")
    return {
        "kind": kind,
        "path": display_path(path, root),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "present": True,
    }


def build_candidate_artifact(args: argparse.Namespace) -> dict[str, Any] | None:
    if not args.stdout and not args.gpgpusim_config:
        return None
    if not args.stdout or not args.gpgpusim_config:
        raise IngestError("--stdout and --gpgpusim-config must be provided together")

    root = args.repo_root.resolve()
    stdout_path = resolve_path(args.stdout, root)
    config_path = resolve_path(args.gpgpusim_config, root)
    stdout_text = read_text_file(stdout_path)
    config_text = read_text_file(config_path)
    explicit_stub_map = parse_stub_map(args.kernel_stub_map)
    core_mhz = core_clock_mhz_from_config(config_text)
    parsed = parse_simulator_stdout(stdout_text, explicit_stub_map, core_mhz)
    values = parse_key_values(args.candidate_value)
    benchmark_id = args.benchmark_id
    candidate_id = args.candidate_id
    metrics = {benchmark_id: parsed["metrics"]}

    artifact = {
        "schema_version": 1,
        "schema_id": "sm120_simulator_candidate_metrics_v1",
        "candidate_id": candidate_id,
        "gpu": args.gpu,
        "architecture": args.architecture,
        "status": "draft_not_applied",
        "generated_at": args.generated_at or iso_utc_now(),
        "fixture_only": bool(args.fixture_only),
        "simulator_candidate_metrics": True,
        "hardware_target_metrics": False,
        "source_kind": args.source_kind,
        "source_label": args.source_label,
        "collector": {
            "script": "simulator-remodeled/util/tuner/ingest_sm120_simulator_candidate_metrics.py",
            "script_sha256": sha256_file(Path(__file__).resolve()),
        },
        "repository": {
            "root": str(root),
            "git_commit": run_git(root, ["rev-parse", "HEAD"]) or "unknown",
            "git_branch": run_git(root, ["rev-parse", "--abbrev-ref", "HEAD"]) or "unknown",
        },
        "benchmark_cases": [
            {
                "id": benchmark_id,
                "suite": args.benchmark_suite,
                "benchmark": args.benchmark_name,
                "benchmark_selector": args.benchmark_selector,
                "args": args.benchmark_args,
            }
        ],
        "source_files": [
            source_file_record(stdout_path, root, "simulator_stdout"),
            source_file_record(config_path, root, "simulator_gpgpusim_config"),
        ],
        "candidate_values": values,
        "metric_name_mapping": {
            "time_metric_method": TIME_FROM_CYCLES_METHOD,
            "clock_source": "-gpgpu_clock_domains first field",
            "core_clock_mhz": core_mhz,
            "kernel_stub_policy": (
                "explicit --kernel-stub-map entries first; otherwise c++filt demangle and "
                "collect_sm120_hardware_metrics.normalize_metric_name after stripping argument lists"
            ),
            "not_mapped": [
                {
                    "metric": "native_wall_time_seconds",
                    "reason": "simulator stdout and config do not provide native wall-clock execution time",
                }
            ],
        },
        "parsed_simulator_observations": {
            "application_passed": parsed["application_passed"],
            "gpgpu_simulation_time_seconds_observed": parsed["simulation_times_sec"],
            "kernel_count": len(parsed["kernels"]),
            "kernels": parsed["kernels"],
        },
        "candidate_metrics_entry": {
            "values": values,
            "metrics": metrics,
            "provenance": {
                "candidate_metrics_artifact_schema": "sm120_simulator_candidate_metrics_v1",
                "source_kind": args.source_kind,
                "source_label": args.source_label,
                "metric_derivation": TIME_FROM_CYCLES_METHOD,
                "hardware_target_metrics": False,
            },
        },
        "handoff": {
            "do_not_claim_calibrated": True,
            "do_not_use_as_hardware_target_metrics": True,
            "do_not_apply_automatically": [
                "flat tested configs",
                "generated tested-cfgs outputs",
                "calibration-results/latest",
            ],
        },
    }
    return artifact


def normalize_candidate_entry(artifact: dict[str, Any]) -> dict[str, Any]:
    entry = artifact.get("candidate_metrics_entry")
    if not isinstance(entry, dict):
        raise IngestError("candidate artifact lacks candidate_metrics_entry mapping")
    values = entry.get("values")
    metrics = entry.get("metrics")
    if not isinstance(values, dict) or not isinstance(metrics, dict):
        raise IngestError("candidate_metrics_entry requires values and metrics mappings")
    entry = {"values": values, "metrics": metrics}
    validate_candidate_metric_names(entry, str(artifact.get("candidate_id", "candidate artifact")))
    return entry


def is_bridge_supported_candidate_metric(metric: str) -> bool:
    if metric == "cuda_kernel_invocations":
        return True
    return metric.startswith("cuda_kernel_") and metric.endswith("_time_ms")


def validate_candidate_metric_names(entry: dict[str, Any], label: str) -> None:
    metrics = entry.get("metrics")
    if not isinstance(metrics, dict):
        raise IngestError(f"{label} metrics must be a mapping")
    for benchmark, benchmark_metrics in metrics.items():
        if not isinstance(benchmark_metrics, dict):
            raise IngestError(f"{label} metrics for {benchmark} must be a mapping")
        for metric in benchmark_metrics:
            if not is_bridge_supported_candidate_metric(str(metric)):
                raise IngestError(
                    f"{label} contains unsupported simulator candidate metric {benchmark}.{metric}; "
                    "this bridge only supplies cuda_kernel_*_time_ms metrics and cuda_kernel_invocations"
                )


def load_candidate_artifacts(paths: list[str], root: Path) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for path_text in paths:
        path = resolve_path(path_text, root)
        data = load_yaml(path)
        if data.get("schema_id") != "sm120_simulator_candidate_metrics_v1":
            raise IngestError(f"{path} is not an sm120_simulator_candidate_metrics_v1 artifact")
        if data.get("hardware_target_metrics"):
            raise IngestError(f"{path} is marked as hardware_target_metrics and cannot be candidate metrics")
        artifacts.append(
            {
                "path": display_path(path, root),
                "sha256": sha256_file(path),
                "data": data,
                "entry": normalize_candidate_entry(data),
            }
        )
    return artifacts


def decimal_to_string(value: Decimal) -> str:
    if value == value.to_integral_value():
        return str(value.quantize(Decimal("1")))
    return format(value.normalize(), "f")


def normalize_value(value: Any) -> str:
    if isinstance(value, bool) or value is None or isinstance(value, (dict, list)):
        raise IngestError(f"candidate value must be scalar string/number, got {value!r}")
    if isinstance(value, float):
        return decimal_to_string(Decimal(str(value)))
    return str(value).strip()


def bounded_range_values(raw_range: Any, key: str) -> list[str]:
    if not isinstance(raw_range, dict):
        raise IngestError(f"{key} range must be a mapping with start/stop/step")
    required = {"start", "stop", "step"}
    missing = sorted(required - set(raw_range))
    if missing:
        raise IngestError(f"{key} range missing {', '.join(missing)}")
    try:
        start = Decimal(str(raw_range["start"]))
        stop = Decimal(str(raw_range["stop"]))
        step = Decimal(str(raw_range["step"]))
    except (InvalidOperation, ValueError) as exc:
        raise IngestError(f"{key} range values must be numeric") from exc
    if step == 0:
        raise IngestError(f"{key} range step must not be zero")
    if start < stop and step < 0:
        raise IngestError(f"{key} range step sign does not reach stop")
    if start > stop and step > 0:
        raise IngestError(f"{key} range step sign does not reach stop")
    max_values = int(raw_range.get("max_values", 16))
    values: list[str] = []
    current = start
    while current <= stop if step > 0 else current >= stop:
        values.append(decimal_to_string(current))
        if len(values) > max_values:
            raise IngestError(f"{key} range exceeds max_values={max_values}")
        current += step
    if not values:
        raise IngestError(f"{key} range produced no values")
    return values


def values_from_parameter(entry: dict[str, Any]) -> list[str]:
    if "values" in entry and "range" in entry:
        raise IngestError(f"{entry.get('key')} must not define both values and range")
    if "values" in entry:
        raw_values = entry["values"]
        if not isinstance(raw_values, list) or not raw_values:
            raise IngestError(f"{entry.get('key')} values must be a non-empty list")
        values = [normalize_value(value) for value in raw_values]
    elif "range" in entry:
        values = bounded_range_values(entry["range"], str(entry.get("key")))
    else:
        raise IngestError(f"{entry.get('key')} must define values or range")
    if len(set(values)) != len(values):
        raise IngestError(f"{entry.get('key')} has duplicate values after normalization")
    return values


def candidate_signature(values_by_key: dict[str, Any], ordered_keys: list[str]) -> tuple[tuple[str, str], ...]:
    return tuple((key, normalize_value(values_by_key[key])) for key in ordered_keys)


def expected_candidate_signatures(search: dict[str, Any]) -> tuple[list[str], set[tuple[tuple[str, str], ...]]]:
    parameters = search.get("parameters")
    if not isinstance(parameters, list) or not parameters:
        return [], set()
    ordered_keys: list[str] = []
    value_lists: list[list[str]] = []
    for parameter in parameters:
        if not isinstance(parameter, dict):
            raise IngestError("search parameters must be mappings")
        key = parameter.get("key")
        if not isinstance(key, str) or not key:
            raise IngestError("search parameters require non-empty key")
        ordered_keys.append(key)
        value_lists.append(values_from_parameter(parameter))
    signatures: set[tuple[tuple[str, str], ...]] = set()

    def walk(index: int, values: dict[str, str]) -> None:
        if index == len(ordered_keys):
            signatures.add(candidate_signature(values, ordered_keys))
            return
        key = ordered_keys[index]
        for value in value_lists[index]:
            next_values = dict(values)
            next_values[key] = value
            walk(index + 1, next_values)

    walk(0, {})
    return ordered_keys, signatures


def target_metric_ids(template: dict[str, Any]) -> list[tuple[str, str]]:
    targets = template.get("target_metrics")
    if not isinstance(targets, list) or not targets:
        return []
    ids: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for target in targets:
        if not isinstance(target, dict):
            raise IngestError("target_metrics entries must be mappings")
        benchmark = target.get("benchmark")
        metric = target.get("metric")
        if not isinstance(benchmark, str) or not isinstance(metric, str) or not metric:
            raise IngestError("target_metrics entries require benchmark and metric")
        item = (benchmark, metric)
        if item in seen:
            raise IngestError(f"duplicate target metric {benchmark}.{metric}")
        seen.add(item)
        ids.append(item)
    return ids


def entry_metric_value(entry: dict[str, Any], benchmark: str, metric: str) -> Any | None:
    metrics = entry.get("metrics")
    if not isinstance(metrics, dict):
        return None
    benchmark_metrics = metrics.get(benchmark)
    if not isinstance(benchmark_metrics, dict):
        return None
    return benchmark_metrics.get(metric)


def validate_s6_readiness(
    template: dict[str, Any],
    entries: list[dict[str, Any]],
    reviewed: bool,
    root: Path | None = None,
) -> dict[str, Any]:
    blockers: list[str] = []
    target_ids = target_metric_ids(template)
    if not target_ids:
        blockers.append("template_has_no_target_metrics")

    search = template.get("search")
    if not isinstance(search, dict):
        blockers.append("template_has_no_search_mapping")
        ordered_keys: list[str] = []
        expected_signatures: set[tuple[tuple[str, str], ...]] = set()
    else:
        try:
            ordered_keys, expected_signatures = expected_candidate_signatures(search)
        except IngestError as exc:
            blockers.append(f"search_space_invalid:{exc}")
            ordered_keys = []
            expected_signatures = set()
        if not ordered_keys:
            blockers.append("search_parameters_missing")
        try:
            max_candidates = int(search.get("max_candidates", 0))
        except (TypeError, ValueError):
            max_candidates = 0
        if max_candidates <= 0:
            blockers.append("search_max_candidates_not_positive")
        elif expected_signatures and len(expected_signatures) > max_candidates:
            blockers.append(
                f"search_space_exceeds_max_candidates:{len(expected_signatures)}>{max_candidates}"
            )

    if not reviewed:
        blockers.append("candidate_metrics_not_marked_reviewed")

    supplied_signatures: set[tuple[tuple[str, str], ...]] = set()
    missing_metrics: list[dict[str, str]] = []
    invalid_entries: list[str] = []
    duplicate_candidate_count = 0
    for index, entry in enumerate(entries, 1):
        values = entry.get("values")
        if not isinstance(values, dict):
            invalid_entries.append(f"entry_{index}_values_not_mapping")
            continue
        if ordered_keys and set(values) != set(ordered_keys):
            invalid_entries.append(
                f"entry_{index}_values_do_not_match_search_keys:{sorted(values)} vs {sorted(ordered_keys)}"
            )
            continue
        if ordered_keys:
            signature = candidate_signature(values, ordered_keys)
            if signature in supplied_signatures:
                duplicate_candidate_count += 1
                invalid_entries.append(f"entry_{index}_duplicate_candidate_signature")
                continue
            supplied_signatures.add(signature)
        for benchmark, metric in target_ids:
            value = entry_metric_value(entry, benchmark, metric)
            if value is None:
                missing_metrics.append(
                    {
                        "entry": f"entry_{index}",
                        "benchmark": benchmark,
                        "metric": metric,
                    }
                )
                continue
            parse_decimal(value, f"candidate metric {benchmark}.{metric}")

    if invalid_entries:
        blockers.extend(invalid_entries)
    if duplicate_candidate_count:
        blockers.append(f"duplicate_candidate_metrics:{duplicate_candidate_count}")
    if expected_signatures and supplied_signatures != expected_signatures:
        missing = sorted(expected_signatures - supplied_signatures)
        extra = sorted(supplied_signatures - expected_signatures)
        if missing:
            blockers.append(f"missing_candidate_signatures:{len(missing)}")
        if extra:
            blockers.append(f"extra_candidate_signatures:{len(extra)}")
    if missing_metrics:
        blockers.append(f"missing_target_metrics:{len(missing_metrics)}")
    if template.get("status") == "template_not_runnable":
        blockers.append("input_template_status_template_not_runnable")

    if not blockers:
        if root is None:
            blockers.append("s6_validation_root_missing")
        else:
            try:
                s6_validate_manifest(template, entries, root)
            except IngestError as exc:
                blockers.append(f"s6_validation_error:{exc}")

    return {
        "ready": not blockers,
        "blockers": blockers,
        "ordered_search_keys": ordered_keys,
        "expected_candidate_count": len(expected_signatures),
        "supplied_candidate_count": len(entries),
        "target_metric_count": len(target_ids),
        "missing_target_metrics": missing_metrics,
    }


def s6_validate_manifest(template: dict[str, Any], entries: list[dict[str, Any]], root: Path) -> None:
    manifest = dict(template)
    manifest["evaluation"] = {"mode": "supplied_metrics", "candidate_metrics": entries}
    try:
        schema_path = resolve_path(s6_search.DEFAULT_SCHEMA_REL, root)
        schema = load_yaml(schema_path)
        s6_search.validate_manifest_header(manifest, schema)
        base_paths = s6_search.validate_generated_base_paths(manifest["base"], root)
        base_options = {file_name: s6_search.active_option_map(path) for file_name, path in base_paths.items()}
        parameters = s6_search.validate_search_space(manifest, schema, base_options)
        known_benchmarks = s6_search.benchmark_ids(manifest)
        targets = s6_search.target_metrics(manifest, known_benchmarks)
        search_id = str(manifest.get("search_id") or "sm120-correlation-search")
        candidates = s6_search.generate_candidates(search_id, parameters)
        ordered_keys = [param["key"] for param in parameters]
        _mode, metrics_by_signature = s6_search.evaluation_map(manifest, candidates, ordered_keys)
        s6_search.score_candidates(candidates, metrics_by_signature, targets)
    except s6_search.SearchError as exc:
        raise IngestError(str(exc)) from exc


def build_s6_output(
    template: dict[str, Any],
    entries: list[dict[str, Any]],
    readiness: dict[str, Any],
    args: argparse.Namespace,
    candidate_sources: list[dict[str, Any]],
) -> dict[str, Any]:
    root = args.repo_root.resolve()
    if readiness["ready"]:
        manifest = dict(template)
        manifest["schema_version"] = 1
        manifest["schema_id"] = "sm120_correlation_search_manifest_v1"
        manifest["status"] = "draft_not_applied"
        manifest["evaluation"] = {
            "mode": "supplied_metrics",
            "candidate_metrics": entries,
            "candidate_metric_source_policy": (
                "local simulator candidate metrics only; not hardware target data; reviewed before S6 scoring"
            ),
        }
        manifest["fixture_only"] = bool(args.fixture_only or template.get("fixture_only", False))
        manifest["generated_by_bridge"] = {
            "script": "simulator-remodeled/util/tuner/ingest_sm120_simulator_candidate_metrics.py",
            "script_sha256": sha256_file(Path(__file__).resolve()),
            "generated_at": args.generated_at or iso_utc_now(),
            "candidate_sources": candidate_sources,
        }
        manifest["source_template"] = {
            "schema_id": template.get("schema_id"),
            "status": template.get("status"),
        }
        manifest["handoff"] = {
            **(manifest.get("handoff") if isinstance(manifest.get("handoff"), dict) else {}),
            "do_not_claim_calibrated": True,
            "result_policy": "draft_not_applied",
            "ready_for_search_sm120_correlation": True,
            "do_not_apply_automatically": [
                "flat tested configs",
                "generated tested-cfgs outputs",
                "calibration-results/latest",
            ],
        }
        return manifest

    return {
        "schema_version": 1,
        "schema_id": "sm120_s6_supplied_metrics_bridge_scaffold_v1",
        "status": "draft_not_applied",
        "s6_manifest_runnable": False,
        "generated_at": args.generated_at or iso_utc_now(),
        "fixture_only": bool(args.fixture_only or template.get("fixture_only", False)),
        "gpu": template.get("gpu", args.gpu),
        "architecture": template.get("architecture", args.architecture),
        "search_id": template.get("search_id", "sm120-s6-supplied-metrics-bridge-scaffold"),
        "bridge": {
            "script": "simulator-remodeled/util/tuner/ingest_sm120_simulator_candidate_metrics.py",
            "script_sha256": sha256_file(Path(__file__).resolve()),
            "repository": {
                "root": str(root),
                "git_commit": run_git(root, ["rev-parse", "HEAD"]) or "unknown",
                "git_branch": run_git(root, ["rev-parse", "--abbrev-ref", "HEAD"]) or "unknown",
            },
        },
        "source_template": {
            "schema_id": template.get("schema_id"),
            "status": template.get("status"),
        },
        "readiness": readiness,
        "benchmark_cases": template.get("benchmark_cases", []),
        "target_metrics": template.get("target_metrics", []),
        "candidate_metrics": entries,
        "candidate_sources": candidate_sources,
        "blocked_reason": (
            "The bridge parsed simulator candidate metrics, but the S6 manifest is not runnable until "
            "reviewed search parameters and candidate metrics cover every target metric for every generated candidate."
        ),
        "handoff": {
            "do_not_claim_calibrated": True,
            "do_not_run_search_sm120_correlation_as_is": True,
            "do_not_apply_automatically": [
                "flat tested configs",
                "generated tested-cfgs outputs",
                "calibration-results/latest",
            ],
        },
    }


def check_output_target(path: Path, root: Path) -> None:
    rel = "/" + display_path(path, root)
    for part in FORBIDDEN_OUTPUT_PARTS:
        if part in rel:
            raise IngestError(f"refusing to write simulator candidate/S6 bridge output into protected path: {path}")


def write_yaml(path_text: str, data: dict[str, Any], root: Path) -> None:
    if path_text == "-":
        sys.stdout.write(yaml.safe_dump(data, sort_keys=False, width=120))
        return
    path = resolve_path(path_text, root)
    check_output_target(path, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, width=120), encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gpu", choices=GPU_CHOICES, required=True, help="Target GPU SKU.")
    parser.add_argument("--repo-root", type=Path, default=repo_root_from_script(), help="Repository root.")
    parser.add_argument("--architecture", default=DEFAULT_ARCHITECTURE, help="Architecture label.")
    parser.add_argument("--generated-at", default="", help="Deterministic generated_at timestamp.")
    parser.add_argument("--fixture-only", action="store_true", help="Mark output as fixture-only.")

    parser.add_argument("--stdout", help="Local simulator stdout file.")
    parser.add_argument("--gpgpusim-config", help="Simulator run gpgpusim.config used for clock-domain conversion.")
    parser.add_argument("--candidate-id", default="candidate_0001", help="Candidate id for this run artifact.")
    parser.add_argument(
        "--candidate-value",
        action="append",
        default=[],
        help="Search candidate value as -config_key=value. Repeat for every S6 search parameter.",
    )
    parser.add_argument(
        "--kernel-stub-map",
        action="append",
        default=[],
        help="Explicit kernel mapping as RAW_KERNEL_NAME=metric_stub when demangling does not match hardware names.",
    )
    parser.add_argument("--source-kind", default=DEFAULT_SOURCE_KIND, help="Simulator source kind/provenance label.")
    parser.add_argument("--source-label", default="", help="Short source run label.")
    parser.add_argument("--output", default="", help="Optional draft simulator candidate metrics YAML output.")

    parser.add_argument(
        "--candidate-artifact",
        action="append",
        default=[],
        help="Existing sm120_simulator_candidate_metrics_v1 YAML to include in S6 bridge output.",
    )
    parser.add_argument("--s6-template", default="", help="S6 template or manifest scaffold to fill with supplied metrics.")
    parser.add_argument("--s6-manifest-output", default="", help="S6 supplied_metrics manifest/scaffold output path.")
    parser.add_argument(
        "--reviewed",
        action="store_true",
        help="Allow runnable S6 manifest output if search space and metrics are complete.",
    )

    parser.add_argument("--benchmark-id", default=DEFAULT_BENCHMARK_ID, help="Benchmark case id used by S6.")
    parser.add_argument("--benchmark-suite", default=DEFAULT_BENCHMARK_SUITE, help="Benchmark suite label.")
    parser.add_argument("--benchmark-name", default=DEFAULT_BENCHMARK_NAME, help="Benchmark executable/app label.")
    parser.add_argument("--benchmark-selector", default=DEFAULT_BENCHMARK_SELECTOR, help="Job-launching benchmark selector.")
    parser.add_argument("--benchmark-args", default=DEFAULT_ARGS, help="Benchmark arguments.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        root = args.repo_root.resolve()
        candidate_artifact = build_candidate_artifact(args)
        loaded_candidates = load_candidate_artifacts(args.candidate_artifact, root)

        candidate_sources: list[dict[str, Any]] = []
        entries: list[dict[str, Any]] = []
        if candidate_artifact is not None:
            entries.append(normalize_candidate_entry(candidate_artifact))
            candidate_sources.append(
                {
                    "candidate_id": candidate_artifact["candidate_id"],
                    "source": "direct_parse",
                    "source_kind": candidate_artifact["source_kind"],
                    "source_label": candidate_artifact["source_label"],
                }
            )
            if args.output:
                write_yaml(args.output, candidate_artifact, root)
        elif args.output:
            raise IngestError("--output requires --stdout and --gpgpusim-config")

        for item in loaded_candidates:
            entries.append(item["entry"])
            data = item["data"]
            candidate_sources.append(
                {
                    "candidate_id": data.get("candidate_id", ""),
                    "source": item["path"],
                    "sha256": item["sha256"],
                    "source_kind": data.get("source_kind", ""),
                    "source_label": data.get("source_label", ""),
                }
            )

        if args.s6_manifest_output:
            if not args.s6_template:
                raise IngestError("--s6-manifest-output requires --s6-template")
            if not entries:
                raise IngestError("--s6-manifest-output requires direct parsed metrics or --candidate-artifact")
            template_path = resolve_path(args.s6_template, root)
            template = load_yaml(template_path)
            readiness = validate_s6_readiness(template, entries, reviewed=args.reviewed, root=root)
            s6_output = build_s6_output(template, entries, readiness, args, candidate_sources)
            s6_output["source_template"].update(
                {
                    "path": display_path(template_path, root),
                    "sha256": sha256_file(template_path),
                }
            )
            write_yaml(args.s6_manifest_output, s6_output, root)
        elif args.s6_template:
            raise IngestError("--s6-template requires --s6-manifest-output")

        if candidate_artifact is None and not args.s6_manifest_output:
            raise IngestError("nothing to do; provide --stdout/--gpgpusim-config and/or --s6-manifest-output")
    except IngestError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
