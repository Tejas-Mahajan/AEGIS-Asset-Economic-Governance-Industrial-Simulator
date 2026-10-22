"""Predictive Analytics Module — Smart Industrial Asset Evaluation System.

This module consumes Asset Records (from data_simulation or mock stream), fits baseline regression models on C-MAPSS data,
and produces RUL Prediction Records matching SCHEMAS.md Section 2 with dynamic confidence intervals.
"""

from predictive_analytics.model import RULPredictor, predict_rul, get_model_rmse
from predictive_analytics.mock_generator import generate_mock_asset_records
from predictive_analytics.model_comparison import compare_models

__all__ = [
    "RULPredictor",
    "predict_rul",
    "get_model_rmse",
    "generate_mock_asset_records",
    "compare_models",
]
