"""
Example: End-to-end workflow using flowsense-doe
"""

import numpy as np
import pandas as pd
import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from flowsense_doe import DOEDesigner, DOEAnalyzer, BayesianSuggester


def main():
    print("=== 1. Generating a Central Composite Design (CCD) ===")
    designer = DOEDesigner()
    factors = ["Temp", "pH"]
    levels = [[30.0, 37.0], [6.0, 7.0]]
    
    design_df = designer.central_composite(factors, levels, center_points=4)
    print("\nGenerated Experimental Matrix:")
    print(design_df)

    print("\n=== 2. Simulating Responses and Running Analysis ===")
    # Simulate a quadratic response surface: Y = 20 - (Temp-34)^2 - 10*(pH-6.5)^2
    # We add some noise.
    responses = []
    for idx, row in design_df.iterrows():
        t = row["Temp"]
        p = row["pH"]
        y = 20.0 - (t - 34.0)**2 - 10.0 * (p - 6.5)**2 + np.random.normal(0, 0.5)
        responses.append(y)
        
    design_df["Response"] = responses
    
    # Fit standard DOE Model
    analyzer = DOEAnalyzer(design_df)
    results = analyzer.fit_model(include_quadratic=True)
    
    print("\nModel Summary:")
    print(f"R-Squared: {results['r_squared']:.4f}")
    print(f"Equation: {analyzer.get_regression_equation()}")

    print("\n=== 3. Suggesting the Next Point via Bayesian Optimization ===")
    # Setup suggester
    factors_def = [
        {'name': 'Temp', 'min': 30.0, 'max': 37.0},
        {'name': 'pH', 'min': 6.0, 'max': 7.0}
    ]
    suggester = BayesianSuggester(factors_def, objective='maximize')
    
    X_obs = design_df[factors].values
    y_obs = design_df["Response"].values
    
    next_point = suggester.suggest(X_obs, y_obs)
    print("\nNext Recommended Experiment Run:")
    print(next_point['suggestion'])


if __name__ == "__main__":
    main()
