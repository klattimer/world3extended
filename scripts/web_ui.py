#!/usr/bin/env python3
"""
Interactive Bokeh web interface for World3 Extended parameter exploration.

Provides real-time simulation with adjustable core subsystem rates, scenario selection,
and shock timing/severity tuning. Uses 10-year horizon (2025-2035) for rapid feedback.

Run with: bokeh serve scripts/web_ui.py --show

Or from root directory:
    python -m bokeh serve scripts/web_ui.py --show --allow-websocket-origin=localhost:5006

Then open: http://localhost:5006/web_ui
"""

from __future__ import annotations

import copy
import hashlib
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Div, RangeSlider, Select, Slider, Tabs, TabPanel
from bokeh.plotting import figure
from bokeh.palettes import Category10

# Set up path to import world3 modules
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from world3.model import SimulationConfig, World3Model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_base_config() -> dict:
    """Load default configuration."""
    cfg_path = Path(__file__).parent.parent / "config" / "default.yaml"
    return World3Model.load_yaml(cfg_path)


def run_simulation_preview(
    raw_cfg: dict,
    scenario_name: str,
    param_overrides: dict | None = None,
    start_year: int = 2025,
    end_year: int = 2035,
) -> pd.DataFrame:
    """
    Run simulation with 10-year horizon (2025-2035) for rapid feedback.

    Args:
        raw_cfg: Base configuration dict
        scenario_name: Name of scenario module
        param_overrides: Dict of parameter overrides to apply

    Returns:
        DataFrame with simulation results
    """
    cfg = copy.deepcopy(raw_cfg)

    # Apply parameter overrides if provided
    if param_overrides:
        logger.info(f"Applying {len(param_overrides)} parameter overrides")
        applied_count = 0
        for path, value in param_overrides.items():
            keys = path.split(".")
            target = cfg
            try:
                for key in keys[:-1]:
                    target = target[key]
                old_value = target.get(keys[-1])
                target[keys[-1]] = value
                logger.debug(f"Override {path}: {old_value} → {value}")
                applied_count += 1
            except KeyError:
                logger.warning("Skipping override for unknown config path: %s", path)
        logger.info(f"Successfully applied {applied_count}/{len(param_overrides)} overrides")

    # Use user-selected horizon for web UI exploration.
    cfg["simulation"]["start_year"] = int(start_year)
    cfg["simulation"]["end_year"] = int(end_year)
    cfg["simulation"]["timestep_years"] = 1.0  # Annual steps for web UI

    try:
        sim_cfg = SimulationConfig.from_mapping(cfg)
        model = World3Model(config=sim_cfg, raw_config=cfg, scenario_name=scenario_name)
        df = model.run()
        return df
    except Exception as e:
        logger.error("Simulation failed: %s", e)
        return pd.DataFrame()


def build_plot_payload(df: pd.DataFrame) -> dict[str, np.ndarray]:
    """Convert model output dataframe into plotting payload for Bokeh data sources."""
    n = len(df)

    def normalize(series: pd.Series) -> np.ndarray:
        arr = series.to_numpy(dtype=float)
        if len(arr) == 0:
            return arr
        base = arr[0]
        if abs(base) < 1e-9:
            return np.zeros_like(arr)
        return arr / base

    population = df.get("population_billions", pd.Series(np.zeros(n)))
    industrial_output = df.get("industrial_output_index", pd.Series(np.zeros(n)))
    energy_supply = df.get("energy_supply_ej", pd.Series(np.zeros(n)))
    food_index = df.get("food_index", pd.Series(np.zeros(n)))
    stability = df.get("systemic_stability", pd.Series(np.zeros(n)))

    return {
        "year": df.get("year", pd.Series(dtype=float)).to_numpy(),
        "population": population.to_numpy(dtype=float),
        "industrial_output": industrial_output.to_numpy(dtype=float),
        "energy_supply": energy_supply.to_numpy(dtype=float),
        "food_index": food_index.to_numpy(dtype=float),
        "stability": stability.to_numpy(dtype=float),
        "population_rel": normalize(population),
        "industrial_output_rel": normalize(industrial_output),
        "energy_supply_rel": normalize(energy_supply),
        "food_index_rel": normalize(food_index),
        "stability_rel": normalize(stability),
        "financial_stress": df.get("financial_stress", pd.Series(np.zeros(n))).to_numpy(),
        "food_stress": df.get("food_stress", pd.Series(np.zeros(n))).to_numpy(),
        "energy_shortage": df.get("energy_shortage", pd.Series(np.zeros(n))).to_numpy(),
        "conflict_intensity": df.get("conflict_intensity", pd.Series(np.zeros(n))).to_numpy(),
        "climate_damage": df.get("climate_damage", pd.Series(np.zeros(n))).to_numpy(),
    }


