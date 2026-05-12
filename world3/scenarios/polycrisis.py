from __future__ import annotations

from typing import Any


def scenario() -> dict[str, Any]:
    return {
        "description": "Unified all-hazards cascade combining AI arms race, Hormuz/Panama/Suez chokepoint shocks, Taiwan semiconductor conflict, and fertilizer crisis.",
        "overrides": {
            "geopolitics": {
                "baseline_tension": 0.5,
                "random_event_scale": 0.14,
                "escalation_sensitivity": 0.58,
            },
            "energy": {
                "depletion": {
                    "oil_annual": 0.03,
                    "gas_annual": 0.02,
                    "coal_annual": 0.01,
                },
                "renewables_growth": 0.03,
            },
            "finance": {
                "fragility_sensitivity": 0.5,
            },
            "trade": {
                "fragmentation_drift": 0.035,
                "rerouting_penalty": 0.38,
            },
            "ai_compute": {
                "annual_compute_growth": 0.36,
                "capital_competition_weight": 0.18,
                "baseline_ai_power_ej": 12.0,
                "semiconductor_bottleneck_sensitivity": 0.65,
            },
            "agriculture": {
                "fertilizer_dependency": 0.5,
            },
        },
        "shock_schedule": {
            2028: {"panama": 0.95, "hormuz": 0.8},
            2029: {"hormuz": 0.95, "panama": 0.9, "suez": 0.95},
            2030: {"hormuz": 0.9, "panama": 0.75, "suez": 0.9},
            2031: {"hormuz": 0.8, "panama": 0.6, "suez": 0.7, "taiwan_semis": 0.95},
            2032: {"panama": 0.5, "taiwan_semis": 0.9},
            2033: {"taiwan_semis": 0.75},
            2037: {"taiwan_semis": 0.75},
        },
        "exogenous_shocks": {
            2028: {"fertilizer_shock": 0.35},
            2029: {"fertilizer_shock": 0.45},
            2030: {"fertilizer_shock": 0.4},
            2031: {"fertilizer_shock": 0.3},
        },
    }
