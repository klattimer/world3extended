from __future__ import annotations

from world3.systems.population import PopulationSystem


def test_population_death_rate_rises_under_stress() -> None:
    system = PopulationSystem()
    calm_state = {
        "population_billions": 8.2,
        "industrial_output_index": 1.0,
        "financial_stress": 0.1,
        "food_stress": 0.05,
        "climate_damage": 0.06,
        "conflict_intensity": 0.1,
        "political_stability": 0.8,
    }
    crisis_state = {
        "population_billions": 8.2,
        "industrial_output_index": 0.6,
        "financial_stress": 0.8,
        "food_stress": 0.8,
        "climate_damage": 0.3,
        "conflict_intensity": 0.7,
        "political_stability": 0.5,
    }

    calm = system.step(calm_state, dt_years=1.0)
    crisis = system.step(crisis_state, dt_years=1.0)

    assert crisis["death_rate"] > calm["death_rate"]
    assert crisis["famine_mortality"] > calm["famine_mortality"]