def create_scenario_config_panel() -> tuple:
    """Create scenario and shock configuration controls."""
    scenarios = [
        "baseline",
        "ai_energy_crisis",
        "hormuz_closure",
        "panama_closure",
        "fertilizer_shock",
        "suez_taiwan_escalation",
        "polycrisis",
    ]

    scenario_select = Select(title="Scenario:", value="polycrisis", options=scenarios)
    year_range = RangeSlider(title="Simulation Year Range", start=2025, end=2100, value=(2025, 2035), step=1)

    # Shock timing controls
    hormuz_timing = Slider(title="Hormuz Closure Year:", start=2025, end=2040, value=2029, step=1)
    hormuz_severity = Slider(title="Hormuz Severity (0-1):", start=0, end=1, value=0.95, step=0.05)

    suez_timing = Slider(title="Suez Closure Year:", start=2025, end=2040, value=2029, step=1)
    suez_severity = Slider(title="Suez Severity (0-1):", start=0, end=1, value=0.95, step=0.05)

    panama_timing = Slider(title="Panama Closure Year:", start=2025, end=2040, value=2028, step=1)
    panama_severity = Slider(title="Panama Severity (0-1):", start=0, end=1, value=0.95, step=0.05)

    taiwan_timing = Slider(title="Taiwan Shock Year:", start=2025, end=2040, value=2031, step=1)
    taiwan_severity = Slider(title="Taiwan Severity (0-1):", start=0, end=1, value=0.95, step=0.05)

    fertilizer_timing = Slider(title="Fertilizer Shock Year:", start=2025, end=2040, value=2028, step=1)
    fertilizer_severity = Slider(title="Fertilizer Severity (0-1):", start=0, end=1, value=1.0, step=0.05)

    controls = column(
        scenario_select,
        year_range,
        hormuz_timing,
        hormuz_severity,
        suez_timing,
        suez_severity,
        panama_timing,
        panama_severity,
        taiwan_timing,
        taiwan_severity,
        fertilizer_timing,
        fertilizer_severity,
    )

    return controls, {
        "scenario_select": scenario_select,
        "year_range": year_range,
        "hormuz_timing": hormuz_timing,
        "hormuz_severity": hormuz_severity,
        "suez_timing": suez_timing,
        "suez_severity": suez_severity,
        "panama_timing": panama_timing,
        "panama_severity": panama_severity,
        "taiwan_timing": taiwan_timing,
        "taiwan_severity": taiwan_severity,
        "fertilizer_timing": fertilizer_timing,
        "fertilizer_severity": fertilizer_severity,
    }


