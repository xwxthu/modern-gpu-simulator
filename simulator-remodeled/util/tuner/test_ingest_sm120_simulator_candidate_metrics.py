#!/usr/bin/env python3
"""Focused tests for SM120 simulator candidate metric ingestion."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

import yaml


TUNER_DIR = Path(__file__).resolve().parent
REPO_ROOT = TUNER_DIR.parents[2]
if str(TUNER_DIR) not in sys.path:
    sys.path.insert(0, str(TUNER_DIR))

spec = importlib.util.spec_from_file_location(
    "ingest_sm120_simulator_candidate_metrics",
    TUNER_DIR / "ingest_sm120_simulator_candidate_metrics.py",
)
assert spec and spec.loader
ingest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ingest)


class SimulatorCandidateMetricIngestionTest(unittest.TestCase):
    def test_fixture_kernel_cycles_map_to_hardware_metric_names(self) -> None:
        stdout = (TUNER_DIR / "testdata/sm120_sim_candidate_stdout.txt").read_text()
        config = (TUNER_DIR / "testdata/sm120_sim_candidate_gpgpusim.config").read_text()
        core_mhz = ingest.core_clock_mhz_from_config(config)

        parsed = ingest.parse_simulator_stdout(stdout, {}, core_mhz)
        metrics = parsed["metrics"]

        self.assertEqual(core_mhz, 1320.0)
        self.assertEqual(parsed["application_passed"], True)
        self.assertEqual(len(parsed["kernels"]), 2)
        self.assertEqual(metrics["cuda_kernel_total_time_ms"], 0.15)
        self.assertEqual(metrics["cuda_kernel_avg_time_ms"], 0.075)
        self.assertEqual(metrics["cuda_kernel_bpnn_layerforward_cuda_total_time_ms"], 0.1)
        self.assertEqual(metrics["cuda_kernel_bpnn_adjust_weights_cuda_total_time_ms"], 0.05)
        self.assertNotIn("native_wall_time_seconds", metrics)

    def test_s6_readiness_blocks_missing_native_wall_time(self) -> None:
        entry = {
            "values": {"-latency_L0_to_L1": "39"},
            "metrics": {
                "backprop_4096": {
                    "cuda_kernel_total_time_ms": 0.15,
                    "cuda_kernel_avg_time_ms": 0.075,
                }
            },
        }
        template = {
            "status": "template_not_runnable",
            "target_metrics": [
                {"benchmark": "backprop_4096", "metric": "cuda_kernel_total_time_ms"},
                {"benchmark": "backprop_4096", "metric": "native_wall_time_seconds"},
            ],
            "search": {
                "stage": "rf_prefetch_remodeled_parameters",
                "candidate_strategy": "cartesian_product",
                "max_candidates": 0,
                "parameters": [],
            },
        }

        readiness = ingest.validate_s6_readiness(template, [entry], reviewed=True)

        self.assertFalse(readiness["ready"])
        self.assertIn("search_parameters_missing", readiness["blockers"])
        self.assertIn("search_max_candidates_not_positive", readiness["blockers"])
        self.assertIn("missing_target_metrics:1", readiness["blockers"])
        self.assertIn("input_template_status_template_not_runnable", readiness["blockers"])
        self.assertEqual(
            readiness["missing_target_metrics"],
            [{"entry": "entry_1", "benchmark": "backprop_4096", "metric": "native_wall_time_seconds"}],
        )

    def test_s6_readiness_blocks_duplicate_candidate_entries(self) -> None:
        entry = {
            "values": {"-latency_L0_to_L1": "39"},
            "metrics": {
                "backprop_4096": {
                    "cuda_kernel_total_time_ms": 0.15,
                }
            },
        }
        template = {
            "status": "draft_not_applied",
            "target_metrics": [
                {"benchmark": "backprop_4096", "metric": "cuda_kernel_total_time_ms"},
            ],
            "search": {
                "stage": "rf_prefetch_remodeled_parameters",
                "candidate_strategy": "cartesian_product",
                "max_candidates": 1,
                "parameters": [
                    {
                        "key": "-latency_L0_to_L1",
                        "values": [39],
                    }
                ],
            },
        }

        readiness = ingest.validate_s6_readiness(template, [entry, entry], reviewed=True)

        self.assertFalse(readiness["ready"])
        self.assertIn("entry_2_duplicate_candidate_signature", readiness["blockers"])
        self.assertIn("duplicate_candidate_metrics:1", readiness["blockers"])

    def test_s6_readiness_blocks_search_space_larger_than_max_candidates(self) -> None:
        entries = [
            {
                "values": {"-latency_L0_to_L1": "37"},
                "metrics": {"backprop_4096": {"cuda_kernel_total_time_ms": 0.14}},
            },
            {
                "values": {"-latency_L0_to_L1": "39"},
                "metrics": {"backprop_4096": {"cuda_kernel_total_time_ms": 0.15}},
            },
        ]
        template = {
            "status": "draft_not_applied",
            "target_metrics": [
                {"benchmark": "backprop_4096", "metric": "cuda_kernel_total_time_ms"},
            ],
            "search": {
                "stage": "rf_prefetch_remodeled_parameters",
                "candidate_strategy": "cartesian_product",
                "max_candidates": 1,
                "parameters": [
                    {
                        "key": "-latency_L0_to_L1",
                        "values": [37, 39],
                    }
                ],
            },
        }

        readiness = ingest.validate_s6_readiness(template, entries, reviewed=True)

        self.assertFalse(readiness["ready"])
        self.assertIn("search_space_exceeds_max_candidates:2>1", readiness["blockers"])

    def test_loaded_candidate_artifact_rejects_native_wall_time(self) -> None:
        artifact = {
            "candidate_id": "bad_candidate",
            "candidate_metrics_entry": {
                "values": {"-latency_L0_to_L1": "39"},
                "metrics": {
                    "backprop_4096": {
                        "native_wall_time_seconds": 0.38,
                    }
                },
            },
        }

        with self.assertRaisesRegex(ingest.IngestError, "native_wall_time_seconds"):
            ingest.normalize_candidate_entry(artifact)

    def test_s6_readiness_uses_s6_manifest_validation(self) -> None:
        template_path = TUNER_DIR / "testdata/sm120_sim_candidate_s6_template.yaml"
        template = yaml.safe_load(template_path.read_text())
        del template["target_metrics"][0]["target"]
        entry = {
            "values": {"-latency_L0_to_L1": "39"},
            "metrics": {
                "backprop_4096": {
                    "cuda_kernel_total_time_ms": 0.15,
                    "cuda_kernel_avg_time_ms": 0.075,
                    "cuda_kernel_bpnn_layerforward_cuda_total_time_ms": 0.1,
                    "cuda_kernel_bpnn_adjust_weights_cuda_total_time_ms": 0.05,
                }
            },
        }

        readiness = ingest.validate_s6_readiness(template, [entry], reviewed=True, root=REPO_ROOT)

        self.assertFalse(readiness["ready"])
        self.assertTrue(
            any(blocker.startswith("s6_validation_error:") for blocker in readiness["blockers"]),
            readiness["blockers"],
        )


if __name__ == "__main__":
    unittest.main()
