from __future__ import annotations

from typing import Any


def scenario() -> dict[str, Any]:
    return {
        "description": "AI energy arms race with rapid compute growth and stronger power competition.",
        "overrides": {
            "ai_compute": {
                "annual_compute_growth": 0.36,
                "capital_competition_weight": 0.18,
                "baseline_ai_power_ej": 12.0,
            },
            "energy": {
                "renewables_growth": 0.03,
            },
        },
        "shock_schedule": {
            2031: {"taiwan_semis": 0.65},
            2037: {"taiwan_semis": 0.75},
        },
        "exogenous_shocks": {},
    }
