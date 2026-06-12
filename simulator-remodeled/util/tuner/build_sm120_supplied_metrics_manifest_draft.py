#!/usr/bin/env python3
"""Build a review-gated S7 supplied-metrics manifest draft.

This is intentionally not an S6 runnable manifest generator. It records the
current high-latency RTX5060 evidence slice and the approval gap that blocks
search_sm120_correlation.py.
"""

from __future__ import annotations

import argparse
import copy
import datetime as _dt
import hashlib
from pathlib import Path
import subprocess
from typing import Any

import yaml


FORBIDDEN_OUTPUT_PARTS = (
    "/configs/tested-cfgs/",
    "/configs/generated/",
    "/calibration-results/",
    "/accepted/",
    "/latest/",
    "/promotion",
    "/s6/",
)
EXPECTED_HIGH_LATENCY_SIGNATURES = (
    ("39", "8"),
    ("39", "10"),
)
SEARCH_KEYS = ("-latency_L0_to_L1", "-prefetch_per_stream_buffer_size")


class DraftError(RuntimeError):
    pass


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[3]


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise DraftError(f"{path} did not load as a YAML mapping")
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


def iso_utc_now() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_git(root: Path, args: list[str]) -> str:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def check_output_target(path: Path, root: Path) -> None:
    resolved = path.resolve()
    artifacts_s7 = (root / "artifacts/s7").resolve()
    try:
        resolved.relative_to(artifacts_s7)
    except ValueError as exc:
        raise DraftError(f"draft output must be under ignored artifacts/s7/: {path}") from exc
    rel = "/" + display_path(resolved, root)
    for part in FORBIDDEN_OUTPUT_PARTS:
        if part in rel:
            raise DraftError(f"refusing protected output path containing {part}: {path}")


def require_flags(data: dict[str, Any], path: Path, expected: dict[str, Any]) -> None:
    for key, value in expected.items():
        if data.get(key) != value:
            raise DraftError(f"{path} expected {key}={value!r}, got {data.get(key)!r}")


def source_record(path: Path, root: Path, schema_id: str | None = None) -> dict[str, Any]:
    return {
        "path": display_path(path, root),
        "sha256": sha256_file(path),
        "schema_id": schema_id,
    }


def metric_key(item: dict[str, Any]) -> tuple[str, str]:
    return (str(item["benchmark"]), str(item["metric"]))


def candidate_signature(values: dict[str, Any]) -> tuple[str, str]:
    try:
        return tuple(str(values[key]) for key in SEARCH_KEYS)  # type: ignore[return-value]
    except KeyError as exc:
        raise DraftError(f"candidate values missing {exc.args[0]}") from exc


def candidate_alias(signature: tuple[str, str]) -> str:
    return f"{signature[0]}/{signature[1]}"


def signature_sort_key(signature: tuple[str, str]) -> tuple[int, int]:
    return (int(signature[0]), int(signature[1]))


