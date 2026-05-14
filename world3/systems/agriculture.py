from __future__ import annotations

from typing import Any

import numpy as np


class AgricultureSystem:
    """Simulates food production under fertilizer, climate, trade, and energy constraints."""

    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params

    def step(self, state: dict[str, float], shocks: dict[str, float], dt_years: float) -> dict[str, float]:
        p = self.params

        fertilizer_blend = (
            0.45 * state["nitrogen_supply_index"]
            + 0.3 * state["phosphate_supply_index"]
            + 0.25 * state["potash_supply_index"]
        )

        energy_penalty = 1.0 - float(p["diesel_dependency"]) * state["energy_shortage"]
        shipping_penalty = 1.0 - 0.7 * state["shipping_disruption"]
        climate_penalty = 1.0 - float(p["climate_sensitivity"]) * state["crop_damage"]
        irrigation_penalty = 1.0 - float(p["irrigation_stress"]) * (0.4 + state["warming_c"] / 5.0)
        fert_penalty = 1.0 - float(p["fertilizer_dependency"]) * (1.0 - fertilizer_blend)

        shock_penalty = 1.0 - shocks.get("fertilizer_shock", 0.0)

        raw_food = (
            state["food_index"]
            * max(0.25, energy_penalty) ** dt_years
            * max(0.2, shipping_penalty) ** dt_years
            * max(0.2, climate_penalty) ** dt_years
            * max(0.2, fert_penalty) ** dt_years
            * max(0.3, irrigation_penalty) ** dt_years
            * max(0.25, shock_penalty) ** dt_years
        )

        adaptive_recovery = 0.015 * state["industrial_output_index"] * (1.0 - state["food_stress"]) * dt_years
        food_index = np.clip(raw_food + adaptive_recovery, 0.1, 1.5)

        food_per_capita = food_index / max(0.1, state["population_billions"] / 8.2)
        food_stress = float(np.clip(1.0 - food_per_capita, 0.0, 1.0))

        return {
            "food_index": float(food_index),
            "food_stress": food_stress,
            "fertilizer_effective_index": float(np.clip(fertilizer_blend, 0.0, 1.2)),
        }
