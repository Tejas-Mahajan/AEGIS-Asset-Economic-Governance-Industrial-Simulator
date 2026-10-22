import copy
import math
import random
from typing import Any, Dict, List, Optional


def inject_noise(
    record: Dict[str, Any], rate: float = 0.1, noise_scale: float = 0.05, seed: Optional[int] = None
) -> Dict[str, Any]:
    """Randomly perturbs a % of sensor_readings in record.

    If rate == 0, returns record completely unchanged.
    """
    if seed is not None:
        random.seed(seed)

    rec = copy.deepcopy(record)
    if rate <= 0.0:
        return rec

    sensors = rec.get("sensor_readings", {})
    for key, val in sensors.items():
        if val is not None and random.random() < rate:
            # Perturb by Gaussian noise scaled by noise_scale
            noise = random.gauss(0, abs(val) * noise_scale if val != 0 else noise_scale)
            sensors[key] = round(val + noise, 4)

    return rec


def inject_missing(
    record: Dict[str, Any], rate: float = 0.1, seed: Optional[int] = None
) -> Dict[str, Any]:
    """Randomly drops a % of readings and sets data_quality_flag: 'missing'.

    If rate == 0, returns record completely unchanged.
    """
    if seed is not None:
        random.seed(seed)

    rec = copy.deepcopy(record)
    if rate <= 0.0:
        return rec

    sensors = rec.get("sensor_readings", {})
    missing_occurred = False

    for key in list(sensors.keys()):
        if random.random() < rate:
            sensors[key] = None
            missing_occurred = True

    if missing_occurred:
        rec["data_quality_flag"] = "missing"

    return rec


def detect_anomaly(
    record: Dict[str, Any], history: List[Dict[str, Any]], n_std: float = 3.0
) -> Dict[str, Any]:
    """Flags anomaly_detected: true if a reading jumps > n_std standard deviations from recent history."""
    rec = copy.deepcopy(record)
    sensors = rec.get("sensor_readings", {})

    if not history or len(history) < 3:
        rec["anomaly_detected"] = rec.get("anomaly_detected", False)
        return rec

    anomaly_found = False

    for key, val in sensors.items():
        if val is None:
            continue

        # Extract historical values for this sensor
        hist_vals = [
            h["sensor_readings"][key]
            for h in history
            if "sensor_readings" in h and h["sensor_readings"].get(key) is not None
        ]

        if len(hist_vals) < 3:
            continue

        mean = sum(hist_vals) / float(len(hist_vals))
        variance = sum((x - mean) ** 2 for x in hist_vals) / float(len(hist_vals))
        std_dev = math.sqrt(variance)

        if std_dev > 1e-6:
            z_score = abs(val - mean) / std_dev
            if z_score > n_std:
                anomaly_found = True
                break
        else:
            # If historical std_dev is near 0, any noticeable delta (> 0.01) is an anomaly jump
            if abs(val - mean) > 0.01:
                anomaly_found = True
                break

    rec["anomaly_detected"] = rec.get("anomaly_detected", False) or anomaly_found
    return rec


class PipelineConfig:
    """Config flags to independently toggle noise, missing data, and anomaly detection."""

    def __init__(
        self,
        enable_noise: bool = False,
        noise_rate: float = 0.1,
        enable_missing: bool = False,
        missing_rate: float = 0.1,
        enable_anomaly: bool = False,
        anomaly_n_std: float = 3.0,
    ):
        self.enable_noise = enable_noise
        self.noise_rate = noise_rate
        self.enable_missing = enable_missing
        self.missing_rate = missing_rate
        self.enable_anomaly = enable_anomaly
        self.anomaly_n_std = anomaly_n_std


def process_record_pipeline(
    record: Dict[str, Any], history: List[Dict[str, Any]], config: PipelineConfig
) -> Dict[str, Any]:
    """Process an Asset Record through noise, missing data, and anomaly detection steps."""
    rec = copy.deepcopy(record)

    if config.enable_noise:
        rec = inject_noise(rec, rate=config.noise_rate)

    if config.enable_missing:
        rec = inject_missing(rec, rate=config.missing_rate)

    if config.enable_anomaly:
        rec = detect_anomaly(rec, history=history, n_std=config.anomaly_n_std)
    else:
        rec["anomaly_detected"] = False

    return rec
