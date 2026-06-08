#!/usr/bin/env python3
"""Rank small SM120 correlation-search candidate deltas from a manifest.

The harness is intentionally draft-only. It never runs the simulator and never
writes tested configs or accepted calibration results.
"""

from __future__ import annotations

import argparse
import datetime as _dt
from decimal import Decimal, InvalidOperation
import hashlib
import itertools
from pathlib import Path
import re
import shlex
import subprocess
import sys
from typing import Any

import yaml

from parse_sm120_microbench import STAGES


GPU_CHOICES = ("RTX5060", "RTX5070_TI")
DEFAULT_ARCHITECTURE = "SM120"
DEFAULT_SCHEMA_REL = (
    "simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/"
    "schema/sm120.schema.yaml"
)
DEFAULT_CONTRACT_REL = (
    "simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120/"
    "schema/correlation-search.schema.yaml"
)
HARD_CANDIDATE_LIMIT = 64
HARD_PARAMETER_VALUE_LIMIT = 16
KEY_RE = re.compile(r"^-[A-Za-z0-9_][A-Za-z0-9_:.-]*$")
SAFE_ALIAS_RE = re.compile(r"^[A-Za-z0-9_]+$")
ALLOWED_FILES = ("gpgpusim.config", "trace.config")
FORBIDDEN_OUTPUT_FRAGMENTS = (
    "/configs/tested-cfgs/",
    "/configs/generated/tested-cfgs/",
)
FORBIDDEN_OUTPUT_DIRS_REL = (
    "simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120",
)


class SearchError(RuntimeError):
    pass


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[3]


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise SearchError(f"{path} did not load as a YAML mapping")
    return data


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


