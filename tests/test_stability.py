from __future__ import annotations

from pathlib import Path

from world3.model import SimulationConfig, World3Model
from world3.utils.metrics import detect_collapse


def _load_cfg() -> dict:
    return World3Model.load_yaml(Path("config/default.yaml"))


def test_polycrisis_has_lower_stability_than_baseline() -> None:
    raw = _load_cfg()

    sim_a = SimulationConfig.from_mapping(raw)
    model_a = World3Model(sim_a, raw, scenario_name="baseline")
    df_a = model_a.run()

    sim_b = SimulationConfig.from_mapping(raw)
    model_b = World3Model(sim_b, raw, scenario_name="polycrisis")
    df_b = model_b.run()

    assert df_b["systemic_stability"].mean() < df_a["systemic_stability"].mean()


def test_collapse_signal_series_boolean() -> None:
    raw = _load_cfg()
    sim = SimulationConfig.from_mapping(raw)
    model = World3Model(sim, raw, scenario_name="polycrisis")
    df = model.run()
    collapse = detect_collapse(df)
    assert collapse.dtype == bool
    assert len(collapse) == len(df)
