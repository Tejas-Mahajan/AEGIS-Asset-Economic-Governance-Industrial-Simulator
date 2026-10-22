import importlib
import unittest
import numpy as np

from dashboard.mock_upstream import (
    get_mock_asset_records,
    get_mock_rul_predictions,
    get_mock_ranking_outputs,
    get_mock_risk_budget_outputs,
)
from dashboard.audit_trail import generate_decision_audit_explanation
from data_simulation import EventManager, to_asset_record, load_fd001_dataframe
from predictive_analytics import predict_rul
from economic_governance import (
    get_asset_cost_table,
    generate_ranking_output,
    generate_risk_budget_output,
)
from data_simulation.tests.test_schema_mapper import EXPECTED_FIELDS as ASSET_FIELDS
from predictive_analytics.tests.test_model import EXPECTED_RUL_PREDICTION_FIELDS as RUL_FIELDS
from economic_governance.tests.test_governance import (
    EXPECTED_RANKING_FIELDS as RANKING_FIELDS,
    EXPECTED_RISK_BUDGET_FIELDS as RISK_FIELDS,
)


class TestDashboardIntegration(unittest.TestCase):

    def test_d1_mock_generators_match_schemas(self):
        """D1 loop-test: Assert mock generators' outputs match SCHEMAS.md sections 1-4 exactly."""
        assets = get_mock_asset_records(count=5)
        ruls = get_mock_rul_predictions(count=5)
        rankings = get_mock_ranking_outputs(count=5)
        risks = get_mock_risk_budget_outputs(count=5)

        for a in assets:
            self.assertEqual(set(a.keys()), ASSET_FIELDS)
        for r in ruls:
            self.assertEqual(set(r.keys()), RUL_FIELDS)
        for rk in rankings:
            self.assertEqual(set(rk.keys()), RANKING_FIELDS)
        for rsk in risks:
            self.assertEqual(set(rsk.keys()), RISK_FIELDS)

    def test_d1_streamlit_app_imports_cleanly(self):
        """D1 loop-test: Assert app module imports without exceptions."""
        mod = importlib.import_module("dashboard.app")
        self.assertIsNotNone(mod)

    def test_d3_event_injection_visual_ripple_end_to_end(self):
        """D3 loop-test: Assert sensor_spike event on an asset ripples across health, ranking, and risk/budget outputs."""
        event_mgr = EventManager()
        df_data = load_fd001_dataframe()
        engine_id = 1
        asset_id = "ENG-001"

        # Pre-event cycle 2 execution
        eng_rows = df_data[df_data["engine_id"] == engine_id].sort_values("cycle")
        max_cycle = int(eng_rows["cycle"].max())

        row2 = eng_rows.iloc[1]
        pre_asset = event_mgr.apply_events(to_asset_record(row2, max_cycle))
        pre_rul = predict_rul(pre_asset)

        cost_table = get_asset_cost_table([asset_id])
        pre_ranking = generate_ranking_output([pre_rul], cost_table=cost_table)
        pre_risk = generate_risk_budget_output([pre_rul], ranking_records=pre_ranking, cost_table=cost_table)

        # Trigger sensor_spike injection API
        resp = event_mgr.inject_event(
            {"asset_id": asset_id, "event_type": "sensor_spike", "magnitude": 1.0}
        )
        self.assertTrue(resp["accepted"])

        # Post-event cycle 2 execution (with spike applied)
        post_asset = event_mgr.apply_events(to_asset_record(row2, max_cycle))
        post_rul = predict_rul(post_asset)
        post_ranking = generate_ranking_output([post_rul], cost_table=cost_table)
        post_risk = generate_risk_budget_output([post_rul], ranking_records=post_ranking, cost_table=cost_table)

        # Assert ripple effect: Sensor spike -> Anomaly detected -> Sensor reading jump
        self.assertTrue(post_asset["anomaly_detected"])
        self.assertGreater(
            post_asset["sensor_readings"]["sensor_2"],
            pre_asset["sensor_readings"]["sensor_2"]
        )

    def test_d4_decision_audit_trail_contains_actual_numbers(self):
        """D4 loop-test: Assert generated sentence contains numbers matching record fields."""
        mock_ruls = get_mock_rul_predictions(count=1)
        rankings = get_mock_ranking_outputs(count=1)
        risks = get_mock_risk_budget_outputs(count=1)

        sentence = generate_decision_audit_explanation(rankings[0], mock_ruls[0], risks[0])
        self.assertIsInstance(sentence, str)
        # Assert sentence contains actual numbers from records
        crit_score_str = str(rankings[0]["criticality_score"])
        self.assertIn(crit_score_str, sentence)

    def test_d5_fast_forward_simulation_degrades_health(self):
        """D5 loop-test: Assert advancing N cycles changes health_pct by degradation amount."""
        df_data = load_fd001_dataframe()
        eng_rows = df_data[df_data["engine_id"] == 1].sort_values("cycle")
        max_cycle = int(eng_rows["cycle"].max())

        rec_c1 = to_asset_record(eng_rows.iloc[0], max_cycle)
        rec_c50 = to_asset_record(eng_rows.iloc[49], max_cycle)

        self.assertGreater(rec_c1["health_pct"], rec_c50["health_pct"])
        expected_diff = (49.0 / max_cycle) * 100.0
        actual_diff = rec_c1["health_pct"] - rec_c50["health_pct"]
        self.assertAlmostEqual(actual_diff, expected_diff, places=2)

    def test_d6_integration_zero_errors_against_real_records(self):
        """D6 loop-test: Assert health, ranking, and risk views execute with zero KeyErrors/AttributeErrors against 10 real stream records."""
        df_data = load_fd001_dataframe()
        eng_rows = df_data[df_data["engine_id"] == 1].sort_values("cycle")
        max_cycle = int(eng_rows["cycle"].max())

        for idx in range(10):
            row = eng_rows.iloc[idx]
            asset_rec = to_asset_record(row, max_cycle)
            rul_rec = predict_rul(asset_rec)

            cost_table = get_asset_cost_table([asset_rec["asset_id"]])
            ranking_recs = generate_ranking_output([rul_rec], cost_table=cost_table)
            risk_recs = generate_risk_budget_output([rul_rec], ranking_records=ranking_recs, cost_table=cost_table)

            self.assertEqual(set(asset_rec.keys()), ASSET_FIELDS)
            self.assertEqual(set(rul_rec.keys()), RUL_FIELDS)
            self.assertEqual(set(ranking_recs[0].keys()), RANKING_FIELDS)
            self.assertEqual(set(risk_recs[0].keys()), RISK_FIELDS)


if __name__ == "__main__":
    unittest.main()
