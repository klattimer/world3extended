from __future__ import annotations

from typing import Any

import numpy as np


class AIComputeSystem:
    """Models compute scaling limits from energy, semiconductor bottlenecks, and diminishing returns."""

    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params

    def step(
        self,
        state: dict[str, float],
        semiconductor_constraint: float,
        available_power_ej: float,
        financial_stress: float,
    ) -> dict[str, float]:
        p = self.params
        base_growth = float(p["annual_compute_growth"])
        efficiency_gain = float(p["efficiency_improvement"])
        diminishing = float(p["diminishing_return_exponent"])
        cooling_multiplier = float(p["cooling_multiplier"])

        compute = max(1e-6, state["ai_compute_index"])
        scaling_penalty = compute**diminishing
        constrained_growth = base_growth / (1.0 + scaling_penalty)

        bottleneck = float(p["semiconductor_bottleneck_sensitivity"]) * semiconductor_constraint
        finance_penalty = 0.25 * financial_stress
        real_growth = max(-0.2, constrained_growth - bottleneck - finance_penalty)

        new_compute = max(0.2, compute * (1.0 + real_growth))

        gains_decay = 1.0 / (1.0 + 0.4 * scaling_penalty)
        new_efficiency = min(4.0, state["ai_efficiency_index"] * (1.0 + efficiency_gain * gains_decay))

        baseline_power = float(p["baseline_ai_power_ej"])
        raw_power = baseline_power * new_compute / max(new_efficiency, 1e-6)
        ai_power = raw_power * cooling_multiplier

        power_cap = max(1.0, available_power_ej * (0.06 + 0.08 * (1.0 - financial_stress)))
        curtailed = max(0.0, ai_power - power_cap)
        if curtailed > 0.0:
            ai_power = power_cap
            new_compute *= max(0.7, 1.0 - curtailed / max(raw_power, 1e-6) * 0.3)

        capital_competition = float(np.clip(float(p["capital_competition_weight"]) * new_compute, 0.0, 0.5))

        return {
            "ai_compute_index": float(new_compute),
            "ai_efficiency_index": float(new_efficiency),
            "ai_power_demand_ej": float(ai_power),
            "ai_power_curtailed_ej": float(curtailed),
            "ai_capital_competition": capital_competition,
        }