def resolve_path(path_text: str, root: Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path.resolve()
    return (root / path).resolve()


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def require_relative_to(path: Path, parent: Path, description: str) -> None:
    if not is_relative_to(path.resolve(), parent.resolve()):
        raise SearchError(f"{description} must be under {parent}: {path}")


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


def owner_lookup(schema: dict[str, Any], file_name: str) -> dict[str, str]:
    table = schema.get("active_option_key_owners", {}).get(file_name)
    if not isinstance(table, dict):
        raise SearchError(f"schema missing active_option_key_owners for {file_name}")
    lookup: dict[str, str] = {}
    conflicts: dict[str, list[str]] = {}
    for owner, keys in table.items():
        for key in keys or []:
            if key in lookup:
                conflicts.setdefault(key, [lookup[key]]).append(owner)
            lookup[key] = owner
    if conflicts:
        details = ", ".join(f"{key}: {owners}" for key, owners in sorted(conflicts.items()))
        raise SearchError(f"schema owner conflicts in {file_name}: {details}")
    return lookup


def active_option_map(path: Path) -> dict[str, str]:
    options: dict[str, str] = {}
    for lineno, line in enumerate(path.read_text().splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or not stripped.startswith("-"):
            continue
        parts = stripped.split(maxsplit=1)
        key = parts[0]
        value = parts[1] if len(parts) > 1 else ""
        if key in options:
            raise SearchError(f"{path}:{lineno}: duplicate active option {key}")
        options[key] = value
    return options


def decimal_to_string(value: Decimal) -> str:
    if value == value.to_integral_value():
        return str(value.quantize(Decimal("1")))
    return format(value.normalize(), "f")


def normalize_value(value: Any) -> str:
    if isinstance(value, bool) or value is None or isinstance(value, (dict, list)):
        raise SearchError(f"candidate value must be scalar string/number, got {value!r}")
    if isinstance(value, float):
        return decimal_to_string(Decimal(str(value)))
    return str(value).strip()


def bounded_range_values(raw_range: Any, key: str) -> list[str]:
    if not isinstance(raw_range, dict):
        raise SearchError(f"{key} range must be a mapping with start/stop/step")
    required = {"start", "stop", "step"}
    missing = sorted(required - set(raw_range))
    if missing:
        raise SearchError(f"{key} range is unbounded; missing {', '.join(missing)}")
    try:
        start = Decimal(str(raw_range["start"]))
        stop = Decimal(str(raw_range["stop"]))
        step = Decimal(str(raw_range["step"]))
    except (InvalidOperation, ValueError) as exc:
        raise SearchError(f"{key} range values must be numeric") from exc
    if step == 0:
        raise SearchError(f"{key} range step must not be zero")
    if start < stop and step < 0:
        raise SearchError(f"{key} range step sign does not reach stop")
    if start > stop and step > 0:
        raise SearchError(f"{key} range step sign does not reach stop")
    try:
        max_values = int(raw_range.get("max_values", HARD_PARAMETER_VALUE_LIMIT))
    except (TypeError, ValueError) as exc:
        raise SearchError(f"{key} range max_values must be an integer") from exc
    if max_values <= 0 or max_values > HARD_PARAMETER_VALUE_LIMIT:
        raise SearchError(f"{key} range max_values must be 1..{HARD_PARAMETER_VALUE_LIMIT}")
    values: list[str] = []
    current = start
    while current <= stop if step > 0 else current >= stop:
        values.append(decimal_to_string(current))
        if len(values) > max_values:
            raise SearchError(f"{key} range exceeds declared max_values={max_values}")
        current += step
    if not values:
        raise SearchError(f"{key} range produced no candidate values")
    return values


def values_from_parameter(entry: dict[str, Any]) -> list[str]:
    if "values" in entry and "range" in entry:
        raise SearchError(f"{entry.get('key')} must not define both values and range")
    if "values" in entry:
        values_raw = entry["values"]
        if not isinstance(values_raw, list) or not values_raw:
            raise SearchError(f"{entry.get('key')} values must be a non-empty list")
        values = [normalize_value(value) for value in values_raw]
    elif "range" in entry:
        values = bounded_range_values(entry["range"], str(entry.get("key")))
    else:
        raise SearchError(f"{entry.get('key')} must define explicit values or a bounded range")
    if len(values) > HARD_PARAMETER_VALUE_LIMIT:
        raise SearchError(f"{entry.get('key')} has more than {HARD_PARAMETER_VALUE_LIMIT} values")
    if any(value == "" for value in values):
        raise SearchError(f"{entry.get('key')} has an empty candidate value")
    if len(set(values)) != len(values):
        raise SearchError(f"{entry.get('key')} has duplicate candidate values after normalization")
    return values


def stage_key_map() -> dict[str, set[str]]:
    return {stage: set(info.get("keys", [])) for stage, info in STAGES.items()}


def validate_generated_base_paths(base: dict[str, Any], root: Path) -> dict[str, Path]:
    if not isinstance(base, dict):
        raise SearchError("manifest base must be a mapping")
    required = ["gpgpusim_config", "trace_config", "profile", "generated_config_alias"]
    missing = [field for field in required if field not in base]
    if missing:
        raise SearchError(f"manifest base missing fields: {', '.join(missing)}")

    gpgpu_path = resolve_path(str(base["gpgpusim_config"]), root)
    trace_path = resolve_path(str(base["trace_config"]), root)
    if not gpgpu_path.is_file():
        raise SearchError(f"base gpgpusim_config does not exist: {gpgpu_path}")
    if not trace_path.is_file():
        raise SearchError(f"base trace_config does not exist: {trace_path}")

    require_relative_to(
        gpgpu_path,
        root / "simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated/tested-cfgs",
        "base gpgpusim_config",
    )
    require_relative_to(
        trace_path,
        root / "simulator-remodeled/gpu-simulator/configs/generated/tested-cfgs",
        "base trace_config",
    )
    return {"gpgpusim.config": gpgpu_path, "trace.config": trace_path}


def validate_manifest_header(manifest: dict[str, Any], schema: dict[str, Any]) -> None:
    if manifest.get("schema_version") != 1:
        raise SearchError("manifest schema_version must be 1")
    if manifest.get("schema_id") != "sm120_correlation_search_manifest_v1":
        raise SearchError("manifest schema_id must be sm120_correlation_search_manifest_v1")
    if manifest.get("gpu") not in GPU_CHOICES:
        raise SearchError(f"manifest gpu must be one of {', '.join(GPU_CHOICES)}")
    if manifest.get("architecture", DEFAULT_ARCHITECTURE) != DEFAULT_ARCHITECTURE:
        raise SearchError("S6 MVP only accepts architecture SM120")
    if not isinstance(manifest.get("base"), dict):
        raise SearchError("manifest base must be a mapping")
    profile = manifest["base"].get("profile")
    if profile not in schema.get("profiles", {}):
        raise SearchError(f"base profile {profile!r} is not in the SM120 schema")


def validate_search_space(
    manifest: dict[str, Any],
    schema: dict[str, Any],
    base_options: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    search = manifest.get("search")
    if not isinstance(search, dict):
        raise SearchError("manifest search must be a mapping")
    stage = search.get("stage")
    if stage not in STAGES:
        raise SearchError(f"search stage {stage!r} is not a known S5/S6 stage")
    expected_sources = STAGES[stage].get("expected_source_types", [])
    if "correlation_search" not in expected_sources:
        raise SearchError(f"search stage {stage} does not accept correlation_search provenance")
    if search.get("candidate_strategy") != "cartesian_product":
        raise SearchError("S6 MVP requires candidate_strategy: cartesian_product")
    if "max_candidates" not in search:
        raise SearchError("search max_candidates is required to keep the search bounded")
    try:
        max_candidates = int(search["max_candidates"])
    except (TypeError, ValueError) as exc:
        raise SearchError("search max_candidates must be an integer") from exc
    if max_candidates <= 0 or max_candidates > HARD_CANDIDATE_LIMIT:
        raise SearchError(f"search max_candidates must be 1..{HARD_CANDIDATE_LIMIT}")

    raw_parameters = search.get("parameters")
    if not isinstance(raw_parameters, list) or not raw_parameters:
        raise SearchError("search parameters must be a non-empty list")

    owners_by_file = {file_name: owner_lookup(schema, file_name) for file_name in ALLOWED_FILES}
    keys_by_stage = stage_key_map()
    seen_keys: set[tuple[str, str]] = set()
    seen_plain_keys: set[str] = set()
    parameters: list[dict[str, Any]] = []
    product_count = 1
    for entry in raw_parameters:
        if not isinstance(entry, dict):
            raise SearchError("each search parameter must be a mapping")
        file_name = entry.get("file")
        key = entry.get("key")
        owner = entry.get("owner")
        entry_stage = entry.get("stage")
        provenance = entry.get("provenance")
        if file_name not in ALLOWED_FILES:
            raise SearchError(f"parameter {key!r} has unsupported file {file_name!r}")
        if not isinstance(key, str) or not KEY_RE.match(key):
            raise SearchError(f"parameter key is invalid: {key!r}")
        if (file_name, key) in seen_keys:
            raise SearchError(f"duplicate search parameter {file_name} {key}")
        if key in seen_plain_keys:
            raise SearchError(f"S6 MVP requires globally unique parameter keys; duplicate {key}")
        seen_keys.add((file_name, key))
        seen_plain_keys.add(key)
        schema_owner = owners_by_file[file_name].get(key)
        if schema_owner is None:
            raise SearchError(f"{file_name} key {key} is unknown to schema active_option_key_owners")
        if owner != schema_owner:
            raise SearchError(f"{file_name} key {key} owner {owner!r} does not match schema owner {schema_owner!r}")
        if owner != "calibration_result":
            raise SearchError(f"S6 MVP only searches calibration_result keys; {key} is owned by {owner}")
        if entry_stage != stage:
            raise SearchError(f"{key} stage {entry_stage!r} does not match search stage {stage!r}")
        if key not in keys_by_stage.get(stage, set()):
            raise SearchError(f"{key} is not listed in S5/S6 stage {stage}")
        if provenance != "correlation_search":
            raise SearchError(f"{key} provenance must be correlation_search")
        if key not in base_options[file_name]:
            raise SearchError(f"{file_name} key {key} is not active in the base generated config")

        values = values_from_parameter(entry)
        product_count *= len(values)
        if product_count > max_candidates:
            raise SearchError(
                f"search expands to {product_count} candidates, exceeding max_candidates={max_candidates}"
            )
        parameters.append(
            {
                "file": file_name,
                "key": key,
                "owner": owner,
                "stage": stage,
                "provenance": provenance,
                "base_value": base_options[file_name][key],
                "values": values,
                "description": entry.get("description", ""),
            }
        )
    return parameters


def candidate_signature(values_by_key: dict[str, str], ordered_keys: list[str]) -> tuple[tuple[str, str], ...]:
    return tuple((key, values_by_key[key]) for key in ordered_keys)


def generate_candidates(search_id: str, parameters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    ordered_keys = [param["key"] for param in parameters]
    value_lists = [param["values"] for param in parameters]
    for index, combo in enumerate(itertools.product(*value_lists), 1):
        values_by_key = dict(zip(ordered_keys, combo))
        deltas: dict[str, list[dict[str, Any]]] = {"gpgpusim.config": [], "trace.config": []}
        changed_count = 0
        for param in parameters:
            value = values_by_key[param["key"]]
            changed = value != param["base_value"]
            if changed:
                changed_count += 1
            deltas[param["file"]].append(
                {
                    "key": param["key"],
                    "value": value,
                    "base_value": param["base_value"],
                    "owner": param["owner"],
                    "stage": param["stage"],
                    "provenance": param["provenance"],
                    "status": "draft_not_applied",
                    "changed_from_base": changed,
                }
            )
        candidates.append(
            {
                "candidate_id": f"candidate_{index:04d}",
                "search_id": search_id,
                "values_by_key": values_by_key,
                "signature": candidate_signature(values_by_key, ordered_keys),
                "deltas": deltas,
                "changed_key_count": changed_count,
            }
        )
    return candidates


def benchmark_ids(manifest: dict[str, Any]) -> set[str]:
    cases = manifest.get("benchmark_cases")
    if not isinstance(cases, list) or not cases:
        raise SearchError("benchmark_cases must be a non-empty list")
    ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str) or not case["id"]:
            raise SearchError("each benchmark case must have a non-empty id")
        if case["id"] in ids:
            raise SearchError(f"duplicate benchmark case id {case['id']}")
        ids.add(case["id"])
    return ids


def target_metrics(manifest: dict[str, Any], known_benchmarks: set[str]) -> list[dict[str, Any]]:
    raw_targets = manifest.get("target_metrics")
    if not isinstance(raw_targets, list) or not raw_targets:
        raise SearchError("target_metrics must be a non-empty list")
    targets: list[dict[str, Any]] = []
    for item in raw_targets:
        if not isinstance(item, dict):
            raise SearchError("each target metric must be a mapping")
        benchmark = item.get("benchmark")
        metric = item.get("metric")
        if benchmark not in known_benchmarks:
            raise SearchError(f"target metric uses unknown benchmark {benchmark!r}")
        if not isinstance(metric, str) or not metric:
            raise SearchError("target metric must have a non-empty metric name")
        try:
            target = float(item["target"])
            weight = float(item.get("weight", 1.0))
            epsilon = float(item.get("epsilon", 1.0))
        except (KeyError, TypeError, ValueError) as exc:
            raise SearchError(f"target metric {benchmark}.{metric} has invalid numeric fields") from exc
        if weight <= 0:
            raise SearchError(f"target metric {benchmark}.{metric} weight must be positive")
        if epsilon <= 0:
            raise SearchError(f"target metric {benchmark}.{metric} epsilon must be positive")
        targets.append(
            {
                "benchmark": benchmark,
                "metric": metric,
                "target": target,
                "weight": weight,
                "epsilon": epsilon,
                "normalization": item.get("normalization", "target_abs_or_epsilon"),
            }
        )
    return targets


def evaluation_map(
    manifest: dict[str, Any],
    candidates: list[dict[str, Any]],
    ordered_keys: list[str],
) -> tuple[str, dict[tuple[tuple[str, str], ...], dict[str, Any]]]:
    evaluation = manifest.get("evaluation")
    if not isinstance(evaluation, dict):
        raise SearchError("evaluation must be a mapping")
    mode = evaluation.get("mode")
    if mode not in {"fixture", "supplied_metrics"}:
        raise SearchError("evaluation mode must be fixture or supplied_metrics")
    raw_items = evaluation.get("candidate_metrics")
    if not isinstance(raw_items, list) or not raw_items:
        raise SearchError("evaluation candidate_metrics must be a non-empty list")

    known_signatures = {candidate["signature"] for candidate in candidates}
    by_signature: dict[tuple[tuple[str, str], ...], dict[str, Any]] = {}
    for item in raw_items:
        if not isinstance(item, dict):
            raise SearchError("each candidate_metrics item must be a mapping")
        values = item.get("values")
        metrics = item.get("metrics")
        if not isinstance(values, dict) or not isinstance(metrics, dict):
            raise SearchError("candidate_metrics items require values and metrics mappings")
        normalized_values = {str(key): normalize_value(value) for key, value in values.items()}
        if set(normalized_values) != set(ordered_keys):
            raise SearchError(
                "candidate_metrics values must exactly match search parameter keys: "
                f"{sorted(normalized_values)} vs {sorted(ordered_keys)}"
            )
        signature = candidate_signature(normalized_values, ordered_keys)
        if signature not in known_signatures:
            raise SearchError(f"candidate_metrics item does not match generated search space: {signature}")
        if signature in by_signature:
            raise SearchError(f"duplicate candidate_metrics item for {signature}")
        by_signature[signature] = metrics
    missing = sorted(set(known_signatures) - set(by_signature))
    if missing:
        raise SearchError(f"evaluation candidate_metrics missing {len(missing)} generated candidates")
    return mode, by_signature


def metric_value(metrics: dict[str, Any], benchmark: str, metric: str) -> float:
    bench_metrics = metrics.get(benchmark)
    if not isinstance(bench_metrics, dict) or metric not in bench_metrics:
        raise SearchError(f"evaluation metrics missing {benchmark}.{metric}")
    try:
        return float(bench_metrics[metric])
    except (TypeError, ValueError) as exc:
        raise SearchError(f"evaluation metric {benchmark}.{metric} is not numeric") from exc


def round_metric(value: float) -> float:
    return round(value, 6)


def score_candidates(
    candidates: list[dict[str, Any]],
    metrics_by_signature: dict[tuple[tuple[str, str], ...], dict[str, Any]],
    targets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    weight_sum = sum(target["weight"] for target in targets)
    scored: list[dict[str, Any]] = []
    for candidate in candidates:
        metrics = metrics_by_signature[candidate["signature"]]
        metric_errors: list[dict[str, Any]] = []
        weighted_error_sum = 0.0
        for target in targets:
            simulated = metric_value(metrics, target["benchmark"], target["metric"])
            denom = max(abs(target["target"]), target["epsilon"])
            normalized_error = abs(simulated - target["target"]) / denom
            weighted_error = target["weight"] * normalized_error
            weighted_error_sum += weighted_error
            metric_errors.append(
                {
                    "benchmark": target["benchmark"],
                    "metric": target["metric"],
                    "target": round_metric(target["target"]),
                    "simulated": round_metric(simulated),
                    "weight": round_metric(target["weight"]),
                    "normalized_error": round_metric(normalized_error),
                    "weighted_error": round_metric(weighted_error),
                }
            )
        score = weighted_error_sum / weight_sum
        scored.append(
            {
                **candidate,
                "score": round_metric(score),
                "weighted_normalized_error": round_metric(score),
                "metrics": metrics,
                "metric_errors": metric_errors,
            }
        )
    scored.sort(key=lambda item: (item["score"], item["changed_key_count"], item["candidate_id"]))
    for rank, candidate in enumerate(scored, 1):
        candidate["rank"] = rank
    return scored


def planned_commands(
    manifest: dict[str, Any],
    ranked_candidates: list[dict[str, Any]],
    root: Path,
    limit: int,
) -> list[dict[str, Any]]:
    planning = manifest.get("planning", {})
    if not isinstance(planning, dict):
        raise SearchError("planning must be a mapping when present")
    if not planning:
        return []
    base_alias = str(planning.get("base_config_alias") or manifest["base"]["generated_config_alias"])
    if not SAFE_ALIAS_RE.match(base_alias):
        raise SearchError(f"planning base_config_alias must be a safe alias token: {base_alias!r}")
    benchmark_list = str(planning.get("benchmark_list", ""))
    if not benchmark_list:
        raise SearchError("planning benchmark_list is required when planning is present")
    run_simulations = str(
        planning.get("run_simulations", "simulator-remodeled/util/job_launching/run_simulations.py")
    )
    run_directory = str(planning.get("run_directory", "sm120_s6_correlation_runs"))
    launcher = str(planning.get("launcher", "local"))
    launch_name_prefix = str(planning.get("launch_name_prefix", manifest["search_id"]))
    trace_dir = str(planning.get("trace_dir", ""))
    commands: list[dict[str, Any]] = []
    for candidate in ranked_candidates[:limit]:
        if candidate["deltas"].get("trace.config"):
            raise SearchError(
                "planned commands currently support only gpgpusim.config extra_params; "
                "trace.config candidate deltas require a reviewed temporary trace config"
            )
        token = f"S6CAND{candidate['rank']:04d}"
        extra_lines: list[str] = []
        for item in candidate["deltas"].get("gpgpusim.config", []):
            extra_lines.append(f"{item['key']} {item['value']}")
        command = [
            "python3",
            run_simulations,
            "-B",
            benchmark_list,
            "-C",
            f"{base_alias}-{token}",
            "-N",
            f"{launch_name_prefix}-{candidate['candidate_id']}",
            "-r",
            run_directory,
            "-l",
            launcher,
            "-n",
        ]
        if trace_dir:
            command.extend(["-T", trace_dir])
        commands.append(
            {
                "rank": candidate["rank"],
                "candidate_id": candidate["candidate_id"],
                "requires_manual_temporary_alias": True,
                "temporary_extra_params_alias": token,
                "temporary_config_yaml_snippet": {
                    token: {
                        "extra_params": "\n".join(extra_lines),
                    }
                },
                "command": command,
                "command_string": shlex.join(command),
                "note": (
                    "Plan only. The harness does not write define-standard-cfgs.yml "
                    "or launch this command."
                ),
            }
        )
    return commands


def check_output_target(path: Path, root: Path) -> None:
    resolved = path.resolve()
    for rel_dir in FORBIDDEN_OUTPUT_DIRS_REL:
        protected_dir = (root / rel_dir).resolve()
        try:
            resolved.relative_to(protected_dir)
        except ValueError:
            pass
        else:
            raise SearchError(f"refusing to write S6 report into protected config/calibration path: {path}")
    rel = "/" + display_path(path, root)
    for fragment in FORBIDDEN_OUTPUT_FRAGMENTS:
        if fragment in rel:
            raise SearchError(f"refusing to write S6 report into protected config/calibration path: {path}")


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    root = args.repo_root.resolve()
    manifest_path = resolve_path(str(args.manifest), root)
    schema_path = resolve_path(str(args.schema), root)
    contract_path = resolve_path(str(args.contract), root)
    manifest = load_yaml(manifest_path)
    schema = load_yaml(schema_path)
    if contract_path.is_file():
        contract = load_yaml(contract_path)
    else:
        raise SearchError(f"contract file does not exist: {contract_path}")

    validate_manifest_header(manifest, schema)
    base_paths = validate_generated_base_paths(manifest["base"], root)
    base_options = {file_name: active_option_map(path) for file_name, path in base_paths.items()}
    parameters = validate_search_space(manifest, schema, base_options)
    known_benchmarks = benchmark_ids(manifest)
    targets = target_metrics(manifest, known_benchmarks)

    search_id = str(manifest.get("search_id") or "sm120-correlation-search")
    candidates = generate_candidates(search_id, parameters)
    ordered_keys = [param["key"] for param in parameters]
    evaluation_mode, metrics_by_signature = evaluation_map(manifest, candidates, ordered_keys)
    ranked = score_candidates(candidates, metrics_by_signature, targets)
    command_limit = min(args.command_candidate_limit, len(ranked))
    want_planned_commands = args.emit_planned_commands or args.print_planned_commands
    commands = planned_commands(manifest, ranked, root, command_limit) if want_planned_commands else []
    best = ranked[0]
    fixture_only = bool(args.fixture_only or manifest.get("fixture_only") or evaluation_mode == "fixture")

    report = {
        "schema_version": 1,
        "schema_id": "sm120_correlation_search_report_v1",
        "search_id": search_id,
        "gpu": manifest["gpu"],
        "architecture": manifest.get("architecture", DEFAULT_ARCHITECTURE),
        "status": "draft_not_applied",
        "generated_at": args.generated_at or iso_utc_now(),
        "fixture_only": fixture_only,
        "search_harness": {
            "script": display_path(Path(__file__).resolve(), root),
            "script_sha256": sha256_file(Path(__file__).resolve()),
            "schema": display_path(schema_path, root),
            "schema_sha256": sha256_file(schema_path),
            "contract": display_path(contract_path, root),
            "contract_sha256": sha256_file(contract_path),
            "contract_schema_id": contract.get("schema_id"),
        },
        "repository": {
            "root": str(root),
            "git_commit": run_git(root, ["rev-parse", "HEAD"]) or "unknown",
        },
        "source_manifest": {
            "path": display_path(manifest_path, root),
            "sha256": sha256_file(manifest_path),
        },
        "base": {
            "generated_config_alias": manifest["base"]["generated_config_alias"],
            "profile": manifest["base"]["profile"],
            "gpgpusim_config": display_path(base_paths["gpgpusim.config"], root),
            "trace_config": display_path(base_paths["trace.config"], root),
            "active_key_counts": {file_name: len(options) for file_name, options in base_options.items()},
        },
        "summary": {
            "evaluation_mode": evaluation_mode,
            "candidate_strategy": manifest["search"]["candidate_strategy"],
            "candidate_count": len(candidates),
            "parameter_count": len(parameters),
            "benchmark_count": len(known_benchmarks),
            "target_metric_count": len(targets),
            "best_candidate_id": best["candidate_id"],
            "best_score": best["score"],
            "planned_command_count": len(commands),
        },
        "ranking_metric": {
            "name": "weighted_normalized_error",
            "formula": "sum(weight * abs(simulated - target) / max(abs(target), epsilon)) / sum(weight)",
            "lower_is_better": True,
        },
        "search_space": {
            "stage": manifest["search"]["stage"],
            "max_candidates": manifest["search"]["max_candidates"],
            "hard_candidate_limit": HARD_CANDIDATE_LIMIT,
            "parameters": parameters,
        },
        "benchmark_cases": manifest["benchmark_cases"],
        "target_metrics": targets,
        "ranked_candidates": [
            {
                "rank": candidate["rank"],
                "candidate_id": candidate["candidate_id"],
                "score": candidate["score"],
                "weighted_normalized_error": candidate["weighted_normalized_error"],
                "changed_key_count": candidate["changed_key_count"],
                "deltas": candidate["deltas"],
                "metrics": candidate["metrics"],
                "metric_errors": candidate["metric_errors"],
            }
            for candidate in ranked
        ],
        "planned_simulator_commands": commands,
        "handoff": {
            "s4_generator_status": "bootstrap-current-flat only; S6 reports are not consumed automatically",
            "result_policy": "draft_not_applied",
            "do_not_claim_calibrated": True,
            "do_not_apply_automatically": [
                "flat SM120 tested configs",
                "S4 generated tested-cfgs outputs",
                "calibration-results/<GPU>/latest.yaml",
            ],
            "next_step": (
                "After real simulator runs and reviewer approval, copy only selected owner-matched "
                "calibration_result entries into a staged delta or latest.yaml in a later stage."
            ),
        },
        "limitations": [
            "Synthetic fixture reports are only CI/local validation evidence.",
            "The harness does not run simulator workloads.",
            "The selected best candidate is a ranked draft, not an accepted hardware calibration.",
            "Search is limited to explicitly bounded calibration_result keys in one S5/S6 stage.",
        ],
    }
    return report


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path, help="S6 search manifest YAML.")
    parser.add_argument("--output", default="-", help="Report YAML output path, or '-' for stdout.")
    parser.add_argument("--repo-root", type=Path, default=repo_root_from_script(), help="Repository root.")
    parser.add_argument("--schema", default=DEFAULT_SCHEMA_REL, help="SM120 active-key schema.")
    parser.add_argument("--contract", default=DEFAULT_CONTRACT_REL, help="S6 contract file.")
    parser.add_argument("--generated-at", default="", help="Deterministic generated_at timestamp.")
    parser.add_argument("--fixture-only", action="store_true", help="Force fixture_only true in the report.")
    parser.add_argument(
        "--emit-planned-commands",
        action="store_true",
        help="Include plan-only run_simulations.py commands in the report.",
    )
    parser.add_argument(
        "--print-planned-commands",
        action="store_true",
        help="Print planned command strings after validation. Does not launch them.",
    )
    parser.add_argument(
        "--command-candidate-limit",
        type=int,
        default=8,
        help="Maximum ranked candidates to include in planned commands.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate, score, and optionally print planned commands without writing a report.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.command_candidate_limit <= 0:
        print("error: --command-candidate-limit must be positive", file=sys.stderr)
        return 1
    try:
        report = build_report(args)
        root = args.repo_root.resolve()
        if args.dry_run:
            summary = report["summary"]
            print(
                "validated "
                f"{report['search_id']} candidates={summary['candidate_count']} "
                f"best={summary['best_candidate_id']} score={summary['best_score']}"
            )
            if args.print_planned_commands:
                for item in report["planned_simulator_commands"]:
                    print(item["command_string"])
            return 0
        output = yaml.safe_dump(report, sort_keys=False, width=120)
        if args.output == "-":
            sys.stdout.write(output)
        else:
            output_path = resolve_path(args.output, root)
            check_output_target(output_path, root)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output)
        if args.print_planned_commands:
            for item in report["planned_simulator_commands"]:
                print(item["command_string"])
    except SearchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
