"""
Bioprocess / Fermentation / Synthetic Biology Industry Preset.
"""

PRESET = {
    "industry": "bioprocess",
    "label": "Bioprocess / Fermentation / Synthetic Biology",
    "common_factors": [
        {"name": "Temperature", "unit": "℃", "typical_low": 25, "typical_high": 42, "role": "continuous"},
        {"name": "pH", "unit": "", "typical_low": 5.5, "typical_high": 7.5, "role": "continuous"},
        {"name": "DO", "unit": "%", "typical_low": 20, "typical_high": 80, "role": "continuous"},
        {"name": "Stir_Rate", "unit": "rpm", "typical_low": 200, "typical_high": 800, "role": "continuous"},
        {"name": "Feed_Rate", "unit": "mL/h", "typical_low": 0, "typical_high": 50, "role": "continuous"},
        {"name": "Substrate_Conc", "unit": "g/L", "typical_low": 5, "typical_high": 50, "role": "continuous"},
        {"name": "Inducer_Conc", "unit": "mM", "typical_low": 0, "typical_high": 1.0, "role": "continuous"},
        {"name": "Inoculum_OD", "unit": "OD600", "typical_low": 0.05, "typical_high": 0.2, "role": "continuous"},
        {"name": "Time", "unit": "h", "typical_low": 4, "typical_high": 72, "role": "continuous"},
        {"name": "Carbon_Source", "unit": "", "typical_low": None, "typical_high": None, "role": "categorical"},
        {"name": "Strain", "unit": "", "typical_low": None, "typical_high": None, "role": "categorical"},
    ],
    "common_responses": [
        {"name": "Titer", "unit": "g/L", "direction": "maximize"},
        {"name": "Yield_Yps", "unit": "g/g", "direction": "maximize"},
        {"name": "Productivity_Qp", "unit": "g/(L·h)", "direction": "maximize"},
        {"name": "Specific_Growth_Rate_mu", "unit": "1/h", "direction": "maximize"},
        {"name": "Final_Biomass", "unit": "g/L (DCW)", "direction": "maximize"},
        {"name": "Viability", "unit": "%", "direction": "maximize"},
        {"name": "Impurity", "unit": "%", "direction": "minimize"},
        {"name": "Cost_per_gram", "unit": "$/g", "direction": "minimize"},
    ],
    "units": ["g/L", "g/g", "%", "1/h", "h", "rpm", "℃", "mL/h", "mM", "OD600"],
    "recommendation_rules": [
        {
            "condition": "n_factors >= 8",
            "suggestion": "Plackett-Burman or Definitive Screening Design is recommended for the screening phase.",
            "design_type": ["plackett_burman", "definitive_screening"],
        },
        {
            "condition": "n_factors in [3,4,5]",
            "suggestion": "Box-Behnken or Central Composite is recommended for response surface methodology.",
            "design_type": ["box_behnken", "central_composite"],
        },
        {
            "condition": "n_responses >= 2",
            "suggestion": "Multiple CQAs detected. Multi-objective optimization (e.g. ParEGO) is recommended.",
            "solver": "parego",
        },
    ],
}
