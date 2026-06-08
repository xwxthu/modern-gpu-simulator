#!/usr/bin/env python3
"""Dry-run checker and command planner for SM120 S7 validation."""

from __future__ import annotations

import argparse
from pathlib import Path
import shlex
import sys
from typing import Iterable

import yaml


GPU_CHOICES = ("RTX5060", "RTX5070_TI")
DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RUN_ID = "rtx5060-s7-YYYYMMDD-HHMMSS"


class CheckError(RuntimeError):
    pass


def rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def require_file(path: Path, root: Path, label: str) -> None:
    if not path.is_file():
        raise CheckError(f"missing {label}: {rel(path, root)}")


def require_dir(path: Path, root: Path, label: str) -> None:
    if not path.is_dir():
        raise CheckError(f"missing {label}: {rel(path, root)}")


def load_yaml(path: Path) -> dict:
    with path.open() as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise CheckError(f"{rel(path, DEFAULT_REPO_ROOT)} did not load as a YAML mapping")
    return data


def config_alias(gpu: str) -> str:
    return "RTX5070_TI_SM120_GEN" if gpu == "RTX5070_TI" else "RTX5060_SM120_GEN"


def config_dir(gpu: str) -> str:
    return "SM120_RTX5070_TI" if gpu == "RTX5070_TI" else "SM120_RTX5060"


def check_repo_files(root: Path, gpu: str) -> list[str]:
    required_files = {
        "S3 official-tool collector": root / "simulator-remodeled/util/hw_stats/collect_sm120_device_info.py",
        "S5 parser": root / "simulator-remodeled/util/tuner/parse_sm120_microbench.py",
        "S6 correlation harness": root / "simulator-remodeled/util/tuner/search_sm120_correlation.py",
        "S4 generator": root / "simulator-remodeled/util/tuner/generate_sm120_configs.py",
        "S7 runbook": root / "docs/sm120-calibration/s7-validation-runbook.md",
        "S7 manifest template": root / "docs/sm120-calibration/s7-validation-manifest-template.yaml",
        "S6 fixture manifest": root / "simulator-remodeled/util/tuner/testdata/sm120_correlation_search_fixture.yaml",
        "S5 sample output": root / "simulator-remodeled/util/tuner/testdata/sm120_microbench_sample.txt",
        "job launcher": root / "simulator-remodeled/util/job_launching/run_simulations.py",
        "job config aliases": root / "simulator-remodeled/util/job_launching/configs/define-standard-cfgs.yml",
        "tuner Makefile": root / "simulator-remodeled/util/tuner/GPU_Microbenchmark/Makefile",
        "tuner run_all.sh": root / "simulator-remodeled/util/tuner/GPU_Microbenchmark/run_all.sh",
    }
    for label, path in required_files.items():
        require_file(path, root, label)

    generated_gpgpu = (
        root
        / "simulator-remodeled/gpu-simulator/gpgpu-sim/configs/generated/tested-cfgs"
        / config_dir(gpu)
    )
    generated_trace = root / "simulator-remodeled/gpu-simulator/configs/generated/tested-cfgs" / config_dir(gpu)
    require_dir(generated_gpgpu, root, f"{gpu} generated GPGPU-Sim config directory")
    require_dir(generated_trace, root, f"{gpu} generated trace config directory")
    require_file(generated_gpgpu / "gpgpusim.config", root, f"{gpu} generated gpgpusim.config")
    require_file(generated_trace / "trace.config", root, f"{gpu} generated trace.config")

    aliases = load_yaml(required_files["job config aliases"])
    alias = config_alias(gpu)
    if alias not in aliases:
        raise CheckError(f"missing generated job-launch alias {alias}")
    base_file = str(aliases[alias].get("base_file", ""))
    expected_fragment = f"configs/generated/tested-cfgs/{config_dir(gpu)}/gpgpusim.config"
    if expected_fragment not in base_file:
        raise CheckError(f"alias {alias} does not point at generated SM120 config: {base_file}")

    return [
        f"found {gpu} generated config alias {alias}",
        f"found generated config directory {rel(generated_gpgpu, root)}",
        f"found generated trace directory {rel(generated_trace, root)}",
    ]


