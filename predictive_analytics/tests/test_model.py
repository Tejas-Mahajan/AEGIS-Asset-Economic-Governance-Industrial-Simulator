import math
import unittest
from predictive_analytics.mock_generator import generate_mock_asset_records
from predictive_analytics.model import RULPredictor, predict_rul, get_model_rmse

EXPECTED_RUL_PREDICTION_FIELDS = {
    "asset_id",
    "rul_cycles",
    "rul_cycles_confidence_low",
    "rul_cycles_confidence_high",
    "rul_days",
}


class TestPredictiveModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.predictor = RULPredictor()
        cls.rmse, cls.residual_std = cls.predictor.train()

    def test_b2_model_predictions_non_negative(self):
        """B2 loop-test: Assert predictions are non-negative for test records."""
        mock_records = generate_mock_asset_records(count=5)
        for record in mock_records:
            pred = self.predictor.predict_record(record)
            self.assertGreaterEqual(
                pred["rul_cycles"],
                0.0,
                f"RUL prediction is negative: {pred['rul_cycles']}"
            )

    def test_b3_model_rmse_finite_positive_float(self):
        """B3 loop-test: Assert model_rmse is a finite positive float, not NaN or None."""
        rmse = get_model_rmse()
        self.assertIsNotNone(rmse)
        self.assertFalse(math.isnan(rmse))
        self.assertFalse(math.isinf(rmse))
        self.assertGreater(rmse, 0.0)
        self.assertIsInstance(rmse, float)

    def test_b4_confidence_bands_valid_and_dynamic(self):
        """B4 loop-test: Assert confidence_low <= rul_cycles <= confidence_high and width varies across inputs."""
        rec_early = generate_mock_asset_records(count=1)[0]
        rec_early["cycle"] = 10

        rec_late = generate_mock_asset_records(count=1)[0]
        rec_late["cycle"] = 250

        pred_early = predict_rul(rec_early)
        pred_late = predict_rul(rec_late)

        # Assert confidence interval bounds
        for pred in [pred_early, pred_late]:
            low = pred["rul_cycles_confidence_low"]
            mid = pred["rul_cycles"]
            high = pred["rul_cycles_confidence_high"]
            self.assertLessEqual(low, mid, f"confidence_low ({low}) > rul_cycles ({mid})")
            self.assertLessEqual(mid, high, f"rul_cycles ({mid}) > confidence_high ({high})")

        # Assert interval width varies across inputs (cycle 10 vs cycle 250)
        width_early = pred_early["rul_cycles_confidence_high"] - pred_early["rul_cycles_confidence_low"]
        width_late = pred_late["rul_cycles_confidence_high"] - pred_late["rul_cycles_confidence_low"]
        self.assertNotEqual(
            width_early,
            width_late,
            "Confidence interval width should not be constant across different inputs"
        )

    def test_b5_output_schema_exact_match(self):
        """B5 loop-test: Assert output field names match SCHEMAS.md section 2 exactly and rul_days is null."""
        sample_rec = generate_mock_asset_records(count=1)[0]
        pred_record = predict_rul(sample_rec)

        self.assertEqual(
            set(pred_record.keys()),
            EXPECTED_RUL_PREDICTION_FIELDS,
            f"Fields mismatch: expected {EXPECTED_RUL_PREDICTION_FIELDS}, got {set(pred_record.keys())}"
        )
        self.assertIsNone(pred_record["rul_days"], "rul_days must be explicitly None")


if __name__ == "__main__":
    unittest.main()
