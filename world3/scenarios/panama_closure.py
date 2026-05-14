from __future__ import annotations

from typing import Any


def scenario() -> dict[str, Any]:
    return {
        "description": "Multi-year Panama Canal disruption with rerouting and trade fragmentation stress.",
        "overrides": {
            "geopolitics": {
                    "baseline_tension": 0.29,
                "random_event_scale": 0.1,
            },
            "trade": {
                "fragmentation_drift": 0.022,
                "rerouting_penalty": 0.34,
            },
            "finance": {
                "fragility_sensitivity": 0.4,
            },
        },
        "shock_schedule": {
            2028: {"panama": 0.95},
            2029: {"panama": 0.9, "suez": 0.3},
            2030: {"panama": 0.75},
            2031: {"panama": 0.6},
        },
        "exogenous_shocks": {},
    }
