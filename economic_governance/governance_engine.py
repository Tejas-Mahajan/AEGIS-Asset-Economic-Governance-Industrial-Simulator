from typing import Any, Dict, List, Optional
from economic_governance.ahp import (
    compute_ahp_weights,
    rank_assets_ahp,
    compute_sensitivity_threshold,
    DEFAULT_PAIRWISE_MATRIX,
)
from economic_governance.mock_generator import get_asset_cost_table
from economic_governance.risk_budget import compute_risk_and_budget_allocations, TOTAL_BUDGET_POOL


def generate_ranking_output(
    rul_records: List[Dict[str, Any]],
    cost_table: Optional[Dict[str, Dict[str, float]]] = None,
    asset_records: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Generate Ranking Output records matching SCHEMAS.md Section 3 exactly."""
    asset_ids = [r["asset_id"] for r in rul_records]
    if cost_table is None:
        cost_table = get_asset_cost_table(asset_ids)

    weights_used, cr = compute_ahp_weights(DEFAULT_PAIRWISE_MATRIX)
    ranked_list = rank_assets_ahp(rul_records, cost_table, weights_used, asset_records=asset_records)
    sensitivity_pct = compute_sensitivity_threshold(rul_records, cost_table)

    ranking_output_records = []
    for item in ranked_list:
        asset_id = item["asset_id"]
        rec = {
            "asset_id": asset_id,
            "priority_rank": item["priority_rank"],
            "criticality_score": item["criticality_score"],
            "weights_used": weights_used,
            "consistency_ratio": cr,
            "metadata": {
                "sensitivity_threshold_pct": sensitivity_pct,
                "rul_cycles": item["rul_cycles"],
            },
        }
        ranking_output_records.append(rec)

    return ranking_output_records


def generate_risk_budget_output(
    rul_records: List[Dict[str, Any]],
    ranking_records: Optional[List[Dict[str, Any]]] = None,
    cost_table: Optional[Dict[str, Dict[str, float]]] = None,
    total_budget: float = TOTAL_BUDGET_POOL,
) -> List[Dict[str, Any]]:
    """Generate Risk/Budget Output records matching SCHEMAS.md Section 4 exactly."""
    asset_ids = [r["asset_id"] for r in rul_records]
    if cost_table is None:
        cost_table = get_asset_cost_table(asset_ids)

    if ranking_records is None:
        ranking_records = generate_ranking_output(rul_records, cost_table)

    risk_budget_records = compute_risk_and_budget_allocations(
        rul_records, ranking_records, cost_table, total_budget=total_budget
    )

    # Ensure character-for-character field alignment with SCHEMAS.md Section 4
    output_records = []
    for r in risk_budget_records:
        rec = {
            "asset_id": r["asset_id"],
            "cvar_95": r["cvar_95"],
            "expected_cost": r["expected_cost"],
            "recommended_budget_allocation": r["recommended_budget_allocation"],
            "baseline_reactive_cost": r["baseline_reactive_cost"],
            "predictive_savings": r["predictive_savings"],
            "budget_pool_id": r.get("budget_pool_id", "default"),
            "metadata": r.get("metadata", {}),
        }
        output_records.append(rec)

    return output_records
