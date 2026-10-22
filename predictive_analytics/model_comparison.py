import numpy as np
import pandas as pd
from typing import Dict
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_squared_error

from predictive_analytics.dataset_loader import load_training_data
from predictive_analytics.model import FEATURE_COLUMNS


def compare_models() -> Dict[str, float]:
    """Train Gradient Boosting and Random Forest on exact same train/test split to compare RMSE.

    Returns:
        Dict mapping model name to RMSE score.
    """
    df = load_training_data()

    # Fixed seed train/test split by engine_id
    unique_engines = df["engine_id"].unique()
    np.random.seed(42)
    test_engines = np.random.choice(
        unique_engines, size=int(len(unique_engines) * 0.2), replace=False
    )
    train_mask = ~df["engine_id"].isin(test_engines)
    test_mask = df["engine_id"].isin(test_engines)

    train_df = df[train_mask]
    test_df = df[test_mask]

    X_train, y_train = train_df[FEATURE_COLUMNS], train_df["RUL"]
    X_test, y_test = test_df[FEATURE_COLUMNS], test_df["RUL"]

    # Model 1: Gradient Boosting
    gbr = GradientBoostingRegressor(n_estimators=100, learning_rate=0.05, max_depth=4, random_state=42)
    gbr.fit(X_train, y_train)
    y_pred_gbr = np.clip(gbr.predict(X_test), 0, None)
    rmse_gbr = float(np.sqrt(mean_squared_error(y_test, y_pred_gbr)))

    # Model 2: Random Forest
    rf = RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42)
    rf.fit(X_train, y_train)
    y_pred_rf = np.clip(rf.predict(X_test), 0, None)
    rmse_rf = float(np.sqrt(mean_squared_error(y_test, y_pred_rf)))

    return {
        "gradient_boosting_rmse": round(rmse_gbr, 4),
        "random_forest_rmse": round(rmse_rf, 4),
    }


if __name__ == "__main__":
    results = compare_models()
    print("=== Model Performance Comparison (RMSE) ===")
    for model_name, rmse_val in results.items():
        print(f"  - {model_name}: {rmse_val}")
