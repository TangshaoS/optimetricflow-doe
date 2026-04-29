# FlowSense DOE v0.1.0

First public release of `flowsense-doe`, the open-source DOE and optimization engine used in OptimetricFlow workflows.

## Highlights

- DOE matrix generation for common industrial designs
  - Full/fractional factorial
  - Box-Behnken
  - Central composite design (CCD)
- Screening designs
  - Plackett-Burman
  - Definitive screening design (DSD)
- Mixture design support
- Regression-based DOE analysis utilities
- Bayesian next-experiment suggestion for sequential optimization
- Bioprocess preset module for common factor templates

## Installation

```bash
pip install flowsense-doe
```

## Quick example

See `examples/run_doe.py` for an end-to-end example:

- Generate a DOE design
- Simulate/fill responses
- Fit analysis model
- Request next experiment suggestion

## Notes

- License: MIT
- Documentation entry point: `README.md`
- Citation metadata: `CITATION.cff`

## Feedback

Issues and feature requests are welcome in GitHub Issues.
