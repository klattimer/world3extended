from __future__ import annotations

from typing import Any

import numpy as np


class PopulationSystem:
    """Population dynamics with famine, conflict, and climate-mediated mortality."""

    def __init__(self, params: dict[str, Any] | None = None) -> None:
        self.params = params or {}

    def step(self, state: dict[str, float], dt_years: float) -> dict[str, float]:
        population = max(0.1, state["population_billions"])

        fertility_decline = 0.004 * np.log1p(max(0.0, state["industrial_output_index"] - 0.8))
        birth_rate = np.clip(0.015 - fertility_decline - 0.003 * state["financial_stress"], 0.005, 0.028)

        baseline_death = 0.009
        famine_mortality = np.clip(0.02 * state["food_stress"] ** 1.3, 0.0, 0.04)
        climate_mortality = 0.005 * state["climate_damage"]
        conflict_mortality = 0.006 * state["conflict_intensity"]
        health_system_penalty = 0.004 * state["financial_stress"]

        death_rate = np.clip(
            baseline_death + famine_mortality + climate_mortality + conflict_mortality + health_system_penalty,
            0.006,
            0.08,
        )

        net_growth = birth_rate - death_rate
        new_population = np.clip(population * (1.0 + net_growth * dt_years), 0.2, 13.0)

        instability_hit = 0.2 * state["conflict_intensity"] + 0.15 * state["food_stress"]
        political_stability = np.clip(
            state["political_stability"]
            + (-instability_hit + 0.05 * (1.0 - state["financial_stress"])) * dt_years,
            0.0,
            1.0,
        )

        return {
            "population_billions": float(new_population),
            "birth_rate": float(birth_rate),
            "death_rate": float(death_rate),
            "famine_mortality": float(famine_mortality),
            "political_stability": float(political_stability),
        }
