import json
import unittest
import numpy as np

from economic_governance.mock_generator import generate_mock_rul_predictions, get_asset_cost_table
from economic_governance.ahp import compute_ahp_weights, rank_assets_ahp, compute_sensitivity_threshold, DEFAULT_PAIRWISE_MATRIX
from economic_governance.risk_budget import compute_asset_risk_and_cvar, TOTAL_BUDGET_POOL
from economic_governance.governance_engine import generate_ranking_output, generate_risk_budget_output
from predictive_analytics.tests.test_model import EXPECTED_RUL_PREDICTION_FIELDS

EXPECTED_RANKING_FIELDS = {
    "asset_id",
    "priority_rank",
    "criticality_score",
    "weights_used",
    "consistency_ratio",
    "metadata",
}

EXPECTED_RISK_BUDGET_FIELDS = {
    "asset_id",
    "cvar_95",
    "expected_cost",
    "recommended_budget_allocation",
    "baseline_reactive_cost",
    "predictive_savings",
    "budget_pool_id",
    "metadata",
}


class TestEconomicGovernance(unittest.TestCase):

    def setUp(self):
        self.mock_ruls = generate_mock_rul_predictions(count=5)
        self.asset_ids = [r["asset_id"] for r in self.mock_ruls]
        self.cost_table = get_asset_cost_table(self.asset_ids)

    def test_c1_mock_output_and_cost_table_positive(self):
        """C1 loop-test: Assert mock matches SCHEMAS.md section 2 and every cost table value is positive."""
        self.assertEqual(len(self.mock_ruls), 5)
        for rec in self.mock_ruls:
            self.assertEqual(set(rec.keys()), EXPECTED_RUL_PREDICTION_FIELDS)

        for asset_id, costs in self.cost_table.items():
            for key, val in costs.items():
                self.assertGreater(val, 0.0, f"Cost table value for {asset_id}.{key} is non-positive: {val}")

    def test_c2_ahp_weights_and_permutation_ranks(self):
        """C2 loop-test: Assert weights sum to 1.0 and priority_rank forms valid 1..N permutation."""
        weights, cr = compute_ahp_weights(DEFAULT_PAIRWISE_MATRIX)
        total_w = sum(weights.values())
        self.assertAlmostEqual(total_w, 1.0, places=4)

        ranked = rank_assets_ahp(self.mock_ruls, self.cost_table, weights)
        ranks = [item["priority_rank"] for item in ranked]
        expected_ranks = list(range(1, len(self.mock_ruls) + 1))
        self.assertEqual(ranks, expected_ranks, "priority_rank is not a valid 1..N permutation without gaps/duplicates")

    def test_c3_consistency_ratio_under_threshold(self):
        """C3 loop-test: Assert consistency_ratio < 0.1."""
        _, cr = compute_ahp_weights(DEFAULT_PAIRWISE_MATRIX)
        self.assertLess(cr, 0.1, f"Consistency ratio ({cr}) is >= 0.1")

    def test_c4_sensitivity_check(self):
        """C4 loop-test: Assert returned sensitivity_threshold_pct is a positive float and flips rank #1."""
        sens_pct = compute_sensitivity_threshold(self.mock_ruls, self.cost_table)
        self.assertIsInstance(sens_pct, float)
        self.assertGreater(sens_pct, 0.0)

    def test_c5_cvar_95_greater_or_equal_expected_cost(self):
        """C5 loop-test: Assert cvar_95 >= expected_cost for every asset."""
        for rec in self.mock_ruls:
            cost_info = self.cost_table[rec["asset_id"]]
            risk_res = compute_asset_risk_and_cvar(rec, cost_info)
            cvar = risk_res["cvar_95"]
            exp_cost = risk_res["expected_cost"]
            self.assertGreaterEqual(
                cvar,
                exp_cost,
                f"CVaR 95% ({cvar}) is lower than expected cost ({exp_cost}) for {rec['asset_id']}"
            )

    def test_c6_recommended_budget_allocations_sum_to_total(self):
        """C6 loop-test: Assert recommended_budget_allocation values sum to total budget within tolerance."""
        risk_budgets = generate_risk_budget_output(self.mock_ruls, cost_table=self.cost_table)
        allocations = [r["recommended_budget_allocation"] for r in risk_budgets]
        sum_alloc = sum(allocations)
        self.assertAlmostEqual(sum_alloc, TOTAL_BUDGET_POOL, places=2)
        for r in risk_budgets:
            self.assertEqual(r["budget_pool_id"], "default")

    def test_c7_reactive_vs_predictive_comparator(self):
        """C7 loop-test: Assert baseline_reactive_cost > expected_cost for majority of assets and math consistent."""
        risk_budgets = generate_risk_budget_output(self.mock_ruls, cost_table=self.cost_table)
        savings_count = 0
        for r in risk_budgets:
            baseline = r["baseline_reactive_cost"]
            expected = r["expected_cost"]
            savings = r["predictive_savings"]
            self.assertAlmostEqual(savings, round(baseline - expected, 2), places=2)
            if baseline > expected:
                savings_count += 1

        self.assertGreater(savings_count, len(risk_budgets) // 2)

    def test_c8_downtime_cost_per_hour_present(self):
        """C8 loop-test: Assert downtime_cost_per_hour is present and a positive float on every record metadata."""
        risk_budgets = generate_risk_budget_output(self.mock_ruls, cost_table=self.cost_table)
        for r in risk_budgets:
            dt_cost = r["metadata"].get("downtime_cost_per_hour")
            self.assertIsNotNone(dt_cost)
            self.assertIsInstance(dt_cost, float)
            self.assertGreater(dt_cost, 0.0)

    def test_c9_output_schemas_exact_match(self):
        """C9 loop-test: Assert every field name in both outputs matches SCHEMAS.md sections 3 and 4 character-for-character."""
        rankings = generate_ranking_output(self.mock_ruls, cost_table=self.cost_table)
        risk_budgets = generate_risk_budget_output(self.mock_ruls, ranking_records=rankings, cost_table=self.cost_table)

        self.assertEqual(len(rankings), 5)
        for r in rankings:
            self.assertEqual(
                set(r.keys()),
                EXPECTED_RANKING_FIELDS,
                f"Ranking field mismatch: {set(r.keys())}"
            )

        self.assertEqual(len(risk_budgets), 5)
        for r in risk_budgets:
            self.assertEqual(
                set(r.keys()),
                EXPECTED_RISK_BUDGET_FIELDS,
                f"Risk/Budget field mismatch: {set(r.keys())}"
            )


if __name__ == "__main__":
    unittest.main()
