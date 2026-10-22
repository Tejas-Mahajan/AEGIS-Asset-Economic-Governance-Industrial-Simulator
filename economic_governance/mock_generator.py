from typing import Any, Dict, List
from predictive_analytics.tests.test_model import EXPECTED_RUL_PREDICTION_FIELDS


def generate_mock_rul_predictions(count: int = 5) -> List[Dict[str, Any]]:
    """Generate 5 fake RUL Prediction Records matching SCHEMAS.md Section 2 exactly."""
    mock_records = []
    for i in range(1, count + 1):
        asset_id = f"ENG-{i:03d}"
        rul_cycles = round(150.0 - (i * 25.0), 2)  # Decreasing RUL for asset differentiation
        rec = {
            "asset_id": asset_id,
            "rul_cycles": max(5.0, rul_cycles),
            "rul_cycles_confidence_low": max(0.0, round(rul_cycles - 30.0, 2)),
            "rul_cycles_confidence_high": round(rul_cycles + 30.0, 2),
            "rul_days": None,
        }
        mock_records.append(rec)
    return mock_records


def get_asset_cost_table(asset_ids: List[str]) -> Dict[str, Dict[str, float]]:
    """Generate standard cost table per asset.

    Fields:
      - repair_cost: Cost to perform preventive repair (INR)
      - replacement_cost: Cost to fully replace asset (INR)
      - safety_impact_rating: Rating 1.0 (low) to 10.0 (critical safety impact)
      - environmental_impact_rating: Rating 1.0 (low) to 10.0 (high env impact)
      - downtime_cost_per_hour: Downtime cost per hour (INR/hr)
    """
    cost_table = {}
    base_repair = 150000.0
    base_replacement = 800000.0
    base_downtime_rate = 25000.0

    for idx, asset_id in enumerate(asset_ids, start=1):
        # Scale factors to provide varied asset risk profiles
        scale = 1.0 + (idx * 0.15)
        cost_table[asset_id] = {
            "repair_cost": round(base_repair * scale, 2),
            "replacement_cost": round(base_replacement * scale, 2),
            "safety_impact_rating": round(min(10.0, 3.0 + (idx * 1.2)), 2),
            "environmental_impact_rating": round(min(10.0, 2.0 + (idx * 1.5)), 2),
            "downtime_cost_per_hour": round(base_downtime_rate * scale, 2),
        }
    return cost_table
