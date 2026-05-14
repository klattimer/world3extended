from __future__ import annotations

from typing import Any

import numpy as np


class PopulationSystem:
    """Population dynamics with famine, conflict, and climate-mediated mortality."""

    def __init__(self, params: dict[str, Any] | None = None) -> None:
        self.params = params or {}

    def step(self, state: dict[str, float], dt_years: float) -> dict[str, float]:
        population = max(0.1, state["population_billions"])
        prev_population = population

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
        population_change_rate = (new_population - prev_population) / max(prev_population, 1e-6)

        population_ratio = np.clip(new_population / 8.2, 0.15, 1.5)
        labor_force_index = float(np.clip(population_ratio**0.7, 0.2, 1.2))

        migration_pressure = np.clip(
            state.get("migration_pressure", 0.0)
            + (
                0.22 * state["food_stress"]
                + 0.18 * state["conflict_intensity"]
                + 0.12 * state["climate_damage"]
                + 0.5 * max(0.0, -population_change_rate)
                - 0.06 * state["political_stability"]
            )
            * dt_years,
            0.0,
            1.0,
        )

        instability_hit = 0.2 * state["conflict_intensity"] + 0.15 * state["food_stress"]
        political_stability = np.clip(
            state["political_stability"]
            + (-instability_hit + 0.05 * (1.0 - state["financial_stress"])) * dt_years,
            0.0,
            1.0,
        )

        return {
            "population_billions": float(new_population),
            "population_change_rate": float(population_change_rate),
            "labor_force_index": labor_force_index,
            "birth_rate": float(birth_rate),
            "death_rate": float(death_rate),
            "famine_mortality": float(famine_mortality),
            "migration_pressure": float(migration_pressure),
            "political_stability": float(political_stability),
        }
