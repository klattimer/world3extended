from __future__ import annotations

import copy
import importlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from world3.systems.agriculture import AgricultureSystem
from world3.systems.ai_compute import AIComputeSystem
from world3.systems.climate import ClimateSystem
from world3.systems.energy import EnergySystem
from world3.systems.finance import FinanceSystem
from world3.systems.geopolitics import GeopoliticsSystem
from world3.systems.industry import IndustrySystem
from world3.systems.population import PopulationSystem
from world3.systems.trade import TradeSystem
from world3.utils.metrics import cascade_pressure, compute_systemic_stability, detect_collapse


logger = logging.getLogger(__name__)


def deep_merge(dst: dict[str, Any], src: dict[str, Any]) -> dict[str, Any]:
	for key, value in src.items():
		if isinstance(value, dict) and isinstance(dst.get(key), dict):
			deep_merge(dst[key], value)
		else:
			dst[key] = value
	return dst


@dataclass
class SimulationConfig:
	start_year: int
	end_year: int
	timestep_years: float
	timestep_days: int | None
	seed: int
	monte_carlo_runs: int
	scenario: str

	@classmethod
	def from_mapping(cls, mapping: dict[str, Any]) -> "SimulationConfig":
		sim = mapping["simulation"]
		timestep_days = sim.get("timestep_days")
		return cls(
			start_year=int(sim["start_year"]),
			end_year=int(sim["end_year"]),
			timestep_years=float(sim.get("timestep_years", 1.0)),
			timestep_days=int(timestep_days) if timestep_days is not None else None,
			seed=int(sim["seed"]),
			monte_carlo_runs=int(sim["monte_carlo_runs"]),
			scenario=str(sim["scenario"]),
		)

	@property
	def dt_years(self) -> float:
		if self.timestep_days is not None:
			return max(1.0 / 365.0, float(self.timestep_days) / 365.0)
		return max(1e-6, float(self.timestep_years))


