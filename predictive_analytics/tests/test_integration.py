import json
import unittest
import numpy as np
from predictive_analytics.model_comparison import compare_models
from predictive_analytics.export_samples import print_sample_rul_predictions_json, get_sample_rul_prediction_records
from predictive_analytics.tests.test_model import EXPECTED_RUL_PREDICTION_FIELDS


class TestPredictiveIntegration(unittest.TestCase):

    def test_b6_apples_to_apples_rmse_comparison(self):
        """B6 loop-test: Assert comparison metrics are finite positive floats computed on identical split."""
        comparison = compare_models()
        self.assertIn("gradient_boosting_rmse", comparison)
        self.assertIn("random_forest_rmse", comparison)

        for name, rmse in comparison.items():
            self.assertIsInstance(rmse, float)
            self.assertGreater(rmse, 0.0)
            self.assertFalse(np.isnan(rmse))

    def test_b7_integration_with_real_simulation_stream(self):
        """B7 loop-test: Assert predict_rul output matches SCHEMAS.md section 2 running against real data_simulation stream."""
        sample_predictions = get_sample_rul_prediction_records(count=3)
        self.assertEqual(len(sample_predictions), 3)

        for record in sample_predictions:
            fields = set(record.keys())
            self.assertEqual(
                fields,
                EXPECTED_RUL_PREDICTION_FIELDS,
                f"Field name mismatch on real stream input: expected {EXPECTED_RUL_PREDICTION_FIELDS}, got {fields}"
            )
            self.assertIsNone(record["rul_days"])
            self.assertGreaterEqual(record["rul_cycles"], 0.0)
            self.assertLessEqual(record["rul_cycles_confidence_low"], record["rul_cycles"])
            self.assertLessEqual(record["rul_cycles"], record["rul_cycles_confidence_high"])

    def test_b7_printed_json_round_trip(self):
        """B7 loop-test: Assert sample RUL JSON round-trips through json.loads without error."""
        json_str = print_sample_rul_predictions_json()
        parsed = json.loads(json_str)
        self.assertEqual(len(parsed), 3)
        for item in parsed:
            self.assertEqual(set(item.keys()), EXPECTED_RUL_PREDICTION_FIELDS)


if __name__ == "__main__":
    unittest.main()
