#!/usr/bin/env python3
"""Generate SM120 bootstrap configs from layered MVP inputs."""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

import yaml


GPU_CHOICES = ("RTX5070_TI", "RTX5060")
DEFAULT_PROFILE = "bootstrap"
CONFIG_NAME_RE = re.compile(r"^[A-Za-z0-9_][-A-Za-z0-9_]*$")


class ConfigError(RuntimeError):
    pass


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[3]


def load_yaml(path: Path) -> dict:
    with path.open() as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ConfigError(f"{path} did not load as a YAML mapping")
    return data


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def relpath(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def require_relative_to(path: Path, parent: Path, description: str) -> None:
    if not is_relative_to(path, parent):
        raise ConfigError(f"{description} must be under {parent}: {path}")


def validate_config_name(config_name: object) -> str:
    if not isinstance(config_name, str) or not config_name:
        raise ConfigError(f"invalid config_name {config_name!r}")
    config_path = Path(config_name)
    if config_path.is_absolute() or len(config_path.parts) != 1 or ".." in config_path.parts:
        raise ConfigError(f"config_name must be a single safe path component: {config_name!r}")
    if not CONFIG_NAME_RE.fullmatch(config_name):
        raise ConfigError(
            "config_name must match ^[A-Za-z0-9_][-A-Za-z0-9_]*$: "
            f"{config_name!r}"
        )
    return config_name


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


def default_manifest_timestamp(root: Path) -> str:
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch is None:
        epoch = run_git(root, ["show", "-s", "--format=%ct", "HEAD"])
    if epoch is not None:
        try:
            ts = _dt.datetime.fromtimestamp(int(epoch), tz=_dt.timezone.utc)
            return ts.isoformat().replace("+00:00", "Z")
        except ValueError:
            pass
    return "unknown"


def active_option_map(path: Path) -> dict[str, str]:
    options: dict[str, str] = {}
    for lineno, line in enumerate(path.read_text().splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not stripped.startswith("-"):
            continue
        parts = stripped.split(maxsplit=1)
        key = parts[0]
        value = parts[1] if len(parts) > 1 else ""
        if key in options:
            raise ConfigError(f"{path}:{lineno}: duplicate active option {key}")
        options[key] = value
    return options


def normalized_active_lines(path: Path) -> list[str]:
    lines: list[str] = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("-"):
            lines.append(re.sub(r"\s+", " ", stripped))
    return lines


def normalized_icnt_lines(path: Path) -> list[str]:
    lines: list[str] = []
    for line in path.read_text().splitlines():
        before_comment = line.split("//", 1)[0].strip()
        if before_comment:
            lines.append(re.sub(r"\s+", " ", before_comment))
    return lines


def xml_inventory(path: Path) -> list[dict[str, str]]:
    root = ET.parse(path).getroot()
    inventory: list[dict[str, str]] = []
    stack: list[tuple[ET.Element, str]] = [(root, root.tag)]
    while stack:
        elem, elem_path = stack.pop()
        if elem.tag in {"param", "stat"} and "name" in elem.attrib and "value" in elem.attrib:
            inventory.append(
                {
                    "path": elem_path,
                    "tag": elem.tag,
                    "name": elem.attrib["name"],
                    "value": elem.attrib["value"],
                }
            )
        child_counts: dict[str, int] = {}
        children = list(elem)
        for child in reversed(children):
            ident = child.attrib.get("id") or child.attrib.get("name") or child.tag
            base = f"{elem_path}/{child.tag}[@{ident}]"
            count = child_counts.get(base, 0)
            child_counts[base] = count + 1
            suffix = "" if count == 0 else f"[{count}]"
            stack.append((child, base + suffix))
    return sorted(inventory, key=lambda item: (item["path"], item["tag"], item["name"], item["value"]))


def owner_lookup(schema: dict, file_name: str) -> dict[str, str]:
    table = schema.get("active_option_key_owners", {}).get(file_name)
    if not isinstance(table, dict):
        raise ConfigError(f"schema missing active_option_key_owners for {file_name}")
    lookup: dict[str, str] = {}
    conflicts: dict[str, list[str]] = {}
    for owner, keys in table.items():
        for key in keys or []:
            if key in lookup:
                conflicts.setdefault(key, [lookup[key]]).append(owner)
            lookup[key] = owner
    if conflicts:
        details = ", ".join(f"{key}: {owners}" for key, owners in sorted(conflicts.items()))
        raise ConfigError(f"schema owner conflicts in {file_name}: {details}")
    return lookup


def validate_active_key_coverage(schema: dict, file_name: str, options: dict[str, str], profile: str) -> dict[str, str]:
    lookup = owner_lookup(schema, file_name)
    missing = sorted(set(options) - set(lookup))
    if missing:
        raise ConfigError(f"{file_name} active keys missing schema owners: {', '.join(missing)}")
    profile_policies = schema.get("profiles", {})
    if profile not in profile_policies:
        raise ConfigError(f"schema missing profile policy for {profile}")
    owners = schema.get("owners", {})
    key_owners = {key: lookup[key] for key in sorted(options)}
    for key, owner in key_owners.items():
        owner_policy = owners.get(owner)
        if not owner_policy:
            raise ConfigError(f"{file_name} key {key} uses unknown owner {owner}")
        if profile not in owner_policy.get("allowed_profiles", []):
            raise ConfigError(f"{file_name} key {key} owner {owner} is not allowed for profile {profile}")
    return key_owners


def compare_active(label: str, source: Path, generated: Path) -> None:
    src = normalized_active_lines(source)
    gen = normalized_active_lines(generated)
    if src != gen:
        raise ConfigError(f"{label} active golden diff failed for {source} vs {generated}")


def compare_icnt(source: Path, generated: Path) -> None:
    if normalized_icnt_lines(source) != normalized_icnt_lines(generated):
        raise ConfigError(f"icnt golden diff failed for {source} vs {generated}")


def compare_xml(source: Path, generated: Path) -> list[dict[str, str]]:
    src = xml_inventory(source)
    gen = xml_inventory(generated)
    if src != gen:
        raise ConfigError(f"XML active param/stat diff failed for {source} vs {generated}")
    return gen


def parse_pair(value: str, key: str) -> tuple[str, str]:
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 2:
        raise ConfigError(f"{key} expected latency,initiation pair, got {value!r}")
    return parts[0], parts[1]


def validate_latency_groups(schema: dict, gpgpu_opts: dict[str, str], trace_opts: dict[str, str]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    groups = schema.get("latency_groups", {})
    for group_name, rule in groups.items():
        if rule.get("drift_policy") != "same_value":
            continue
        glat_key = rule["gpgpusim_latency_key"]
        ginit_key = rule["gpgpusim_initiation_key"]
        trace_key = rule["trace_key"]
        missing = [key for key in (glat_key, ginit_key) if key not in gpgpu_opts]
        if trace_key not in trace_opts:
            missing.append(trace_key)
        if missing:
            raise ConfigError(f"latency group {group_name} missing keys: {', '.join(missing)}")
        tlat, tinit = parse_pair(trace_opts[trace_key], trace_key)
        if gpgpu_opts[glat_key] != tlat or gpgpu_opts[ginit_key] != tinit:
            raise ConfigError(
                f"latency group {group_name} drift: "
                f"{glat_key}={gpgpu_opts[glat_key]}, {ginit_key}={gpgpu_opts[ginit_key]}, "
                f"{trace_key}={trace_opts[trace_key]}"
            )
        result.append(
            {
                "group": group_name,
                "latency": tlat,
                "initiation": tinit,
                "policy": "same_value",
            }
        )
    return result


def ensure_no_power_default_added(options: dict[str, str], profile: str) -> None:
    if profile == "bootstrap" and "-power_simulation_enabled" in options:
        raise ConfigError("bootstrap output must not add -power_simulation_enabled")


def copy_file(source: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    lines = [line.rstrip(" \t\r") for line in source.read_text().splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    cleaned = "\n".join(lines)
    if cleaned:
        cleaned += "\n"
    with dest.open("w", newline="\n") as f:
        f.write(cleaned)


def input_hashes(paths: list[Path], root: Path) -> dict[str, str]:
    return {relpath(path, root): sha256_file(path) for path in paths}


def key_provenance(key_owners: dict[str, str], provenance: dict[str, dict]) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    for key, owner in key_owners.items():
        owner_provenance = provenance.get(owner, {})
        entries[key] = {
            "owner": owner,
            "source_type": owner_provenance.get("source_type", "unknown"),
            "confidence": owner_provenance.get("confidence", "unknown"),
        }
    return entries


def xml_provenance_items(xml_items: list[dict[str, str]], xml_provenance: dict) -> list[dict[str, str]]:
    source_type = xml_provenance.get("source_type", "unknown")
    confidence = xml_provenance.get("confidence", "unknown")
    return [
        {
            "path": item["path"],
            "tag": item["tag"],
            "name": item["name"],
            "owner": "calibration_result",
            "source_type": source_type,
            "confidence": confidence,
        }
        for item in xml_items
    ]


def source_file_set(overlay: dict, root: Path) -> dict[str, Path]:
    sources = overlay.get("bootstrap_source_files")
    if not isinstance(sources, dict):
        raise ConfigError(f"overlay {overlay.get('layer_id')} missing bootstrap_source_files")
    gpgpu_flat_root = (
        root / "simulator-remodeled/gpu-simulator/gpgpu-sim/configs/tested-cfgs"
    ).resolve()
    trace_flat_root = (root / "simulator-remodeled/gpu-simulator/configs/tested-cfgs").resolve()
    generated_roots = [
        (
            root / "simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated/tested-cfgs"
        ).resolve(),
        (root / "simulator-remodeled/gpu-simulator/configs/generated/tested-cfgs").resolve(),
    ]
    allowed_roots = {
        "gpgpusim_config": gpgpu_flat_root,
        "accelwattch_xml": gpgpu_flat_root,
        "icnt": gpgpu_flat_root,
        "trace_config": trace_flat_root,
    }
    missing_keys = sorted(set(allowed_roots) - set(sources))
    if missing_keys:
        raise ConfigError(f"overlay {overlay.get('layer_id')} missing source keys: {', '.join(missing_keys)}")
    resolved: dict[str, Path] = {}
    for name, raw_path in sources.items():
        if name not in allowed_roots:
            raise ConfigError(f"overlay {overlay.get('layer_id')} has unknown source key {name!r}")
        source_path = Path(raw_path)
        if source_path.is_absolute() or ".." in source_path.parts:
            raise ConfigError(f"source {name} must be a non-escaping repo-relative path: {raw_path!r}")
        candidate = (root / source_path).resolve()
        if not candidate.is_file():
            raise ConfigError(f"source {name} does not exist: {candidate}")
        require_relative_to(candidate, allowed_roots[name], f"source {name}")
        for generated_root in generated_roots:
            if is_relative_to(candidate, generated_root):
                raise ConfigError(f"source {name} must not come from generated configs: {candidate}")
        resolved[name] = candidate
    return resolved


def generated_roots(root: Path) -> dict[str, Path]:
    return {
        "gpgpusim": (
            root / "simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated/tested-cfgs"
        ).resolve(),
        "trace": (root / "simulator-remodeled/gpu-simulator/configs/generated/tested-cfgs").resolve(),
    }


def output_paths(root: Path, config_name: str) -> dict[str, Path]:
    safe_config_name = validate_config_name(config_name)
    roots = generated_roots(root)
    return {
        "gpgpusim_config": roots["gpgpusim"]
        / safe_config_name
        / "gpgpusim.config",
        "trace_config": roots["trace"]
        / safe_config_name
        / "trace.config",
        "accelwattch_xml": roots["gpgpusim"]
        / safe_config_name
        / "accelwattch_sass_sim.xml",
        "icnt": roots["gpgpusim"]
        / safe_config_name
        / "config_ampere_islip.icnt",
    }


def validate_output_safety(paths: dict[str, Path], root: Path) -> None:
    roots = generated_roots(root)
    expected_roots = {
        "gpgpusim_config": roots["gpgpusim"],
        "accelwattch_xml": roots["gpgpusim"],
        "icnt": roots["gpgpusim"],
        "trace_config": roots["trace"],
    }
    for name, path in paths.items():
        resolved = path.resolve()
        expected_root = expected_roots.get(name)
        if expected_root is None:
            raise ConfigError(f"unknown output key {name!r}")
        require_relative_to(resolved, expected_root, f"output {name}")


def mirrored_trace_path_ok(root: Path, gpgpu_path: Path, trace_path: Path) -> bool:
    gpgpu_cfg_root = root / "simulator-remodeled/gpu-simulator/gpgpu-sim"
    accel_cfg_root = root / "simulator-remodeled/gpu-simulator"
    suffix = gpgpu_path.relative_to(gpgpu_cfg_root)
    expected = accel_cfg_root / suffix.parent / "trace.config"
    return expected == trace_path


def build_manifest(
    *,
    root: Path,
    gpu: str,
    config_name: str,
    profile: str,
    timestamp: str,
    command: list[str],
    generated_paths: dict[str, Path],
    source_paths: dict[str, Path],
    layer_paths: list[Path],
    schema_path: Path,
    profile_path: Path,
    gpgpu_owners: dict[str, str],
    trace_owners: dict[str, str],
    gpgpu_opts: dict[str, str],
    trace_opts: dict[str, str],
    xml_items: list[dict[str, str]],
    latency_groups: list[dict[str, str]],
    overlay: dict,
    calibration: dict,
    base: dict,
) -> dict:
    git_commit = run_git(root, ["rev-parse", "HEAD"]) or "unknown"
    git_status = run_git(root, ["status", "--short", "--branch"]) or "unknown"
    script_path = Path(__file__).resolve()
    all_inputs = [script_path, schema_path, profile_path, *layer_paths, *source_paths.values()]
    provenance = {
        "sm120_base": base.get("provenance_by_owner", {}).get("sm120_base", {}),
        "gpu_overlay": overlay.get("provenance_by_owner", {}).get("gpu_overlay", {}),
        "calibration_result": calibration.get("provenance_by_owner", {}).get("calibration_result", {}),
        "accelwattch_xml": calibration.get("xml_provenance", {}),
        "icnt": base.get("icnt_provenance", {}),
    }
    manifest = {
        "schema_version": 1,
        "generator": {
            "script": relpath(script_path, root),
            "script_sha256": sha256_file(script_path),
            "command": command,
            "git_commit": git_commit,
            "timestamp": timestamp,
        },
        "repository": {
            "root": str(root),
            "git_commit": git_commit,
            "git_status_short_branch": git_status.splitlines(),
        },
        "selection": {
            "gpu": gpu,
            "config_name": config_name,
            "profile": profile,
            "calibration_id": calibration.get("calibration_id"),
            "layers": [
                base.get("layer_id"),
                overlay.get("layer_id"),
                calibration.get("calibration_id"),
                profile,
            ],
        },
        "input_hashes_sha256": input_hashes(all_inputs, root),
        "source_files": {name: relpath(path, root) for name, path in source_paths.items()},
        "outputs": {name: relpath(path, root) for name, path in generated_paths.items()},
        "provenance": provenance,
        "active_key_inventory": {
            "gpgpusim.config": {
                "count": len(gpgpu_opts),
                "owners": gpgpu_owners,
                "provenance_by_key": key_provenance(gpgpu_owners, provenance),
            },
            "trace.config": {
                "count": len(trace_opts),
                "owners": trace_owners,
                "provenance_by_key": key_provenance(trace_owners, provenance),
            },
        },
        "xml_inventory": {
            "accelwattch_sass_sim.xml": {
                "active_param_or_stat_count": len(xml_items),
                "owner": "calibration_result",
                "source_type": calibration.get("xml_provenance", {}).get("source_type"),
                "sha256": sha256_file(generated_paths["accelwattch_xml"]),
                "provenance_items": xml_provenance_items(xml_items, provenance["accelwattch_xml"]),
            },
        },
        "icnt_inventory": {
            "config_ampere_islip.icnt": {
                "owner": "sm120_base",
                "active_with_current_bootstrap": gpgpu_opts.get("-network_mode") == "1",
                "network_mode": gpgpu_opts.get("-network_mode"),
                "sha256": sha256_file(generated_paths["icnt"]),
            },
        },
        "validations": {
            "active_key_coverage": "pass",
            "owner_profile_policy": "pass",
            "golden_bootstrap_active_diff": "pass",
            "golden_xml_inventory_diff": "pass",
            "golden_icnt_non_comment_diff": "pass",
            "mirrored_trace_path": "pass",
            "bootstrap_implicit_power_default": "not_rendered",
            "latency_groups": latency_groups,
        },
        "compatibility": {
            "legacy_extra_params_policy": "unmanifested_override",
            "existing_flat_sm120_configs_modified": False,
        },
        "limitations": [
            "bootstrap-current-flat copies current flat values; it is not a new calibration result",
            "RTX5060 timing, memory, trace, and XML values remain inherited or placeholder until S5/S6",
            "power is not enabled or calibrated by the bootstrap profile",
        ],
    }
    return manifest


def write_manifest(path_base: Path, manifest: dict) -> None:
    path_base.mkdir(parents=True, exist_ok=True)
    yaml_path = path_base / "manifest.yaml"
    json_path = path_base / "manifest.json"
    with yaml_path.open("w") as f:
        yaml.safe_dump(manifest, f, sort_keys=False, width=120)
    with json_path.open("w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")


def generate_one(root: Path, gpu: str, profile: str, timestamp: str, command: list[str], check_only: bool) -> dict:
    if profile != DEFAULT_PROFILE:
        raise ConfigError("MVP generator currently supports only the bootstrap profile")

    layered_root = root / "simulator-remodeled/gpu-simulator/gpgpu-sim/configs/layered/sm120"
    trace_rules_path = root / "simulator-remodeled/gpu-simulator/configs/layered/sm120/trace-render-rules.yaml"
    schema_path = layered_root / "schema/sm120.schema.yaml"
    profile_path = layered_root / f"profiles/{profile}.yaml"
    base_path = layered_root / "base/SM120_BASE.yaml"
    overlay_path = layered_root / f"overlays/{gpu}.yaml"
    calibration_path = layered_root / f"calibration-results/{gpu}/bootstrap-current-flat.yaml"

    schema = load_yaml(schema_path)
    profile_data = load_yaml(profile_path)
    base = load_yaml(base_path)
    overlay = load_yaml(overlay_path)
    calibration = load_yaml(calibration_path)
    trace_rules = load_yaml(trace_rules_path)

    if profile_data.get("profile") != profile:
        raise ConfigError(f"profile file {profile_path} does not describe {profile}")
    if calibration.get("profile") != profile:
        raise ConfigError(f"calibration file {calibration_path} does not describe {profile}")
    if trace_rules.get("rendered_file") != "trace.config":
        raise ConfigError(f"unexpected trace render rules in {trace_rules_path}")

    config_name = overlay.get("config_name")
    if not config_name:
        raise ConfigError(f"overlay {overlay_path} missing config_name")
    source_paths = source_file_set(overlay, root)
    generated_paths = output_paths(root, config_name)
    validate_output_safety(generated_paths, root)
    if not mirrored_trace_path_ok(root, generated_paths["gpgpusim_config"], generated_paths["trace_config"]):
        raise ConfigError(f"generated trace path does not mirror gpgpusim path for {config_name}")

    if not check_only:
        for source_key, dest_key in [
            ("gpgpusim_config", "gpgpusim_config"),
            ("trace_config", "trace_config"),
            ("accelwattch_xml", "accelwattch_xml"),
            ("icnt", "icnt"),
        ]:
            copy_file(source_paths[source_key], generated_paths[dest_key])

    for path in generated_paths.values():
        if not path.is_file():
            raise ConfigError(f"generated output missing: {path}")

    gpgpu_opts = active_option_map(generated_paths["gpgpusim_config"])
    trace_opts = active_option_map(generated_paths["trace_config"])
    ensure_no_power_default_added(gpgpu_opts, profile)
    gpgpu_owners = validate_active_key_coverage(schema, "gpgpusim.config", gpgpu_opts, profile)
    trace_owners = validate_active_key_coverage(schema, "trace.config", trace_opts, profile)

    compare_active("gpgpusim.config", source_paths["gpgpusim_config"], generated_paths["gpgpusim_config"])
    compare_active("trace.config", source_paths["trace_config"], generated_paths["trace_config"])
    xml_items = compare_xml(source_paths["accelwattch_xml"], generated_paths["accelwattch_xml"])
    compare_icnt(source_paths["icnt"], generated_paths["icnt"])
    latency_groups = validate_latency_groups(schema, gpgpu_opts, trace_opts)

    layer_paths = [base_path, overlay_path, calibration_path, trace_rules_path]
    manifest = build_manifest(
        root=root,
        gpu=gpu,
        config_name=config_name,
        profile=profile,
        timestamp=timestamp,
        command=command,
        generated_paths=generated_paths,
        source_paths=source_paths,
        layer_paths=layer_paths,
        schema_path=schema_path,
        profile_path=profile_path,
        gpgpu_owners=gpgpu_owners,
        trace_owners=trace_owners,
        gpgpu_opts=gpgpu_opts,
        trace_opts=trace_opts,
        xml_items=xml_items,
        latency_groups=latency_groups,
        overlay=overlay,
        calibration=calibration,
        base=base,
    )

    if not check_only:
        write_manifest(generated_paths["gpgpusim_config"].parent, manifest)
        trace_manifest = {
            **manifest,
            "outputs": {
                "trace_config": manifest["outputs"]["trace_config"],
                "manifest_yaml": relpath(generated_paths["trace_config"].parent / "manifest.yaml", root),
                "manifest_json": relpath(generated_paths["trace_config"].parent / "manifest.json", root),
            },
            "note": "Trace-root mirror manifest. Full generated artifacts are recorded in the gpgpu-sim generated directory.",
        }
        write_manifest(generated_paths["trace_config"].parent, trace_manifest)
    return manifest


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gpu", choices=GPU_CHOICES, action="append", help="GPU overlay to generate. Defaults to both.")
    parser.add_argument("--profile", default=DEFAULT_PROFILE, help="Render profile. MVP supports bootstrap.")
    parser.add_argument("--repo-root", type=Path, default=repo_root_from_script(), help="Repository root.")
    parser.add_argument("--manifest-timestamp", help="Stable manifest timestamp. Defaults to SOURCE_DATE_EPOCH or HEAD commit time.")
    parser.add_argument("--check-only", action="store_true", help="Validate existing generated outputs without rewriting files.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = args.repo_root.resolve()
    timestamp = args.manifest_timestamp or default_manifest_timestamp(root)
    gpus = args.gpu or list(GPU_CHOICES)
    command = [Path(sys.argv[0]).as_posix(), *argv]
    try:
        manifests = [
            generate_one(root, gpu, args.profile, timestamp, command, args.check_only)
            for gpu in gpus
        ]
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for manifest in manifests:
        selection = manifest["selection"]
        print(
            "generated "
            f"{selection['config_name']} profile={selection['profile']} "
            f"gpgpu_keys={manifest['active_key_inventory']['gpgpusim.config']['count']} "
            f"trace_keys={manifest['active_key_inventory']['trace.config']['count']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
