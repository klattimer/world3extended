from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class GeopoliticsOutput:
    conflict_intensity: float
    sanctions_level: float
    chokepoint_disruption: dict[str, float]
    political_stability_delta: float


class GeopoliticsSystem:
    """Models conflict escalation and stochastic chokepoint disruptions."""

    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params

    def step(
        self,
        state: dict[str, float],
        trade_fragmentation: float,
        rng: np.random.Generator,
        forced_shocks: dict[str, float] | None = None,
    ) -> GeopoliticsOutput:
        baseline_tension = float(self.params["baseline_tension"])
        escalation_sensitivity = float(self.params["escalation_sensitivity"])
        sanctions_sensitivity = float(self.params["sanctions_sensitivity"])
        event_scale = float(self.params["random_event_scale"])

        fragility_pressure = state["financial_stress"] + state["energy_shortage"] + trade_fragmentation
        climate_pressure = state["climate_damage"] * 0.8 + state["migration_pressure"] * 0.6
        random_draw = float(rng.normal(0.0, event_scale))

        conflict_intensity = np.clip(
            baseline_tension + escalation_sensitivity * (fragility_pressure + climate_pressure) + random_draw,
            0.0,
            1.0,
        )
        sanctions_level = np.clip(
            sanctions_sensitivity * conflict_intensity + 0.2 * trade_fragmentation,
            0.0,
            1.0,
        )

        disruptions: dict[str, float] = {}
        for cp_name, cp_data in self.params["chokepoints"].items():
            risk = float(cp_data["baseline_risk"])
            risk = np.clip(risk + 0.35 * conflict_intensity + 0.15 * climate_pressure, 0.0, 0.95)
            event_occurs = float(rng.uniform()) < risk
            severity = float(rng.uniform(0.35, 0.9)) if event_occurs else 0.0
            disruptions[cp_name] = severity

        if forced_shocks:
            for name, sev in forced_shocks.items():
                disruptions[name] = float(np.clip(sev, 0.0, 1.0))

        political_stability_delta = -0.08 * conflict_intensity - 0.06 * sanctions_level

        return GeopoliticsOutput(
            conflict_intensity=float(conflict_intensity),
            sanctions_level=float(sanctions_level),
            chokepoint_disruption=disruptions,
            political_stability_delta=float(political_stability_delta),
        )
