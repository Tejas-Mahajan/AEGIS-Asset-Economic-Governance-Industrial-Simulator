import os
import unittest
from datetime import datetime
from data_simulation.dataset import load_fd001_dataframe
from data_simulation.schema_mapper import to_asset_record, SELECTED_SENSORS

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "train_FD001.txt")
EXPECTED_FIELDS = {
    "asset_id",
    "asset_type",
    "cycle",
    "timestamp",
    "sensor_readings",
    "health_pct",
    "data_quality_flag",
    "anomaly_detected",
    "metadata",
}


class TestSchemaMapper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = load_fd001_dataframe(target_path=DATA_PATH)
        cls.max_cycles_per_engine = cls.df.groupby("engine_id")["cycle"].max().to_dict()

    def test_schema_field_names_exact_match(self):
        """Assert every field name matches SCHEMAS.md section 1 character-for-character."""
        sample_row = self.df.iloc[0]
        engine_id = int(sample_row["engine_id"])
        max_cycle = self.max_cycles_per_engine[engine_id]

        record = to_asset_record(sample_row, max_cycle)
        record_keys = set(record.keys())

        self.assertEqual(
            record_keys,
            EXPECTED_FIELDS,
            f"Field names mismatch. Expected: {EXPECTED_FIELDS}, Got: {record_keys}"
        )
        self.assertEqual(record["asset_type"], "physical")

    def test_health_pct_range(self):
        """Assert health_pct is always between 0 and 100 across all dataset rows."""
        for idx in [0, 50, 100, 191, 500, len(self.df) - 1]:
            row = self.df.iloc[idx]
            engine_id = int(row["engine_id"])
            max_cycle = self.max_cycles_per_engine[engine_id]
            record = to_asset_record(row, max_cycle)

            health = record["health_pct"]
            self.assertGreaterEqual(health, 0.0, f"health_pct below 0: {health}")
            self.assertLessEqual(health, 100.0, f"health_pct above 100: {health}")

    def test_valid_iso_8601_timestamp(self):
        """Assert timestamp is a valid ISO-8601 string."""
        sample_row = self.df.iloc[10]
        engine_id = int(sample_row["engine_id"])
        max_cycle = self.max_cycles_per_engine[engine_id]

        record = to_asset_record(sample_row, max_cycle)
        timestamp_str = record["timestamp"]

        # Parse ISO string to verify format
        try:
            # Handle ISO string ending with 'Z'
            clean_ts = timestamp_str.replace("Z", "+00:00")
            parsed_dt = datetime.fromisoformat(clean_ts)
            self.assertIsNotNone(parsed_dt)
        except ValueError as e:
            self.fail(f"timestamp '{timestamp_str}' is not a valid ISO-8601 string: {e}")

    def test_selected_sensors_subset(self):
        """Assert sensor_readings contains only the documented sensor subset."""
        sample_row = self.df.iloc[0]
        record = to_asset_record(sample_row, 200)
        sensors = record["sensor_readings"]

        self.assertEqual(set(sensors.keys()), set(SELECTED_SENSORS))
        for key, val in sensors.items():
            self.assertIsInstance(val, float)


if __name__ == "__main__":
    unittest.main()
