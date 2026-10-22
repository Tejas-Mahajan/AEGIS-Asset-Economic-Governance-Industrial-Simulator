# Data Schemas Specification

## Section 1: Asset Record
- `asset_id`: str
- `asset_type`: str (e.g. "physical")
- `cycle`: int
- `timestamp`: str (ISO-8601 string)
- `sensor_readings`: dict (mapping sensor names to numerical values)
- `health_pct`: float (0.0 to 100.0)
- `data_quality_flag`: str (e.g. "ok", "missing")
- `anomaly_detected`: bool
- `metadata`: dict

## Section 2: RUL Prediction Record
- `asset_id`: str
- `rul_cycles`: float
- `rul_cycles_confidence_low`: float
- `rul_cycles_confidence_high`: float
- `rul_days`: Optional[float] (null for MVP)

## Section 3: Ranking Output
- `asset_id`: str
- `priority_rank`: int (1..N permutation)
- `criticality_score`: float
- `weights_used`: dict (AHP weights for safety, cost, environment)
- `consistency_ratio`: float (CR < 0.1)
- `metadata`: dict

## Section 4: Risk/Budget Output
- `asset_id`: str
- `cvar_95`: float
- `expected_cost`: float
- `recommended_budget_allocation`: float
- `baseline_reactive_cost`: float
- `predictive_savings`: float
- `budget_pool_id`: str (default: "default")
- `metadata`: dict

## Section 5: Event Injection API
### Request
- `asset_id`: str
- `event_type`: str (e.g. "sensor_spike", "manual_failure")
- `magnitude`: float

### Response
- `asset_id`: str
- `accepted`: bool
- `affected_cycle`: int
- `message`: str
