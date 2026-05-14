from __future__ import annotations

from typing import Any

import numpy as np


class TradeSystem:
    """Models shipping capacity degradation from chokepoint disruptions and fragmentation."""

    def __init__(self, params: dict[str, Any], geopolitics_params: dict[str, Any]) -> None:
        self.params = params
        self.geopolitics_params = geopolitics_params

    def step(
        self,
        state: dict[str, float],
        sanctions_level: float,
        dt_years: float,
        chokepoint_disruption: dict[str, float],
    ) -> dict[str, float]:
        rerouting_penalty = float(self.params["rerouting_penalty"])
        elasticity = float(self.params["shipping_elasticity"])
        frag_drift = float(self.params["fragmentation_drift"])

        weighted_disruption = 0.0
        for cp_name, cp_data in self.geopolitics_params["chokepoints"].items():
            share = float(cp_data["flow_share"])
            weighted_disruption += share * chokepoint_disruption.get(cp_name, 0.0)

        weighted_disruption = float(np.clip(weighted_disruption, 0.0, 1.0))
        max_chokepoint_disruption = float(max(chokepoint_disruption.values(), default=0.0))

        fragmentation = np.clip(
            state["trade_fragmentation"]
            + (frag_drift + 0.08 * sanctions_level + 0.05 * weighted_disruption - 0.01 * state["political_stability"]) * dt_years,
            0.0,
            1.0,
        )

        shipping_disruption = np.clip(
            elasticity * weighted_disruption
            + rerouting_penalty * fragmentation
            + 0.35 * max(0.0, max_chokepoint_disruption - 0.6),
            0.0,
            1.0,
        )

        trade_flow = np.clip(
            1.0 - shipping_disruption - 0.25 * sanctions_level - 0.2 * max_chokepoint_disruption,
            0.0,
            1.1,
        )

        semiconductor_constraint = np.clip(
            chokepoint_disruption.get("taiwan_semis", 0.0)
            + 0.4 * shipping_disruption
            + 0.3 * sanctions_level,
            0.0,
            1.0,
        )

        return {
            "trade_fragmentation": float(fragmentation),
            "shipping_disruption": float(shipping_disruption),
            "trade_flow_index": float(trade_flow),
            "semiconductor_constraint": float(semiconductor_constraint),
        }
