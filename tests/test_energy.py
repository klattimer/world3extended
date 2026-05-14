from __future__ import annotations

from pathlib import Path

from world3.model import SimulationConfig, World3Model
from world3.systems.energy import EnergySystem


def _load_cfg() -> dict:
    return World3Model.load_yaml(Path("config/default.yaml"))


def test_energy_shortage_rises_when_supply_constrained() -> None:
    cfg = _load_cfg()
    system = EnergySystem(cfg["energy"])
    state = {
        "oil_ej": 60.0,
        "gas_ej": 55.0,
        "coal_ej": 80.0,
        "renewables_ej": 35.0,
        "nuclear_ej": 20.0,
        "oil_eroi": 8.0,
        "gas_eroi": 10.0,
        "coal_eroi": 16.0,
        "renewables_eroi": 14.0,
        "nuclear_eroi": 50.0,
        "energy_demand_ej": 700.0,
        "population_billions": 8.5,
    }
    out = system.step(state=state, trade_flow=0.7, instability=0.6, finance_stress=0.7, dt_years=1.0)
    assert out["energy_shortage"] > 0.2


def test_model_runs_energy_columns() -> None:
    raw = _load_cfg()
    sim = SimulationConfig.from_mapping(raw)
    model = World3Model(sim, raw, scenario_name="baseline")
    df = model.run()
    assert {"energy_supply_ej", "energy_shortage", "oil_ej"}.issubset(df.columns)
