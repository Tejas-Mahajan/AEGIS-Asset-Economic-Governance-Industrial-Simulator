import numpy as np
from typing import Any, Dict, List

TOTAL_BUDGET_POOL = 1000000.0  # ₹10,00,000 fixed budget pool


def compute_asset_risk_and_cvar(
    rul_record: Dict[str, Any],
    cost_info: Dict[str, float],
    num_samples: int = 1000,
) -> Dict[str, float]:
    """Sample N points across RUL confidence interval to build explicit loss distribution.

    Computes:
      - expected_cost: Mean of loss distribution
      - cvar_95: Conditional Value at Risk at 95% level (mean of worst 5% of loss outcomes)
    """
    low = float(rul_record["rul_cycles_confidence_low"])
    high = float(rul_record["rul_cycles_confidence_high"])
    rul_mid = float(rul_record["rul_cycles"])

    if high <= low:
        high = low + 10.0

    # Sample N points across confidence interval using triangular distribution centered at rul_mid
    np.random.seed(42)
    sample_ruls = np.random.triangular(left=low, mode=max(low, min(rul_mid, high)), right=high, size=num_samples)

    repair_cost = cost_info.get("repair_cost", 150000.0)
    replacement_cost = cost_info.get("replacement_cost", 800000.0)
    downtime_rate = cost_info.get("downtime_cost_per_hour", 25000.0)

    # Map sample RULs to failure loss distribution
    losses = []
    for r in sample_ruls:
        if r < 15.0:
            # Major catastrophic failure: full replacement + 24 hrs downtime
            loss = replacement_cost + (24.0 * downtime_rate)
        elif r < 40.0:
            # Accelerated failure: repair + 12 hrs downtime
            loss = repair_cost + (12.0 * downtime_rate)
        elif r < 80.0:
            # Minor component breakdown: repair + 4 hrs downtime
            loss = repair_cost + (4.0 * downtime_rate)
        else:
            # Planned routine maintenance
            loss = repair_cost * 0.4

        losses.append(loss)

    losses = np.array(losses)

    # Expected cost = mean of loss distribution
    expected_cost = round(float(np.mean(losses)), 2)

    # CVaR 95% = mean of top 5% worst losses
    sorted_losses = np.sort(losses)[::-1]
    cutoff_idx = max(1, int(num_samples * 0.05))
    cvar_95 = round(float(np.mean(sorted_losses[:cutoff_idx])), 2)

    # Ensure CVaR 95% is never below expected_cost
    if cvar_95 < expected_cost:
        cvar_95 = expected_cost

    return {"expected_cost": expected_cost, "cvar_95": cvar_95}


def compute_risk_and_budget_allocations(
    rul_records: List[Dict[str, Any]],
    ranking_records: List[Dict[str, Any]],
    cost_table: Dict[str, Dict[str, float]],
    total_budget: float = TOTAL_BUDGET_POOL,
) -> List[Dict[str, Any]]:
    """Compute Risk and Budget allocations matching SCHEMAS.md Section 4.

    Allocation Rule:
      Share is proportional to (criticality_score * cvar_95).
    """
    ranking_map = {r["asset_id"]: r["criticality_score"] for r in ranking_records}
    asset_risk_results = []
    allocation_weights = []

    for rec in rul_records:
        asset_id = rec["asset_id"]
        cost_info = cost_table.get(asset_id, {})

        # Compute CVaR 95% & expected_cost
        risk_res = compute_asset_risk_and_cvar(rec, cost_info)
        expected_cost = risk_res["expected_cost"]
        cvar_95 = risk_res["cvar_95"]

        crit_score = ranking_map.get(asset_id, 50.0)

        # C7 — Reactive vs Predictive comparator
        replacement_cost = cost_info.get("replacement_cost", 800000.0)
        downtime_rate = cost_info.get("downtime_cost_per_hour", 25000.0)
        baseline_reactive_cost = round(replacement_cost + (16.0 * downtime_rate), 2)
        predictive_savings = round(baseline_reactive_cost - expected_cost, 2)

        # Weight for budget allocation: higher criticality AND higher cvar_95 -> larger share
        weight = crit_score * cvar_95
        allocation_weights.append(weight)

        asset_risk_results.append(
            {
                "asset_id": asset_id,
                "cvar_95": cvar_95,
                "expected_cost": expected_cost,
                "baseline_reactive_cost": baseline_reactive_cost,
                "predictive_savings": predictive_savings,
                "budget_pool_id": "default",
                "metadata": {
                    "criticality_score": crit_score,
                    "downtime_cost_per_hour": downtime_rate,
                    "repair_cost": cost_info.get("repair_cost", 150000.0),
                    "replacement_cost": replacement_cost,
                },
            }
        )

    # C6 — Calculate recommended_budget_allocation proportional to weight
    total_weight = sum(allocation_weights)
    for idx, item in enumerate(asset_risk_results):
        if total_weight > 0:
            alloc = round((allocation_weights[idx] / total_weight) * total_budget, 2)
        else:
            alloc = round(total_budget / len(asset_risk_results), 2)
        item["recommended_budget_allocation"] = alloc

    # Fix rounding sum to ensure exact match to total_budget
    allocated_sum = sum(item["recommended_budget_allocation"] for item in asset_risk_results)
    diff = round(total_budget - allocated_sum, 2)
    if abs(diff) > 0 and asset_risk_results:
        asset_risk_results[0]["recommended_budget_allocation"] = round(
            asset_risk_results[0]["recommended_budget_allocation"] + diff, 2
        )

    return asset_risk_results
