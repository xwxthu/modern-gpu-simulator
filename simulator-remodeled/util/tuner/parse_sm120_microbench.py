#!/usr/bin/env python3
"""Parse SM120 tuner microbenchmark output into a calibration-result draft."""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
from pathlib import Path
import re
import sys
from typing import Any

import yaml


GPU_CHOICES = ("RTX5060", "RTX5070_TI")
SOURCE_TYPES = ("microbenchmark", "system_config")
DEFAULT_ARCHITECTURE = "SM120"
DEFAULT_SCHEMA_REL = (
    "simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/"
    "schema/sm120.schema.yaml"
)

CONFIG_LINE_PREFIXES = (
    "-gpgpu_",
    "-trace_",
    "-ptx_",
    "-specialized_unit_",
    "-dram_",
    "-latency_",
    "-tensor_",
    "-branch_",
    "-half_",
    "-uniform_",
    "-predicate_",
    "-miscellaneous_",
    "-memory_",
    "-sm_memory_",
    "-memmory_",
    "-prefetch_",
    "-num_",
    "-max_",
    "-is_",
    "-custom_",
    "-scoreboard_",
    "-prt_",
    "-interwarp_",
    "-measure_",
    "-number_",
    "-offset_",
    "-dp_",
    "-constant_",
    "-ibuffer_",
)

BENCHMARK_RE = re.compile(r"^running\s+(?P<path>\S+)\s+microbenchmark\b")
KEY_RE = re.compile(r"^-[A-Za-z0-9_][A-Za-z0-9_:.-]*$")


class ParseError(RuntimeError):
    pass


