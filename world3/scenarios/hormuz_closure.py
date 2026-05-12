from __future__ import annotations

from typing import Any


def scenario() -> dict[str, Any]:
    return {
        "description": "Prolonged Strait of Hormuz closure and secondary sanctions shock.",
        "overrides": {
            "geopolitics": {
                "baseline_tension": 0.35,
            },
            "trade": {
                "fragmentation_drift": 0.02,
            },
        },
        "shock_schedule": {
            2029: {"hormuz": 0.95},
            2030: {"hormuz": 0.9, "suez": 0.5},
            2031: {"hormuz": 0.8},
        },
        "exogenous_shocks": {},
    }
