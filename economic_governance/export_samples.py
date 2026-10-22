import sys
import os
import json
from typing import Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from economic_governance import (
    generate_mock_rul_predictions,
    generate_ranking_output,
    generate_risk_budget_output,
)


def get_economic_governance_samples() -> Dict[str, Any]:
    """Generate sample Ranking Output and Risk/Budget Output records."""
    mock_ruls = generate_mock_rul_predictions(count=5)
    rankings = generate_ranking_output(mock_ruls)
    risk_budgets = generate_risk_budget_output(mock_ruls, rankings)
    return {"ranking_output": rankings, "risk_budget_output": risk_budgets}


def print_economic_samples_json() -> str:
    """Return pretty-printed JSON string of economic governance sample outputs."""
    samples = get_economic_governance_samples()
    return json.dumps(samples, indent=2)


if __name__ == "__main__":
    print("=== Economic Governance Outputs (JSON) ===")
    print(print_economic_samples_json())