def create_subsystem_param_panel() -> tuple:
    """Create subsystem rate and parameter adjustment controls."""
    # Energy system
    oil_depletion = Slider(
        title="Oil Depletion Rate (annual %):", start=0.01, end=0.1, value=0.025, step=0.005
    )
    eroi_decline = Slider(
        title="EROI Decline Rate (annual %):", start=0.005, end=0.05, value=0.02, step=0.005
    )
    renewable_growth = Slider(
        title="Renewable Growth Rate (annual %):", start=0.05, end=0.25, value=0.12, step=0.02
    )

    # AI system
    ai_compute_growth = Slider(
        title="AI Compute Growth Rate (annual %):", start=0.15, end=0.5, value=0.36, step=0.05
    )
    ai_power_fraction = Slider(
        title="AI Capital Competition Weight:", start=0.05, end=0.30, value=0.12, step=0.01
    )

    # Population
    death_rate_stress_sensitivity = Slider(
        title="Geopolitical Escalation Sensitivity:", start=0.2, end=1.0, value=0.45, step=0.05
    )

    # Finance
    debt_growth = Slider(title="Debt Growth Rate (annual %):", start=0.01, end=0.10, value=0.03, step=0.01)
    financial_fragility = Slider(
        title="Financial Fragility Sensitivity:", start=0.1, end=1.0, value=0.5, step=0.1
    )

    # Trade
    fragmentation_drift = Slider(
        title="Trade Fragmentation Drift (annual):", start=0.005, end=0.05, value=0.02, step=0.005
    )

    # Climate
    warming_sensitivity = Slider(
        title="Climate Warming Sensitivity:", start=0.005, end=0.05, value=0.017, step=0.001
    )

    controls = column(
        oil_depletion,
        eroi_decline,
        renewable_growth,
        ai_compute_growth,
        ai_power_fraction,
        death_rate_stress_sensitivity,
        debt_growth,
        financial_fragility,
        fragmentation_drift,
        warming_sensitivity,
    )

    return controls, {
        "oil_depletion": oil_depletion,
        "eroi_decline": eroi_decline,
        "renewable_growth": renewable_growth,
        "ai_compute_growth": ai_compute_growth,
        "ai_power_fraction": ai_power_fraction,
        "death_rate_stress_sensitivity": death_rate_stress_sensitivity,
        "debt_growth": debt_growth,
        "financial_fragility": financial_fragility,
        "fragmentation_drift": fragmentation_drift,
        "warming_sensitivity": warming_sensitivity,
    }


def create_output_plots(output_sources: dict) -> dict:
    """Create Bokeh plots bound to live ColumnDataSource data."""
    plots = {}

    # Time series plot
    p_ts = figure(
        title="Core State Variables (Normalized To Start Year = 1.0)",
        x_axis_label="Year",
        y_axis_label="Relative Index",
        width=800,
        height=400,
        toolbar_location="right",
    )

    colors = Category10[10]
    p_ts.line("year", "population_rel", source=output_sources["timeseries"], legend_label="Population", color=colors[0], line_width=2)
    p_ts.line(
        "year",
        "industrial_output_rel",
        source=output_sources["timeseries"],
        legend_label="Industrial Output",
        color=colors[1],
        line_width=2,
    )
    p_ts.line(
        "year",
        "energy_supply_rel",
        source=output_sources["timeseries"],
        legend_label="Energy Supply",
        color=colors[2],
        line_width=2,
    )
    p_ts.line("year", "food_index_rel", source=output_sources["timeseries"], legend_label="Food Index", color=colors[3], line_width=2)
    p_ts.line("year", "stability_rel", source=output_sources["timeseries"], legend_label="Systemic Stability", color=colors[4], line_width=2)

    p_ts.legend.location = "center_right"
    p_ts.legend.click_policy = "hide"
    plots["timeseries"] = p_ts

    # Stability trajectory
    p_stability = figure(
        title="Systemic Stability Trajectory",
        x_axis_label="Year",
        y_axis_label="Stability Index",
        width=400,
        height=300,
    )
    p_stability.line("year", "stability", source=output_sources["timeseries"], color=colors[4], line_width=2)
    p_stability.scatter("year", "stability", source=output_sources["timeseries"], color=colors[4], size=5)
    plots["stability"] = p_stability

    # Stress components
    p_stress = figure(
        title="Stress Components",
        x_axis_label="Year",
        y_axis_label="Stress Level",
        width=400,
        height=300,
    )
    p_stress.line("year", "financial_stress", source=output_sources["stress"], legend_label="financial_stress", color=colors[5], line_width=1.5)
    p_stress.line("year", "food_stress", source=output_sources["stress"], legend_label="food_stress", color=colors[6], line_width=1.5)
    p_stress.line("year", "energy_shortage", source=output_sources["stress"], legend_label="energy_shortage", color=colors[7], line_width=1.5)
    p_stress.line("year", "conflict_intensity", source=output_sources["stress"], legend_label="conflict_intensity", color=colors[8], line_width=1.5)
    p_stress.line("year", "climate_damage", source=output_sources["stress"], legend_label="climate_damage", color=colors[9], line_width=1.5)
    p_stress.legend.location = "bottom_left"
    plots["stress"] = p_stress

    return plots


