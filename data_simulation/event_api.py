import copy
from typing import Any, Dict, List, Optional

RESPONSE_FIELDS = {"asset_id", "accepted", "affected_cycle", "message"}


class EventManager:
    """Manages event injection requests and applies them to asset stream records."""

    def __init__(self):
        # Pending events per asset_id: asset_id -> list of event dicts
        self._pending_events: Dict[str, List[Dict[str, Any]]] = {}
        # Tracks latest cycle per asset_id
        self._latest_cycle: Dict[str, int] = {}

    def update_latest_cycle(self, asset_id: str, cycle: int) -> None:
        """Register the current cycle count for an asset."""
        self._latest_cycle[asset_id] = cycle

    def inject_event(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process an Event Injection Request matching SCHEMAS.md section 5.

        Request shape:
          - asset_id: str
          - event_type: str ("sensor_spike" | "manual_failure")
          - magnitude: float

        Response shape:
          - asset_id: str
          - accepted: bool
          - affected_cycle: int
          - message: str
        """
        asset_id = str(request.get("asset_id", ""))
        event_type = str(request.get("event_type", ""))
        try:
            magnitude = float(request.get("magnitude", 1.0))
        except (ValueError, TypeError):
            magnitude = 1.0

        if event_type not in ("sensor_spike", "manual_failure"):
            return {
                "asset_id": asset_id,
                "accepted": False,
                "affected_cycle": self._latest_cycle.get(asset_id, 0),
                "message": f"Unsupported event_type: '{event_type}'. Allowed: sensor_spike, manual_failure.",
            }

        # Calculate affected cycle (next cycle)
        curr_cycle = self._latest_cycle.get(asset_id, 0)
        affected_cycle = curr_cycle + 1

        event_obj = {
            "event_type": event_type,
            "magnitude": magnitude,
            "target_cycle": affected_cycle,
        }

        if asset_id not in self._pending_events:
            self._pending_events[asset_id] = []
        self._pending_events[asset_id].append(event_obj)

        return {
            "asset_id": asset_id,
            "accepted": True,
            "affected_cycle": affected_cycle,
            "message": f"Successfully scheduled '{event_type}' (magnitude={magnitude}) for cycle {affected_cycle}.",
        }

    def apply_events(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Apply any pending events for record's asset_id to modify the emitted record."""
        rec = copy.deepcopy(record)
        asset_id = rec["asset_id"]
        cycle = rec["cycle"]
        self.update_latest_cycle(asset_id, cycle)

        if asset_id not in self._pending_events or not self._pending_events[asset_id]:
            return rec

        events_to_apply = self._pending_events[asset_id]
        remaining_events = []

        for evt in events_to_apply:
            event_type = evt["event_type"]
            mag = evt["magnitude"]

            if event_type == "sensor_spike":
                # Increase all sensor values by magnitude factor (e.g. mag * standard delta or 1.5x)
                sensors = rec.get("sensor_readings", {})
                for k, v in sensors.items():
                    if v is not None:
                        sensors[k] = round(v * (1.0 + mag), 4)
                rec["anomaly_detected"] = True

            elif event_type == "manual_failure":
                # Drop health_pct to 0 and flag anomaly
                rec["health_pct"] = 0.0
                rec["anomaly_detected"] = True

        # Clear applied events
        self._pending_events[asset_id] = remaining_events
        return rec
