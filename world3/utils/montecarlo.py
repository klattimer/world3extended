from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from world3.model import SimulationConfig, World3Model
from world3.utils.metrics import summarize_runs


@dataclass
class MonteCarloResult:
    runs: list[pd.DataFrame]
    summary: pd.DataFrame


def _sampled_config(base_cfg: dict[str, Any], rng: np.random.Generator) -> dict[str, Any]:
    cfg = copy.deepcopy(base_cfg)

    cfg["energy"]["renewables_growth"] *= float(rng.uniform(0.8, 1.25))
    cfg["energy"]["depletion"]["oil_annual"] *= float(rng.uniform(0.9, 1.2))
    cfg["ai_compute"]["annual_compute_growth"] *= float(rng.uniform(0.75, 1.25))
    cfg["agriculture"]["climate_sensitivity"] *= float(rng.uniform(0.8, 1.3))
    cfg["finance"]["fragility_sensitivity"] *= float(rng.uniform(0.85, 1.25))
    cfg["geopolitics"]["baseline_tension"] = float(
        np.clip(cfg["geopolitics"]["baseline_tension"] + rng.normal(0.0, 0.03), 0.05, 0.7)
    )
    return cfg


def run_monte_carlo(
    base_cfg: dict[str, Any],
    scenario_name: str,
    runs: int,
    seed: int,
) -> MonteCarloResult:
    rng = np.random.default_rng(seed)
    outputs: list[pd.DataFrame] = []

    for i in range(runs):
        sampled_cfg = _sampled_config(base_cfg, rng)
        sim_cfg = SimulationConfig.from_mapping(sampled_cfg)
        sim_cfg.seed = int(seed + i)
        model = World3Model(config=sim_cfg, raw_config=sampled_cfg, scenario_name=scenario_name)
        outputs.append(model.run())

    return MonteCarloResult(runs=outputs, summary=summarize_runs(outputs))
