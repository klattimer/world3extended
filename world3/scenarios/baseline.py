from __future__ import annotations

from typing import Any


def scenario() -> dict[str, Any]:
    return {
        "description": "Baseline gradual decline with moderate adaptation.",
        "overrides": {},
        "shock_schedule": {
            2034: {"hormuz": 0.45},
            2048: {"suez": 0.35},
        },
        "exogenous_shocks": {},
    }
