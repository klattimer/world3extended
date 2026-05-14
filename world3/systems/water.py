"""
Water system subsystem.

Models water availability, data centre cooling demand, agricultural water stress,
and thermal pollution feedback to the climate system.

Key dynamics:
  - AI data centres demand cooling water proportional to compute growth
  - Potable water diverted from agriculture to data centres
  - Irrigation stress reduces agricultural yields
  - Thermal pollution affects ecosystem health and climate damage
"""

from __future__ import annotations

from typing import Any

import numpy as np


class WaterSystem:
    """Tracks freshwater availability, cooling demands, and agricultural water stress."""

    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params

    def step(
        self,
        state: dict[str, float],
        ai_compute_index: float,
        population_billions: float,
        industrial_output: float,
        dt_years: float,
    ) -> dict[str, float]:
        """
        Update water state variables.

        Args:
            state: Current simulation state dict
            ai_compute_index: AI compute growth factor (1.0 = baseline)
            population_billions: Population in billions
            industrial_output: Industrial output index
            dt_years: Time step in years

        Returns:
            Updated state variables for water system
        """
        p = self.params

        # === DATA CENTRE COOLING DEMAND ===
        # AI compute scales cooling water demand exponentially with compute growth
        baseline_ai_power_ej = float(p["baseline_ai_power_ej"])
        cooling_multiplier = float(p["cooling_multiplier"])
        # Cooling water demand in km³/year (proportional to power in EJ)
        # Baseline: ~8 EJ → ~0.5 km³/year, scaled by compute index
        ai_cooling_demand_km3 = 0.06 * baseline_ai_power_ej * ai_compute_index * cooling_multiplier

        # === AGRICULTURAL WATER DEMAND ===
        # Based on population and baseline per-capita requirement
        # World baseline: ~70,000 km³/year for ~8B people
        human_consumption_per_capita = float(p["human_consumption_per_capita_km3"])  # km³ per person per year
        human_water_demand_km3 = population_billions * human_consumption_per_capita

        # Agricultural water (irrigation) as fraction of total demand
        agricultural_fraction = float(p["agricultural_fraction"])
        agricultural_water_demand_km3 = human_water_demand_km3 * agricultural_fraction / (1.0 - agricultural_fraction)

        # === POTABLE WATER SUPPLY ===
        # Start with renewable freshwater availability (including groundwater depletion)
        renewable_freshwater_km3 = float(p["renewable_freshwater_km3"])
        groundwater_depletion_rate = float(p["groundwater_depletion_rate"])

        # Groundwater availability declines due to over-extraction
        groundwater_remaining = state["groundwater_remaining_km3"] * max(0.0, 1.0 - groundwater_depletion_rate * dt_years)
        total_potable_available = renewable_freshwater_km3 + groundwater_remaining

        # === WATER ALLOCATION ===
        # Data centre cooling claims first (non-negotiable industrial demand)
        # Then human consumption
        # Then agriculture gets what's left

        water_to_cooling = min(ai_cooling_demand_km3, total_potable_available * 0.3)  # Cap cooling at 30% of potable
        remaining_after_cooling = total_potable_available - water_to_cooling

        # Human consumption is prioritized over irrigation
        water_to_human = min(human_water_demand_km3, remaining_after_cooling * 0.8)  # Reserve some for ecosystem
        remaining_for_agriculture = max(0.0, remaining_after_cooling - water_to_human)

        # Agricultural water stress: ratio of demand to available
        agricultural_stress = 1.0 - np.clip(remaining_for_agriculture / max(agricultural_water_demand_km3, 0.1), 0.0, 1.0)

        # === THERMAL POLLUTION ===
        # Data centre cooling releases warm water to hydrosphere
        # Thermal energy ~= power * (1 - efficiency_loss)
        thermal_energy_tj = ai_cooling_demand_km3 * 4.18e9  # Convert km³ water to thermal energy
        # Scale to contribute to warming feedback
        thermal_pollution_index = float(p["thermal_pollution_multiplier"]) * thermal_energy_tj / 1e12

        # === WATER STRESS INDEX ===
        # Combines agricultural water stress with total demand vs supply
        total_water_demand = agricultural_water_demand_km3 + human_water_demand_km3 + ai_cooling_demand_km3
        water_shortage = 1.0 - np.clip(total_potable_available / max(total_water_demand, 0.1), 0.0, 1.0)
        water_stress_index = float(np.clip(0.6 * agricultural_stress + 0.4 * water_shortage, 0.0, 1.0))

        # === FEEDBACK: WATER CONSTRAINTS ON HUMAN CONSUMPTION ===
        # If water stress severe, human consumption constrained → health impacts
        human_water_scarcity = 1.0 - np.clip(water_to_human / max(human_water_demand_km3, 0.01), 0.0, 1.0)

        return {
            "groundwater_remaining_km3": float(groundwater_remaining),
            "water_to_cooling_km3": float(water_to_cooling),
            "water_to_human_km3": float(water_to_human),
            "water_to_agriculture_km3": float(remaining_for_agriculture),
            "agricultural_water_stress": float(agricultural_stress),
            "water_stress_index": float(water_stress_index),
            "human_water_scarcity": float(human_water_scarcity),
            "thermal_pollution_index": float(thermal_pollution_index),
            "ai_cooling_demand_km3": float(ai_cooling_demand_km3),
        }
