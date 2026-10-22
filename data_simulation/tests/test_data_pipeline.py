import copy
import unittest
from data_simulation.data_pipeline import (
    inject_noise,
    inject_missing,
    detect_anomaly,
    PipelineConfig,
    process_record_pipeline,
)

SAMPLE_RECORD = {
    "asset_id": "ENG-001",
    "asset_type": "physical",
    "cycle": 10,
    "timestamp": "2026-01-01T10:00:00Z",
    "sensor_readings": {
        "sensor_2": 642.15,
        "sensor_3": 1589.70,
        "sensor_4": 1400.60,
        "sensor_7": 554.36,
        "sensor_11": 47.47,
        "sensor_12": 521.66,
        "sensor_15": 8.4195,
    },
    "health_pct": 95.0,
    "data_quality_flag": "ok",
    "anomaly_detected": False,
    "metadata": {},
}


class TestDataPipeline(unittest.TestCase):

    def test_inject_noise_rate_zero_unchanged(self):
        """Assert that with noise rate=0 the record is completely unchanged."""
        record = copy.deepcopy(SAMPLE_RECORD)
        noisy = inject_noise(record, rate=0.0)
        self.assertEqual(record, noisy)

    def test_inject_noise_rate_one_modifies_readings(self):
        """Assert that with noise rate=1.0 sensor readings are perturbed."""
        record = copy.deepcopy(SAMPLE_RECORD)
        noisy = inject_noise(record, rate=1.0, seed=42)
        self.assertNotEqual(record["sensor_readings"], noisy["sensor_readings"])

    def test_inject_missing_rate_zero_unchanged(self):
        """Assert that with missing rate=0 the record is completely unchanged."""
        record = copy.deepcopy(SAMPLE_RECORD)
        result = inject_missing(record, rate=0.0)
        self.assertEqual(record, result)
        self.assertEqual(result["data_quality_flag"], "ok")

    def test_inject_missing_rate_one_flag_fires(self):
        """Assert that with missing rate=1.0 data_quality_flag fires 'missing' and values drop."""
        record = copy.deepcopy(SAMPLE_RECORD)
        result = inject_missing(record, rate=1.0, seed=42)
        self.assertEqual(result["data_quality_flag"], "missing")
        for val in result["sensor_readings"].values():
            self.assertIsNone(val)

    def test_anomaly_detected_false_on_clean_sequence(self):
        """Assert that anomaly_detected is false on a clean synthetic sequence with no jumps."""
        history = []
        for c in range(1, 10):
            rec = copy.deepcopy(SAMPLE_RECORD)
            rec["cycle"] = c
            # Slight steady values around 642.0
            rec["sensor_readings"]["sensor_2"] = 642.0 + (c * 0.01)
            history.append(rec)

        current = copy.deepcopy(SAMPLE_RECORD)
        current["cycle"] = 10
        current["sensor_readings"]["sensor_2"] = 642.10

        result = detect_anomaly(current, history, n_std=3.0)
        self.assertFalse(
            result["anomaly_detected"],
            "Clean sequence without jumps falsely triggered anomaly_detected: True"
        )

    def test_anomaly_detected_true_on_spike(self):
        """Assert that anomaly_detected becomes true when a sensor value spikes beyond n_std."""
        history = []
        for c in range(1, 10):
            rec = copy.deepcopy(SAMPLE_RECORD)
            rec["cycle"] = c
            rec["sensor_readings"]["sensor_2"] = 642.0
            history.append(rec)

        current = copy.deepcopy(SAMPLE_RECORD)
        current["cycle"] = 10
        current["sensor_readings"]["sensor_2"] = 750.0  # Huge jump from 642.0

        result = detect_anomaly(current, history, n_std=3.0)
        self.assertTrue(
            result["anomaly_detected"],
            "Sensor spike failed to trigger anomaly_detected: True"
        )

    def test_pipeline_config_toggles(self):
        """Assert config flags can be toggled independently."""
        record = copy.deepcopy(SAMPLE_RECORD)
        cfg_clean = PipelineConfig(enable_noise=False, enable_missing=False, enable_anomaly=False)
        out_clean = process_record_pipeline(record, history=[], config=cfg_clean)
        self.assertEqual(out_clean["data_quality_flag"], "ok")
        self.assertFalse(out_clean["anomaly_detected"])

        cfg_missing = PipelineConfig(enable_missing=True, missing_rate=1.0)
        out_missing = process_record_pipeline(record, history=[], config=cfg_missing)
        self.assertEqual(out_missing["data_quality_flag"], "missing")


if __name__ == "__main__":
    unittest.main()
