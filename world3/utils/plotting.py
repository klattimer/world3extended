from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.sankey import Sankey


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def plot_time_series(df: pd.DataFrame, output_dir: Path, scenario_name: str) -> Path:
    _ensure_dir(output_dir)
    fig, axes = plt.subplots(3, 2, figsize=(14, 10), sharex=True)
    axes = axes.flatten()

    series = [
        ("population_billions", "Population (billions)"),
        ("industrial_output_index", "Industrial Output Index"),
        ("food_index", "Food Index"),
        ("energy_shortage", "Energy Shortage"),
        ("financial_stress", "Financial Stress"),
        ("systemic_stability", "Systemic Stability"),
    ]

    for ax, (col, title) in zip(axes, series):
        ax.plot(df["year"], df[col], lw=2)
        ax.set_title(title)
        ax.grid(alpha=0.3)

    fig.suptitle(f"World3 Extended Dynamics: {scenario_name}")
    fig.tight_layout()
    out = output_dir / f"timeseries_{scenario_name}.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def plot_sensitivity_heatmap(summary_df: pd.DataFrame, output_dir: Path, scenario_name: str) -> Path:
    _ensure_dir(output_dir)
    corr = summary_df[["min_stability", "max_food_stress", "max_energy_shortage"]].corr()

    fig, ax = plt.subplots(figsize=(5, 4))
    cax = ax.imshow(corr.values, cmap="viridis", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr.columns)), corr.columns, rotation=30, ha="right")
    ax.set_yticks(range(len(corr.columns)), corr.columns)
    fig.colorbar(cax, ax=ax, fraction=0.046)
    ax.set_title("Sensitivity Correlation Heatmap")

    out = output_dir / f"heatmap_{scenario_name}.png"
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def plot_collapse_probability_curve(summary_df: pd.DataFrame, output_dir: Path, scenario_name: str) -> Path:
    _ensure_dir(output_dir)
    collapse_years = summary_df["collapse_year"].dropna().astype(int)
    years = np.arange(2025, 2101)
    probs = np.array([(collapse_years <= y).mean() if len(collapse_years) else 0.0 for y in years])

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(years, probs, color="crimson", lw=2)
    ax.set_ylim(0, 1)
    ax.set_title("Cumulative Collapse Probability")
    ax.set_xlabel("Year")
    ax.set_ylabel("Probability")
    ax.grid(alpha=0.3)

    out = output_dir / f"collapse_prob_{scenario_name}.png"
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def plot_energy_sankey(df: pd.DataFrame, output_dir: Path, scenario_name: str) -> Path:
    _ensure_dir(output_dir)
    last = df.iloc[-1]

    oil = float(last["oil_ej"])
    gas = float(last["gas_ej"])
    coal = float(last["coal_ej"])
    ren = float(last["renewables_ej"])
    nuc = float(last["nuclear_ej"])
    ai = float(last["ai_power_demand_ej"])
    industry = float(last["energy_supply_ej"] * 0.5)
    society = float(max(0.0, last["energy_supply_ej"] - ai - industry))

    fig, ax = plt.subplots(figsize=(9, 5))
    sankey = Sankey(ax=ax, unit=" EJ", format="%.1f")
    sankey.add(
        flows=[oil, gas, coal, ren, nuc, -ai, -industry, -society],
        labels=["Oil", "Gas", "Coal", "Renewables", "Nuclear", "AI/Data", "Industry", "Society"],
        orientations=[1, 1, 1, 1, 1, -1, -1, -1],
    )
    sankey.finish()
    plt.title("Energy Flow Sankey (final year)")

    out = output_dir / f"sankey_{scenario_name}.png"
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def plot_regional_stress_map(df: pd.DataFrame, output_dir: Path, scenario_name: str) -> Path:
    _ensure_dir(output_dir)
    last = df.iloc[-1]

    regions = ["North America", "Europe", "MENA", "South Asia", "East Asia", "Sub-Saharan Africa"]
    base = np.array([0.45, 0.4, 0.62, 0.58, 0.52, 0.7])
    modifiers = np.array(
        [
            0.4 * last["financial_stress"],
            0.35 * last["energy_shortage"],
            0.45 * last["conflict_intensity"],
            0.5 * last["food_stress"],
            0.35 * last["shipping_disruption"],
            0.55 * last["climate_damage"],
        ]
    )
    stress = np.clip(base + modifiers, 0.0, 1.0)

    fig, ax = plt.subplots(figsize=(8, 3.8))
    heat = stress.reshape(2, 3)
    im = ax.imshow(heat, cmap="magma", vmin=0, vmax=1)
    ax.set_xticks([0, 1, 2], [regions[0], regions[1], regions[2]], rotation=20, ha="right")
    ax.set_yticks([0, 1], ["Block A", "Block B"])
    fig.colorbar(im, ax=ax, fraction=0.04)
    ax.set_title("Regional Stress Proxy Map")

    out = output_dir / f"regional_stress_{scenario_name}.png"
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out
