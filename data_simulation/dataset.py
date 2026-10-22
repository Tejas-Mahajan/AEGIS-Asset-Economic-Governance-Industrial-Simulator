import os
import urllib.request
import pandas as pd

FD001_URL = "https://raw.githubusercontent.com/hankroark/Turbofan-Engine-Degradation/master/CMAPSSData/train_FD001.txt"

COLUMN_NAMES = [
    "engine_id",
    "cycle",
    "setting_1",
    "setting_2",
    "setting_3",
] + [f"sensor_{i}" for i in range(1, 22)]


def download_fd001(target_path: str = "train_FD001.txt") -> str:
    """Download the NASA C-MAPSS FD001 dataset if not present locally."""
    if not os.path.exists(target_path):
        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
        urllib.request.urlretrieve(FD001_URL, target_path)
    return target_path


def load_fd001_dataframe(target_path: str = "train_FD001.txt") -> pd.DataFrame:
    """Load the NASA C-MAPSS FD001 dataset into a DataFrame with named columns."""
    path = download_fd001(target_path)
    df = pd.read_csv(path, sep=r"\s+", header=None, names=COLUMN_NAMES)
    return df


def inspect_dataset_structure(df: pd.DataFrame) -> dict:
    """Inspect and display raw column structure and engine-level summary."""
    max_cycles_per_engine = df.groupby("engine_id")["cycle"].max()
    info = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": list(df.columns),
        "unique_engines": df["engine_id"].nunique(),
        "cycle_count_min": max_cycles_per_engine.min(),
        "cycle_count_max": max_cycles_per_engine.max(),
        "cycle_counts_sample": max_cycles_per_engine.head(5).to_dict(),
    }
    return info


if __name__ == "__main__":
    df = load_fd001_dataframe()
    info = inspect_dataset_structure(df)
    print("=== Raw Column Structure ===")
    print(f"Total Columns ({info['total_columns']}): {info['columns']}")
    print("\n=== Engine Level Summary ===")
    print(f"Total Unique Engines: {info['unique_engines']}")
    print(f"Cycle Count Range: {info['cycle_count_min']} to {info['cycle_count_max']}")
    print(f"Sample Engine Max Cycles: {info['cycle_counts_sample']}")
