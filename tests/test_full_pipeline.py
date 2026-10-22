import time
import unittest

from data_simulation import (
    load_fd001_dataframe,
    to_asset_record,
    EventManager,
    PipelineConfig,
    process_record_pipeline,
)
from predictive_analytics import predict_rul
from economic_governance import (
    get_asset_cost_table,
    generate_ranking_output,
    generate_risk_budget_output,
)


class TestFullSystemPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Warm up RUL predictor model and load dataset once before timing the live ripple
        dummy_rec = {
            "asset_id": "ENG-000",
            "cycle": 1,
            "sensor_readings": {"sensor_2": 640.0},
            "health_pct": 100.0,
        }
        predict_rul(dummy_rec)
        load_fd001_dataframe()

    def test_full_pipeline_end_to_end_with_event_injection_ripple(self):
        """End-to-End Pipeline Check:

        data_simulation -> predictive_analytics -> economic_governance -> dashboard data.
        Triggers a sensor_spike event and asserts the full ripple through all modules.
        """
        start_time = time.time()
        event_mgr = EventManager()
        df_data = load_fd001_dataframe()

        asset_ids = [f"ENG-{i:03d}" for i in range(1, 6)]
        max_cycles_map = df_data.groupby("engine_id")["cycle"].max().to_dict()
        cost_table = get_asset_cost_table(asset_ids)

        # -------------------------------------------------------------
        # STEP 1: Pre-Event Execution (Cycle 10)
        # -------------------------------------------------------------
        pre_asset_records = []
        pre_rul_records = []
        for eng_id in range(1, 6):
            eng_rows = df_data[df_data["engine_id"] == eng_id].sort_values("cycle")
            max_c = max_cycles_map[eng_id]
            row_10 = eng_rows.iloc[9]  # Cycle 10

            rec = event_mgr.apply_events(to_asset_record(row_10, max_c))
            proc_rec = process_record_pipeline(
                rec, history=[], config=PipelineConfig(enable_anomaly=True)
            )
            pre_asset_records.append(proc_rec)

            rul_rec = predict_rul(proc_rec)
            pre_rul_records.append(rul_rec)

        pre_rankings = generate_ranking_output(pre_rul_records, cost_table=cost_table)
        pre_risks = generate_risk_budget_output(
            pre_rul_records, ranking_records=pre_rankings, cost_table=cost_table
        )

        pre_eng1_asset = next(r for r in pre_asset_records if r["asset_id"] == "ENG-001")
        pre_eng1_rul = next(r for r in pre_rul_records if r["asset_id"] == "ENG-001")
        pre_eng1_rank = next(r for r in pre_rankings if r["asset_id"] == "ENG-001")
        pre_eng1_risk = next(r for r in pre_risks if r["asset_id"] == "ENG-001")

        # -------------------------------------------------------------
        # STEP 2: Trigger Event Injection (sensor_spike magnitude=1.5 on ENG-001)
        # -------------------------------------------------------------
        resp = event_mgr.inject_event(
            {"asset_id": "ENG-001", "event_type": "sensor_spike", "magnitude": 1.5}
        )
        self.assertTrue(resp["accepted"])
        self.assertEqual(resp["affected_cycle"], 11)

        # -------------------------------------------------------------
        # STEP 3: Post-Event Execution (Cycle 11 with Event Applied)
        # -------------------------------------------------------------
        post_asset_records = []
        post_rul_records = []
        for eng_id in range(1, 6):
            eng_rows = df_data[df_data["engine_id"] == eng_id].sort_values("cycle")
            max_c = max_cycles_map[eng_id]
            row_11 = eng_rows.iloc[10]  # Cycle 11

            rec = event_mgr.apply_events(to_asset_record(row_11, max_c))
            proc_rec = process_record_pipeline(
                rec, history=[pre_eng1_asset], config=PipelineConfig(enable_anomaly=True)
            )
            post_asset_records.append(proc_rec)

            rul_rec = predict_rul(proc_rec)
            post_rul_records.append(rul_rec)

        post_rankings = generate_ranking_output(
            post_rul_records, cost_table=cost_table, asset_records=post_asset_records
        )
        post_risks = generate_risk_budget_output(
            post_rul_records, ranking_records=post_rankings, cost_table=cost_table
        )

        post_eng1_asset = next(r for r in post_asset_records if r["asset_id"] == "ENG-001")
        post_eng1_rul = next(r for r in post_rul_records if r["asset_id"] == "ENG-001")
        post_eng1_rank = next(r for r in post_rankings if r["asset_id"] == "ENG-001")
        post_eng1_risk = next(r for r in post_risks if r["asset_id"] == "ENG-001")

        elapsed = round(time.time() - start_time, 3)

        # -------------------------------------------------------------
        # STEP 4: Assert End-to-End Event Ripple
        # -------------------------------------------------------------
        # 1. Ripple completed within reasonable execution time (< 3 seconds)
        self.assertLess(elapsed, 3.0, f"Full pipeline ripple took too long: {elapsed}s")

        # 2. Asset Record: anomaly_detected became True and sensor reading jumped
        self.assertTrue(
            post_eng1_asset["anomaly_detected"],
            "ENG-001 anomaly_detected failed to trigger True after sensor_spike"
        )
        self.assertGreater(
            post_eng1_asset["sensor_readings"]["sensor_2"],
            pre_eng1_asset["sensor_readings"]["sensor_2"] * 1.5,
        )

        # 3. Criticality Score increased after event
        self.assertGreater(
            post_eng1_rank["criticality_score"],
            pre_eng1_rank["criticality_score"],
            "ENG-001 criticality_score did not increase after sensor_spike event"
        )

        # 4. Financial Risk (CVaR 95%) or Recommended Budget Allocation increased
        self.assertGreaterEqual(
            post_eng1_risk["cvar_95"],
            pre_eng1_risk["cvar_95"],
        )


if __name__ == "__main__":
    unittest.main()
