import copy
from typing import Any, Dict, List
from data_simulation.schema_mapper import SELECTED_SENSORS
from data_simulation.tests.test_schema_mapper import EXPECTED_FIELDS


def generate_mock_asset_records(count: int = 5) -> List[Dict[str, Any]]:
    """Generate mock Asset Records matching SCHEMAS.md Section 1 exactly."""
    mock_records = []
    base_timestamp = "2026-01-01T00:00:00Z"

    for i in range(1, count + 1):
        asset_id = f"ENG-{i:03d}"
        cycle = 20 * i
        health_pct = max(0.0, 100.0 - (i * 15.0))
        record = {
            "asset_id": asset_id,
            "asset_type": "physical",
            "cycle": cycle,
            "timestamp": base_timestamp,
            "sensor_readings": {
                sensor: round(500.0 + (i * 10.0) + idx, 2)
                for idx, sensor in enumerate(SELECTED_SENSORS)
            },
            "health_pct": health_pct,
            "data_quality_flag": "ok",
            "anomaly_detected": False,
            "metadata": {"engine_id": i, "engine_max_cycle": 200},
        }
        mock_records.append(record)

    return mock_records
