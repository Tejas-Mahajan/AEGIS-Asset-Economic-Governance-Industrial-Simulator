import unittest
from predictive_analytics.mock_generator import generate_mock_asset_records
from data_simulation.tests.test_schema_mapper import EXPECTED_FIELDS


class TestPredictiveMockGenerator(unittest.TestCase):

    def test_mock_generator_field_names_exact_match(self):
        """Assert the mock generator's output field names match SCHEMAS.md section 1 exactly."""
        mock_records = generate_mock_asset_records(count=5)
        self.assertEqual(len(mock_records), 5)

        for record in mock_records:
            record_keys = set(record.keys())
            self.assertEqual(
                record_keys,
                EXPECTED_FIELDS,
                f"Mock field names mismatch. Expected: {EXPECTED_FIELDS}, Got: {record_keys}"
            )
            self.assertEqual(record["asset_type"], "physical")
            self.assertIsInstance(record["sensor_readings"], dict)


if __name__ == "__main__":
    unittest.main()
