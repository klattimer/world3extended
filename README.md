# World3 Extended: 21st-Century Global Polycrisis Simulator

[![Tests](https://github.com/karllattimer/w4/actions/workflows/tests.yml/badge.svg)](https://github.com/karllattimer/w4/actions/workflows/tests.yml)

World3 Extended is a production-quality, modular Python package for exploratory system-dynamics simulation of civilisational stability under interacting 21st-century constraints.

It extends World3-style dynamics to include:
- Population, food, energy, and industrial feedbacks
- Fossil depletion and EROI decline
- AI/data-centre compute-energy competition
- Geopolitical chokepoint disruptions (Hormuz, Suez, Panama, Taiwan semiconductors)
- Fertilizer and trade fragility
- Climate stress and pollution accumulation
- Debt/financial instability amplification
- Composite systemic stability and collapse detection

## Critical Disclaimer

This project is **not a forecasting engine**.

Outputs are exploratory scenario simulations only, intended for stress-testing assumptions and reasoning about nonlinear interactions. They are highly sensitive to model structure, parameter values, and stochastic shock realization.

- Precise collapse timing cannot be predicted.
- Nonlinearity and path dependence dominate outcomes.
- Cascading effects can produce overshoot and Seneca-cliff style declines.
- Adaptation exists but can be outpaced by reinforcing stressors.

## Conceptual Lineage

The model references and operationalizes ideas from:
- World3 and *Limits to Growth*
- EROI decline and net-energy constraints
- Ecological overshoot
- Seneca cliff dynamics
- Tainter-style complexity/collapse frameworks
- Supply-chain fragility and chokepoint dependence

## Installation

Python 3.12+ recommended.

```bash
pip install -r requirements.txt
```

## Run

### Standard annual resolution

```bash
python main.py
python main.py --scenario polycrisis --output outputs_poly
```

### Daily resolution (higher temporal detail)

```bash
python main.py --scenario polycrisis --timestep-days 1 --output outputs_poly_daily
```

### Map video generation

Generate national-resolution choropleth map videos showing systemic stress over time:

```bash
# Run a scenario and generate map frames for all years
python scripts/generate_video.py --scenario polycrisis --fps 4

# Keep PNG frames for manual editing
python scripts/generate_video.py --scenario baseline --fps 6 --keep-frames

# Combine daily resolution run with video
python main.py --scenario polycrisis --timestep-days 1 --output outputs_daily
python scripts/generate_video.py --scenario polycrisis --fps 8
```

### Interactive web interface

Explore parameter space and run scenario sensitivity analysis with real-time feedback using the Bokeh-based web interface:

```bash
bokeh serve scripts/web_ui.py --show
```

This launches an interactive dashboard at `http://localhost:5006/web_ui` with:
- **Scenario & shock tuning:** Select scenarios and adjust shock timing/severity
- **Subsystem parameter sliders:** Modify energy depletion rates, EROI decline, AI growth, financial fragility, and more
- **Live 10-year preview:** Simulation updates as you adjust parameters
- **Key metrics dashboard:** Final stability, minimum stability, collapse indicator

Example workflow:
1. Change to `polycrisis` scenario
2. Increase AI compute growth from 36% to 45%
3. Shift Suez closure 1 year later (2030 instead of 2029)
4. Observe resulting stability trajectory and collapse risk

The 10-year horizon (2025–2035) enables rapid exploration before running full 75-year deterministic or Monte Carlo analyses.

## Interactive Modelling

The web interface enables exploratory hypothesis testing and sensitivity analysis without requiring command-line proficiency or deep familiarity with the codebase.

### Typical Interactive Workflow

1. **Load baseline:** Start with `baseline` scenario to understand nominal dynamics
2. **Introduce shock:** Switch to `polycrisis` or a specific scenario (e.g., `hormuz_closure`)
3. **Adjust parameters:** Use sliders to explore:
   - How does increasing AI compute growth accelerate collapse?
   - What if oil depletion slows (improved efficiency) or accelerates?
   - How sensitive is stability to financial fragility?
4. **Compare outcomes:** Observe real-time changes in:
   - Stability trajectory over 10 years
   - Minimum stability reached
   - Whether collapse signal triggers
5. **Document findings:** Screenshot dashboard or export CSV results for documentation

### Parameter Space Coverage

The web interface exposes ~20 key parameters across:
- **Energy:** depletion rates (fossil fuels), EROI decline, renewable growth capacity
- **AI/Compute:** accelerating growth rates, power demand limits
- **Population:** stress-induced mortality sensitivity
- **Finance:** debt accumulation, financial system fragility
- **Trade:** supply-chain fragmentation risk
- **Climate:** warming sensitivity to cumulative emissions

This allows rapid exploration of:
- **Robustness:** Which assumptions matter most for collapse timing?
- **Policy levers:** What parameter changes most delay systemic failure?
- **Scenario coupling:** How do multiple simultaneous shocks cascade?

### Limitations of Interactive Mode

- **10-year horizon:** Designed for near-term trend exploration, not long-term dynamics (use full 75-year runs for those)
- **No Monte Carlo:** Interactive mode runs deterministic simulations; use `main.py` for uncertainty quantification
- **Single trajectory:** Shows one path per parameter set; see `main.py` output for probability distributions

For production-grade analysis, export results to CSV and conduct full Monte Carlo sensitivity via `main.py --scenario polycrisis`.

## Model Design

- Time horizon: annual timesteps from 2025 to 2100.
- Temporal resolution: supports annual or sub-annual integration via `timestep_years` or `timestep_days`.
- Dynamics: coupled timestep system-dynamics engine with nonlinear feedbacks.
- Stochasticity: random geopolitical events and Monte Carlo parameter uncertainty.
- Determinism: fixed seed for reproducibility unless user changes config.

### Collapse Definition

Collapse is represented as:

**persistent self-reinforcing decline in industrial and institutional capacity**,

operationalized by sustained drops in rolling industrial output and low systemic stability.

## Included Scenarios

- `baseline`: gradual degradation with intermittent shocks
- `ai_energy_crisis`: accelerated AI compute-power race
- `hormuz_closure`: major oil chokepoint disruption
- `panama_closure`: prolonged Panama Canal shutdown and rerouting stress
- `fertilizer_shock`: fertilizer availability crisis
- `polycrisis`: coupled multi-domain stress cascade
- `suez_taiwan_escalation`: Suez war shock followed by Taiwan semiconductor conflict

## Output Artifacts

A standard run generates:
- Time-series chart of core state variables
- Sensitivity correlation heatmap from Monte Carlo summary
- Collapse probability curve
- Energy Sankey flow diagram
- Regional stress proxy map
- Scenario run CSV
- Monte Carlo summary CSV

## Map Video Generation

The script `scripts/generate_video.py` creates national-resolution world map videos from simulation output using the country-level stress mapping in `world3/utils/geomap.py`.

Basic usage:

```bash
python scripts/generate_video.py
```

Useful options:
- `--config`: YAML config path (default `config/default.yaml`)
- `--scenario`: scenario module name (for example `polycrisis`)
- `--output`: output video file path (defaults to `outputs/map_<scenario>.mp4`)
- `--frames-dir`: temporary frame directory (defaults to `outputs/frames_<scenario>`)
- `--fps`: output frame rate (default `4`)
- `--keep-frames`: keep PNG frames after encoding

Examples:

```bash
python scripts/generate_video.py --scenario polycrisis --fps 6
python scripts/generate_video.py --scenario polycrisis --fps 6 --keep-frames
python scripts/generate_video.py --config config/claude-opinion.yaml --scenario polycrisis --output outputs_poly/map_poly.mp4
```

Daily-resolution video generation:

```bash
python scripts/generate_video.py --config config/default.yaml --scenario polycrisis
```

To force daily integration for this script, set `simulation.timestep_days: 1` in your chosen config file before running.

## Testing

Run tests locally with:

```bash
pytest
```

All tests run automatically on push and pull request to `main` or `develop` branches via GitHub Actions. See the test status badge at the top of this README.

To run tests with coverage reporting:

```bash
pytest --cov=world3 --cov-report=term
```

## Limitations

- Aggregated global variables mask distributional and regional heterogeneity.
- No endogenous technological breakthroughs beyond constrained trend assumptions.
- Climate module is stylized and should not be interpreted as Earth-system prediction.
- Financial module captures fragility channels, not market microstructure.
- AI scaling assumptions are plausible but uncertain under frontier innovation shifts.

## Parameter Sensitivity & Web UI Behavior

### Why Sliders Have Different Effects by Scenario

Diagnostic analysis shows that subsystem parameter sliders *are* correctly applied and affect underlying model variables (energy supplies vary 50-150% with slider changes). However, **stability metrics show different sensitivity depending on scenario severity**:

| Scenario | Slider Effect on Stability | Reason |
|----------|---------------------------|--------|
| **baseline** | HIGH | Gradual degradation; parameter tuning significantly delays collapse |
| **ai_energy_crisis** | MEDIUM-HIGH | AI growth dominates, but renewable/EROI adjustments provide resilience |
| **hormuz_closure** | MEDIUM | Single chokepoint; financial/energy parameters can mitigate impact |
| **polycrisis** | LOW | Simultaneous geopolitical + climate + financial shocks overwhelm individual parameter effects |

**Key finding:** In the polycrisis scenario, geopolitical shocks trigger maximum financial stress (→ exponential debt growth) and conflict intensity (→ immediate institutional failure), which dominate outcomes regardless of whether oil depletes 1% or 8% annually. This is **not a bug**—it reflects genuine dynamics where extreme simultaneous crises exceed adaptive capacity.

**Implication:** To explore parameter sensitivity, use milder scenarios (baseline, hormuz_closure) or shorter time horizons. Polycrisis represents worst-case collapse; slider effects are visible on longer timescales (2025–2200) or in scenarios with fewer simultaneous shocks.

See `SLIDER_ANALYSIS_FINDINGS.md` for detailed diagnostic results.

### Planned Enhancements to Model Realism

**Water System Coupling** (in development)
- Data centre cooling water demand: scales with AI compute index; redirects from potable supplies
- Agricultural water stress: feedback from cooling redirection + thermal pollution
- Food security impact: water scarcity → reduced irrigation → yield penalty

**CO2 Availability Constraint** (in development)
- CO2 as industrial byproduct (cement, ammonia production)
- Competing demands: food processing, agriculture, medical, euthanasia
- Livestock culling bottleneck: when CO2 scarce, culling capacity constrained → unsustainable herds → food production collapse

**Enhanced Commodity Price Dynamics** (future)
- Granular tracking of agricultural commodity prices separate from inflation
- Oil/gas price volatility tied to supply/demand imbalances
- Feedback from prices to investment & consumption decisions

These enhancements will expand the model's ability to capture supply-chain bottlenecks and resource competition that currently affect outputs indirectly through aggregate stress metrics.

## Suggested Research Extensions

- Add regional agent-based layers (for example with Mesa) and migration corridors.
- Implement water system subsystem with data centre cooling + agricultural water competition.
- Add CO2 availability constraint affecting livestock culling capacity and food production.
- Endogenize policy adaptation and demand destruction pathways.
- Couple to richer climate/economic IAM structures.
- Integrate sector-level supply chain graphs and inventory dynamics.
- Add individual parameter response curves to sensitivity analysis in `main.py` output.