def command(argv: list[str]) -> str:
    return shlex.join(argv)


def print_section(title: str, commands: Iterable[str]) -> None:
    print(f"\n## {title}")
    for item in commands:
        print(item)


def planned_commands(args: argparse.Namespace, root: Path) -> dict[str, list[str]]:
    artifact_root = args.artifact_root.rstrip("/")
    run_id = args.run_id
    gpu = args.gpu
    alias = config_alias(gpu)
    hw_def = "SM120_RTX5070_TI" if gpu == "RTX5070_TI" else "SM120_RTX5060"
    microbench_name = f"sm120-{gpu.lower().replace('_', '-')}-microbench.txt"
    draft_name = f"{gpu}-real-microbench-draft.yaml"
    smoke_bench = args.smoke_benchmark
    trace_dir = args.trace_dir

    local_prep = [
        "cd " + shlex.quote(str(root)),
        command(["python3", "simulator-remodeled/util/tuner/generate_sm120_configs.py", "--check-only"]),
        command(
            [
                "python3",
                "simulator-remodeled/util/tuner/search_sm120_correlation.py",
                "--manifest",
                "simulator-remodeled/util/tuner/testdata/sm120_correlation_search_fixture.yaml",
                "--dry-run",
                "--print-planned-commands",
                "--command-candidate-limit",
                "2",
            ]
        ),
    ]

    hardware_collect = [
        "# Run from local shell; output is written locally, command execution happens through ssh.",
        command(
            [
                "python3",
                "simulator-remodeled/util/hw_stats/collect_sm120_device_info.py",
                "--remote",
                args.hardware_host,
                "--device",
                args.device,
            ]
        ),
        "# Copy only the tuner subtree to a temporary directory on the hardware host.",
        "tar --exclude 'bin' --exclude '*.o' -czf /tmp/sm120-tuner-src.tgz "
        "-C simulator-remodeled/util/tuner GPU_Microbenchmark",
        command(["scp", "/tmp/sm120-tuner-src.tgz", f"{args.hardware_host}:/tmp/"]),
        command(
            [
                "ssh",
                args.hardware_host,
                (
                    "set -e; "
                    "rm -rf /tmp/sm120-tuner-collection; "
                    "mkdir -p /tmp/sm120-tuner-collection; "
                    "tar -xzf /tmp/sm120-tuner-src.tgz -C /tmp/sm120-tuner-collection; "
                    "cd /tmp/sm120-tuner-collection/GPU_Microbenchmark; "
                    f"make CUDA_PATH={args.cuda_path} CUDA_ARCH=sm_120 HW_DEF={hw_def}; "
                    f"./run_all.sh > {microbench_name} 2>&1"
                ),
            ]
        ),
        command(["mkdir", "-p", f"{artifact_root}/{run_id}"]),
        command(
            [
                "scp",
                f"{args.hardware_host}:/tmp/sm120-tuner-collection/GPU_Microbenchmark/{microbench_name}",
                f"{artifact_root}/{run_id}/{microbench_name}",
            ]
        ),
    ]

    local_parse = [
        command(
            [
                "python3",
                "simulator-remodeled/util/tuner/parse_sm120_microbench.py",
                "--input",
                f"{artifact_root}/{run_id}/{microbench_name}",
                "--output",
                f"{artifact_root}/{run_id}/{draft_name}",
                "--gpu",
                gpu,
                "--source-type",
                "microbenchmark",
                "--source-label",
                f"{args.hardware_host}-run-all",
                "--collection-host",
                args.hardware_host,
                "--collection-command",
                f"./run_all.sh > {microbench_name} 2>&1",
            ]
        )
    ]

    smoke_common = [
        "export CUDA_INSTALL_PATH=${CUDA_INSTALL_PATH:-" + args.cuda_path + "}",
        "source simulator-remodeled/gpu-simulator/setup_environment_no_git.sh release",
        "source simulator-remodeled/gpu-app-collection/src/setup_environment",
    ]
    smoke_plan = [
        *smoke_common,
        command(
            [
                "python3",
                "simulator-remodeled/util/job_launching/run_simulations.py",
                "-B",
                smoke_bench,
                "-C",
                alias,
                "-N",
                f"{run_id}-smoke-plan",
                "-r",
                f"{artifact_root}/{run_id}/sim-smoke-plan",
                "-l",
                "local",
                "-n",
            ]
            + (["-T", trace_dir] if trace_dir else [])
        ),
    ]
    hardware_section_title = f"{args.hardware_host} collection plan"
    if gpu != "RTX5060" and not args.include_hardware_plan:
        hardware_section_title = "hardware collection plan"
        hardware_collect = [
            "# RTX5070Ti compatibility checks are config/alias checks by default.",
            "# Do not run hardware collection unless RTX5070Ti hardware is explicitly available.",
            "# Re-run with --include-hardware-plan --hardware-host <rtx5070ti-host> to print that plan.",
        ]
        local_parse = [
            "# Not planned by default for RTX5070Ti compatibility; no RTX5070Ti hardware evidence was requested.",
        ]
    smoke_run = [
        *smoke_common,
        "# Local strong server only. Remove -n only after the setup-only plan is reviewed.",
        command(
            [
                "python3",
                "simulator-remodeled/util/job_launching/run_simulations.py",
                "-B",
                smoke_bench,
                "-C",
                alias,
                "-N",
                f"{run_id}-smoke",
                "-r",
                f"{artifact_root}/{run_id}/sim-smoke",
                "-l",
                "local",
                "-c",
                args.local_cores,
            ]
            + (["-T", trace_dir] if trace_dir else [])
        ),
    ]
    compat = [
        command(["python3", "simulator-remodeled/util/tuner/generate_sm120_configs.py", "--check-only"]),
        command(
            [
                "python3",
                str(Path(__file__).relative_to(root)),
                "--gpu",
                "RTX5070_TI",
                "--run-id",
                "rtx5070ti-compat-plan",
                "--no-command-plan",
            ]
        ),
    ]
    return {
        "local repository checks": local_prep,
        hardware_section_title: hardware_collect,
        "local S5 parsing": local_parse,
        "local smoke setup-only plan": smoke_plan,
        "local smoke run command": smoke_run,
        "RTX5070Ti compatibility checks": compat,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--gpu", choices=GPU_CHOICES, default="RTX5060")
    parser.add_argument("--hardware-host", default="dsp5060")
    parser.add_argument("--device", default="0")
    parser.add_argument("--cuda-path", default="/usr/local/cuda-13.2")
    parser.add_argument("--artifact-root", default="artifacts/s7")
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--smoke-benchmark", default="rodinia_2.0-ft:backprop-rodinia-2.0-ft:0")
    parser.add_argument("--trace-dir", default="", help="Optional trace root for trace-driven smoke planning.")
    parser.add_argument("--local-cores", default="4")
    parser.add_argument(
        "--include-hardware-plan",
        action="store_true",
        help="Print hardware collection commands for non-RTX5060 GPUs only when matching hardware is explicitly available.",
    )
    parser.add_argument(
        "--no-command-plan",
        action="store_true",
        help="Only check required files and aliases; do not print planned commands.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Default mode. Kept explicit to show this checker never launches work.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = args.repo_root.resolve()
    try:
        require_dir(root, root, "repository root")
        checks = check_repo_files(root, args.gpu)
    except CheckError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print("SM120 S7 validation dry-run checker")
    print(f"repo_root: {root}")
    print(f"gpu: {args.gpu}")
    print("mode: dry-run; no ssh, no hardware command, no simulator launch")
    for item in checks:
        print(f"check: {item}")

    if not args.no_command_plan:
        for title, commands in planned_commands(args, root).items():
            print_section(title, commands)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
