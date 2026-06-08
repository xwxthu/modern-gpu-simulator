#!/usr/bin/env python3
"""Collect lightweight official-tool device info for SM120 calibration.

The script runs short NVIDIA tool queries either locally or through ssh and
writes every command's stdout, stderr, and return code to a local output
directory. It does not run benchmarks or simulator workloads.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Iterable


QUERY_GPU_COMMON = (
    "timestamp,index,name,uuid,pci.bus_id,driver_version,pstate,"
    "temperature.gpu,power.draw,power.limit,clocks.current.graphics,"
    "clocks.current.sm,clocks.current.memory,clocks.max.graphics,"
    "clocks.max.sm,clocks.max.memory,memory.total,memory.free,memory.used"
)

QUERY_GPU_COMPUTE_CAP = "index,name,uuid,pci.bus_id,compute_cap"


def default_output_root() -> Path:
    return Path(__file__).resolve().parent / "device_info"


def build_commands(device: str, include_metric_discovery: bool) -> list[tuple[str, str]]:
    commands = [
        ("date_iso", "date -Is"),
        ("hostname", "hostname"),
        ("uname", "uname -a"),
        ("nvidia_smi_L", "nvidia-smi -L"),
        ("nvidia_smi", f"nvidia-smi -i {device}"),
        ("nvidia_smi_q_xml", f"nvidia-smi -q -x -i {device}"),
        (
            "nvidia_smi_query_gpu_common",
            f"nvidia-smi -i {device} --query-gpu={QUERY_GPU_COMMON} "
            "--format=csv,noheader,nounits",
        ),
        (
            "nvidia_smi_query_gpu_compute_cap",
            f"nvidia-smi -i {device} --query-gpu={QUERY_GPU_COMPUTE_CAP} "
            "--format=csv,noheader,nounits",
        ),
        ("nvidia_smi_help_query_gpu", "nvidia-smi --help-query-gpu"),
        ("which_nvcc", "command -v nvcc"),
        ("nvcc_version", "nvcc --version"),
        ("nvcc_list_gpu_code", "nvcc --list-gpu-code"),
        ("which_ncu", "command -v ncu"),
        ("ncu_version", "ncu --version"),
        ("which_nsys", "command -v nsys"),
        ("nsys_version", "nsys --version"),
    ]
    if include_metric_discovery:
        commands.append(("ncu_query_metrics", f"ncu --query-metrics --devices {device}"))
    return commands


def run_command(
    command: str,
    remote: str | None,
    timeout: int,
    ssh_options: list[str],
) -> subprocess.CompletedProcess:
    if remote:
        argv = ["ssh", *ssh_options, remote, f"bash -lc {shlex.quote(command)}"]
    else:
        argv = ["bash", "-lc", command]
    return subprocess.run(
        argv,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def normalize_text(content: str | bytes | None) -> str:
    if content is None:
        return ""
    if isinstance(content, bytes):
        return content.decode("utf-8", errors="replace")
    return content


def write_text(path: Path, content: str | bytes | None) -> None:
    path.write_text(normalize_text(content), encoding="utf-8")


def collect(args: argparse.Namespace) -> int:
    timestamp = _dt.datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    target = args.remote or "local"
    run_dir = args.output_dir / f"{timestamp}-{target}-device{args.device}"
    run_dir.mkdir(parents=True, exist_ok=False)

    manifest: dict[str, object] = {
        "schema_version": 1,
        "generated_at": _dt.datetime.now().astimezone().isoformat(),
        "target": target,
        "remote": args.remote,
        "device": args.device,
        "timeout_seconds": args.timeout,
        "include_metric_discovery": args.include_metric_discovery,
        "commands": [],
    }

    command_entries: list[dict[str, object]] = []
    for command_id, command in build_commands(args.device, args.include_metric_discovery):
        stdout_name = f"{command_id}.stdout.txt"
        stderr_name = f"{command_id}.stderr.txt"
        entry: dict[str, object] = {
            "id": command_id,
            "command": command,
            "stdout": stdout_name,
            "stderr": stderr_name,
        }
        if args.dry_run:
            entry["returncode"] = None
            entry["skipped"] = True
            write_text(run_dir / stdout_name, "")
            write_text(run_dir / stderr_name, "")
        else:
            try:
                result = run_command(command, args.remote, args.timeout, args.ssh_option)
                entry["returncode"] = result.returncode
                entry["timed_out"] = False
                write_text(run_dir / stdout_name, result.stdout)
                write_text(run_dir / stderr_name, result.stderr)
            except subprocess.TimeoutExpired as exc:
                entry["returncode"] = None
                entry["timed_out"] = True
                write_text(run_dir / stdout_name, exc.stdout)
                write_text(run_dir / stderr_name, exc.stderr)
        command_entries.append(entry)

    manifest["commands"] = command_entries
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(run_dir)
    if args.strict and any(
        entry.get("returncode") not in (0, None) or entry.get("timed_out")
        for entry in command_entries
    ):
        return 1
    return 0


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Collect lightweight official NVIDIA tool output for SM120 "
            "calibration prerequisites."
        )
    )
    parser.add_argument(
        "--remote",
        help="Optional ssh target, for example dsp5060. If omitted, collect locally.",
    )
    parser.add_argument(
        "--device",
        default="0",
        help="nvidia-smi/Nsight device index to query. Default: 0.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_output_root(),
        help="Local output root. Default: util/hw_stats/device_info.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=90,
        help="Per-command timeout in seconds. Default: 90.",
    )
    parser.add_argument(
        "--ssh-option",
        action="append",
        default=[
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=15",
            "-o",
            "StrictHostKeyChecking=accept-new",
        ],
        help=(
            "Option passed to ssh when --remote is used. Repeat to add more. "
            "Defaults to noninteractive batch mode with a short connect timeout."
        ),
    )
    parser.add_argument(
        "--include-metric-discovery",
        action="store_true",
        help="Also run ncu --query-metrics. This is still lightweight but can be verbose.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Create the output directory and manifest without executing commands.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return nonzero if any executed command returns nonzero.",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str]) -> int:
    return collect(parse_args(argv))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
