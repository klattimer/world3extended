from __future__ import annotations

from typing import Iterable

import networkx as nx
import numpy as np
import pandas as pd


def compute_systemic_stability(state: dict[str, float], weights: dict[str, float]) -> float:
    """Composite stability index in [0, 1], where lower values indicate systemic fragility."""
    food_security = 1.0 - state["food_stress"]
    energy_availability = 1.0 - state["energy_shortage"]
    industrial = np.clip(state["industrial_output_index"], 0.0, 1.2) / 1.2
    politics = state["political_stability"]
    finance_health = 1.0 - state["financial_stress"]
    climate_component = 1.0 - state["climate_damage"]

    score = (
        weights["food_security"] * food_security
        + weights["energy_availability"] * energy_availability
        + weights["industrial_output"] * industrial
        + weights["political_stability"] * politics
        + weights["financial_health"] * finance_health
        + weights["climate_damage"] * climate_component
    )
    return float(np.clip(score, 0.0, 1.0))


def build_cascade_graph() -> nx.DiGraph:
    """Static influence graph for estimating cascade amplification pressure."""
    g = nx.DiGraph()
    nodes = [
        "energy",
        "food",
        "industry",
        "finance",
        "climate",
        "geopolitics",
        "trade",
        "population",
        "ai",
    ]
    g.add_nodes_from(nodes)
    edges = [
        ("energy", "food", 0.9),
        ("energy", "industry", 1.0),
        ("energy", "finance", 0.7),
        ("trade", "food", 0.8),
        ("trade", "industry", 0.9),
        ("geopolitics", "trade", 1.0),
        ("finance", "industry", 0.7),
        ("climate", "food", 0.8),
        ("climate", "population", 0.6),
        ("ai", "energy", 0.6),
        ("industry", "finance", 0.4),
    ]
    for src, dst, w in edges:
        g.add_edge(src, dst, weight=w)
    return g


def cascade_pressure(state: dict[str, float], graph: nx.DiGraph | None = None) -> float:
    graph = graph or build_cascade_graph()
    stress = {
        "energy": state["energy_shortage"],
        "food": state["food_stress"],
        "industry": 1.0 - min(1.0, state["industrial_output_index"]),
        "finance": state["financial_stress"],
        "climate": state["climate_damage"],
        "geopolitics": state["conflict_intensity"],
        "trade": state["shipping_disruption"],
        "population": state["migration_pressure"],
        "ai": min(1.0, state["ai_power_demand_ej"] / max(1.0, state["energy_supply_ej"])),
    }

    pressure = 0.0
    for src, dst, data in graph.edges(data=True):
        pressure += stress[src] * stress[dst] * float(data["weight"])
    norm = max(1.0, graph.number_of_edges())
    return float(np.clip(pressure / norm, 0.0, 1.0))


def detect_collapse(df: pd.DataFrame) -> pd.Series:
    """Collapse is persistent self-reinforcing decline in institutional-industrial capacity."""
    industrial_ma = df["industrial_output_index"].rolling(8, min_periods=3).mean()
    stability_ma = df["systemic_stability"].rolling(8, min_periods=3).mean()
    trend = industrial_ma.diff().rolling(4, min_periods=2).mean()
    collapse = (stability_ma < 0.45) & (trend < -0.01)
    return collapse.fillna(False)


def summarize_runs(run_frames: Iterable[pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, float]] = []
    for i, df in enumerate(run_frames):
        collapse = detect_collapse(df)
        collapse_year = int(df.loc[collapse, "year"].min()) if collapse.any() else np.nan
        rows.append(
            {
                "run": i,
                "min_stability": float(df["systemic_stability"].min()),
                "max_food_stress": float(df["food_stress"].max()),
                "max_energy_shortage": float(df["energy_shortage"].max()),
                "collapse_year": collapse_year,
                "collapsed": bool(collapse.any()),
            }
        )
    return pd.DataFrame(rows)
