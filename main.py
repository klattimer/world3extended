from __future__ import annotations

import argparse
import copy
import logging
from pathlib import Path

from world3.model import SimulationConfig, World3Model
from world3.utils.montecarlo import run_monte_carlo
from world3.utils.plotting import (
    plot_collapse_probability_curve,
    plot_energy_sankey,
    plot_regional_stress_map,
    plot_sensitivity_heatmap,
    plot_time_series,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="World3 Extended exploratory simulation")
    parser.add_argument("--config", default="config/default.yaml", help="Path to YAML config")
    parser.add_argument("--scenario", default=None, help="Scenario module name under world3/scenarios")
    parser.add_argument("--output", default="outputs", help="Output directory")
    parser.add_argument("--timestep-days", type=int, default=None, help="Override simulation timestep in days")
    parser.add_argument("--timestep-years", type=float, default=None, help="Override simulation timestep in years")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    args = parse_args()

    cfg_path = Path(args.config)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_cfg = World3Model.load_yaml(cfg_path)
    if args.timestep_days is not None:
        raw_cfg["simulation"]["timestep_days"] = int(args.timestep_days)
    if args.timestep_years is not None:
        raw_cfg["simulation"]["timestep_years"] = float(args.timestep_years)

    sim_cfg = SimulationConfig.from_mapping(raw_cfg)
    scenario_name = args.scenario or sim_cfg.scenario

    logging.info("Running scenario: %s", scenario_name)
    model = World3Model(config=sim_cfg, raw_config=raw_cfg, scenario_name=scenario_name)
    df = model.run()

    run_csv = output_dir / f"run_{scenario_name}.csv"
    df.to_csv(run_csv, index=False)

    plot_paths = [
        plot_time_series(df, output_dir, scenario_name),
        plot_energy_sankey(df, output_dir, scenario_name),
        plot_regional_stress_map(df, output_dir, scenario_name),
    ]

    mc_runs = sim_cfg.monte_carlo_runs
    if sim_cfg.dt_years <= (7.0 / 365.0) and mc_runs > 20:
        mc_runs = 20
        logging.warning(
            "High temporal resolution detected (dt=%.2f days); capping Monte Carlo runs to %d for runtime safety.",
            sim_cfg.dt_years * 365.0,
            mc_runs,
        )

    mc_base_cfg = copy.deepcopy(raw_cfg)
    mc_base_cfg["simulation"]["monte_carlo_runs"] = mc_runs

    mc = run_monte_carlo(
        base_cfg=mc_base_cfg,
        scenario_name=scenario_name,
        runs=mc_runs,
        seed=sim_cfg.seed,
    )
    mc.summary.to_csv(output_dir / f"monte_carlo_summary_{scenario_name}.csv", index=False)

    plot_paths.extend(
        [
            plot_sensitivity_heatmap(mc.summary, output_dir, scenario_name),
            plot_collapse_probability_curve(mc.summary, output_dir, scenario_name),
        ]
    )

    print("World3 Extended run complete.")
    print(f"Scenario: {scenario_name}")
    print(f"Main output: {run_csv}")
    print("Generated charts:")
    for p in plot_paths:
        print(f"- {p}")


if __name__ == "__main__":
    main()
