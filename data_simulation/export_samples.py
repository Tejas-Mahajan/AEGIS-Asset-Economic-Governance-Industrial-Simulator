import sys
import os
import json
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_simulation import replay_engine


def get_sample_asset_records(count: int = 3) -> List[Dict[str, Any]]:
    """Fetch sample Asset Records from the stream."""
    stream = replay_engine(engine_id=1, delay=0.0)
    samples = []
    for _ in range(count):
        samples.append(next(stream))
    return samples


def print_sample_asset_records_json() -> str:
    """Return pretty-printed JSON string of 3 sample Asset Records."""
    samples = get_sample_asset_records(count=3)
    json_str = json.dumps(samples, indent=2)
    return json_str


if __name__ == "__main__":
    print("=== 3 Sample Asset Records (JSON) ===")
    print(print_sample_asset_records_json())
