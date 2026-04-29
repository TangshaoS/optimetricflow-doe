"""
DOE Results Analysis Module.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures


class DOEAnalyzer:
    """DOE Analyzer - fits models and evaluates factor effects."""
    
    def __init__(self, design_data: pd.DataFrame):
        self.data = design_data.copy()
        self.factors = [col for col in design_data.columns 
                       if col not in ['StdOrder', 'RunOrder', 'Response']]
        self.response_col = 'Response'
        self.model = None
        self.results = {}
        self.is_mixture = self._detect_if_mixture()

    def _detect_if_mixture(self) -> bool:
        if self.data[self.factors].empty:
            return False
        sums = self.data[self.factors].sum(axis=1)
        return np.allclose(sums, 1.0, atol=1e-3)
        
    def fit_model(self, 
                  include_interactions: bool = True,
                  include_quadratic: bool = False,
                  excluded_terms: List[str] = None) -> Dict[str, Any]:
        """Fits a linear regression model."""
        X = self.data[self.factors].values
        y = self.data[self.response_col].dropna().values
        X = X[:len(y)]
        
        if include_quadratic:
            poly = PolynomialFeatures(degree=2, include_bias=False)
            X_poly = poly.fit_transform(X)
            feature_names = poly.get_feature_names_out(self.factors)
        elif include_interactions:
            poly = PolynomialFeatures(degree=2, include_bias=False, interaction_only=True)
            X_poly = poly.fit_transform(X)
            feature_names = poly.get_feature_names_out(self.factors)
        else:
            X_poly = X
            feature_names = self.factors
            
        if excluded_terms:
            keep_indices = [i for i, name in enumerate(feature_names) if name not in excluded_terms]
            if not keep_indices:
                X_poly = np.zeros((len(y), 0)) 
                feature_names = []
            else:
                X_poly = X_poly[:, keep_indices]
                feature_names = [feature_names[i] for i in keep_indices]
        
        fit_intercept = not self.is_mixture
        self.model = LinearRegression(fit_intercept=fit_intercept)
        self.model.fit(X_poly, y)
        
        y_pred = self.model.predict(X_poly)
        
        ss_total = np.sum((y - np.mean(y)) ** 2)
        ss_residual = np.sum((y - y_pred) ** 2)
        ss_regression = ss_total - ss_residual
        
        r_squared = 1 - (ss_residual / ss_total)
        n = len(y)
        p = X_poly.shape[1]
        adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - p - 1)
        
        mse = ss_residual / (n - p - 1)
        rmse = np.sqrt(mse)
        
        coefficients = dict(zip(feature_names, self.model.coef_))
        coefficients['Intercept'] = self.model.intercept_
        
        if fit_intercept:
            X_with_intercept = np.column_stack([np.ones(len(X_poly)), X_poly])
        else:
            X_with_intercept = X_poly
            
        try:
            xtx_inv = np.linalg.pinv(X_with_intercept.T @ X_with_intercept)
            var_b = mse * xtx_inv.diagonal()
            se = np.sqrt(np.maximum(var_b, 0))
            
            all_params = np.append(self.model.intercept_, self.model.coef_) if fit_intercept else self.model.coef_
            t_stats = all_params / se
            p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), n - p - 1))
        except Exception:
            p_values = np.array([np.nan] * (p + (1 if fit_intercept else 0)))
        
        param_names = (['Intercept'] if fit_intercept else []) + list(feature_names)
        p_val_dict = dict(zip(param_names, p_values))
        if not fit_intercept:
            p_val_dict['Intercept'] = np.nan
        
        df_regression = p
        df_residual = n - p - 1
        df_total = n - 1
        
        ms_regression = ss_regression / df_regression
        ms_residual = ss_residual / df_residual
        
        f_statistic = ms_regression / ms_residual
        f_pvalue = 1 - stats.f.cdf(f_statistic, df_regression, df_residual)
        
        anova_table = pd.DataFrame({
            'Source': ['Regression', 'Residual', 'Total'],
            'DF': [df_regression, df_residual, df_total],
            'SS': [ss_regression, ss_residual, ss_total],
            'MS': [ms_regression, ms_residual, np.nan],
            'F': [f_statistic, np.nan, np.nan],
            'P-value': [f_pvalue, np.nan, np.nan]
        })
        
        self.results = {
            'coefficients': coefficients,
            'p_values': p_val_dict,
            'r_squared': r_squared,
            'adj_r_squared': adj_r_squared,
            'rmse': rmse,
            'anova': anova_table,
            'predictions': y_pred,
            'residuals': y - y_pred,
            'feature_names': feature_names
        }
        
        return self.results
    
    def get_regression_equation(self) -> str:
        if not self.results:
            raise ValueError("Please fit the model first.")
        
        coeffs = self.results['coefficients']
        equation = f"Response = {coeffs['Intercept']:.4f}"
        
        for term, coef in coeffs.items():
            if term != 'Intercept':
                sign = '+' if coef >= 0 else '-'
                equation += f" {sign} {abs(coef):.4f}*{term}"
        
        return equation
    
    def analyze_effects(self) -> pd.DataFrame:
        if not self.results:
            raise ValueError("Please fit the model first.")
        
        effects_data = []
        for term, coef in self.results['coefficients'].items():
            if term != 'Intercept':
                p_val = self.results['p_values'][term]
                effects_data.append({
                    'Term': term,
                    'Coefficient': coef,
                    'P-value': p_val,
                    'Significant': 'Yes' if p_val < 0.05 else 'No'
                })
        
        effects_df = pd.DataFrame(effects_data)
        effects_df = effects_df.sort_values('P-value')
        return effects_df
    
    def plot_main_effects(self, figsize: Tuple[int, int] = (12, 4)) -> plt.Figure:
        n_factors = len(self.factors)
        fig, axes = plt.subplots(1, n_factors, figsize=figsize)
        
        if n_factors == 1:
            axes = [axes]
        
        for i, factor in enumerate(self.factors):
            grouped = self.data.groupby(factor)[self.response_col].mean()
            axes[i].plot(grouped.index, grouped.values, 'o-', linewidth=2, markersize=8)
            axes[i].set_xlabel(factor)
            axes[i].set_ylabel('Mean Response')
            axes[i].set_title(f'Main Effect of {factor}')
            axes[i].grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_interaction(self, factor1: str, factor2: str, figsize: Tuple[int, int] = (8, 6)) -> plt.Figure:
        fig, ax = plt.subplots(figsize=figsize)
        levels2 = sorted(self.data[factor2].unique())
        
        for level2 in levels2:
            subset = self.data[self.data[factor2] == level2]
            grouped = subset.groupby(factor1)[self.response_col].mean()
            ax.plot(grouped.index, grouped.values, 'o-', label=f'{factor2}={level2}', linewidth=2, markersize=8)
        
        ax.set_xlabel(factor1)
        ax.set_ylabel('Mean Response')
        ax.set_title(f'Interaction: {factor1} vs {factor2}')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig

    def plot_response_surface(self, factor1: str, factor2: str, fixed_values: Dict[str, float] = None, figsize: Tuple[int, int] = (12, 5)) -> plt.Figure:
        if self.model is None:
            raise ValueError("Please fit the model first.")
        
        f1_range = np.linspace(self.data[factor1].min(), self.data[factor1].max(), 50)
        f2_range = np.linspace(self.data[factor2].min(), self.data[factor2].max(), 50)
        F1, F2 = np.meshgrid(f1_range, f2_range)
        
        X_pred = np.zeros((len(f1_range) * len(f2_range), len(self.factors)))
        
        if fixed_values is None:
            fixed_values = {f: self.data[f].mean() for f in self.factors if f not in [factor1, factor2]}
        
        factor_idx = {f: i for i, f in enumerate(self.factors)}
        for i, (f1_val, f2_val) in enumerate(zip(F1.ravel(), F2.ravel())):
            for f in self.factors:
                if f == factor1:
                    X_pred[i, factor_idx[f]] = f1_val
                elif f == factor2:
                    X_pred[i, factor_idx[f]] = f2_val
                else:
                    X_pred[i, factor_idx[f]] = fixed_values[f]
        
        poly = PolynomialFeatures(degree=2, include_bias=False)
        X_pred_poly = poly.fit_transform(X_pred)
        Z = self.model.predict(X_pred_poly).reshape(F1.shape)
        
        fig = plt.figure(figsize=figsize)
        
        ax1 = fig.add_subplot(121, projection='3d')
        surf = ax1.plot_surface(F1, F2, Z, cmap='viridis', alpha=0.8, edgecolor='none')
        ax1.set_xlabel(factor1)
        ax1.set_ylabel(factor2)
        ax1.set_zlabel('Response')
        ax1.set_title('Response Surface')
        fig.colorbar(surf, ax=ax1, shrink=0.5)
        
        ax2 = fig.add_subplot(122)
        contour = ax2.contourf(F1, F2, Z, levels=20, cmap='viridis')
        ax2.contour(F1, F2, Z, levels=10, colors='black', alpha=0.3, linewidths=0.5)
        ax2.set_xlabel(factor1)
        ax2.set_ylabel(factor2)
        ax2.set_title('Contour Plot')
        fig.colorbar(contour, ax=ax2)
        
        plt.tight_layout()
        return fig
    
    def get_summary_report(self) -> str:
        if not self.results:
            raise ValueError("Please fit the model first.")
        
        report = "="* 60 + "\n"
        report += "DOE Analysis Report\n"
        report += "=" * 60 + "\n\n"
        
        report += "Model Summary:\n"
        report += f"  R2: {self.results['r_squared']:.4f}\n"
        report += f"  Adj R2: {self.results['adj_r_squared']:.4f}\n"
        report += f"  RMSE: {self.results['rmse']:.4f}\n\n"
        
        report += "Regression Equation:\n"
        report += f"  {self.get_regression_equation()}\n\n"
        
        report += "ANOVA Table:\n"
        report += self.results['anova'].to_string(index=False) + "\n\n"
        
        report += "Factor Effects:\n"
        effects = self.analyze_effects()
        report += effects.to_string(index=False) + "\n\n"
        report += "=" * 60 + "\n"
        
        return report
