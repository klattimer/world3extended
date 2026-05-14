from __future__ import annotations

from typing import Any

import numpy as np


class IndustrySystem:
    """Industrial production and capital maintenance under energy and instability pressure."""

    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params

    def step(self, state: dict[str, float], dt_years: float) -> dict[str, float]:
        p = self.params
        maintenance_need = float(p["maintenance_need"])
        resilience = float(p["supply_chain_resilience"])
        depreciation = float(p["capital_depreciation"])
        energy_intensity = float(p["energy_intensity"])

        available_energy_for_industry = max(0.0, state["energy_supply_ej"] - state["ai_power_demand_ej"])
        required_energy = max(20.0, state["energy_demand_ej"] * energy_intensity)
        energy_factor = np.clip(available_energy_for_industry / required_energy, 0.0, 1.2)
        liquid_fuel_factor = np.clip(1.0 - 0.85 * state.get("liquid_fuel_shortage", 0.0), 0.05, 1.0)
        labor_factor = np.clip(state.get("labor_force_index", 1.0), 0.2, 1.2)

        disruption_penalty = (
            0.25 * state["shipping_disruption"]
            + 0.2 * (1.0 - resilience) * state["trade_fragmentation"]
            + 0.2 * state["financial_stress"]
            + 0.15 * state["conflict_intensity"]
            + 0.1 * state["climate_damage"]
            + state["ai_capital_competition"]
        )

        gross_output = (
            state["industrial_output_index"]
            * energy_factor
            * liquid_fuel_factor
            * labor_factor
            * max(0.12, 1.0 - disruption_penalty)
        )
        adaptation = 0.015 * (1.0 - state["financial_stress"]) * (1.0 - state["trade_fragmentation"]) * dt_years
        industrial_output = np.clip(
            state["industrial_output_index"] + (gross_output - state["industrial_output_index"]) * dt_years + adaptation,
            0.005,
            2.0,
        )

        maintenance_gap = max(0.0, maintenance_need - 0.06 * industrial_output)
        industrial_capital = np.clip(
            state["industrial_capital_index"] * (1.0 - (depreciation + maintenance_gap) * dt_years)
            + 0.03 * industrial_output * dt_years,
            0.01,
            2.0,
        )

        return {
            "industrial_output_index": float(industrial_output),
            "industrial_capital_index": float(industrial_capital),
        }
