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
def _net_energy(gross: float, eroi: float) -> float:
    if eroi <= 1.01:
        return gross * 0.05
    return gross * (1.0 - 1.0 / eroi)


class EnergySystem:
    """Tracks fossil depletion, EROI decline, and low-carbon expansion under constraints."""

    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params

    def step(
        self,
        state: dict[str, float],
        trade_flow: float,
        instability: float,
        finance_stress: float,
    ) -> dict[str, float]:
        p = self.params
        decay = float(p["infrastructure_decay"])

        fossil_sources = ("oil", "gas", "coal")
        outputs: dict[str, float] = {}
        total_gross = 0.0
        total_net = 0.0

        for src in fossil_sources:
            level_key = f"{src}_ej"
            eroi_key = f"{src}_eroi"
            depletion = float(p["depletion"][f"{src}_annual"])
            eroi_decline = float(p["eroi_decline"][src])

            remaining = max(0.0, state[level_key] * (1.0 - depletion))
            eroi = max(2.5, state[eroi_key] * (1.0 - eroi_decline))
            extraction_penalty = np.clip(1.0 - 0.35 * instability - 0.22 * finance_stress, 0.45, 1.02)
            trade_penalty = np.clip(0.7 + 0.3 * trade_flow, 0.5, 1.0)
            gross = remaining * extraction_penalty * trade_penalty

            outputs[level_key] = float(gross)
            outputs[eroi_key] = float(eroi)
            total_gross += gross
            total_net += _net_energy(gross, eroi)

        renewables_growth = float(p["renewables_growth"])
        nuclear_growth = float(p["nuclear_growth"])
        build_penalty = np.clip(1.0 - 0.3 * finance_stress - 0.2 * instability, 0.5, 1.0)

        renewables = max(0.0, state["renewables_ej"] * (1.0 + renewables_growth * build_penalty - decay))
        nuclear = max(0.0, state["nuclear_ej"] * (1.0 + nuclear_growth * build_penalty - 0.7 * decay))

        outputs["renewables_ej"] = float(renewables)
        outputs["nuclear_ej"] = float(nuclear)

        total_gross += renewables + nuclear
        total_net += _net_energy(renewables, state["renewables_eroi"]) + _net_energy(nuclear, state["nuclear_eroi"])

        demand = max(100.0, state["energy_demand_ej"] * (1.0 + 0.012 * state["population_billions"] - 0.02 * finance_stress))
        shortage = float(np.clip((demand - total_net) / max(demand, 1e-6), 0.0, 1.0))

        outputs.update(
            {
                "energy_supply_ej": float(total_net),
                "energy_gross_supply_ej": float(total_gross),
                "energy_demand_ej": float(demand),
                "energy_shortage": shortage,
                "energy_price_index": float(1.0 + 2.2 * shortage + 0.6 * instability),
            }
        )
        return outputs
