from __future__ import annotations

from typing import Any


def scenario() -> dict[str, Any]:
    return {
        "description": "Nitrogen-phosphate-potash supply crunch causing persistent food stress.",
        "overrides": {
            "agriculture": {
                "fertilizer_dependency": 0.5,
            },
            "geopolitics": {
                "baseline_tension": 0.33,
            },
        },
        "shock_schedule": {},
        "exogenous_shocks": {
            2028: {"fertilizer_shock": 0.35},
            2029: {"fertilizer_shock": 0.45},
            2030: {"fertilizer_shock": 0.4},
        },
    }
