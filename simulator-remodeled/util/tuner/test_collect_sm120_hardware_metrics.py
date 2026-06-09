#!/usr/bin/env python3
"""Focused tests for SM120 hardware target metric collection."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


TUNER_DIR = Path(__file__).resolve().parent
REPO_ROOT = TUNER_DIR.parents[2]
if str(TUNER_DIR) not in sys.path:
    sys.path.insert(0, str(TUNER_DIR))

spec = importlib.util.spec_from_file_location(
    "collect_sm120_hardware_metrics",
    TUNER_DIR / "collect_sm120_hardware_metrics.py",
)
assert spec and spec.loader
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


class HardwareTargetMetricPolicyTest(unittest.TestCase):
    def test_native_wall_time_is_characterization_not_s6_target(self) -> None:
        args = collector.parse_args(
            [
                "--gpu",
                "RTX5060",
                "--repo-root",
                str(REPO_ROOT),
                "--stdout",
                "simulator-remodeled/util/tuner/testdata/sm120_hardware_backprop_stdout.txt",
                "--time-output",
                "simulator-remodeled/util/tuner/testdata/sm120_hardware_backprop_time.txt",
                "--nsys-kernel-csv",
                "simulator-remodeled/util/tuner/testdata/sm120_hardware_backprop_nsys_kernel_sum.txt",
                "--nvidia-smi-query",
                "simulator-remodeled/util/tuner/testdata/sm120_hardware_backprop_nvidia_smi.txt",
                "--collection-host",
                "fixture",
                "--source-label",
                "fixture",
                "--collection-command",
                "fixture native command",
                "--target-id",
                "fixture-sm120-backprop-hardware-target",
                "--generated-at",
                "2026-06-09T00:00:00Z",
                "--fixture-only",
                "--output",
                "/tmp/unused.yaml",
            ]
        )

        result = collector.build_result(args)
        by_metric = {item["metric"]: item for item in result["target_metrics"]}
        handoff_metrics = {
            item["metric"] for item in result["s6_supplied_metrics_handoff"]["target_metrics"]
        }

        self.assertIn("native_wall_time_seconds", by_metric)
        self.assertEqual(
            by_metric["native_wall_time_seconds"]["metric_role"],
            collector.METRIC_ROLE_HARDWARE_CHARACTERIZATION,
        )
        self.assertFalse(by_metric["native_wall_time_seconds"]["include_in_s6_template"])
        self.assertNotIn("native_wall_time_seconds", handoff_metrics)

        self.assertIn("cuda_kernel_total_time_ms", handoff_metrics)
        self.assertEqual(
            by_metric["cuda_kernel_total_time_ms"]["metric_role"],
            collector.METRIC_ROLE_SIMULATOR_COMPARABLE_CALIBRATION_TARGET,
        )
        self.assertNotIn("cuda_kernel_invocations", handoff_metrics)


if __name__ == "__main__":
    unittest.main()
