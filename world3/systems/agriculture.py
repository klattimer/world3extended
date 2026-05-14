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
        liquid_fuel_penalty = 1.0 - 0.9 * state.get("liquid_fuel_shortage", 0.0)
        shipping_penalty = 1.0 - 0.7 * state["shipping_disruption"]
        climate_penalty = 1.0 - float(p["climate_sensitivity"]) * state["crop_damage"]
        irrigation_penalty = 1.0 - float(p["irrigation_stress"]) * (0.4 + state["warming_c"] / 5.0)
        fert_penalty = 1.0 - float(p["fertilizer_dependency"]) * (1.0 - fertilizer_blend)
        labor_penalty = np.clip(state.get("labor_force_index", 1.0), 0.25, 1.2)

        # === NEW: Water stress penalty ===
        # Water system diverts potable water to data centre cooling
        # Agricultural water stress directly reduces irrigation capacity
        water_stress = state.get("agricultural_water_stress", 0.0)
        water_penalty = 1.0 - 0.6 * water_stress

        # === NEW: CO2 scarcity feedback ===
        # CO2 shortage prevents livestock culling → unsustainable herds → feed demand surge
        # Uncullable livestock compete with human food production
        livestock_feed_pressure = state.get("livestock_feed_pressure", 0.0)
        co2_penalty = 1.0 - 0.5 * livestock_feed_pressure

        shock_penalty = 1.0 - shocks.get("fertilizer_shock", 0.0)

        raw_food = (
            state["food_index"]
            * max(0.25, energy_penalty) ** dt_years
            * max(0.1, liquid_fuel_penalty) ** dt_years
            * max(0.2, shipping_penalty) ** dt_years
            * max(0.2, climate_penalty) ** dt_years
            * max(0.2, fert_penalty) ** dt_years
            * labor_penalty**dt_years
            * max(0.3, irrigation_penalty) ** dt_years
            * max(0.3, water_penalty) ** dt_years
            * max(0.4, co2_penalty) ** dt_years
            * max(0.25, shock_penalty) ** dt_years
        )

        adaptive_recovery = 0.015 * state["industrial_output_index"] * (1.0 - state["food_stress"]) * dt_years
        food_index = np.clip(raw_food + adaptive_recovery, 0.02, 1.5)

        food_per_capita = food_index / max(0.1, state["population_billions"] / 8.2)
        food_stress = float(np.clip(1.0 - food_per_capita, 0.0, 1.0))

        return {
            "food_index": float(food_index),
            "food_stress": food_stress,
            "fertilizer_effective_index": float(np.clip(fertilizer_blend, 0.0, 1.2)),
        }
