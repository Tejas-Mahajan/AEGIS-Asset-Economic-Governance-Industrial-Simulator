import time
from typing import Dict, Generator, List, Optional, Union
import pandas as pd

from data_simulation.dataset import load_fd001_dataframe
from data_simulation.schema_mapper import to_asset_record

_DATASET_CACHE: Optional[pd.DataFrame] = None


def get_dataset() -> pd.DataFrame:
    """Lazy-load and cache the C-MAPSS dataset."""
    global _DATASET_CACHE
    if _DATASET_CACHE is None:
        _DATASET_CACHE = load_fd001_dataframe()
    return _DATASET_CACHE


def replay_engine(
    engine_id: int,
    df: Optional[pd.DataFrame] = None,
    delay: float = 0.0,
) -> Generator[Dict, None, None]:
    """Generator yielding Asset Records for a specific engine one cycle at a time.

    Args:
        engine_id: Engine unit number (e.g. 1, 2, 3...).
        df: Optional dataframe override.
        delay: Configurable sleep delay in seconds between cycle yields.

    Yields:
        Asset Record dict matching SCHEMAS.md Section 1.
    """
    if df is None:
        df = get_dataset()

    engine_data = df[df["engine_id"] == engine_id].sort_values("cycle")
    if engine_data.empty:
        raise ValueError(f"No engine data found for engine_id={engine_id}")

    engine_max_cycle = int(engine_data["cycle"].max())

    for _, row in engine_data.iterrows():
        record = to_asset_record(row, engine_max_cycle)
        if delay > 0:
            time.sleep(delay)
        yield record


class MultiEngineScheduler:
    """Round-robin scheduler to stream 3-5 engines concurrently without thread-contention.

    Why Round-Robin Scheduler?
    1. Deterministic and lightweight: Avoids thread context-switching overhead and race conditions.
    2. Streamlit & UI Friendly: Works natively inside single-threaded or event-driven frameworks.
    3. Guarantees ordering: Yields records from multiple engine streams in fair round-robin turns.
    """

    def __init__(self, engine_ids: List[int], delay: float = 0.0, df: Optional[pd.DataFrame] = None):
        self.engine_ids = engine_ids
        self.delay = delay
        self.df = df if df is not None else get_dataset()
        self._generators = {
            eng_id: replay_engine(eng_id, df=self.df, delay=self.delay)
            for eng_id in engine_ids
        }

    def stream_all(self) -> Generator[Dict, None, None]:
        """Yield records from all engines in round-robin order until all complete."""
        active_engines = list(self.engine_ids)

        while active_engines:
            for eng_id in list(active_engines):
                try:
                    record = next(self._generators[eng_id])
                    yield record
                except StopIteration:
                    active_engines.remove(eng_id)
