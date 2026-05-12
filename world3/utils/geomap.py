"""
National-resolution choropleth map renderer for World3 Extended.

Generates per-year PNG frames of a Systemic Failure Index at country level,
then assembles them into an MP4 video (or animated GIF fallback).

How country-level stress is computed
--------------------------------------
The simulation produces global aggregate variables. Each country is assigned
an exposure weight vector that reflects its structural sensitivity to each
global stressor. The per-country Systemic Failure Index is then:

  SFI_c = clip(
      base_vuln_c
      + energy_exp_c   * global_energy_shortage
      + food_exp_c     * global_food_stress
      + finance_exp_c  * global_financial_stress
      + conflict_exp_c * global_conflict_intensity
      + climate_exp_c  * global_climate_damage
      + trade_exp_c    * global_shipping_disruption
  , 0, 1)

Calibrating these weights with real country-level data (ND-GAIN, IEA,
World Bank WDI, FSI) will substantially improve plausibility.  See README
for data sources.

NOTE: Outputs are exploratory scenario simulations only, not forecasts.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Country exposure table
# ---------------------------------------------------------------------------
# Keys are ISO 3166-1 alpha-3 codes as used by Natural Earth ("ISO_A3" column).
# Weights: base_vuln, energy_exp, food_exp, finance_exp, conflict_exp,
#          climate_exp, trade_exp
# Derived from qualitative literature review.  Replace with ND-GAIN /
# World Bank calibration for a more rigorous analysis.
# ---------------------------------------------------------------------------
_DEFAULT_WEIGHTS = (0.30, 0.70, 0.50, 0.55, 0.35, 0.50, 0.55)

COUNTRY_EXPOSURE: dict[str, tuple[float, ...]] = {
    # (base_vuln, energy_exp, food_exp, finance_exp, conflict_exp, climate_exp, trade_exp)
    # North America
    "USA": (0.12, 0.30, 0.20, 0.70, 0.15, 0.30, 0.40),
    "CAN": (0.10, 0.20, 0.15, 0.65, 0.10, 0.45, 0.50),
    "MEX": (0.28, 0.55, 0.50, 0.60, 0.45, 0.55, 0.65),
    # Europe
    "DEU": (0.12, 0.80, 0.25, 0.65, 0.20, 0.28, 0.70),
    "FRA": (0.12, 0.55, 0.22, 0.60, 0.22, 0.30, 0.65),
    "GBR": (0.13, 0.70, 0.40, 0.70, 0.18, 0.30, 0.68),
    "ITA": (0.16, 0.75, 0.35, 0.65, 0.22, 0.35, 0.68),
    "ESP": (0.15, 0.72, 0.30, 0.62, 0.18, 0.38, 0.65),
    "POL": (0.16, 0.78, 0.30, 0.58, 0.28, 0.28, 0.62),
    "UKR": (0.35, 0.60, 0.50, 0.55, 0.90, 0.40, 0.55),
    "TUR": (0.25, 0.78, 0.42, 0.62, 0.55, 0.45, 0.68),
    "NLD": (0.11, 0.65, 0.22, 0.70, 0.15, 0.42, 0.78),
    "CHE": (0.10, 0.60, 0.28, 0.68, 0.12, 0.28, 0.72),
    "NOR": (0.09, 0.15, 0.18, 0.58, 0.10, 0.42, 0.55),
    "SWE": (0.09, 0.35, 0.20, 0.62, 0.10, 0.40, 0.65),
    "GRC": (0.20, 0.78, 0.38, 0.60, 0.28, 0.45, 0.65),
    "ROU": (0.22, 0.68, 0.38, 0.52, 0.28, 0.38, 0.58),
    # Russia / Central Asia
    "RUS": (0.22, 0.20, 0.30, 0.55, 0.60, 0.35, 0.45),
    "KAZ": (0.28, 0.35, 0.45, 0.48, 0.38, 0.42, 0.50),
    # Middle East / North Africa
    "SAU": (0.22, 0.18, 0.70, 0.50, 0.48, 0.55, 0.58),
    "IRN": (0.30, 0.25, 0.55, 0.58, 0.65, 0.50, 0.55),
    "IRQ": (0.45, 0.22, 0.68, 0.58, 0.85, 0.58, 0.55),
    "ARE": (0.18, 0.20, 0.80, 0.45, 0.38, 0.60, 0.65),
    "ISR": (0.18, 0.72, 0.45, 0.60, 0.72, 0.42, 0.65),
    "EGY": (0.38, 0.78, 0.75, 0.62, 0.58, 0.65, 0.60),
    "LBY": (0.48, 0.25, 0.72, 0.58, 0.88, 0.60, 0.52),
    "MAR": (0.32, 0.82, 0.60, 0.55, 0.38, 0.58, 0.62),
    "DZA": (0.30, 0.30, 0.60, 0.52, 0.45, 0.55, 0.55),
    "YEM": (0.65, 0.55, 0.88, 0.65, 0.95, 0.68, 0.55),
    "SYR": (0.68, 0.58, 0.88, 0.62, 0.98, 0.65, 0.50),
    # Sub-Saharan Africa
    "NGA": (0.48, 0.58, 0.72, 0.65, 0.75, 0.68, 0.58),
    "ETH": (0.55, 0.65, 0.85, 0.60, 0.80, 0.78, 0.50),
    "COD": (0.65, 0.60, 0.88, 0.65, 0.92, 0.72, 0.45),
    "TZA": (0.48, 0.68, 0.78, 0.58, 0.48, 0.78, 0.52),
    "KEN": (0.42, 0.70, 0.72, 0.58, 0.58, 0.72, 0.55),
    "ZAF": (0.30, 0.62, 0.50, 0.62, 0.42, 0.55, 0.60),
    "GHA": (0.38, 0.65, 0.65, 0.58, 0.40, 0.62, 0.58),
    "MOZ": (0.58, 0.68, 0.82, 0.58, 0.62, 0.82, 0.48),
    "MDG": (0.55, 0.68, 0.80, 0.58, 0.42, 0.82, 0.48),
    "SDN": (0.60, 0.55, 0.85, 0.62, 0.88, 0.72, 0.48),
    "SOM": (0.75, 0.60, 0.92, 0.65, 0.95, 0.72, 0.40),
    # South / Southeast Asia
    "IND": (0.30, 0.75, 0.55, 0.60, 0.42, 0.65, 0.58),
    "PAK": (0.48, 0.78, 0.72, 0.65, 0.72, 0.68, 0.55),
    "BGD": (0.52, 0.80, 0.75, 0.65, 0.50, 0.82, 0.60),
    "NPL": (0.45, 0.72, 0.70, 0.58, 0.38, 0.68, 0.50),
    "LKA": (0.40, 0.80, 0.68, 0.65, 0.42, 0.65, 0.65),
    "IDN": (0.32, 0.55, 0.55, 0.58, 0.42, 0.72, 0.65),
    "PHL": (0.38, 0.78, 0.62, 0.58, 0.50, 0.78, 0.68),
    "VNM": (0.28, 0.72, 0.50, 0.55, 0.35, 0.68, 0.72),
    "MMR": (0.50, 0.60, 0.70, 0.60, 0.85, 0.68, 0.48),
    "THA": (0.22, 0.68, 0.40, 0.58, 0.32, 0.62, 0.72),
    "KHM": (0.40, 0.72, 0.65, 0.58, 0.38, 0.70, 0.62),
    "AFG": (0.72, 0.60, 0.90, 0.65, 0.98, 0.65, 0.42),
    # East Asia
    "CHN": (0.18, 0.62, 0.38, 0.55, 0.28, 0.48, 0.65),
    "JPN": (0.14, 0.88, 0.48, 0.65, 0.18, 0.35, 0.72),
    "KOR": (0.14, 0.85, 0.42, 0.68, 0.28, 0.32, 0.75),
    "TWN": (0.15, 0.85, 0.45, 0.68, 0.62, 0.35, 0.75),
    "PRK": (0.55, 0.65, 0.82, 0.58, 0.68, 0.45, 0.38),
    "MNG": (0.35, 0.55, 0.58, 0.50, 0.30, 0.48, 0.52),
    # Latin America
    "BRA": (0.25, 0.40, 0.38, 0.60, 0.38, 0.55, 0.58),
    "ARG": (0.30, 0.38, 0.38, 0.65, 0.28, 0.48, 0.58),
    "COL": (0.32, 0.55, 0.50, 0.60, 0.60, 0.55, 0.58),
    "PER": (0.32, 0.55, 0.52, 0.58, 0.42, 0.55, 0.60),
    "VEN": (0.45, 0.25, 0.68, 0.68, 0.68, 0.55, 0.50),
    "CHL": (0.22, 0.65, 0.38, 0.60, 0.25, 0.45, 0.65),
    "BOL": (0.38, 0.55, 0.58, 0.58, 0.35, 0.58, 0.55),
    # Pacific / Oceania
    "AUS": (0.12, 0.28, 0.22, 0.62, 0.12, 0.42, 0.58),
    "NZL": (0.10, 0.32, 0.20, 0.60, 0.10, 0.38, 0.60),
}

_STRESSOR_KEYS = (
    "energy_shortage",
    "food_stress",
    "financial_stress",
    "conflict_intensity",
    "climate_damage",
    "shipping_disruption",
)
# Indices map: [0]=base, [1]=energy, [2]=food, [3]=finance, [4]=conflict, [5]=climate, [6]=trade


def _load_world_geodataframe() -> Any:
    """Load a country-level GeoDataFrame from Natural Earth via geopandas."""
    import geopandas as gpd

    # geopandas ≥ 0.13 deprecated built-in datasets; use URL instead.
    url = (
        "https://naturalearth.s3.amazonaws.com/50m_cultural/ne_50m_admin_0_countries.zip"
    )
    try:
        world = gpd.read_file(url)
        logger.info("Loaded Natural Earth 50m country geometries from remote URL.")
    except Exception as exc:  # pragma: no cover
        logger.warning("Remote load failed (%s). Falling back to geopandas built-in.", exc)
        # Still works on geopandas 0.14 with deprecation warning; fine for offline use.
        # world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))  # type: ignore[attr-defined]
        world = gpd.read_file(
            "http://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_admin_0_countries.geojson"
        )
    # Normalise ISO column name across Natural Earth schema versions
    for candidate in ("ISO_A3", "iso_a3", "ADM0_A3"):
        if candidate in world.columns:
            world = world.rename(columns={candidate: "ISO_A3"})
            break
    return world


def compute_country_stress(state_row: pd.Series) -> pd.Series:
    """Map a single-year global state row to a per-country Systemic Failure Index.

    Returns a pd.Series indexed by ISO_A3 code, values in [0, 1].
    """
    global_vals = tuple(float(state_row.get(k, 0.0)) for k in _STRESSOR_KEYS)
    # energy, food, finance, conflict, climate, trade

    results: dict[str, float] = {}
    for iso, weights in COUNTRY_EXPOSURE.items():
        base = weights[0]
        score = (
            base
            + weights[1] * global_vals[0]  # energy
            + weights[2] * global_vals[1]  # food
            + weights[3] * global_vals[2]  # finance
            + weights[4] * global_vals[3]  # conflict
            + weights[5] * global_vals[4]  # climate
            + weights[6] * global_vals[5]  # trade
        )
        results[iso] = float(np.clip(score / (1.0 + sum(weights[1:])), 0.0, 1.0))

    return pd.Series(results)


def _default_stress(state_row: pd.Series) -> float:
    """Fallback stress for countries not in the exposure table."""
    dw = _DEFAULT_WEIGHTS
    global_vals = tuple(float(state_row.get(k, 0.0)) for k in _STRESSOR_KEYS)
    score = (
        dw[0]
        + dw[1] * global_vals[0]
        + dw[2] * global_vals[1]
        + dw[3] * global_vals[2]
        + dw[4] * global_vals[3]
        + dw[5] * global_vals[4]
        + dw[6] * global_vals[5]
    )
    return float(np.clip(score / (1.0 + sum(dw[1:])), 0.0, 1.0))


def plot_world_frame(
    world_gdf: Any,
    stress: pd.Series,
    year: int,
    output_dir: Path,
    scenario_name: str,
    cmap: str = "RdYlGn_r",
    vmin: float = 0.0,
    vmax: float = 1.0,
) -> Path:
    """Render one PNG choropleth frame for a given year."""
    import geopandas as gpd

    gdf = world_gdf.copy()
    default = _default_stress
    gdf["sfi"] = gdf["ISO_A3"].apply(lambda iso: stress.get(iso, None))
    # Fill unmapped countries with the global default
    missing_mask = gdf["sfi"].isna()
    # We need a representative state row for default computation; use the median stress
    gdf.loc[missing_mask, "sfi"] = float(stress.mean())

    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    cmap_obj = plt.get_cmap(cmap)

    fig, ax = plt.subplots(1, 1, figsize=(16, 8))
    ax.set_facecolor("#a8c8e8")
    fig.patch.set_facecolor("#1a1a2e")

    gdf.plot(
        column="sfi",
        ax=ax,
        cmap=cmap_obj,
        norm=norm,
        edgecolor="#333333",
        linewidth=0.3,
        missing_kwds={"color": "#555555"},
    )

    sm = plt.cm.ScalarMappable(cmap=cmap_obj, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.02, pad=0.01, orientation="vertical")
    cbar.set_label("Systemic Failure Index", color="white", fontsize=10)
    cbar.ax.yaxis.set_tick_params(color="white")
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color="white")

    ax.set_title(
        f"World3 Extended — {scenario_name} — {year}",
        color="white",
        fontsize=14,
        pad=12,
    )
    ax.axis("off")

    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / f"frame_{year:04d}.png"
    fig.savefig(out, dpi=140, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return out


def generate_map_frames(
    df: pd.DataFrame,
    frames_dir: Path,
    scenario_name: str,
    world_gdf: Any | None = None,
) -> list[Path]:
    """Generate one choropleth PNG per simulation year.

    Parameters
    ----------
    df:
        Simulation output DataFrame from World3Model.run().
    frames_dir:
        Directory to write PNG frames into.
    scenario_name:
        Used in the frame title.
    world_gdf:
        Pre-loaded GeoDataFrame (optional; loaded automatically if None).

    Returns
    -------
    Sorted list of output frame paths.
    """
    if world_gdf is None:
        world_gdf = _load_world_geodataframe()

    frames_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    for _, row in df.iterrows():
        year = int(row["year"])
        stress = compute_country_stress(row)
        path = plot_world_frame(world_gdf, stress, year, frames_dir, scenario_name)
        paths.append(path)
        logger.info("Rendered frame %d", year)

    return sorted(paths)


def frames_to_video(
    frame_paths: list[Path],
    output_path: Path,
    fps: int = 4,
) -> Path:
    """Assemble PNG frames into an MP4 video (or GIF if ffmpeg unavailable).

    Parameters
    ----------
    frame_paths:
        Ordered list of PNG paths (one per year).
    output_path:
        Destination file; use .mp4 for video, .gif for animated GIF.
    fps:
        Frames per second.  4 fps → one year displayed every 0.25 s.

    Returns
    -------
    Path to the assembled video/GIF file.
    """
    import imageio

    output_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = output_path.suffix.lower()

    if suffix == ".mp4":
        try:
            writer = imageio.get_writer(
                str(output_path),
                fps=fps,
                codec="libx264",
                quality=8,
                pixelformat="yuv420p",
            )
            for fp in frame_paths:
                writer.append_data(imageio.imread(str(fp)))  # type: ignore[arg-type]
            writer.close()
            logger.info("MP4 written to %s", output_path)
            return output_path
        except Exception as exc:
            logger.warning("MP4 writer failed (%s); falling back to GIF.", exc)
            output_path = output_path.with_suffix(".gif")
            suffix = ".gif"

    # GIF fallback
    images = [imageio.imread(str(fp)) for fp in frame_paths]
    imageio.mimsave(str(output_path), images, fps=fps, loop=0)
    logger.info("GIF written to %s", output_path)
    return output_path
