import sys
import os
import json
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_simulation import replay_engine
from predictive_analytics import predict_rul


def get_sample_rul_prediction_records(count: int = 3) -> List[Dict[str, Any]]:
    """Fetch sample Asset Records from real data_simulation stream and compute RUL predictions."""
    stream = replay_engine(engine_id=1, delay=0.0)
    samples = []
    for _ in range(count):
        real_asset_record = next(stream)
        rul_prediction = predict_rul(real_asset_record)
        samples.append(rul_prediction)
    return samples


def print_sample_rul_predictions_json() -> str:
    """Return pretty-printed JSON string of 3 sample RUL Prediction Records."""
    samples = get_sample_rul_prediction_records(count=3)
    return json.dumps(samples, indent=2)


if __name__ == "__main__":
    print("=== 3 Sample RUL Prediction Records (JSON) ===")
    print(print_sample_rul_predictions_json())