def update_simulation(
    attr, old, new, base_cfg: dict, scenario_controls: dict, subsystem_controls: dict, output_sources: dict
) -> None:
    """Callback to rerun simulation with updated parameters."""
    scenario = scenario_controls["scenario_select"].value
    start_year, end_year = scenario_controls["year_range"].value
    start_year = int(round(start_year))
    end_year = int(round(end_year))
    if end_year <= start_year:
        end_year = start_year + 1

    def timed_intensity(shock_year: float, severity: float) -> float:
        # Emphasize shocks occurring near the selected horizon center.
        center_year = 0.5 * (start_year + end_year)
        half_window = max(2.0, 0.5 * (end_year - start_year))
        proximity = max(0.0, 1.0 - abs(float(shock_year) - center_year) / half_window)
        return float(severity) * proximity

    hormuz_impact = timed_intensity(scenario_controls["hormuz_timing"].value, scenario_controls["hormuz_severity"].value)
    suez_impact = timed_intensity(scenario_controls["suez_timing"].value, scenario_controls["suez_severity"].value)
    panama_impact = timed_intensity(
        scenario_controls["panama_timing"].value,
        scenario_controls["panama_severity"].value,
    )
    taiwan_impact = timed_intensity(
        scenario_controls["taiwan_timing"].value,
        scenario_controls["taiwan_severity"].value,
    )
    fertilizer_impact = timed_intensity(
        scenario_controls["fertilizer_timing"].value,
        scenario_controls["fertilizer_severity"].value,
    )

    # Build parameter overrides from current slider values
    param_overrides = {
        "energy.depletion.oil_annual": subsystem_controls["oil_depletion"].value,
        "energy.eroi_decline.oil": subsystem_controls["eroi_decline"].value,
        "energy.renewables_growth": subsystem_controls["renewable_growth"].value,
        "ai_compute.annual_compute_growth": subsystem_controls["ai_compute_growth"].value,
        "ai_compute.capital_competition_weight": subsystem_controls["ai_power_fraction"].value,
        "geopolitics.escalation_sensitivity": subsystem_controls["death_rate_stress_sensitivity"].value,
        "finance.debt_growth_base": subsystem_controls["debt_growth"].value,
        "finance.fragility_sensitivity": subsystem_controls["financial_fragility"].value,
        "trade.fragmentation_drift": subsystem_controls["fragmentation_drift"].value,
        "climate.warming_sensitivity": subsystem_controls["warming_sensitivity"].value,
    }
    
    logger.info(f"Subsystem parameter slider values:")
    logger.info(f"  oil_depletion: {subsystem_controls['oil_depletion'].value}")
    logger.info(f"  eroi_decline: {subsystem_controls['eroi_decline'].value}")
    logger.info(f"  renewable_growth: {subsystem_controls['renewable_growth'].value}")
    logger.info(f"  ai_compute_growth: {subsystem_controls['ai_compute_growth'].value}")
    logger.info(f"  ai_power_fraction: {subsystem_controls['ai_power_fraction'].value}")
    logger.info(f"  death_rate_stress_sensitivity: {subsystem_controls['death_rate_stress_sensitivity'].value}")
    logger.info(f"  debt_growth: {subsystem_controls['debt_growth'].value}")
    logger.info(f"  financial_fragility: {subsystem_controls['financial_fragility'].value}")
    logger.info(f"  fragmentation_drift: {subsystem_controls['fragmentation_drift'].value}")
    logger.info(f"  warming_sensitivity: {subsystem_controls['warming_sensitivity'].value}")
    
    # Add shock overrides
    param_overrides.update({
        "geopolitics.chokepoints.hormuz.baseline_risk": 0.02 + 0.25 * hormuz_impact,
        "geopolitics.chokepoints.suez.baseline_risk": 0.015 + 0.2 * suez_impact,
        "geopolitics.chokepoints.panama.baseline_risk": 0.01 + 0.18 * panama_impact,
        "geopolitics.chokepoints.taiwan_semis.baseline_risk": 0.02 + 0.22 * taiwan_impact,
        "agriculture.nitrogen_supply_index": max(0.4, 1.0 - 0.6 * fertilizer_impact),
        "agriculture.phosphate_supply_index": max(0.4, 1.0 - 0.5 * fertilizer_impact),
        "agriculture.potash_supply_index": max(0.4, 1.0 - 0.5 * fertilizer_impact),
    })

    # Deterministic short hash to identify the exact parameter state for this run.
    hash_payload = {
        "scenario": scenario,
        "start_year": start_year,
        "end_year": end_year,
        "overrides": {k: round(float(v), 6) for k, v in param_overrides.items()},
    }
    run_hash = hashlib.sha1(json.dumps(hash_payload, sort_keys=True).encode("utf-8")).hexdigest()[:10]

    # Run simulation with overrides
    logger.info(f"Running simulation for scenario: {scenario}")
    df = run_simulation_preview(
        base_cfg,
        scenario,
        param_overrides,
        start_year=start_year,
        end_year=end_year,
    )

    if not df.empty:
        payload = build_plot_payload(df)

        # Update source data for time series
        output_sources["timeseries"].data = {
            "year": payload["year"],
            "population": payload["population"],
            "industrial_output": payload["industrial_output"],
            "energy_supply": payload["energy_supply"],
            "food_index": payload["food_index"],
            "stability": payload["stability"],
            "population_rel": payload["population_rel"],
            "industrial_output_rel": payload["industrial_output_rel"],
            "energy_supply_rel": payload["energy_supply_rel"],
            "food_index_rel": payload["food_index_rel"],
            "stability_rel": payload["stability_rel"],
        }
        output_sources["stress"].data = {
            "year": payload["year"],
            "financial_stress": payload["financial_stress"],
            "food_stress": payload["food_stress"],
            "energy_shortage": payload["energy_shortage"],
            "conflict_intensity": payload["conflict_intensity"],
            "climate_damage": payload["climate_damage"],
        }

        # Compute and display stability metrics
        final_stability = df["systemic_stability"].iloc[-1] if "systemic_stability" in df.columns else 0
        min_stability = df["systemic_stability"].min() if "systemic_stability" in df.columns else 0
        collapse_series = df.get("collapsed")
        if collapse_series is None:
            collapse_series = df.get("collapse_signal")
        collapse_occurred = bool(np.any(collapse_series)) if collapse_series is not None else False

        metrics_text = (
            f"<b>{end_year} Stability:</b> {final_stability:.3f}<br>"
            f"<b>Minimum Stability:</b> {min_stability:.3f}<br>"
            f"<b>Collapse:</b> {'YES' if collapse_occurred else 'NO'}"
        )
        output_sources["metrics"].text = metrics_text
        output_sources["status"].text = (
            f"<b>Last Run Hash:</b> <code>{run_hash}</code><br>"
            f"<b>Scenario:</b> {scenario}<br>"
            f"<b>Years:</b> {start_year}-{end_year}<br>"
            f"<b>Trigger:</b> {attr}<br>"
            f"<b>Rows:</b> {len(df)}"
        )

        logger.info(
            f"Simulation complete: final_stability={final_stability:.3f}, collapse={collapse_occurred}"
        )


