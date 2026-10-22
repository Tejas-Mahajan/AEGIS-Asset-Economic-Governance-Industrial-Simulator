"""Data Simulation Module — Smart Industrial Asset Evaluation System.

This module simulates real-time turbofan engine sensor data streams based on the NASA C-MAPSS FD001 dataset.
It provides data cleaning, mapping to standard Asset Record schemas, streaming generators, configurable noise/anomaly injection,
and an Event Injection API.

Usage Examples:
---------------
1. Single Engine Replay Stream:
   >>> from data_simulation import replay_engine
   >>> stream = replay_engine(engine_id=1, delay=0.0)
   >>> record = next(stream)
   >>> print(record["asset_id"], record["health_pct"])

2. Concurrent Multi-Engine Streaming:
   >>> from data_simulation import MultiEngineScheduler
   >>> scheduler = MultiEngineScheduler(engine_ids=[1, 2, 3])
   >>> for record in scheduler.stream_all():
   ...     print(record["asset_id"], record["cycle"])

3. Event Injection API (sensor_spike / manual_failure):
   >>> from data_simulation import EventManager, to_asset_record
   >>> event_mgr = EventManager()
   >>> resp = event_mgr.inject_event({"asset_id": "ENG-001", "event_type": "sensor_spike", "magnitude": 0.5})
   >>> print(resp)

4. Noise, Missing Data & Anomaly Pipeline:
   >>> from data_simulation import PipelineConfig, process_record_pipeline
   >>> config = PipelineConfig(enable_noise=True, noise_rate=0.1, enable_anomaly=True)
   >>> processed = process_record_pipeline(record, history=[], config=config)
"""

from data_simulation.dataset import load_fd001_dataframe, download_fd001, COLUMN_NAMES
from data_simulation.schema_mapper import to_asset_record, SELECTED_SENSORS
from data_simulation.simulator import replay_engine, MultiEngineScheduler
from data_simulation.data_pipeline import (
    inject_noise,
    inject_missing,
    detect_anomaly,
    PipelineConfig,
    process_record_pipeline,
)
from data_simulation.event_api import EventManager

__all__ = [
    "load_fd001_dataframe",
    "download_fd001",
    "COLUMN_NAMES",
    "to_asset_record",
    "SELECTED_SENSORS",
    "replay_engine",
    "MultiEngineScheduler",
    "inject_noise",
    "inject_missing",
    "detect_anomaly",
    "PipelineConfig",
    "process_record_pipeline",
    "EventManager",
]
