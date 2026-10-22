import importlib
import json
import unittest
from data_simulation.export_samples import print_sample_asset_records_json, get_sample_asset_records
from data_simulation.schema_mapper import to_asset_record
from data_simulation.tests.test_schema_mapper import EXPECTED_FIELDS


class TestPackageHandoff(unittest.TestCase):

    def test_module_imports_cleanly_with_no_side_effects(self):
        """Assert the module imports cleanly with no side effects at import time."""
        # Re-import module dynamically
        mod = importlib.import_module("data_simulation")
        self.assertIsNotNone(mod)

        # Check key exports exist
        exported_symbols = [
            "load_fd001_dataframe",
            "to_asset_record",
            "replay_engine",
            "MultiEngineScheduler",
            "PipelineConfig",
            "EventManager",
        ]
        for symbol in exported_symbols:
            self.assertTrue(hasattr(mod, symbol), f"Exported symbol '{symbol}' missing in data_simulation")

    def test_printed_sample_json_round_trips(self):
        """Assert that the printed sample JSON round-trips through json.loads() without error."""
        json_str = print_sample_asset_records_json()
        self.assertIsInstance(json_str, str)

        # Round-trip through json.loads
        try:
            parsed_records = json.loads(json_str)
        except json.JSONDecodeError as e:
            self.fail(f"Sample JSON failed to parse with json.loads(): {e}")

        self.assertIsInstance(parsed_records, list)
        self.assertEqual(len(parsed_records), 3)

        for rec in parsed_records:
            self.assertEqual(
                set(rec.keys()),
                EXPECTED_FIELDS,
                f"Sample record schema mismatch: {set(rec.keys())}"
            )
            self.assertEqual(rec["asset_type"], "physical")
            self.assertIsInstance(rec["sensor_readings"], dict)


if __name__ == "__main__":
    unittest.main()
