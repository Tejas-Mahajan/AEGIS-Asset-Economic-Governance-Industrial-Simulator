"""Economic Governance Module — Smart Industrial Asset Evaluation System.

This module implements AHP multi-criteria asset ranking, CVaR 95% risk exposure calculations, budget pool allocation,
and reactive-vs-predictive monetary savings analysis matching SCHEMAS.md Sections 3 and 4.
"""

from economic_governance.mock_generator import generate_mock_rul_predictions, get_asset_cost_table
from economic_governance.ahp import compute_ahp_weights, rank_assets_ahp, compute_sensitivity_threshold
from economic_governance.risk_budget import compute_asset_risk_and_cvar, compute_risk_and_budget_allocations
from economic_governance.governance_engine import generate_ranking_output, generate_risk_budget_output

__all__ = [
    "generate_mock_rul_predictions",
    "get_asset_cost_table",
    "compute_ahp_weights",
    "rank_assets_ahp",
    "compute_sensitivity_threshold",
    "compute_asset_risk_and_cvar",
    "compute_risk_and_budget_allocations",
    "generate_ranking_output",
    "generate_risk_budget_output",
]
