"""
Bayesian Optimization for Sequential DOE.
"""

import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern
from scipy.stats import norm


class BayesianSuggester:
    """Bayesian Optimization Suggester - for Sequential DOE."""
    
    def __init__(self, factors: List[Dict[str, Any]], objective: str = 'maximize', is_mixture: bool = False):
        self.factors = factors
        self.objective = objective
        self.is_mixture = is_mixture
        self.factor_names = [f['name'] for f in factors]
        self.bounds = np.array([[f['min'], f['max']] for f in factors])
        
        kernel = Matern(nu=2.5)
        self.model = GaussianProcessRegressor(
            kernel=kernel, 
            alpha=1e-6, 
            normalize_y=True, 
            n_restarts_optimizer=5,
            random_state=42
        )

    def suggest(self, X_obs: np.ndarray, y_obs: np.ndarray, n_candidates: int = 1000) -> Dict[str, Any]:
        """Suggests the next optimal experiment point based on Expected Improvement (EI)."""
        if len(y_obs) == 0:
            suggested = (self.bounds[:, 0] + self.bounds[:, 1]) / 2
            return {
                'suggestion': dict(zip(self.factor_names, suggested.tolist())),
                'expected_improvement': 0.0,
                'is_random': True
            }

        y_train = y_obs
        if self.objective == 'minimize':
            y_train = -y_obs

        self.model.fit(X_obs, y_train)
        
        if self.is_mixture:
            alpha = np.ones(len(self.factors))
            X_candidates = np.random.dirichlet(alpha, size=n_candidates)
        else:
            X_candidates = np.random.uniform(
                self.bounds[:, 0], 
                self.bounds[:, 1], 
                size=(n_candidates, len(self.factors))
            )
        
        mu, sigma = self.model.predict(X_candidates, return_std=True)
        mu_best = np.max(y_train)
        
        with np.errstate(divide='warn'):
            imp = mu - mu_best
            Z = imp / sigma
            ei = imp * norm.cdf(Z) + sigma * norm.pdf(Z)
            ei[sigma == 0.0] = 0.0
            
        best_idx = np.argmax(ei)
        suggested = X_candidates[best_idx]
        
        return {
            'suggestion': dict(zip(self.factor_names, suggested.tolist())),
            'expected_improvement': float(ei[best_idx]),
            'is_random': False
        }


class ParEGOSuggester:
    """ParEGO Multi-Objective Bayesian Optimization Suggester."""

    def __init__(
        self,
        factors: List[Dict[str, Any]],
        responses: List[Dict[str, Any]],
        rho: float = 0.05,
        is_mixture: bool = False,
        random_state: Optional[int] = None,
    ):
        if not responses or len(responses) < 2:
            raise ValueError("ParEGO requires at least 2 target responses.")
        self.factors = factors
        self.responses = responses
        self.rho = float(rho)
        self.is_mixture = bool(is_mixture)
        self._rng = np.random.default_rng(random_state)
        self._inner = BayesianSuggester(
            factors=factors, objective="minimize", is_mixture=is_mixture
        )

    @staticmethod
    def _normalize_for_minimize(
        Y: np.ndarray, directions: List[str]
    ) -> np.ndarray:
        Y_dir = Y.copy().astype(float)
        for j, d in enumerate(directions):
            if d == "maximize":
                Y_dir[:, j] = -Y_dir[:, j]
        Y_min = np.nanmin(Y_dir, axis=0)
        Y_max = np.nanmax(Y_dir, axis=0)
        span = np.where(Y_max - Y_min == 0.0, 1.0, Y_max - Y_min)
        return (Y_dir - Y_min) / span

    def _scalarize(
        self, Y_norm: np.ndarray, weights: np.ndarray
    ) -> np.ndarray:
        z_star = np.min(Y_norm, axis=0)
        diff = Y_norm - z_star
        weighted = diff * weights[np.newaxis, :]
        return weighted.max(axis=1) + self.rho * weighted.sum(axis=1)

    def suggest(
        self,
        X_obs: np.ndarray,
        Y_obs: np.ndarray,
        n_candidates: int = 1000,
        weights: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        Y_obs = np.asarray(Y_obs, dtype=float)
        if Y_obs.ndim != 2 or Y_obs.shape[1] != len(self.responses):
            raise ValueError(f"Y_obs shape mismatch.")
        if Y_obs.shape[0] == 0:
            raise ValueError("Y_obs cannot be empty.")

        directions = [r.get("direction", "maximize") for r in self.responses]
        Y_norm = self._normalize_for_minimize(Y_obs, directions)

        if weights is None:
            weights = self._rng.dirichlet(np.ones(len(self.responses)))
        else:
            weights = np.asarray(weights, dtype=float)
            if weights.shape != (len(self.responses),):
                raise ValueError("Weights shape mismatch.")
            s = float(weights.sum())
            if s <= 0:
                raise ValueError("Weights sum must be > 0.")
            weights = weights / s

        scalar_y = self._scalarize(Y_norm, weights)
        inner_result = self._inner.suggest(
            X_obs, scalar_y, n_candidates=n_candidates
        )
        inner_result["multi_objective"] = {
            "method": "ParEGO_Tchebycheff",
            "responses": [r["name"] for r in self.responses],
            "directions": directions,
            "weights": weights.tolist(),
            "rho": self.rho,
        }
        inner_result["scalarized_min"] = float(np.min(scalar_y))
        return inner_result