STAGES: dict[str, dict[str, Any]] = {
    "official_device_query_facts": {
        "description": "Official facts already emitted as tuner config lines.",
        "expected_source_types": ["system_config", "microbenchmark"],
        "output_target": "base_or_gpu_overlay_candidate",
        "keys": [
            "-gpgpu_compute_capability_major",
            "-gpgpu_compute_capability_minor",
            "-gpgpu_n_clusters",
            "-gpgpu_n_cores_per_cluster",
            "-gpgpu_clock_domains",
            "-gpgpu_shader_registers",
            "-gpgpu_registers_per_block",
            "-gpgpu_occupancy_sm_number",
            "-gpgpu_shader_core_pipeline",
            "-gpgpu_shader_cta",
            "-gpgpu_shmem_size",
            "-gpgpu_shmem_sizeDefault",
            "-gpgpu_shmem_per_block",
        ],
    },
    "system_core_config_microbench": {
        "description": "Core unit counts, issue widths, and opcode latency/initiation lines.",
        "expected_source_types": ["microbenchmark"],
        "output_target": "sm120_base_or_calibration_result_candidate",
        "keys": [
            "-gpgpu_pipeline_widths",
            "-gpgpu_num_sp_units",
            "-gpgpu_num_sfu_units",
            "-gpgpu_num_int_units",
            "-gpgpu_tensor_core_avail",
            "-gpgpu_num_tensor_core_units",
            "-gpgpu_sub_core_model",
            "-gpgpu_enable_specialized_operand_collector",
            "-gpgpu_operand_collector_num_units_gen",
            "-gpgpu_operand_collector_num_in_ports_gen",
            "-gpgpu_operand_collector_num_out_ports_gen",
            "-gpgpu_num_sched_per_core",
            "-gpgpu_inst_fetch_throughput",
            "-gpgpu_max_insn_issue_per_warp",
            "-gpgpu_dual_issue_diff_exec_units",
            "-ptx_opcode_latency_int",
            "-ptx_opcode_initiation_int",
            "-ptx_opcode_latency_fp",
            "-ptx_opcode_initiation_fp",
            "-ptx_opcode_latency_dp",
            "-ptx_opcode_initiation_dp",
            "-ptx_opcode_latency_sfu",
            "-ptx_opcode_initiation_sfu",
            "-ptx_opcode_latency_tesnor",
            "-ptx_opcode_initiation_tensor",
            "-tensor_latency",
            "-tensor_extra_latency_16816_fp32_1688_fp32",
            "-tensor_rate_per_cycle",
        ],
    },
    "memory_l2_l1_config_microbench": {
        "description": "Memory, L2, L1, shared-memory, and DRAM geometry/timing candidates.",
        "expected_source_types": ["microbenchmark", "system_config"],
        "output_target": "gpu_overlay_or_calibration_result_candidate",
        "keys": [
            "-gpgpu_adaptive_cache_config",
            "-gpgpu_l1_banks",
            "-gpgpu_cache:dl1",
            "-gpgpu_l1_banks_hashing_function",
            "-gpgpu_gmem_skip_L1D",
            "-gpgpu_n_cluster_ejection_buffer_size",
            "-gpgpu_l1_cache_write_ratio",
            "-gpgpu_n_sub_partition_per_mchannel",
            "-gpgpu_cache:dl2",
            "-gpgpu_cache:dl2_texture_only",
            "-gpgpu_perf_sim_memcpy",
            "-gpgpu_memory_partition_indexing",
            "-gpgpu_l2_rop_latency",
            "-gpgpu_n_mem",
            "-gpgpu_n_mem_per_ctrlr",
            "-gpgpu_dram_buswidth",
            "-gpgpu_dram_burst_length",
            "-dram_data_command_freq_ratio",
            "-dram_latency",
            "-gpgpu_dram_scheduler",
            "-gpgpu_frfcfs_dram_sched_queue_size",
            "-gpgpu_dram_return_queue_size",
            "-gpgpu_mem_address_mask",
            "-gpgpu_mem_addr_mapping",
            "-gpgpu_dram_timing_opt",
            "-dram_dual_bus_interface",
            "-dram_bnk_indexing_policy",
            "-dram_bnkgrp_indexing_policy",
            "-memory_shared_memory_minimum_latency",
            "-memory_l1d_minimum_latency",
            "-constant_cache_latency_at_sm_structure",
        ],
    },
    "trace_latency_groups": {
        "description": "Trace frontend latency/initiation pairs and specialized-unit trace groups.",
        "expected_source_types": ["microbenchmark"],
        "output_target": "calibration_result_candidate",
        "keys": [
            "-trace_opcode_latency_initiation_int",
            "-trace_opcode_latency_initiation_sp",
            "-trace_opcode_latency_initiation_dp",
            "-trace_opcode_latency_initiation_sfu",
            "-trace_opcode_latency_initiation_tensor",
            "-trace_opcode_latency_initiation_branch",
            "-trace_opcode_latency_initiation_half",
            "-trace_opcode_latency_initiation_uniform",
            "-trace_opcode_latency_initiation_predicate",
            "-trace_opcode_latency_initiation_miscellaneous_queue",
            "-trace_opcode_latency_initiation_miscellaneous_no_queue",
            "-specialized_unit_2",
            "-trace_opcode_latency_initiation_spec_op_2",
        ],
    },
    "rf_prefetch_remodeled_parameters": {
        "description": "Register-file, prefetch, scheduler, PRT, and remodeled SM timing knobs.",
        "expected_source_types": ["microbenchmark", "correlation_search"],
        "output_target": "calibration_result_candidate",
        "keys": [
            "-gpgpu_num_reg_banks",
            "-gpgpu_reg_file_port_throughput",
            "-latency_L0_to_L1",
            "-latency_L1_to_L0",
            "-ibuffer_remodeled_size",
            "-prefetch_per_stream_buffer_size",
            "-prefetch_num_stream_buffers",
            "-num_instruction_prefetches_per_cycle",
            "-is_rf_cache_enabled",
            "-max_operands_regular_register_file",
            "-max_latency_regular_register_file_latency",
            "-num_regular_register_file_read_ports_per_bank",
            "-num_regular_register_file_write_ports_per_bank",
            "-custom_omp_scheduler_ratio_to_dynamic",
            "-number_of_coalescers",
            "-prt_selection_policy_string",
            "-number_of_clusters_for_prt_selection",
            "-is_interwarp_coalescing_enabled",
            "-num_interwarp_coalescing_tables",
            "-interwarp_coalescing_quanta",
            "-interwarp_coalescing_selection_policy_string",
            "-max_size_interwarp_coalescing_per_table",
        ],
    },
    "power_placeholder": {
        "description": "Power calibration placeholder. S5 MVP records no power measurements.",
        "expected_source_types": [],
        "output_target": "no_delta",
        "keys": [],
    },
}


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[3]


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not load as a YAML mapping")
    return data


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def display_path(path: Path, repo_root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def iso_utc_now() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def owner_lookup(schema: dict[str, Any], file_name: str) -> dict[str, str]:
    table = schema.get("active_option_key_owners", {}).get(file_name)
    if not isinstance(table, dict):
        return {}
    lookup: dict[str, str] = {}
    for owner, keys in table.items():
        for key in keys or []:
            lookup[key] = owner
    return lookup


def stage_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for stage, info in STAGES.items():
        for key in info["keys"]:
            lookup[key] = stage
    return lookup


def should_parse_key(key: str, known_schema_keys: set[str]) -> bool:
    if key in known_schema_keys:
        return True
    return any(key.startswith(prefix) for prefix in CONFIG_LINE_PREFIXES)


def classify_file(key: str, trace_keys: set[str]) -> str:
    if key in trace_keys or key.startswith("-trace_") or key.startswith("-specialized_unit_"):
        return "trace.config"
    return "gpgpusim.config"


def clean_benchmark_name(path_text: str) -> str:
    name = Path(path_text).name
    return name or path_text.strip("./")


def normalize_value(value: str) -> str:
    value = re.sub(r"\s+", " ", value.strip())
    if value.startswith("="):
        value = value[1:].strip()
    return value


def parse_config_records(text: str, known_schema_keys: set[str], trace_keys: set[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    current_benchmark: str | None = None
    stages = stage_lookup()
    for lineno, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.strip()
        match = BENCHMARK_RE.match(line)
        if match:
            current_benchmark = clean_benchmark_name(match.group("path"))
            continue
        if not line or line.startswith("#") or not line.startswith("-"):
            continue
        parts = line.split(maxsplit=1)
        key = parts[0]
        if not KEY_RE.match(key) or not should_parse_key(key, known_schema_keys):
            continue
        value = normalize_value(parts[1]) if len(parts) > 1 else ""
        file_name = classify_file(key, trace_keys)
        records.append(
            {
                "key": key,
                "value": value,
                "file": file_name,
                "line": lineno,
                "benchmark": current_benchmark or "single_output",
                "stage": stages.get(key, "unsupported"),
            }
        )
    return records


def target_layer(owner: str | None, gpu: str) -> str:
    if owner == "calibration_result":
        return f"calibration-results/{gpu}/latest.yaml"
    if owner == "gpu_overlay":
        return f"overlays/{gpu}.yaml"
    if owner == "sm120_base":
        return "base/SM120_BASE.yaml"
    return "unassigned"


def apply_owner_and_support(
    records: list[dict[str, Any]],
    gpgpu_owners: dict[str, str],
    trace_owners: dict[str, str],
) -> None:
    stages = stage_lookup()
    for record in records:
        owner_table = trace_owners if record["file"] == "trace.config" else gpgpu_owners
        owner = owner_table.get(record["key"])
        record["owner"] = owner
        if record["key"] not in stages:
            record["support_status"] = "unsupported_by_s5_mvp"
            record["unsupported_reason"] = "key_not_in_s5_supported_stage_map"
        elif owner is None:
            record["support_status"] = "unsupported_by_s4_schema"
            record["unsupported_reason"] = "no_owner_in_sm120_active_schema"
        else:
            record["support_status"] = "supported"


def summarize_duplicates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for record in records:
        grouped.setdefault((record["file"], record["key"]), []).append(record)
    duplicates: list[dict[str, Any]] = []
    for (file_name, key), items in sorted(grouped.items()):
        if len(items) <= 1:
            continue
        values = sorted({item["value"] for item in items})
        duplicates.append(
            {
                "file": file_name,
                "key": key,
                "values": values,
                "conflict": len(values) > 1,
                "observations": [
                    {
                        "line": item["line"],
                        "benchmark": item["benchmark"],
                        "value": item["value"],
                    }
                    for item in items
                ],
            }
        )
    return duplicates


def build_delta(records: list[dict[str, Any]], gpu: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for record in records:
        if record["support_status"] != "supported":
            continue
        grouped.setdefault((record["file"], record["key"]), []).append(record)

    delta: dict[str, list[dict[str, Any]]] = {"gpgpusim.config": [], "trace.config": []}
    for (file_name, key), items in sorted(grouped.items()):
        values = {item["value"] for item in items}
        if len(values) > 1:
            continue
        selected = items[-1]
        delta[file_name].append(
            {
                "key": key,
                "value": selected["value"],
                "owner": selected["owner"],
                "target_layer": target_layer(selected["owner"], gpu),
                "stage": selected["stage"],
                "source_line": selected["line"],
                "source_benchmark": selected["benchmark"],
                "observation_count": len(items),
                "status": "draft_not_applied",
            }
        )
    return delta


def unsupported_summary(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    summary: dict[str, list[dict[str, Any]]] = {"gpgpusim.config": [], "trace.config": []}
    for record in records:
        if record["support_status"] == "supported":
            continue
        summary[record["file"]].append(
            {
                "key": record["key"],
                "value": record["value"],
                "line": record["line"],
                "benchmark": record["benchmark"],
                "reason": record["unsupported_reason"],
            }
        )
    for key in summary:
        summary[key].sort(key=lambda item: (item["key"], item["line"]))
    return summary


def stage_records(records: list[dict[str, Any]], source_type: str, gpu: str) -> dict[str, dict[str, Any]]:
    staged: dict[str, dict[str, Any]] = {}
    for stage, info in STAGES.items():
        staged[stage] = {
            "description": info["description"],
            "expected_source_types": info["expected_source_types"],
            "output_target": info["output_target"],
            "parameter_keys": info["keys"],
            "records": [],
        }
    for record in records:
        stage = record["stage"] if record["stage"] in staged else "unsupported"
        if stage == "unsupported":
            continue
        staged[stage]["records"].append(
            {
                "file": record["file"],
                "key": record["key"],
                "value": record["value"],
                "owner": record["owner"],
                "target_layer": target_layer(record["owner"], gpu),
                "source_type": source_type,
                "benchmark": record["benchmark"],
                "line": record["line"],
                "support_status": record["support_status"],
            }
        )
    return staged


def read_input(path_arg: str, repo_root: Path) -> tuple[str, str, str]:
    if path_arg == "-":
        data = sys.stdin.buffer.read()
        return "stdin", sha256_bytes(data), data.decode("utf-8", errors="replace")
    path = Path(path_arg).resolve()
    data = path.read_bytes()
    return display_path(path, repo_root), sha256_bytes(data), data.decode("utf-8", errors="replace")


def default_calibration_id(gpu: str, source_type: str) -> str:
    stamp = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{gpu.lower()}-{source_type}-draft-{stamp}"


def build_result(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = repo_root_from_script()
    schema_path = Path(args.schema)
    if not schema_path.is_absolute():
        schema_path = repo_root / schema_path
    schema = load_yaml(schema_path)
    gpgpu_owners = owner_lookup(schema, "gpgpusim.config")
    trace_owners = owner_lookup(schema, "trace.config")
    known_schema_keys = set(gpgpu_owners) | set(trace_owners)

    input_path, input_hash, text = read_input(args.input, repo_root)
    records = parse_config_records(text, known_schema_keys, set(trace_owners))
    if not records:
        raise ParseError(
            "no config-style calibration lines found; this parser only accepts "
            "GPU_Microbenchmark run_all.sh, system_config, or other outputs that "
            "emit -gpgpu_* / -trace_* / related config lines"
        )
    apply_owner_and_support(records, gpgpu_owners, trace_owners)

    duplicates = summarize_duplicates(records)
    conflict_keys = {
        (item["file"], item["key"])
        for item in duplicates
        if item["conflict"]
    }
    delta = build_delta(records, args.gpu)
    unsupported = unsupported_summary(records)
    supported_count = sum(1 for record in records if record["support_status"] == "supported")
    unsupported_count = len(records) - supported_count

    source_label = args.source_label or Path(input_path).name or args.source_type
    result = {
        "schema_version": 1,
        "schema_id": "sm120_microbenchmark_calibration_result_v1",
        "calibration_id": args.calibration_id or default_calibration_id(args.gpu, args.source_type),
        "gpu": args.gpu,
        "architecture": args.architecture,
        "status": "draft_not_applied",
        "generated_at": args.generated_at or iso_utc_now(),
        "fixture_only": bool(args.fixture_only),
        "parser": {
            "script": "simulator-remodeled/util/tuner/parse_sm120_microbench.py",
            "script_sha256": sha256_file(Path(__file__).resolve()),
            "schema": schema_path.relative_to(repo_root).as_posix(),
            "schema_sha256": sha256_file(schema_path),
        },
        "source": {
            "source_type": args.source_type,
            "label": source_label,
            "input_path": input_path,
            "input_sha256": input_hash,
            "collection_host": args.collection_host or "unknown",
            "collection_command": args.collection_command or "unknown",
            "notes": args.source_notes or "",
        },
        "summary": {
            "parsed_config_line_count": len(records),
            "supported_line_count": supported_count,
            "unsupported_line_count": unsupported_count,
            "duplicate_key_count": len(duplicates),
            "conflicting_duplicate_key_count": len(conflict_keys),
            "derived_delta_key_count": sum(len(items) for items in delta.values()),
        },
        "stages": stage_records(records, args.source_type, args.gpu),
        "derived_delta": {
            "status": "draft_not_applied",
            "conflicting_keys_withheld": [
                {"file": file_name, "key": key}
                for file_name, key in sorted(conflict_keys)
            ],
            "files": delta,
        },
        "unsupported_keys": unsupported,
        "duplicate_keys": duplicates,
        "handoff": {
            "s4_generator_status": "bootstrap-current-flat only; this draft is not consumed automatically",
            "next_step": (
                "After reviewer approval of real collected data, copy supported calibration_result "
                f"entries into calibration-results/{args.gpu}/latest.yaml or a staged delta file. "
                "Update overlays/base only for owner-matched device facts."
            ),
            "do_not_claim_calibrated": True,
        },
    }
    return result


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Parse tuner GPU_Microbenchmark run_all.sh, system_config, or other "
            "config-line output into an SM120 calibration-result YAML draft. "
            "Raw nvidia-smi or human-readable CUDA deviceQuery text is not supported."
        )
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Config-line output path, or '-' for stdin; raw human-readable deviceQuery/nvidia-smi text is unsupported.",
    )
    parser.add_argument("--output", default="-", help="YAML output path, or '-' for stdout.")
    parser.add_argument("--gpu", required=True, choices=GPU_CHOICES)
    parser.add_argument("--architecture", default=DEFAULT_ARCHITECTURE)
    parser.add_argument("--source-type", required=True, choices=SOURCE_TYPES)
    parser.add_argument("--source-label", default="")
    parser.add_argument("--source-notes", default="")
    parser.add_argument("--collection-host", default="")
    parser.add_argument("--collection-command", default="")
    parser.add_argument("--calibration-id", default="")
    parser.add_argument("--generated-at", default="", help="Override generated_at for deterministic fixtures.")
    parser.add_argument("--schema", default=DEFAULT_SCHEMA_REL)
    parser.add_argument(
        "--fixture-only",
        action="store_true",
        help="Mark the result as a synthetic fixture that must not be used as calibration evidence.",
    )
    parser.add_argument(
        "--fail-on-unsupported",
        action="store_true",
        help="Exit nonzero if any parsed config line is unsupported by the S5 MVP or S4 schema.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        result = build_result(args)
    except ParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    output = yaml.safe_dump(result, sort_keys=False, width=120)
    if args.output == "-":
        sys.stdout.write(output)
    else:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output)
    if args.fail_on_unsupported and result["summary"]["unsupported_line_count"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
