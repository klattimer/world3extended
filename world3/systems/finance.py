from __future__ import annotations

from typing import Any

import numpy as np


class FinanceSystem:
    """Financial fragility channel amplifying real-economy shocks."""

    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params

    def step(self, state: dict[str, float]) -> dict[str, float]:
        p = self.params
        debt_growth_base = float(p["debt_growth_base"])
        fragility_sens = float(p["fragility_sensitivity"])
        infl_energy = float(p["inflation_sensitivity_energy"])
        infl_food = float(p["inflation_sensitivity_food"])
        crisis_threshold = float(p["crisis_threshold"])

        shock_pressure = (
            0.45 * state["energy_shortage"]
            + 0.35 * state["food_stress"]
            + 0.25 * state["conflict_intensity"]
            + 0.2 * state["climate_damage"]
        )

        debt_to_gdp = max(0.3, state["debt_to_gdp"] * (1.0 + debt_growth_base + 0.08 * shock_pressure - 0.02 * state["industrial_output_index"]))
        inflation = max(0.7, state["inflation_index"] * (1.0 + infl_energy * state["energy_shortage"] + infl_food * state["food_stress"]))

        financial_stress = np.clip(
            0.6 * state["financial_stress"]
            + fragility_sens * shock_pressure
            + 0.12 * max(0.0, debt_to_gdp - 2.2)
            + 0.08 * max(0.0, inflation - 1.0),
            0.0,
            1.0,
        )

        banking_instability = float(np.clip(max(0.0, financial_stress - crisis_threshold) * 1.8, 0.0, 1.0))
        currency_instability = float(np.clip(0.5 * financial_stress + 0.15 * state["conflict_intensity"], 0.0, 1.0))

        return {
            "debt_to_gdp": float(debt_to_gdp),
            "inflation_index": float(inflation),
            "financial_stress": float(financial_stress),
            "banking_instability": banking_instability,
            "currency_instability": currency_instability,
        }
