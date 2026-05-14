"""
CO2 availability subsystem.

Models CO2 production as industrial byproduct and competing demand (food processing,
agriculture, medical, livestock euthanasia). When CO2 is scarce, livestock culling
capacity is constrained, forcing unsustainable herd sizes and increased feed demand.

Key dynamics:
  - CO2 production scales with industrial output (cement, ammonia, fermentation)
  - Multiple competing demands (food, medical, euthanasia)
  - CO2 scarcity reduces livestock culling capacity
  - Uncullable livestock increases food demand → agricultural stress
  - Compounds food crisis feedback
"""

from __future__ import annotations

from typing import Any

import numpy as np


class CO2AvailabilitySystem:
    """Tracks CO2 production, demand allocation, and livestock culling constraints."""

    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params

    def step(
        self,
        state: dict[str, float],
        industrial_output: float,
        population_billions: float,
        food_index: float,
        dt_years: float,
    ) -> dict[str, float]:
        """
        Update CO2 availability and livestock culling constraints.

        Args:
            state: Current simulation state dict
            industrial_output: Industrial output index
            population_billions: Population in billions
            food_index: Food production index (0-1)
            dt_years: Time step in years

        Returns:
            Updated state variables for CO2 system
        """
        p = self.params

        # === CO2 PRODUCTION ===
        # CO2 as byproduct of cement (~0.5 kg CO2/kg cement), ammonia, fermentation
        # Production scales with industrial output
        co2_production_baseline_mt = float(p["co2_production_baseline_mt"])  # Megatons/year at IO=1.0
        co2_production_mt = co2_production_baseline_mt * industrial_output

        # === CO2 DEMAND ALLOCATION ===
        # Food processing and packaging
        food_demand_co2_mt = float(p["food_processing_co2_per_capita_mt"]) * population_billions * 1e3

        # Medical and healthcare (anaesthesia, surgery, etc.)
        medical_demand_co2_mt = float(p["medical_co2_per_capita_mt"]) * population_billions * 1e3

        # Fertilizer production (Haber-Bosch uses CO2 as feedstock and byproduct)
        fertilizer_demand_co2_fraction = float(p["fertilizer_demand_co2_fraction"])
        fertilizer_co2_demand_mt = co2_production_mt * fertilizer_demand_co2_fraction

        # Livestock euthanasia (culling, slaughter CO2 use for humane dispatch)
        # UK baseline: ~8,000 tons CO2/year for livestock culling nationwide
        # Scale by population + food stress pressure
        euthanasia_baseline_mt = float(p["euthanasia_demand_baseline_mt"])
        food_stress = state.get("food_stress", 0.2)
        euthanasia_demand_mt = euthanasia_baseline_mt * (1.0 + 2.0 * food_stress)  # Demand rises with food crisis

        # === CO2 SCARCITY ===
        total_co2_demand_mt = (
            food_demand_co2_mt + medical_demand_co2_mt + fertilizer_co2_demand_mt + euthanasia_demand_mt
        )
        co2_scarcity_index = 1.0 - np.clip(co2_production_mt / max(total_co2_demand_mt, 0.1), 0.0, 1.0)

        # === LIVESTOCK CULLING CONSTRAINT ===
        # When CO2 scarce, euthanasia capacity is limited
        if co2_scarcity_index > 0.3:
            # CO2 shortage forces prioritization: food/medical > euthanasia
            available_for_euthanasia = max(0.0, co2_production_mt - food_demand_co2_mt - medical_demand_co2_mt)
            culling_capacity = available_for_euthanasia / max(euthanasia_demand_mt, 0.1)
        else:
            culling_capacity = 1.0

        culling_capacity = float(np.clip(culling_capacity, 0.0, 1.0))

        # === FEEDBACK: UNCULLABLE LIVESTOCK ===
        # If culling capacity constrained, livestock herd remains too large
        # Average livestock feed demand = baseline * herd_fraction
        # If herd can't be culled, surplus livestock consume excess feed
        livestock_feed_multiplier = 1.0 + 0.5 * (1.0 - culling_capacity)  # 50% more feed if 50% can't be culled
        livestock_feed_multiplier = float(np.clip(livestock_feed_multiplier, 1.0, 2.5))

        # === FOOD PRODUCTION IMPACT ===
        # Uncullable livestock diverts feed from human consumption (opportunity cost)
        # High feed demand → grain prices rise → imports compete → food security worsens
        livestock_feed_pressure = (1.0 - culling_capacity) * float(p["livestock_feed_pressure_multiplier"])
        livestock_feed_pressure = float(np.clip(livestock_feed_pressure, 0.0, 0.5))

        return {
            "co2_production_mt": float(co2_production_mt),
            "co2_demand_food_mt": float(food_demand_co2_mt),
            "co2_demand_medical_mt": float(medical_demand_co2_mt),
            "co2_demand_fertilizer_mt": float(fertilizer_co2_demand_mt),
            "co2_demand_euthanasia_mt": float(euthanasia_demand_mt),
            "co2_scarcity_index": float(co2_scarcity_index),
            "livestock_culling_capacity": float(culling_capacity),
            "livestock_feed_multiplier": float(livestock_feed_multiplier),
            "livestock_feed_pressure": float(livestock_feed_pressure),
        }
