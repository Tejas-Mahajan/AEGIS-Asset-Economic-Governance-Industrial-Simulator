import numpy as np
from typing import Any, Dict, List, Tuple

# Random Index table for AHP consistency calculation
RANDOM_INDEX = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12}

# Consistent Pairwise Matrix (Safety, Cost, Environment)
# Pairwise matrix choices:
# Safety vs Cost = 3.0 (Safety moderately preferred to Cost)
# Safety vs Environment = 5.0 (Safety strongly preferred to Environment)
# Cost vs Environment = 2.0 (Cost slightly preferred to Environment)
DEFAULT_PAIRWISE_MATRIX = np.array(
    [
        [1.0, 3.0, 5.0],  # Safety
        [1 / 3.0, 1.0, 2.0],  # Cost
        [1 / 5.0, 1 / 2.0, 1.0],  # Environment
    ]
)


def compute_ahp_weights(matrix: np.ndarray) -> Tuple[Dict[str, float], float]:
    """Compute AHP priority weights via normalized column average method and calculate Consistency Ratio (CR).

    Returns:
        (weights_dict, consistency_ratio)
    """
    n = matrix.shape[0]

    # Step 1: Normalize columns
    col_sums = matrix.sum(axis=0)
    norm_matrix = matrix / col_sums

    # Step 2: Compute priority weight vector (row averages)
    weights = norm_matrix.mean(axis=1)
    weights = weights / weights.sum()  # Ensure exact sum to 1.0

    # Step 3: Compute Consistency Ratio (CR)
    weighted_sum = np.dot(matrix, weights)
    consistency_vector = weighted_sum / weights
    lambda_max = float(np.mean(consistency_vector))

    ci = (lambda_max - n) / float(n - 1)
    ri = RANDOM_INDEX.get(n, 0.58)
    cr = float(ci / ri) if ri > 0 else 0.0

    weights_dict = {
        "safety": round(float(weights[0]), 4),
        "cost": round(float(weights[1]), 4),
        "environment": round(float(weights[2]), 4),
    }

    return weights_dict, round(cr, 4)


def rank_assets_ahp(
    rul_records: List[Dict[str, Any]],
    cost_table: Dict[str, Dict[str, float]],
    weights: Optional[Dict[str, float]] = None,
    asset_records: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Rank assets by combined criticality_score using AHP weights.

    Factors:
      - Safety score: derived from safety_impact_rating & low RUL
      - Cost score: derived from replacement_cost & repair_cost
      - Environment score: derived from environmental_impact_rating
    """
    if weights is None:
        weights, _ = compute_ahp_weights(DEFAULT_PAIRWISE_MATRIX)

    w_safety = weights["safety"]
    w_cost = weights["cost"]
    w_env = weights["environment"]

    asset_map = {}
    if asset_records:
        asset_map = {a["asset_id"]: a for a in asset_records}

    scored_assets = []
    for rec in rul_records:
        asset_id = rec["asset_id"]
        rul = float(rec["rul_cycles"])
        costs = cost_table.get(asset_id, {})

        # Safety factor increases as RUL decreases (urgency) + safety rating
        safety_rating = costs.get("safety_impact_rating", 5.0)
        urgency_factor = max(1.0, 200.0 / max(1.0, rul))
        safety_score = min(100.0, safety_rating * 10.0 * (urgency_factor ** 0.5))

        # Boost safety_score if an anomaly spike or manual failure is detected
        asset_rec = asset_map.get(asset_id, {})
        if asset_rec.get("anomaly_detected", False):
            safety_score = min(100.0, safety_score * 1.5 + 20.0)

        # Cost factor based on potential failure monetary exposure
        replacement_cost = costs.get("replacement_cost", 500000.0)
        cost_score = min(100.0, (replacement_cost / 1000000.0) * 80.0)

        # Environment factor based on environmental impact rating
        env_rating = costs.get("environmental_impact_rating", 5.0)
        env_score = env_rating * 10.0

        criticality_score = round(
            (w_safety * safety_score) + (w_cost * cost_score) + (w_env * env_score),
            2,
        )

        scored_assets.append(
            {
                "asset_id": asset_id,
                "criticality_score": criticality_score,
                "rul_cycles": rul,
            }
        )

    # Sort descending by criticality_score
    scored_assets.sort(key=lambda x: x["criticality_score"], reverse=True)

    # Assign priority_rank (1..N permutation)
    for rank, asset in enumerate(scored_assets, start=1):
        asset["priority_rank"] = rank

    return scored_assets


def compute_sensitivity_threshold(
    rul_records: List[Dict[str, Any]],
    cost_table: Dict[str, Dict[str, float]],
) -> float:
    """Nudge safety weight in 1% steps to find smallest shift that flips rank #1 asset."""
    base_weights, _ = compute_ahp_weights(DEFAULT_PAIRWISE_MATRIX)
    base_rankings = rank_assets_ahp(rul_records, cost_table, base_weights)
    top_asset_id = base_rankings[0]["asset_id"]

    w_s_base = base_weights["safety"]
    w_c_base = base_weights["cost"]
    w_e_base = base_weights["environment"]

    # Step in 1% increments up to +/- 50%
    for shift_pct in np.arange(0.01, 0.50, 0.01):
        for direction in [1.0, -1.0]:
            delta = shift_pct * direction
            new_w_s = max(0.05, w_s_base + delta)
            remaining_base = w_c_base + w_e_base

            if remaining_base > 0:
                scale = (1.0 - new_w_s) / remaining_base
                new_w_c = w_c_base * scale
                new_w_e = w_e_base * scale
            else:
                new_w_c = (1.0 - new_w_s) / 2.0
                new_w_e = (1.0 - new_w_s) / 2.0

            trial_weights = {"safety": new_w_s, "cost": new_w_c, "environment": new_w_e}
            trial_rankings = rank_assets_ahp(rul_records, cost_table, trial_weights)

            if trial_rankings[0]["asset_id"] != top_asset_id:
                return round(float(shift_pct * 100.0), 2)

    return 5.0  # Default fallback threshold if top asset remains stable
