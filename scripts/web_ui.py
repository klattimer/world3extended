#!/usr/bin/env python3
"""
Interactive Bokeh web interface for World3 Extended parameter exploration.

Provides real-time simulation with adjustable core subsystem rates, scenario selection,
and shock timing/severity tuning. Uses 10-year horizon (2025-2035) for rapid feedback.

Run with: bokeh serve scripts/web_ui.py --show

Or from root directory:
    python -m bokeh serve scripts/web_ui.py --show --allow-websocket-origin=localhost:5006
"""

from __future__ import annotations

import copy
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import (
    ColumnDataSource,
    HoverTool,
    RangeSlider,
    Select,
    Slider,
    Tabs,
    TabPanel,
    TextInput,
)
from bokeh.plotting import figure
from bokeh.palettes import Category10
from bokeh.transform import dodge

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
    raw_cfg: dict, scenario_name: str, param_overrides: dict | None = None
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
        for path, value in param_overrides.items():
            keys = path.split(".")
            target = cfg
            for key in keys[:-1]:
                target = target[key]
            target[keys[-1]] = value

    # Force 10-year horizon for web UI responsiveness
    cfg["simulation"]["start_year"] = 2025
    cfg["simulation"]["end_year"] = 2035
    cfg["simulation"]["timestep_years"] = 1.0  # Annual steps for web UI

    try:
        sim_cfg = SimulationConfig.from_mapping(cfg)
        model = World3Model(config=sim_cfg, raw_config=cfg, scenario_name=scenario_name)
        df = model.run()
        return df
    except Exception as e:
        logger.error("Simulation failed: %s", e)
        return pd.DataFrame()


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

    scenario_select = Select(title="Scenario:", value="baseline", options=scenarios)

    # Shock timing controls
    hormuz_timing = Slider(title="Hormuz Closure Year:", min=2025, max=2040, value=2029, step=1)
    hormuz_severity = Slider(title="Hormuz Severity (0-1):", min=0, max=1, value=0.95, step=0.05)

    suez_timing = Slider(title="Suez Closure Year:", min=2025, max=2040, value=2029, step=1)
    suez_severity = Slider(title="Suez Severity (0-1):", min=0, max=1, value=0.95, step=0.05)

    panama_timing = Slider(title="Panama Closure Year:", min=2025, max=2040, value=2028, step=1)
    panama_severity = Slider(title="Panama Severity (0-1):", min=0, max=1, value=0.95, step=0.05)

    taiwan_timing = Slider(title="Taiwan Shock Year:", min=2025, max=2040, value=2031, step=1)
    taiwan_severity = Slider(title="Taiwan Severity (0-1):", min=0, max=1, value=0.95, step=0.05)

    fertilizer_timing = Slider(title="Fertilizer Shock Year:", min=2025, max=2040, value=2028, step=1)
    fertilizer_severity = Slider(title="Fertilizer Severity (0-1):", min=0, max=1, value=1.0, step=0.05)

    controls = column(
        scenario_select,
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
        title="Oil Depletion Rate (annual %):", min=0.01, max=0.1, value=0.025, step=0.005
    )
    eroi_decline = Slider(
        title="EROI Decline Rate (annual %):", min=0.005, max=0.05, value=0.02, step=0.005
    )
    renewable_growth = Slider(
        title="Renewable Growth Rate (annual %):", min=0.05, max=0.25, value=0.12, step=0.02
    )

    # AI system
    ai_compute_growth = Slider(
        title="AI Compute Growth Rate (annual %):", min=0.15, max=0.5, value=0.36, step=0.05
    )
    ai_power_fraction = Slider(
        title="AI Max Power Fraction (%):", min=0.06, max=0.20, value=0.10, step=0.01
    )

    # Population
    death_rate_stress_sensitivity = Slider(
        title="Death Rate Stress Sensitivity:", min=0.5, max=2.0, value=1.3, step=0.1
    )

    # Finance
    debt_growth = Slider(title="Debt Growth Rate (annual %):", min=0.01, max=0.10, value=0.03, step=0.01)
    financial_fragility = Slider(
        title="Financial Fragility Sensitivity:", min=0.1, max=1.0, value=0.5, step=0.1
    )

    # Trade
    fragmentation_drift = Slider(
        title="Trade Fragmentation Drift (annual):", min=0.005, max=0.05, value=0.02, step=0.005
    )

    # Climate
    warming_sensitivity = Slider(
        title="Climate Warming Sensitivity:", min=1.0, max=3.0, value=1.8, step=0.2
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


def create_output_plots(df: pd.DataFrame) -> dict:
    """Create Bokeh plots from simulation results."""
    plots = {}

    if df.empty:
        return plots

    # Time series plot
    p_ts = figure(
        title="Core State Variables (10-year Preview)",
        x_axis_label="Year",
        y_axis_label="Index",
        width=800,
        height=400,
        toolbar_location="right",
    )

    colors = Category10[10]
    if "population" in df.columns:
        population_norm = df["population"] / df["population"].iloc[0]
        p_ts.line(df["year"], population_norm, legend_label="Population", color=colors[0], line_width=2)

    if "industrial_output" in df.columns:
        io_norm = df["industrial_output"] / df["industrial_output"].iloc[0]
        p_ts.line(df["year"], io_norm, legend_label="Industrial Output", color=colors[1], line_width=2)

    if "energy_supply" in df.columns:
        es_norm = df["energy_supply"] / df["energy_supply"].iloc[0]
        p_ts.line(df["year"], es_norm, legend_label="Energy Supply", color=colors[2], line_width=2)

    if "food_index" in df.columns:
        fi_norm = df["food_index"] / df["food_index"].iloc[0]
        p_ts.line(df["year"], fi_norm, legend_label="Food Index", color=colors[3], line_width=2)

    if "systemic_stability" in df.columns:
        p_ts.line(
            df["year"], df["systemic_stability"], legend_label="Systemic Stability", color=colors[4], line_width=2
        )

    p_ts.legend.location = "center_left"
    p_ts.legend.click_policy = "hide"
    plots["timeseries"] = p_ts

    # Stability and stress metrics
    if "systemic_stability" in df.columns:
        p_stability = figure(
            title="Systemic Stability Trajectory",
            x_axis_label="Year",
            y_axis_label="Stability Index",
            width=400,
            height=300,
        )
        p_stability.line(df["year"], df["systemic_stability"], color=colors[4], line_width=2)
        p_stability.circle(df["year"], df["systemic_stability"], color=colors[4], size=5)
        plots["stability"] = p_stability

    # Stress components stacked view
    stress_cols = [col for col in df.columns if "stress" in col.lower() and col != "systemic_stability"]
    if stress_cols:
        p_stress = figure(
            title="Stress Components",
            x_axis_label="Year",
            y_axis_label="Stress Level",
            width=400,
            height=300,
        )
        for i, col in enumerate(stress_cols[:5]):  # Limit to 5 for readability
            p_stress.line(df["year"], df[col], legend_label=col, color=colors[i % 10], line_width=1.5)
        p_stress.legend.location = "top_left"
        plots["stress"] = p_stress

    return plots


def update_simulation(
    attr, old, new, base_cfg: dict, scenario_controls: dict, subsystem_controls: dict, output_sources: dict
) -> None:
    """Callback to rerun simulation with updated parameters."""
    scenario = scenario_controls["scenario_select"].value

    # Build parameter overrides from current slider values
    param_overrides = {
        "subsystems.energy.depletion_rate_oil": subsystem_controls["oil_depletion"].value / 100,
        "subsystems.energy.eroi_decline_rate": subsystem_controls["eroi_decline"].value / 100,
        "subsystems.energy.renewable_growth": subsystem_controls["renewable_growth"].value / 100,
        "subsystems.ai_compute.base_growth_rate": subsystem_controls["ai_compute_growth"].value / 100,
        "subsystems.population.death_rate_stress_sensitivity": subsystem_controls[
            "death_rate_stress_sensitivity"
        ].value,
        "subsystems.finance.debt_growth_rate": subsystem_controls["debt_growth"].value / 100,
        "subsystems.trade.fragmentation_drift": subsystem_controls["fragmentation_drift"].value / 100,
        "subsystems.climate.warming_sensitivity": subsystem_controls["warming_sensitivity"].value,
    }

    # Run simulation with overrides
    logger.info(f"Running simulation for scenario: {scenario}")
    df = run_simulation_preview(base_cfg, scenario, param_overrides)

    if not df.empty:
        # Update source data for time series
        output_sources["timeseries"].data = {
            "year": df["year"],
            "population": df.get("population", np.zeros(len(df))),
            "industrial_output": df.get("industrial_output", np.zeros(len(df))),
            "energy_supply": df.get("energy_supply", np.zeros(len(df))),
            "food_index": df.get("food_index", np.zeros(len(df))),
            "stability": df.get("systemic_stability", np.zeros(len(df))),
        }

        # Compute and display stability metrics
        final_stability = df["systemic_stability"].iloc[-1] if "systemic_stability" in df.columns else 0
        min_stability = df["systemic_stability"].min() if "systemic_stability" in df.columns else 0
        collapse_signal = df.get("collapse_signal", [False] * len(df))
        collapse_occurred = collapse_signal.any()

        metrics_text = (
            f"<b>2035 Stability:</b> {final_stability:.3f}<br>"
            f"<b>Minimum Stability:</b> {min_stability:.3f}<br>"
            f"<b>Collapse:</b> {'YES' if collapse_occurred else 'NO'}"
        )
        output_sources["metrics"].text = metrics_text

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
    initial_df = run_simulation_preview(base_cfg, "baseline")

    # Create output plots
    output_plots = create_output_plots(initial_df)

    # Create data sources for dynamic updates
    output_sources = {
        "timeseries": ColumnDataSource(
            {
                "year": initial_df.get("year", []),
                "population": initial_df.get("population", np.zeros(len(initial_df))),
                "industrial_output": initial_df.get("industrial_output", np.zeros(len(initial_df))),
                "energy_supply": initial_df.get("energy_supply", np.zeros(len(initial_df))),
                "food_index": initial_df.get("food_index", np.zeros(len(initial_df))),
                "stability": initial_df.get("systemic_stability", np.zeros(len(initial_df))),
            }
        ),
        "metrics": TextInput(
            value="<b>Initial Load</b><br>Running...",
            title="Key Metrics (2035)",
            width=300,
        ),
    }

    # Register callbacks
    def on_change(attr, old, new):
        update_simulation(attr, old, new, base_cfg, scenario_controls, subsystem_controls, output_sources)

    # Attach callbacks to all controls
    scenario_controls["scenario_select"].on_change("value", on_change)
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
            ),
        )
    )

    curdoc().add_root(main_layout)
    curdoc().title = "World3 Extended: Interactive Parameter Explorer"

    logger.info("Web UI ready at http://localhost:5006")


if __name__ == "__main__":
    main()
