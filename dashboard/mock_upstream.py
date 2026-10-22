from typing import Any, Dict, List
from data_simulation import replay_engine
from predictive_analytics import generate_mock_asset_records as gen_assets
from predictive_analytics import generate_mock_asset_records, predict_rul
from economic_governance import (
    generate_mock_rul_predictions,
    generate_ranking_output,
    generate_risk_budget_output,
)


def get_mock_asset_records(count: int = 5) -> List[Dict[str, Any]]:
    """Return mock Asset Records matching SCHEMAS.md Section 1."""
    return gen_assets(count=count)


def get_mock_rul_predictions(count: int = 5) -> List[Dict[str, Any]]:
    """Return mock RUL Prediction Records matching SCHEMAS.md Section 2."""
    return generate_mock_rul_predictions(count=count)


def get_mock_ranking_outputs(count: int = 5) -> List[Dict[str, Any]]:
    """Return mock Ranking Output records matching SCHEMAS.md Section 3."""
    mock_ruls = get_mock_rul_predictions(count=count)
    return generate_ranking_output(mock_ruls)


def get_mock_risk_budget_outputs(count: int = 5) -> List[Dict[str, Any]]:
    """Return mock Risk/Budget Output records matching SCHEMAS.md Section 4."""
    mock_ruls = get_mock_rul_predictions(count=count)
    rankings = generate_ranking_output(mock_ruls)
    return generate_risk_budget_output(mock_ruls, ranking_records=rankings)
