from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pipeline_leak_lab.detector import analyze_rows, extract_features, is_candidate_leak
from pipeline_leak_lab.simulator import SAMPLE_COUNT, generate_windows, write_windows
from pipeline_leak_lab.detector import run_analysis


class PipelineLeakLabTests(unittest.TestCase):
    def test_frequency_features_distinguish_leak_like_and_low_frequency_signal(self):
        low = [1.8 * __import__("math").sin(2 * __import__("math").pi * 4 * i / SAMPLE_COUNT) for i in range(SAMPLE_COUNT)]
        high = [1.0 * __import__("math").sin(2 * __import__("math").pi * 20 * i / SAMPLE_COUNT) for i in range(SAMPLE_COUNT)]
        self.assertGreater(extract_features(high)["high_frequency_energy_ratio"], 0.95)
        self.assertLess(extract_features(low)["high_frequency_energy_ratio"], 0.05)

    def test_detector_requires_high_frequency_signal_and_supporting_channel(self):
        leak_features = {"rms": 0.7, "high_frequency_energy_ratio": 0.99}
        tpi_features = {"rms": 1.6, "high_frequency_energy_ratio": 0.01}
        self.assertTrue(is_candidate_leak(leak_features, 0.4, 12.0)[0])
        self.assertFalse(is_candidate_leak(tpi_features, 0.0, 0.4)[0])
        self.assertFalse(is_candidate_leak(leak_features, 0.0, 0.0)[0])

    def test_generated_data_is_reproducible_and_report_files_are_written(self):
        self.assertEqual(generate_windows(8, 4), generate_windows(8, 4))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv_path = root / "synthetic_windows.csv"
            write_windows(csv_path, generate_windows(150, 5))
            metrics = run_analysis(csv_path, root / "reports")
            self.assertEqual(metrics["synthetic_windows"], 150)
            self.assertGreater(metrics["true_positive"], 0)
            self.assertTrue((root / "reports" / "leak_alarms.csv").exists())
            self.assertTrue((root / "reports" / "evaluation.json").exists())


if __name__ == "__main__":
    unittest.main()
