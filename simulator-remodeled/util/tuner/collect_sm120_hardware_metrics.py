#!/usr/bin/env python3
"""Build draft SM120 hardware target metrics from native run artifacts.

This collector is intentionally draft-only. It parses native application
stdout, GNU time output, timing JSON, and optional Nsight Systems CSV summaries.
It rejects simulator smoke-metric markers so ProcMan/GPGPU-Sim output cannot be
accidentally promoted as hardware target metrics.
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

import yaml


GPU_CHOICES = ("RTX5060", "RTX5070_TI")
DEFAULT_ARCHITECTURE = "SM120"
DEFAULT_BENCHMARK_SELECTOR = "rodinia_2.0-ft:backprop-rodinia-2.0-ft:0"
DEFAULT_BENCHMARK_ID = "backprop_4096"
DEFAULT_BENCHMARK_SUITE = "rodinia_2.0-ft"
DEFAULT_BENCHMARK_NAME = "backprop-rodinia-2.0-ft"
DEFAULT_ARGS = "4096 ./data/result-4096.txt"
DEFAULT_GPGPU_CONFIG = (
    "simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated/tested-cfgs/"
    "SM120_RTX5060/gpgpusim.config"
)
DEFAULT_TRACE_CONFIG = (
    "simulator-remodeled/gpu-simulator/configs/generated/tested-cfgs/"
    "SM120_RTX5060/trace.config"
)

TIME_PREFIX = "MGS_HW_TIME_"
SIMULATOR_MARKERS = (
    "gpu_tot_sim_cycle",
    "gpu_tot_sim_insn",
    "gpgpu_simulation_time",
    "gpgpu_simulation_rate",
    "GPGPU-Sim",
    "Accel-Sim",
    "ProcMan job",
)
FORBIDDEN_OUTPUT_PARTS = (
    "/configs/tested-cfgs/",
    "/configs/generated/tested-cfgs/",
    "/configs/layered/sm120/",
)


class CollectError(RuntimeError):
    pass


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[3]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def check_for_simulator_markers(text: str, label: str) -> list[str]:
    found = [marker for marker in SIMULATOR_MARKERS if marker in text]
    if found:
        raise CollectError(
            f"{label} contains simulator markers and cannot be used as hardware target metrics: "
            + ", ".join(found)
        )
    return found


def parse_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or value is None:
        raise CollectError(f"{label} must be numeric")
    try:
        return float(str(value).strip().replace(",", ""))
    except ValueError as exc:
        raise CollectError(f"{label} must be numeric, got {value!r}") from exc


def normalize_metric_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", name.strip().lower()).strip("_")
    if not cleaned:
        raise CollectError(f"empty metric name after normalization: {name!r}")
    return cleaned


def parse_native_stdout(text: str) -> dict[str, Any]:
    observations: dict[str, Any] = {}
    if re.search(r"(^|\n)\s*PASSED\s*(\n|$)", text):
        observations["application_passed"] = True
    elif re.search(r"(^|\n)\s*FAILED\s*(\n|$)", text):
        observations["application_passed"] = False
    checksum = re.search(r"checksum\s*=\s*(\S+)", text)
    if checksum:
        observations["checksum"] = checksum.group(1)
    input_size = re.search(r"Input layer size\s*:\s*(\d+)", text)
    if input_size:
        observations["input_layer_size"] = int(input_size.group(1))
    observations["line_count"] = len(text.splitlines())
    return observations


def parse_time_output(text: str) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith(TIME_PREFIX) or "=" not in line:
            continue
        key, value = line.split("=", 1)
        metric = normalize_metric_name(key[len(TIME_PREFIX) :])
        value = value.strip()
        if metric in {"exit_status", "major_page_faults", "minor_page_faults", "max_rss_kbytes"}:
            try:
                parsed[metric] = int(float(value))
            except ValueError as exc:
                raise CollectError(f"{key} must be an integer-compatible value") from exc
        else:
            parsed[metric] = parse_number(value, key)
    return parsed


def parse_timing_json(text: str) -> dict[str, dict[str, Any]]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CollectError(f"timing JSON is invalid: {exc}") from exc
    raw_metrics = data.get("metrics", data) if isinstance(data, dict) else data
    metrics: dict[str, dict[str, Any]] = {}

    if isinstance(raw_metrics, dict):
        for name, value in raw_metrics.items():
            metric = normalize_metric_name(str(name))
            if isinstance(value, dict):
                if "value" not in value:
                    raise CollectError(f"timing JSON metric {name!r} mapping lacks value")
                target_value = parse_number(value["value"], f"timing JSON {name}")
                unit = str(value.get("unit", "unknown"))
                source = str(value.get("source", "timing_json"))
            else:
                target_value = parse_number(value, f"timing JSON {name}")
                unit = "unknown"
                source = "timing_json"
            metrics[metric] = {"value": target_value, "unit": unit, "source": source}
        return metrics

    if isinstance(raw_metrics, list):
        for item in raw_metrics:
            if not isinstance(item, dict):
                raise CollectError("timing JSON metric list entries must be mappings")
            name = item.get("metric") or item.get("name")
            if not isinstance(name, str) or not name:
                raise CollectError("timing JSON metric list entries require metric/name")
            if "value" not in item and "target" not in item:
                raise CollectError(f"timing JSON metric {name!r} lacks value/target")
            metric = normalize_metric_name(name)
            value = item["value"] if "value" in item else item["target"]
            metrics[metric] = {
                "value": parse_number(value, f"timing JSON {name}"),
                "unit": str(item.get("unit", "unknown")),
                "source": str(item.get("source", "timing_json")),
            }
        return metrics

    raise CollectError("timing JSON must be a mapping or a list of metric mappings")


def normalized_header(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def first_matching_key(row: dict[str, str], candidates: tuple[str, ...]) -> str | None:
    lookup = {normalized_header(key): key for key in row}
    for candidate in candidates:
        if candidate in lookup:
            return lookup[candidate]
    return None


def parse_nsys_kernel_summary(text: str) -> dict[str, Any]:
    sample = text.lstrip()
    if not sample:
        return {"rows": [], "metrics": {}}
    reader = csv.DictReader(sample.splitlines())
    rows: list[dict[str, Any]] = []
    total_ns = 0.0
    total_instances = 0
    per_kernel: dict[str, dict[str, Any]] = {}

    for raw_row in reader:
        if not raw_row:
            continue
        name_key = first_matching_key(raw_row, ("name", "kernelname", "demangledname"))
        total_key = first_matching_key(raw_row, ("totaltimens", "totaltime"))
        instances_key = first_matching_key(raw_row, ("instances", "count", "calls"))
        avg_key = first_matching_key(raw_row, ("avgns", "avg"))
        if not name_key or not total_key:
            continue
        name = str(raw_row.get(name_key, "")).strip()
        if not name:
            continue
        total = parse_number(raw_row.get(total_key, ""), f"Nsight total time for {name}")
        instances = 1
        if instances_key:
            instances = int(parse_number(raw_row.get(instances_key, "1"), f"Nsight instances for {name}"))
        avg_ns = parse_number(raw_row.get(avg_key, total / max(instances, 1)), f"Nsight avg for {name}") if avg_key else total / max(instances, 1)
        total_ns += total
        total_instances += instances
        metric_stub = normalize_metric_name(re.sub(r"\(.*", "", name))
        per_kernel[metric_stub] = {
            "display_name": name,
            "total_time_ms": total / 1_000_000.0,
            "avg_time_ms": avg_ns / 1_000_000.0,
            "instances": instances,
        }
        rows.append(
            {
                "name": name,
                "total_time_ns": total,
                "total_time_ms": total / 1_000_000.0,
                "avg_time_ns": avg_ns,
                "instances": instances,
            }
        )

    metrics: dict[str, Any] = {}
    if rows:
        metrics["cuda_kernel_total_time_ms"] = total_ns / 1_000_000.0
        metrics["cuda_kernel_invocations"] = total_instances
        if total_instances:
            metrics["cuda_kernel_avg_time_ms"] = (total_ns / total_instances) / 1_000_000.0
        for stub, item in per_kernel.items():
            metrics[f"cuda_kernel_{stub}_total_time_ms"] = item["total_time_ms"]
    return {"rows": rows, "metrics": metrics, "per_kernel": per_kernel}


def parse_nvidia_smi_query(text: str) -> dict[str, Any]:
    fields = [
        "name",
        "uuid",
        "driver_version",
        "pci_bus_id",
        "compute_capability",
        "pstate",
        "temperature_gpu_c",
        "clocks_sm_mhz",
        "clocks_mem_mhz",
        "memory_total_mib",
        "memory_used_mib",
    ]
    for line in text.splitlines():
        if not line.strip() or line.lower().startswith("name,"):
            continue
        values = [part.strip() for part in line.split(",")]
        if len(values) < 3:
            continue
        result: dict[str, Any] = {}
        for field, value in zip(fields, values):
            if field.endswith("_mhz") or field.endswith("_mib") or field.endswith("_c"):
                try:
                    result[field] = int(float(value))
                except ValueError:
                    result[field] = value
            else:
                result[field] = value
        return result
    return {}


def metric_epsilon(metric_name: str) -> float:
    if metric_name.endswith("_seconds"):
        return 0.001
    if metric_name.endswith("_ms"):
        return 0.001
    return 1.0


def metric_unit(metric_name: str, explicit: str | None = None) -> str:
    if explicit and explicit != "unknown":
        return explicit
    if metric_name.endswith("_seconds"):
        return "seconds"
    if metric_name.endswith("_ms"):
        return "milliseconds"
    if metric_name.endswith("_kbytes"):
        return "kbytes"
    return "count"


def target_metric_record(
    benchmark_id: str,
    metric_name: str,
    value: float,
    source: str,
    unit: str | None = None,
    include_in_s6: bool = True,
) -> dict[str, Any]:
    record = {
        "benchmark": benchmark_id,
        "metric": metric_name,
        "target": round(float(value), 9),
        "unit": metric_unit(metric_name, unit),
        "source": source,
        "weight": 1.0,
        "epsilon": metric_epsilon(metric_name),
        "normalization": "target_abs_or_epsilon",
        "include_in_s6_template": bool(include_in_s6),
    }
    return record


def source_file_record(path: Path, root: Path, kind: str, required: bool = False) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise CollectError(f"required {kind} source file does not exist: {path}")
        return {"kind": kind, "path": display_path(path, root), "present": False}
    return {
        "kind": kind,
        "path": display_path(path, root),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "present": True,
    }


def check_output_target(path: Path, root: Path) -> None:
    rel = "/" + display_path(path, root)
    for part in FORBIDDEN_OUTPUT_PARTS:
        if part in rel:
            raise CollectError(f"refusing to write draft hardware metrics into protected config path: {path}")


def build_result(args: argparse.Namespace) -> dict[str, Any]:
    root = args.repo_root.resolve()
    benchmark_id = args.benchmark_id
    source_files: list[dict[str, Any]] = []
    raw_observations: dict[str, Any] = {}
    target_metrics: list[dict[str, Any]] = []
    nsys_summary: dict[str, Any] = {}
    device_observation: dict[str, Any] = {}

    if args.stdout:
        stdout_path = resolve_path(args.stdout, root)
        stdout_text = read_text_file(stdout_path)
        check_for_simulator_markers(stdout_text, "native stdout")
        source_files.append(source_file_record(stdout_path, root, "native_stdout", required=True))
        raw_observations["native_stdout"] = parse_native_stdout(stdout_text)

    if args.stderr:
        stderr_path = resolve_path(args.stderr, root)
        stderr_text = read_text_file(stderr_path)
        check_for_simulator_markers(stderr_text, "native stderr")
        source_files.append(source_file_record(stderr_path, root, "native_stderr", required=True))
        raw_observations["native_stderr_line_count"] = len(stderr_text.splitlines())

    if args.time_output:
        time_path = resolve_path(args.time_output, root)
        time_text = read_text_file(time_path)
        check_for_simulator_markers(time_text, "GNU time output")
        source_files.append(source_file_record(time_path, root, "gnu_time_output", required=True))
        time_metrics = parse_time_output(time_text)
        raw_observations["gnu_time"] = time_metrics
        for source_name, metric_name in (
            ("wall_seconds", "native_wall_time_seconds"),
            ("user_seconds", "native_user_time_seconds"),
            ("sys_seconds", "native_sys_time_seconds"),
            ("max_rss_kbytes", "native_max_rss_kbytes"),
        ):
            if source_name in time_metrics:
                include_in_s6 = metric_name in {"native_wall_time_seconds"}
                target_metrics.append(
                    target_metric_record(
                        benchmark_id,
                        metric_name,
                        float(time_metrics[source_name]),
                        "gnu_time",
                        include_in_s6=include_in_s6,
                    )
                )

    if args.timing_json:
        timing_json_path = resolve_path(args.timing_json, root)
        timing_json_text = read_text_file(timing_json_path)
        check_for_simulator_markers(timing_json_text, "timing JSON")
        source_files.append(source_file_record(timing_json_path, root, "timing_json", required=True))
        json_metrics = parse_timing_json(timing_json_text)
        raw_observations["timing_json"] = json_metrics
        for metric_name, item in sorted(json_metrics.items()):
            target_metrics.append(
                target_metric_record(
                    benchmark_id,
                    metric_name,
                    float(item["value"]),
                    str(item.get("source", "timing_json")),
                    unit=str(item.get("unit", "unknown")),
                )
            )

    if args.nsys_kernel_csv:
        nsys_path = resolve_path(args.nsys_kernel_csv, root)
        nsys_text = read_text_file(nsys_path)
        check_for_simulator_markers(nsys_text, "Nsight Systems kernel CSV")
        source_files.append(source_file_record(nsys_path, root, "nsight_systems_cuda_gpu_kern_sum_csv", required=True))
        nsys_summary = parse_nsys_kernel_summary(nsys_text)
        raw_observations["nsight_systems"] = {
            "kernel_row_count": len(nsys_summary.get("rows", [])),
            "per_kernel": nsys_summary.get("per_kernel", {}),
        }
        for metric_name, value in sorted(nsys_summary.get("metrics", {}).items()):
            include_in_s6 = metric_name.endswith("_time_ms")
            target_metrics.append(
                target_metric_record(
                    benchmark_id,
                    metric_name,
                    float(value),
                    "nsight_systems_cuda_gpu_kern_sum",
                    include_in_s6=include_in_s6,
                )
            )

    if args.nvidia_smi_query:
        smi_path = resolve_path(args.nvidia_smi_query, root)
        smi_text = read_text_file(smi_path)
        check_for_simulator_markers(smi_text, "nvidia-smi query")
        source_files.append(source_file_record(smi_path, root, "nvidia_smi_query", required=True))
        device_observation = parse_nvidia_smi_query(smi_text)

    if args.tool_versions:
        tool_path = resolve_path(args.tool_versions, root)
        tool_text = read_text_file(tool_path)
        check_for_simulator_markers(tool_text, "tool versions")
        source_files.append(source_file_record(tool_path, root, "tool_versions", required=True))

    if not target_metrics and not args.allow_template:
        raise CollectError(
            "no hardware timing metrics were parsed; provide --time-output, --timing-json, "
            "or --nsys-kernel-csv, or use --allow-template for a blocker/template artifact"
        )

    target_metrics.sort(key=lambda item: (item["benchmark"], item["metric"], item["source"]))
    s6_target_metrics = [
        {
            "benchmark": item["benchmark"],
            "metric": item["metric"],
            "target": item["target"],
            "weight": item["weight"],
            "epsilon": item["epsilon"],
            "normalization": item["normalization"],
        }
        for item in target_metrics
        if item["include_in_s6_template"]
    ]
    target_id = args.target_id or f"{args.gpu.lower()}-{benchmark_id}-hardware-target-{_dt.datetime.now(tz=_dt.timezone.utc).strftime('%Y%m%d%H%M%S')}"
    return {
        "schema_version": 1,
        "schema_id": "sm120_hardware_target_metrics_v1",
        "target_id": target_id,
        "gpu": args.gpu,
        "architecture": args.architecture,
        "status": "draft_not_applied",
        "generated_at": args.generated_at or iso_utc_now(),
        "fixture_only": bool(args.fixture_only),
        "hardware_target_metrics": True,
        "simulator_smoke_metrics": False,
        "collector": {
            "script": "simulator-remodeled/util/tuner/collect_sm120_hardware_metrics.py",
            "script_sha256": sha256_file(Path(__file__).resolve()),
        },
        "repository": {
            "root": str(root),
            "git_commit": run_git(root, ["rev-parse", "HEAD"]) or "unknown",
            "git_branch": run_git(root, ["rev-parse", "--abbrev-ref", "HEAD"]) or "unknown",
        },
        "collection": {
            "host": args.collection_host,
            "source_label": args.source_label,
            "collection_command": args.collection_command,
            "notes": args.notes,
            "device_observation": device_observation,
        },
        "benchmark_cases": [
            {
                "id": benchmark_id,
                "suite": args.benchmark_suite,
                "benchmark": args.benchmark_name,
                "benchmark_selector": args.benchmark_selector,
                "args": args.benchmark_args,
                "native_case_label": args.native_case_label,
            }
        ],
        "source_files": source_files,
        "source_safety": {
            "simulator_marker_policy": "reject_inputs_containing_known_simulator_smoke_metric_markers",
            "rejected_markers": list(SIMULATOR_MARKERS),
            "job_486_policy": "job_486_simulator_metrics_are_not_hardware_target_metrics",
        },
        "run_observations": raw_observations,
        "target_metrics": target_metrics,
        "s6_supplied_metrics_handoff": {
            "target_metrics": s6_target_metrics,
            "candidate_simulator_metrics_present": False,
            "ready_for_search_sm120_correlation": False,
            "reason": (
                "This artifact supplies hardware targets only. A future S6 supplied_metrics "
                "manifest still needs reviewed candidate simulator metrics for the same metric names."
            ),
        },
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


def build_s6_template(result: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    targets = result["s6_supplied_metrics_handoff"]["target_metrics"]
    gpu_config_suffix = "SM120_RTX5070_TI" if args.gpu == "RTX5070_TI" else "SM120_RTX5060"
    base_alias = args.base_config_alias or ("RTX5070_TI_SM120_GEN" if args.gpu == "RTX5070_TI" else "RTX5060_SM120_GEN")
    gpgpu_config = args.base_gpgpusim_config or DEFAULT_GPGPU_CONFIG.replace("SM120_RTX5060", gpu_config_suffix)
    trace_config = args.base_trace_config or DEFAULT_TRACE_CONFIG.replace("SM120_RTX5060", gpu_config_suffix)
    return {
        "schema_version": 1,
        "schema_id": "sm120_s6_supplied_metrics_template_v1",
        "status": "template_not_runnable",
        "search_id": f"{result['target_id']}-s6-template",
        "gpu": result["gpu"],
        "architecture": result["architecture"],
        "description": (
            "Template scaffold generated from S7 hardware target metrics. It is not a runnable "
            "search_sm120_correlation.py manifest until search parameters and candidate simulator "
            "metrics are reviewed and filled in."
        ),
        "hardware_target_source": {
            "target_id": result["target_id"],
            "hardware_metrics_yaml": args.output,
        },
        "base": {
            "generated_config_alias": base_alias,
            "profile": args.base_profile,
            "gpgpusim_config": gpgpu_config,
            "trace_config": trace_config,
        },
        "benchmark_cases": result["benchmark_cases"],
        "target_metrics": targets,
        "search": {
            "stage": "rf_prefetch_remodeled_parameters",
            "candidate_strategy": "cartesian_product",
            "max_candidates": 0,
            "parameters": [],
            "template_note": "Fill with reviewed bounded calibration_result parameters before running S6.",
        },
        "evaluation": {
            "mode": "supplied_metrics",
            "candidate_metrics": [],
            "template_note": "Fill with local simulator candidate metrics. Do not use simulator smoke job 486 as target metrics.",
        },
        "handoff": {
            "do_not_claim_calibrated": True,
            "do_not_run_as_is": True,
            "missing_for_s6": [
                "reviewed bounded search parameters",
                "candidate simulator metrics matching target metric names",
                "fresh S6 review before ranked report generation",
            ],
        },
    }


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
    parser.add_argument("--output", required=True, help="Draft hardware target metrics YAML path, or '-' for stdout.")
    parser.add_argument("--repo-root", type=Path, default=repo_root_from_script(), help="Repository root.")
    parser.add_argument("--architecture", default=DEFAULT_ARCHITECTURE, help="Architecture label.")
    parser.add_argument("--target-id", default="", help="Stable target id for deterministic outputs.")
    parser.add_argument("--generated-at", default="", help="Deterministic generated_at timestamp.")
    parser.add_argument("--fixture-only", action="store_true", help="Mark output as fixture-only.")
    parser.add_argument("--allow-template", action="store_true", help="Allow output with no timing metrics for blocker templates.")

    parser.add_argument("--stdout", help="Native application stdout file.")
    parser.add_argument("--stderr", help="Native application stderr file.")
    parser.add_argument("--time-output", help="GNU /usr/bin/time output with MGS_HW_TIME_* lines.")
    parser.add_argument("--timing-json", help="JSON file with externally collected native timing metrics.")
    parser.add_argument("--nsys-kernel-csv", help="Nsight Systems cuda_gpu_kern_sum CSV.")
    parser.add_argument("--nvidia-smi-query", help="nvidia-smi noheader CSV query output.")
    parser.add_argument("--tool-versions", help="Tool-version command output ledger.")

    parser.add_argument("--collection-host", default="", help="Hardware collection host.")
    parser.add_argument("--source-label", default="", help="Short label for the source run.")
    parser.add_argument("--collection-command", default="", help="Command used to collect native metrics.")
    parser.add_argument("--notes", default="", help="Free-form collection notes.")

    parser.add_argument("--benchmark-id", default=DEFAULT_BENCHMARK_ID, help="Benchmark case id used by S6.")
    parser.add_argument("--benchmark-suite", default=DEFAULT_BENCHMARK_SUITE, help="Benchmark suite label.")
    parser.add_argument("--benchmark-name", default=DEFAULT_BENCHMARK_NAME, help="Benchmark executable/app label.")
    parser.add_argument("--benchmark-selector", default=DEFAULT_BENCHMARK_SELECTOR, help="Job-launching benchmark selector.")
    parser.add_argument("--benchmark-args", default=DEFAULT_ARGS, help="Native benchmark arguments.")
    parser.add_argument("--native-case-label", default=DEFAULT_BENCHMARK_ID, help="Native run case label.")

    parser.add_argument("--s6-template-output", default="", help="Optional draft S6 supplied_metrics template path.")
    parser.add_argument("--base-config-alias", default="", help="Generated config alias for S6 template.")
    parser.add_argument("--base-profile", default="bootstrap", help="Base profile for S6 template.")
    parser.add_argument("--base-gpgpusim-config", default="", help="Base gpgpusim.config path for S6 template.")
    parser.add_argument("--base-trace-config", default="", help="Base trace.config path for S6 template.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        result = build_result(args)
        root = args.repo_root.resolve()
        write_yaml(args.output, result, root)
        if args.s6_template_output:
            template = build_s6_template(result, args)
            write_yaml(args.s6_template_output, template, root)
    except CollectError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
