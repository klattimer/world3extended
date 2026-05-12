# World3 Extended: 21st-Century Global Polycrisis Simulator

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

## Project Structure

```text
world3_extended/
├── main.py
├── requirements.txt
├── README.md
├── config/
│   └── default.yaml
├── world3/
│   ├── __init__.py
│   ├── init.py
│   ├── model.py
│   ├── systems/
│   │   ├── __init__.py
│   │   ├── population.py
│   │   ├── energy.py
│   │   ├── ai_compute.py
│   │   ├── agriculture.py
│   │   ├── industry.py
│   │   ├── finance.py
│   │   ├── climate.py
│   │   ├── geopolitics.py
│   │   └── trade.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── plotting.py
│   │   ├── metrics.py
│   │   └── montecarlo.py
│   └── scenarios/
│       ├── __init__.py
│       ├── baseline.py
│       ├── ai_energy_crisis.py
│       ├── hormuz_closure.py
│       ├── panama_closure.py
│       ├── fertilizer_shock.py
│       ├── polycrisis.py
│       └── suez_taiwan_escalation.py
├── notebooks/
│   └── exploratory_analysis.ipynb
└── tests/
    ├── test_energy.py
    ├── test_population.py
    └── test_stability.py
```

## Installation

Python 3.12+ recommended.

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

Optional:

```bash
python main.py --scenario polycrisis --output outputs_poly
```

## Model Design

- Time horizon: annual timesteps from 2025 to 2100.
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

## Testing

Run tests with:

```bash
pytest
```

## Limitations

- Aggregated global variables mask distributional and regional heterogeneity.
- No endogenous technological breakthroughs beyond constrained trend assumptions.
- Climate module is stylized and should not be interpreted as Earth-system prediction.
- Financial module captures fragility channels, not market microstructure.
- AI scaling assumptions are plausible but uncertain under frontier innovation shifts.

## Suggested Research Extensions

- Add regional agent-based layers (for example with Mesa) and migration corridors.
- Endogenize policy adaptation and demand destruction pathways.
- Couple to richer climate/economic IAM structures.
- Integrate sector-level supply chain graphs and inventory dynamics.