class World3Model:
	"""Extended World3-style systems model for exploratory scenario simulation."""

	def __init__(
		self,
		config: SimulationConfig,
		raw_config: dict[str, Any],
		scenario_name: str | None = None,
	) -> None:
		self.config = config
		self.raw_config = copy.deepcopy(raw_config)
		self.scenario_name = scenario_name or config.scenario

		self.scenario_data = self._load_scenario(self.scenario_name)
		self.params = deep_merge(copy.deepcopy(self.raw_config), self.scenario_data.get("overrides", {}))

		self.rng = np.random.default_rng(self.config.seed)
		self.state = self._initial_state()

		self.geopolitics = GeopoliticsSystem(self.params["geopolitics"])
		self.trade = TradeSystem(self.params["trade"], self.params["geopolitics"])
		self.energy = EnergySystem(self.params["energy"])
		self.ai_compute = AIComputeSystem(self.params["ai_compute"])
		self.agriculture = AgricultureSystem(self.params["agriculture"])
		self.industry = IndustrySystem(self.params["industry"])
		self.climate = ClimateSystem(self.params["climate"])
		self.finance = FinanceSystem(self.params["finance"])
		self.population = PopulationSystem()

	@staticmethod
	def load_yaml(path: Path) -> dict[str, Any]:
		with path.open("r", encoding="utf-8") as f:
			return yaml.safe_load(f)

	def _load_scenario(self, name: str) -> dict[str, Any]:
		module = importlib.import_module(f"world3.scenarios.{name}")
		data = module.scenario()
		logger.info("Loaded scenario '%s': %s", name, data.get("description", ""))
		return data

	def _initial_state(self) -> dict[str, float]:
		init = self.params["initial_state"]
		en = self.params["energy"]
		ai = self.params["ai_compute"]
		ag = self.params["agriculture"]

		return {
			"year": float(self.config.start_year),
			"population_billions": float(init["population_billions"]),
			"birth_rate": 0.015,
			"death_rate": 0.009,
			"famine_mortality": 0.0,
			"migration_pressure": float(init["migration_pressure"]),
			"political_stability": float(init["political_stability"]),
			"industrial_output_index": float(init["industrial_output_index"]),
			"industrial_capital_index": float(init["industrial_capital_index"]),
			"food_index": float(init["food_index"]),
			"food_stress": 0.0,
			"debt_to_gdp": float(init["debt_to_gdp"]),
			"inflation_index": float(init["inflation_index"]),
			"financial_stress": float(init["financial_stress"]),
			"banking_instability": 0.0,
			"currency_instability": 0.0,
			"pollution_index": float(init["pollution_index"]),
			"cumulative_pollution": float(init["cumulative_pollution"]),
			"warming_c": float(init["warming_c"]),
			"climate_damage": float(init["climate_damage"]),
			"crop_damage": float(init["crop_damage"]),
			"disaster_pressure": 0.08,
			"energy_demand_ej": float(en["demand_ej"]),
			"energy_supply_ej": float(en["demand_ej"] * 0.97),
			"energy_gross_supply_ej": float(en["demand_ej"]),
			"energy_shortage": 0.04,
			"energy_price_index": 1.05,
			"oil_ej": float(en["supply"]["oil_ej"]),
			"gas_ej": float(en["supply"]["gas_ej"]),
			"coal_ej": float(en["supply"]["coal_ej"]),
			"renewables_ej": float(en["supply"]["renewables_ej"]),
			"nuclear_ej": float(en["supply"]["nuclear_ej"]),
			"oil_eroi": float(en["eroi"]["oil"]),
			"gas_eroi": float(en["eroi"]["gas"]),
			"coal_eroi": float(en["eroi"]["coal"]),
			"renewables_eroi": float(en["eroi"]["renewables"]),
			"nuclear_eroi": float(en["eroi"]["nuclear"]),
			"trade_fragmentation": 0.14,
			"shipping_disruption": 0.08,
			"trade_flow_index": 0.95,
			"semiconductor_constraint": 0.12,
			"conflict_intensity": 0.2,
			"sanctions_level": 0.1,
			"ai_compute_index": float(ai["initial_compute_index"]),
			"ai_efficiency_index": 1.0,
			"ai_power_demand_ej": float(ai["baseline_ai_power_ej"]),
			"ai_power_curtailed_ej": 0.0,
			"ai_capital_competition": 0.0,
			"nitrogen_supply_index": float(ag["nitrogen_supply_index"]),
			"phosphate_supply_index": float(ag["phosphate_supply_index"]),
			"potash_supply_index": float(ag["potash_supply_index"]),
			"fertilizer_effective_index": 1.0,
			"emissions": 0.0,
			"cascade_pressure": 0.0,
			"systemic_stability": float(init["systemic_stability"]),
			"collapsed": 0.0,
		}

	def _year_shocks(self, year: int) -> tuple[dict[str, float], dict[str, float]]:
		cp_shocks = self.scenario_data.get("shock_schedule", {}).get(year, {})
		exogenous = self.scenario_data.get("exogenous_shocks", {}).get(year, {})
		return cp_shocks, exogenous

	def run(self) -> pd.DataFrame:
		rows: list[dict[str, float]] = []
		dt_years = self.config.dt_years
		time_year = float(self.config.start_year)
		end_year = float(self.config.end_year)

		if dt_years < 1.0:
			logger.info("Running sub-annual mode with dt_years=%.6f (~%.2f days)", dt_years, dt_years * 365.0)
		else:
			logger.info("Running annual mode with dt_years=%.3f", dt_years)

		while time_year <= end_year + 1e-12:
			self.state["year"] = float(time_year)
			shock_year = int(np.floor(time_year + 1e-9))
			cp_shocks, exogenous_shocks = self._year_shocks(shock_year)

			geo = self.geopolitics.step(
				state=self.state,
				trade_fragmentation=self.state["trade_fragmentation"],
				rng=self.rng,
				dt_years=dt_years,
				forced_shocks=cp_shocks,
			)
			self.state["conflict_intensity"] = geo.conflict_intensity
			self.state["sanctions_level"] = geo.sanctions_level
			self.state["political_stability"] = float(
				np.clip(self.state["political_stability"] + geo.political_stability_delta, 0.0, 1.0)
			)

			trade_out = self.trade.step(
				state=self.state,
				sanctions_level=geo.sanctions_level,
				dt_years=dt_years,
				chokepoint_disruption=geo.chokepoint_disruption,
			)
			self.state.update(trade_out)

			energy_out = self.energy.step(
				state=self.state,
				trade_flow=self.state["trade_flow_index"],
				instability=self.state["conflict_intensity"],
				finance_stress=self.state["financial_stress"],
				dt_years=dt_years,
			)
			self.state.update(energy_out)

			ai_out = self.ai_compute.step(
				state=self.state,
				semiconductor_constraint=self.state["semiconductor_constraint"],
				available_power_ej=self.state["energy_supply_ej"],
				financial_stress=self.state["financial_stress"],
				dt_years=dt_years,
			)
			self.state.update(ai_out)

			ag_out = self.agriculture.step(state=self.state, shocks=exogenous_shocks, dt_years=dt_years)
			self.state.update(ag_out)

			industry_out = self.industry.step(state=self.state, dt_years=dt_years)
			self.state.update(industry_out)

			climate_out = self.climate.step(state=self.state, dt_years=dt_years)
			self.state.update(climate_out)

			finance_out = self.finance.step(state=self.state, dt_years=dt_years)
			self.state.update(finance_out)

			pop_out = self.population.step(state=self.state, dt_years=dt_years)
			self.state.update(pop_out)

			self.state["cascade_pressure"] = cascade_pressure(self.state)
			stability = compute_systemic_stability(self.state, self.params["stability_weights"])
			stability = float(np.clip(stability - 0.2 * self.state["cascade_pressure"], 0.0, 1.0))
			self.state["systemic_stability"] = stability

			rows.append(copy.deepcopy(self.state))
			time_year += dt_years

		df = pd.DataFrame(rows)
		df["collapsed"] = detect_collapse(df).astype(float)
		return df