def main() -> None:
    """Build and serve the Bokeh application."""
    logger.info("Initializing World3 Extended Web UI...")

    base_cfg = load_base_config()

    # Create control panels
    scenario_controls_layout, scenario_controls = create_scenario_config_panel()
    subsystem_controls_layout, subsystem_controls = create_subsystem_param_panel()

    # Initial simulation
    initial_start, initial_end = scenario_controls["year_range"].value
    initial_df = run_simulation_preview(
        base_cfg,
        scenario_controls["scenario_select"].value,
        start_year=int(initial_start),
        end_year=int(initial_end),
    )

    # Create data sources for dynamic updates
    initial_payload = build_plot_payload(initial_df)
    output_sources = {
        "timeseries": ColumnDataSource(
            {
                "year": initial_payload["year"],
                "population": initial_payload["population"],
                "industrial_output": initial_payload["industrial_output"],
                "energy_supply": initial_payload["energy_supply"],
                "food_index": initial_payload["food_index"],
                "stability": initial_payload["stability"],
                "population_rel": initial_payload["population_rel"],
                "industrial_output_rel": initial_payload["industrial_output_rel"],
                "energy_supply_rel": initial_payload["energy_supply_rel"],
                "food_index_rel": initial_payload["food_index_rel"],
                "stability_rel": initial_payload["stability_rel"],
            }
        ),
        "stress": ColumnDataSource(
            {
                "year": initial_payload["year"],
                "financial_stress": initial_payload["financial_stress"],
                "food_stress": initial_payload["food_stress"],
                "energy_shortage": initial_payload["energy_shortage"],
                "conflict_intensity": initial_payload["conflict_intensity"],
                "climate_damage": initial_payload["climate_damage"],
            }
        ),
        "metrics": Div(
            text=f"<b>Key Metrics ({int(initial_end)})</b><br>Initial load running...",
            width=300,
        ),
        "status": Div(
            text="<b>Last Run Hash:</b> <code>pending</code><br><b>Scenario:</b> baseline",
            width=300,
        ),
    }

    # Create output plots (bound to data sources)
    output_plots = create_output_plots(output_sources)

    # Register callbacks
    def on_change(attr, old, new):
        update_simulation(attr, old, new, base_cfg, scenario_controls, subsystem_controls, output_sources)

    # Attach callbacks to all controls
    for control in scenario_controls.values():
        control.on_change("value", on_change)
    for control in subsystem_controls.values():
        control.on_change("value", on_change)

    # Build layout
    control_tabs = Tabs(
        tabs=[
            TabPanel(
                child=scenario_controls_layout, title="Scenarios & Shocks"
            ),
            TabPanel(
                child=subsystem_controls_layout, title="Subsystem Parameters"
            ),
        ]
    )

    plots_column = column(
        output_plots.get("timeseries", figure(title="No data")),
        row(
            output_plots.get("stability", figure(title="No data")),
            output_plots.get("stress", figure(title="No data")),
        ),
    )

    main_layout = column(
        row(
            control_tabs,
            column(
                plots_column,
                output_sources["metrics"],
                output_sources["status"],
            ),
        )
    )

    curdoc().add_root(main_layout)
    curdoc().title = "World3 Extended: Interactive Parameter Explorer"

    logger.info("Web UI ready at http://localhost:5006/web_ui")


# Bokeh executes this script as a module via `bokeh serve`, so initialize on import.
main()
