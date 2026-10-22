from typing import Any, Dict


def generate_decision_audit_explanation(
    ranking_record: Dict[str, Any],
    rul_record: Dict[str, Any],
    risk_record: Dict[str, Any],
) -> str:
    """Generate a plain-English explanation constructed dynamically from actual numbers in records.

    D4 assertion requirement: Sentence must contain numbers matching real record fields.
    """
    asset_id = ranking_record["asset_id"]
    rank = ranking_record["priority_rank"]
    crit_score = ranking_record["criticality_score"]
    weights = ranking_record.get("weights_used", {})
    safety_w_pct = round(weights.get("safety", 0.0) * 100.0, 1)

    rul_cycles = rul_record["rul_cycles"]
    cvar_95 = risk_record["cvar_95"]
    budget_alloc = risk_record["recommended_budget_allocation"]

    explanation = (
        f"Asset {asset_id} is ranked #{rank} with a criticality score of {crit_score} "
        f"(safety weight {safety_w_pct}%) due to predicted remaining useful life of {rul_cycles} cycles. "
        f"Financial CVaR 95% loss exposure is ₹{cvar_95:,.2f}, qualifying for a recommended budget allocation of ₹{budget_alloc:,.2f}."
    )
    return explanation
