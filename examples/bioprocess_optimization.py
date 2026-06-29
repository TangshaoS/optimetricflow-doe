"""
Real usage example: bioprocess yield optimization (synthetic dataset).

Scenario: maximize monoclonal antibody titer by tuning temperature, pH, and stir rate.
Phase 1 — sparse corner screening; Phase 2 — Bayesian optimization suggests the next run.
"""

import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from flowsense_doe import BayesianSuggester, DOEAnalyzer, DOEDesigner


def true_yield(temp: float, ph: float, stir_rate: float) -> float:
    """Synthetic ground-truth response (unknown to the optimizer in practice)."""
    return (
        18.0
        - 0.15 * (temp - 34.0) ** 2
        - 12.0 * (ph - 6.6) ** 2
        - 0.00008 * (stir_rate - 350.0) ** 2
    )


def main():
    np.random.seed(42)

    factors = ["Temperature_C", "pH", "Stir_Rate_rpm"]
    levels = [[30.0, 38.0], [6.0, 7.2], [200.0, 500.0]]

    # Full Box-Behnken design saved as the reference dataset
    designer = DOEDesigner()
    full_design = designer.box_behnken(factors, levels, center_points=3)
    full_design = full_design.drop(columns=["Response"])
    full_design["Titer_g_L"] = [
        true_yield(row["Temperature_C"], row["pH"], row["Stir_Rate_rpm"])
        + np.random.normal(0, 0.3)
        for _, row in full_design.iterrows()
    ]

    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, "synthetic_fermentation.csv")
    full_design.to_csv(csv_path, index=False)

    # Sparse initial screening: four factorial corners only
    corners = pd.DataFrame(
        [
            [30.0, 6.0, 200.0],
            [30.0, 7.2, 500.0],
            [38.0, 6.0, 500.0],
            [38.0, 7.2, 200.0],
        ],
        columns=factors,
    )
    corners["Titer_g_L"] = [
        true_yield(t, p, s) + np.random.normal(0, 0.3)
        for t, p, s in corners[factors].values
    ]

    analyzer_df = full_design.rename(columns={"Titer_g_L": "Response"})
    analyzer = DOEAnalyzer(analyzer_df)
    results = analyzer.fit_model(include_quadratic=True)

    factors_def = [
        {"name": "Temperature_C", "min": 30.0, "max": 38.0},
        {"name": "pH", "min": 6.0, "max": 7.2},
        {"name": "Stir_Rate_rpm", "min": 200.0, "max": 500.0},
    ]
    suggester = BayesianSuggester(factors_def, objective="maximize")
    X_obs = corners[factors].values
    y_obs = corners["Titer_g_L"].values
    next_point = suggester.suggest(X_obs, y_obs)
    sugg = next_point["suggestion"]

    best_before = float(y_obs.max())
    y_after = (
        true_yield(sugg["Temperature_C"], sugg["pH"], sugg["Stir_Rate_rpm"])
        + np.random.normal(0, 0.3)
    )

    stir_fixed = 350.0
    temp_range = np.linspace(30, 38, 50)
    ph_range = np.linspace(6.0, 7.2, 50)
    T, P = np.meshgrid(temp_range, ph_range)
    Z = true_yield(T, P, stir_fixed)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    ax = axes[0]
    cf = ax.contourf(T, P, Z, levels=20, cmap="viridis", alpha=0.85)
    ax.scatter(
        corners["Temperature_C"],
        corners["pH"],
        c=corners["Titer_g_L"],
        cmap="plasma",
        edgecolors="white",
        s=100,
        zorder=5,
        label="Initial screening (4 runs)",
    )
    ax.scatter(
        [sugg["Temperature_C"]],
        [sugg["pH"]],
        marker="*",
        s=300,
        c="red",
        edgecolors="white",
        zorder=6,
        label="BO suggestion",
    )
    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel("pH")
    ax.set_title(f"Response surface at {stir_fixed:.0f} rpm (R²={results['r_squared']:.3f})")
    ax.legend(loc="upper right", fontsize=8)
    plt.colorbar(cf, ax=ax, label="Titer (g/L)")

    ax2 = axes[1]
    bars = ax2.bar(
        ["Best before BO", "After suggested run"],
        [best_before, y_after],
        color=["#5c6bc0", "#26a69a"],
        edgecolor="white",
    )
    ax2.set_ylabel("Titer (g/L)")
    ax2.set_title("Optimization outcome")
    ymax = max(best_before, y_after) * 1.15
    ax2.set_ylim(0, ymax)
    for bar, val in zip(bars, [best_before, y_after]):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            val + 0.15,
            f"{val:.2f}",
            ha="center",
            fontsize=11,
            fontweight="bold",
        )

    plt.tight_layout()
    out_path = os.path.join(project_root, "assets", "optimization_example.png")
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Dataset saved: {csv_path}")
    print(f"Plot saved: {out_path}")
    print(f"Model R²: {results['r_squared']:.4f}")
    print(f"Best before: {best_before:.2f} g/L")
    print(f"After BO run: {y_after:.2f} g/L")
    print(f"Suggested: {next_point['suggestion']}")


if __name__ == "__main__":
    main()