def build_manifest(args: argparse.Namespace) -> dict[str, Any]:
    root = args.repo_root.resolve()
    hardware_path = resolve_path(args.aggregate_hardware_target, root)
    candidate_paths = [resolve_path(path, root) for path in args.candidate_metrics]
    output_path = resolve_path(args.output, root)
    check_output_target(output_path, root)

    hardware = load_yaml(hardware_path)
    require_flags(
        hardware,
        hardware_path,
        {
            "status": "draft_not_applied",
            "aggregate_draft": True,
            "non_promotion": True,
            "promotion_quality": False,
            "hardware_target_metrics": True,
            "simulator_smoke_metrics": False,
        },
    )
    if hardware.get("gpu") != args.gpu:
        raise DraftError(f"hardware target GPU mismatch: {hardware.get('gpu')} vs {args.gpu}")
    handoff = hardware.get("s6_supplied_metrics_handoff")
    if not isinstance(handoff, dict):
        raise DraftError("aggregate hardware target missing s6_supplied_metrics_handoff")
    if handoff.get("ready_for_search_sm120_correlation") is not False:
        raise DraftError("aggregate hardware target handoff must remain not ready")
    target_metrics = handoff.get("target_metrics")
    if not isinstance(target_metrics, list) or not target_metrics:
        raise DraftError("aggregate hardware target handoff has no target metrics")
    target_by_key = {metric_key(item): item for item in target_metrics if isinstance(item, dict)}
    if len(target_by_key) != len(target_metrics):
        raise DraftError("aggregate hardware target handoff target metrics must be unique mappings")

    candidate_entries: list[dict[str, Any]] = []
    supplied_signatures: set[tuple[str, str]] = set()
    matched_keys: set[tuple[str, str]] | None = None
    for path in candidate_paths:
        data = load_yaml(path)
        require_flags(
            data,
            path,
            {
                "status": "draft_not_applied",
                "simulator_candidate_metrics": True,
                "hardware_target_metrics": False,
            },
        )
        if data.get("gpu") != args.gpu:
            raise DraftError(f"{path} GPU mismatch: {data.get('gpu')} vs {args.gpu}")
        observations = data.get("parsed_simulator_observations")
        if not isinstance(observations, dict) or observations.get("application_passed") is not True:
            raise DraftError(f"{path} lacks application_passed simulator evidence")
        entry = data.get("candidate_metrics_entry")
        if not isinstance(entry, dict):
            raise DraftError(f"{path} missing candidate_metrics_entry")
        values = entry.get("values")
        if not isinstance(values, dict):
            raise DraftError(f"{path} candidate_metrics_entry.values must be a mapping")
        signature = candidate_signature(values)
        if signature in supplied_signatures:
            raise DraftError(f"duplicate candidate signature {signature}")
        supplied_signatures.add(signature)

        metrics = entry.get("metrics")
        if not isinstance(metrics, dict):
            raise DraftError(f"{path} candidate_metrics_entry.metrics must be a mapping")
        current_keys: set[tuple[str, str]] = set()
        aligned_metrics: dict[str, dict[str, Any]] = {}
        for benchmark, benchmark_metrics in metrics.items():
            if not isinstance(benchmark_metrics, dict):
                raise DraftError(f"{path} metrics.{benchmark} must be a mapping")
            for metric, value in benchmark_metrics.items():
                key = (str(benchmark), str(metric))
                if key not in target_by_key:
                    continue
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise DraftError(f"{path} metric {benchmark}.{metric} is not numeric")
                aligned_metrics.setdefault(str(benchmark), {})[str(metric)] = value
                current_keys.add(key)
        if matched_keys is None:
            matched_keys = set(current_keys)
        elif matched_keys != current_keys:
            raise DraftError(f"{path} aligned metric names differ from prior candidates")
        if current_keys != set(target_by_key):
            missing = sorted(set(target_by_key) - current_keys)
            raise DraftError(f"{path} missing hardware target metric matches: {missing}")

        candidate_entries.append(
            {
                "candidate_id": data.get("candidate_id"),
                "canonical_s7_candidate_id": "candidate_0003"
                if signature == ("39", "8")
                else "candidate_0004"
                if signature == ("39", "10")
                else "unknown",
                "display_candidate_id": f"candidate_{candidate_alias(signature)}",
                "values": {key: str(values[key]) for key in SEARCH_KEYS},
                "metrics": aligned_metrics,
                "source_artifact": source_record(path, root, data.get("schema_id")),
                "source_label": data.get("source_label"),
                "procman_job": "486" if signature == ("39", "8") else "487" if signature == ("39", "10") else "unknown",
                "provenance": copy.deepcopy(entry.get("provenance", {})),
            }
        )

    expected_signatures = set(EXPECTED_HIGH_LATENCY_SIGNATURES)
    if supplied_signatures != expected_signatures:
        raise DraftError(
            f"expected high-latency signatures {sorted(expected_signatures)}, got {sorted(supplied_signatures)}"
        )

    comparable_metrics = [
        {
            **copy.deepcopy(target_by_key[key]),
            "candidate_values_present_for_all_supplied_candidates": True,
        }
        for key in sorted(target_by_key)
    ]

    candidate_entries.sort(key=lambda item: signature_sort_key(candidate_signature(item["values"])))
    return {
        "schema_version": 1,
        "schema_id": "sm120_s7_supplied_metrics_manifest_decision_draft_v1",
        "manifest_id": args.manifest_id,
        "gpu": args.gpu,
        "architecture": args.architecture,
        "status": "draft_not_applied",
        "review_required": True,
        "template_not_runnable": True,
        "s6_manifest_runnable": False,
        "non_promotion": True,
        "promotion_quality": False,
        "generated_at": args.generated_at or iso_utc_now(),
        "generator": {
            "script": "simulator-remodeled/util/tuner/build_sm120_supplied_metrics_manifest_draft.py",
            "script_sha256": sha256_file(Path(__file__).resolve()),
            "repository": {
                "root": str(root),
                "git_commit": run_git(root, ["rev-parse", "HEAD"]),
                "git_branch": run_git(root, ["rev-parse", "--abbrev-ref", "HEAD"]),
            },
        },
        "source_artifacts": {
            "aggregate_hardware_target": source_record(hardware_path, root, hardware.get("schema_id")),
            "simulator_candidate_metrics": [
                source_record(resolve_path(path, root), root, load_yaml(resolve_path(path, root)).get("schema_id"))
                for path in args.candidate_metrics
            ],
        },
        "search_space_decision": {
            "original_four_candidate_sweep_complete": False,
            "original_four_candidate_signatures": [
                {"-latency_L0_to_L1": "37", "-prefetch_per_stream_buffer_size": "8"},
                {"-latency_L0_to_L1": "37", "-prefetch_per_stream_buffer_size": "10"},
                {"-latency_L0_to_L1": "39", "-prefetch_per_stream_buffer_size": "8"},
                {"-latency_L0_to_L1": "39", "-prefetch_per_stream_buffer_size": "10"},
            ],
            "excluded_or_deprioritized_for_current_s7_pass": [
                {
                    "candidate_id": "candidate_0001",
                    "-latency_L0_to_L1": "37",
                    "-prefetch_per_stream_buffer_size": "8",
                    "reason": "no completion-quality simulator candidate metrics",
                },
                {
                    "candidate_id": "candidate_0002",
                    "-latency_L0_to_L1": "37",
                    "-prefetch_per_stream_buffer_size": "10",
                    "reason": "diagnostic-only evidence; no full benchmark result or candidate metrics",
                },
            ],
            "narrowed_high_latency_slice": {
                "requires_supervisor_approval_before_runnable_s6": True,
                "fixed_parameter": {"-latency_L0_to_L1": "39"},
                "varying_parameter": {
                    "key": "-prefetch_per_stream_buffer_size",
                    "values": ["8", "10"],
                },
                "candidate_count": 2,
                "candidate_signatures": [
                    {"-latency_L0_to_L1": left, "-prefetch_per_stream_buffer_size": right}
                    for left, right in sorted(EXPECTED_HIGH_LATENCY_SIGNATURES, key=signature_sort_key)
                ],
            },
        },
        "target_metrics": comparable_metrics,
        "evaluation": {
            "mode": "supplied_metrics",
            "candidate_metric_source_policy": (
                "draft local simulator candidate metrics aligned by exact metric names to aggregate hardware target metrics"
            ),
            "candidate_metrics": candidate_entries,
        },
        "readiness": {
            "ready_for_search_sm120_correlation": False,
            "s6_manifest_runnable": False,
            "blockers": [
                "narrowed_high_latency_search_space_not_supervisor_approved_as_runnable",
                "original_four_candidate_sweep_incomplete_low_latency_candidates_excluded",
                "artifact_is_review_required_template_not_runnable",
                "no_promotion_gate_review_or_rtx5070ti_compatibility_signoff",
            ],
            "required_approval_fields_before_any_runnable_conversion": {
                "supervisor_approved_narrowed_search_space": False,
                "reviewer_approved_exact_metric_alignment": False,
                "reviewer_approved_s6_manifest_conversion": False,
                "promotion_gate_approval": False,
                "rtx5070ti_compatibility_signoff": False,
            },
        },
        "handoff": {
            "do_not_run_search_sm120_correlation_as_is": True,
            "do_not_claim_calibrated": True,
            "do_not_promote_configs": True,
            "do_not_apply_automatically": [
                "flat tested configs",
                "generated tested-cfgs outputs",
                "calibration-results/latest",
                "S6 ranked reports",
                "promotion artifacts",
            ],
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=repo_root_from_script())
    parser.add_argument("--gpu", default="RTX5060")
    parser.add_argument("--architecture", default="SM120")
    parser.add_argument("--aggregate-hardware-target", required=True)
    parser.add_argument("--candidate-metrics", action="append", required=True)
    parser.add_argument("--manifest-id", required=True)
    parser.add_argument("--generated-at", default="")
    parser.add_argument("--output", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.repo_root.resolve()
    output_path = resolve_path(args.output, root)
    manifest = build_manifest(args)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        yaml.safe_dump(manifest, f, sort_keys=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
