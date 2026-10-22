from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Union
import pandas as pd

# Selected subset of sensors (7 out of 21) that exhibit meaningful variance/degradation signature in FD001:
# - sensor_2: Total temperature at HPC outlet (T30)
# - sensor_3: Total temperature at LPT outlet (T50)
# - sensor_4: Total pressure at HPC outlet (P30)
# - sensor_7: Static pressure at HPC outlet (P15)
# - sensor_11: Static pressure at HPC outlet (Ps30)
# - sensor_12: Ratio of fuel flow to Ps30 (phi)
# - sensor_15: Bypass Ratio (BPR)
SELECTED_SENSORS = [
    "sensor_2",
    "sensor_3",
    "sensor_4",
    "sensor_7",
    "sensor_11",
    "sensor_12",
    "sensor_15",
]

BASE_DATETIME = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


def to_asset_record(
    row: Union[pd.Series, Dict[str, Any]], engine_max_cycle: int
) -> Dict[str, Any]:
    """Convert one raw C-MAPSS row into an Asset Record matching SCHEMAS.md section 1.

    Args:
        row: A row from C-MAPSS DataFrame or dict containing engine_id, cycle, settings, sensors.
        engine_max_cycle: Total life (max cycle count) for this engine ID.

    Returns:
        Dict matching SCHEMAS.md Section 1 Asset Record schema.
    """
    engine_id = int(row["engine_id"])
    cycle = int(row["cycle"])

    # Format asset_id as string
    asset_id = f"ENG-{engine_id:03d}"

    # Calculate ISO-8601 timestamp based on operational cycle offset (1 hour per cycle)
    record_time = BASE_DATETIME + timedelta(hours=cycle)
    timestamp_str = record_time.isoformat().replace("+00:00", "Z")

    # Extract selected sensor readings as floats
    sensor_readings = {
        sensor_name: float(row[sensor_name]) for sensor_name in SELECTED_SENSORS
    }

    # Derive health_pct: remaining cycles / total life * 100
    remaining_cycles = max(0, engine_max_cycle - cycle)
    health_pct = round((remaining_cycles / float(engine_max_cycle)) * 100.0, 4)
    health_pct = max(0.0, min(100.0, health_pct))

    # Build Asset Record matching SCHEMAS.md Section 1 exactly
    asset_record = {
        "asset_id": asset_id,
        "asset_type": "physical",
        "cycle": cycle,
        "timestamp": timestamp_str,
        "sensor_readings": sensor_readings,
        "health_pct": health_pct,
        "data_quality_flag": "ok",
        "anomaly_detected": False,
        "metadata": {
            "engine_id": engine_id,
            "engine_max_cycle": engine_max_cycle,
            "setting_1": float(row["setting_1"]),
            "setting_2": float(row["setting_2"]),
            "setting_3": float(row["setting_3"]),
        },
    }

    return asset_record
