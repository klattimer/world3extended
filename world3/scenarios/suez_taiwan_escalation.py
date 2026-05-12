from __future__ import annotations

from typing import Any


def scenario() -> dict[str, Any]:
    return {
        "description": "High-escalation sequence with Suez control conflict followed by Taiwan semiconductor war shock.",
        "overrides": {
            "geopolitics": {
                "baseline_tension": 0.5,
                "random_event_scale": 0.14,
                "escalation_sensitivity": 0.58,
            },
            "trade": {
                "fragmentation_drift": 0.035,
                "rerouting_penalty": 0.38,
            },
            "finance": {
                "fragility_sensitivity": 0.5,
            },
            "ai_compute": {
                "annual_compute_growth": 0.34,
                "semiconductor_bottleneck_sensitivity": 0.65,
            },
            "energy": {
                "depletion": {
                    "oil_annual": 0.03,
                    "gas_annual": 0.02,
                    "coal_annual": 0.01,
                }
            },
        },
        "shock_schedule": {
            2029: {"suez": 0.95},
            2030: {"suez": 0.9, "hormuz": 0.6},
            2031: {"taiwan_semis": 0.95, "suez": 0.7},
            2032: {"taiwan_semis": 0.9, "panama": 0.5},
            2033: {"taiwan_semis": 0.75},
        },
        "exogenous_shocks": {
            2030: {"fertilizer_shock": 0.25},
            2031: {"fertilizer_shock": 0.3},
        },
    }
