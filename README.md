# OptimetricFlow DOE Engine (FlowSense DOE)

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)

FlowSense DOE is a Python package for industrial Design of Experiments (DOE), response analysis, and Bayesian next-experiment suggestion.

This repository is the open-source DOE engine used by OptimetricFlow.

## What it provides

- Classical DOE: Full/Fractional Factorial, Box-Behnken, Central Composite Design (CCD)
- Screening: Plackett-Burman and Definitive Screening Design (DSD)
- Mixture designs: Simplex Lattice, Simplex Centroid, constrained mixture
- Sequential optimization: Bayesian next-experiment suggestion
- Domain presets: bioprocess factor templates

## Target users

- Process engineers running lab/pilot optimization
- Bioprocess and pharmaceutical scientists building QbD workflows
- Data scientists supporting industrial R&D experiment strategy

## Typical use cases

- Build a DOE matrix for screening or response surface modeling
- Fit a regression model to estimate factor effects and interactions
- Recommend the next experiment using Bayesian optimization
- Standardize factor definitions with domain presets

## Quick start

### 1) Installation

```bash
pip install flowsense-doe
```

### 2) Generate a design

```python
from flowsense_doe import DOEDesigner

designer = DOEDesigner()
factors = ["Temperature", "pH", "Stir_Rate"]
levels = [[30.0, 37.0], [6.0, 7.5], [200.0, 500.0]]

design_df = designer.box_behnken(factors, levels, center_points=3)
print(design_df.head())
```

### 3) Suggest the next experiment

```python
import numpy as np
from flowsense_doe import BayesianSuggester

factors_def = [
    {"name": "Temp", "min": 25.0, "max": 42.0},
    {"name": "pH", "min": 5.5, "max": 7.5},
]

suggester = BayesianSuggester(factors_def, objective="maximize")
X_obs = np.array([[30.0, 6.0], [37.0, 7.0]])
y_obs = np.array([12.5, 24.3])

next_point = suggester.suggest(X_obs, y_obs)
print("Suggested experiment:", next_point["suggestion"])
```

See `examples/run_doe.py` for an end-to-end workflow.

## Domain preset example

```python
from flowsense_doe.presets.bioprocess import bioprocess_preset

print(bioprocess_preset["common_factors"])
```

## Relationship to OptimetricFlow platform

This repository contains the open-source DOE and optimization engine. The full OptimetricFlow platform includes workflow automation, quality reporting, and deployment-oriented analysis pipelines.

Learn more: [https://optimetricflow.cn](https://optimetricflow.cn)

## Limitations

- Not a full ELN/LIMS replacement
- No built-in experiment execution hardware control
- Advanced enterprise workflow features are part of the OptimetricFlow platform

## Citation

If this project supports your research or process development, please cite it using `CITATION.cff`.

## License

This project is licensed under the MIT License.
