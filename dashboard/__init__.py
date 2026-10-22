"""Dashboard & Integration Module — Smart Industrial Asset Evaluation System.

Provides the interactive Streamlit dashboard and decision audit trail components.
"""

from dashboard.mock_upstream import (
    get_mock_asset_records,
    get_mock_rul_predictions,
    get_mock_ranking_outputs,
    get_mock_risk_budget_outputs,
)
from dashboard.audit_trail import generate_decision_audit_explanation

__all__ = [
    "get_mock_asset_records",
    "get_mock_rul_predictions",
    "get_mock_ranking_outputs",
    "get_mock_risk_budget_outputs",
    "generate_decision_audit_explanation",
]
