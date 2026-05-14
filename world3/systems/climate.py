from __future__ import annotations

from typing import Any

import numpy as np

try:
    from numba import njit
except Exception:  # pragma: no cover
    def njit(*args: Any, **kwargs: Any):
        def wrapper(func: Any) -> Any:
            return func

        return wrapper


@njit(cache=True)
def _pollution_update(cumulative: float, emissions: float, sink_rate: float, dt_years: float) -> float:
    return cumulative + emissions * dt_years - sink_rate * cumulative * dt_years


class ClimateSystem:
    """Simplified climate-damage feedback from emissions and cumulative pollution."""

    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params

    def step(self, state: dict[str, float], dt_years: float) -> dict[str, float]:
        p = self.params
        emissions_intensity = float(p["emissions_intensity"])
        sink_rate = float(p["sink_rate"])
        warming_sensitivity = float(p["warming_sensitivity"])
        disaster_scale = float(p["disaster_scale"])

        fossil_energy = state["oil_ej"] + state["gas_ej"] + state["coal_ej"]
        emissions = emissions_intensity * fossil_energy * (0.6 + 0.4 * state["industrial_output_index"])

        cumulative_pollution = float(_pollution_update(state["cumulative_pollution"], emissions, sink_rate, dt_years))
        pollution_index = max(0.0, cumulative_pollution / 100.0)

        warming = state["warming_c"] + warming_sensitivity * np.log1p(max(0.0, pollution_index - 0.8)) * dt_years
        climate_damage = np.clip(0.03 + 0.015 * warming**2, 0.0, 0.95)
        crop_damage = np.clip(0.5 * climate_damage + 0.05 * state["shipping_disruption"], 0.0, 0.95)

        disaster_pressure = float(np.clip(disaster_scale * warming * (1.0 + state["climate_damage"]), 0.0, 1.0))
        migration_pressure = float(
            np.clip(
                state["migration_pressure"] * (0.9**dt_years)
                + (0.25 * disaster_pressure + 0.15 * state["food_stress"]) * dt_years,
                0.0,
                1.0,
            )
        )

        return {
            "emissions": float(emissions),
            "cumulative_pollution": cumulative_pollution,
            "pollution_index": float(pollution_index),
            "warming_c": float(warming),
            "climate_damage": float(climate_damage),
            "crop_damage": float(crop_damage),
            "disaster_pressure": disaster_pressure,
            "migration_pressure": migration_pressure,
        }
