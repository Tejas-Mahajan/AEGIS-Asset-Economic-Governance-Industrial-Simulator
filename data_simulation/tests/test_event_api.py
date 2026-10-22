import os
import unittest
from data_simulation.dataset import load_fd001_dataframe
from data_simulation.schema_mapper import to_asset_record
from data_simulation.event_api import EventManager, RESPONSE_FIELDS
from data_simulation.simulator import replay_engine

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "train_FD001.txt")


class TestEventAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = load_fd001_dataframe(target_path=DATA_PATH)

    def test_response_shape_matches_schemas_section_5(self):
        """Assert the response shape matches SCHEMAS.md section 5 exactly."""
        event_mgr = EventManager()
        req = {"asset_id": "ENG-001", "event_type": "sensor_spike", "magnitude": 0.25}
        resp = event_mgr.inject_event(req)

        self.assertEqual(
            set(resp.keys()),
            RESPONSE_FIELDS,
            f"Response fields mismatch. Expected {RESPONSE_FIELDS}, got {set(resp.keys())}"
        )
        self.assertTrue(resp["accepted"])
        self.assertEqual(resp["asset_id"], "ENG-001")
        self.assertIsInstance(resp["affected_cycle"], int)
        self.assertIsInstance(resp["message"], str)

    def test_sensor_spike_modifies_very_next_record(self):
        """Assert that after calling sensor_spike, the very next Asset Record shows measurably different sensor reading."""
        event_mgr = EventManager()
        engine_id = 1
        asset_id = f"ENG-{engine_id:03d}"

        # Fetch raw engine rows
        engine_rows = self.df[self.df["engine_id"] == engine_id].sort_values("cycle")
        max_cycle = int(engine_rows["cycle"].max())

        row1 = engine_rows.iloc[0]
        row2 = engine_rows.iloc[1]

        rec1 = event_mgr.apply_events(to_asset_record(row1, max_cycle))
        self.assertEqual(rec1["cycle"], 1)

        # Expected natural cycle 2 reading without injection
        natural_rec2 = to_asset_record(row2, max_cycle)
        natural_sensor2 = natural_rec2["sensor_readings"]["sensor_2"]

        # Call sensor_spike injection API
        injection_resp = event_mgr.inject_event(
            {"asset_id": asset_id, "event_type": "sensor_spike", "magnitude": 0.5}
        )
        self.assertTrue(injection_resp["accepted"])

        # Fetch Cycle 2 record via EventManager
        injected_rec2 = event_mgr.apply_events(natural_rec2)
        injected_sensor2 = injected_rec2["sensor_readings"]["sensor_2"]

        # Assert sensor reading is measurably higher (approx 1.5x of natural_sensor2)
        self.assertGreater(
            injected_sensor2,
            natural_sensor2,
            f"Injected sensor_2 ({injected_sensor2}) should be greater than natural sensor_2 ({natural_sensor2})"
        )
        self.assertAlmostEqual(injected_sensor2, natural_sensor2 * 1.5, places=3)
        self.assertTrue(injected_rec2["anomaly_detected"])

    def test_manual_failure_event_sets_health_zero(self):
        """Assert manual_failure event drops health_pct to 0 and flags anomaly."""
        event_mgr = EventManager()
        asset_id = "ENG-002"
        event_mgr.update_latest_cycle(asset_id, 5)

        event_mgr.inject_event({"asset_id": asset_id, "event_type": "manual_failure", "magnitude": 1.0})

        sample_rec = {
            "asset_id": asset_id,
            "asset_type": "physical",
            "cycle": 6,
            "timestamp": "2026-01-01T06:00:00Z",
            "sensor_readings": {"sensor_2": 640.0},
            "health_pct": 90.0,
            "data_quality_flag": "ok",
            "anomaly_detected": False,
            "metadata": {},
        }

        out_rec = event_mgr.apply_events(sample_rec)
        self.assertEqual(out_rec["health_pct"], 0.0)
        self.assertTrue(out_rec["anomaly_detected"])


if __name__ == "__main__":
    unittest.main()
