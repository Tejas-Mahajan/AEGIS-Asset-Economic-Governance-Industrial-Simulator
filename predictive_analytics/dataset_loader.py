"""Offline/Historical Dataset Loader for Model Training.

NOTE: This offline training path reads historical C-MAPSS data to train models.
It is separate from the live streaming Asset Record pipeline.
"""
import os
import pandas as pd
from data_simulation.dataset import load_fd001_dataframe


def load_training_data(data_path: str = "train_FD001.txt") -> pd.DataFrame:
    """Load historical C-MAPSS FD001 training data and calculate actual target RUL per row."""
    # Resolve default data_path relative to data_simulation
    if not os.path.exists(data_path):
        data_path = os.path.join(
            os.path.dirname(__file__), "..", "data_simulation", "train_FD001.txt"
        )

    df = load_fd001_dataframe(target_path=data_path)

    # Compute target Remaining Useful Life (RUL) in cycles for each engine cycle row
    # RUL = (Max Cycle for engine) - (Current Cycle)
    max_cycles = df.groupby("engine_id")["cycle"].transform("max")
    df["RUL"] = max_cycles - df["cycle"]

    return df
