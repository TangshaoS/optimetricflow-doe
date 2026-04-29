"""
Experiment Design (DOE) Matrix Generation Module.
"""

import numpy as np
import pandas as pd
from typing import List, Optional
from itertools import product


class DOEDesigner:
    """Experiment Designer - generates various DOE matrices."""
    
    def __init__(self):
        self.design_matrix = None
        self.factors = []
        self.levels = []
        self.design_type = None
        
    def full_factorial(self, 
                       factors: List[str],
                       levels: List[List[float]],
                       center_points: int = 0,
                       replicates: int = 1,
                       randomize: bool = True) -> pd.DataFrame:
        """Full Factorial Design."""
        self.factors = factors
        self.levels = levels
        self.design_type = 'full_factorial'
        
        design_points = list(product(*levels))
        design = pd.DataFrame(design_points, columns=factors)
        
        if replicates > 1:
            design = pd.concat([design] * replicates, ignore_index=True)
        
        if center_points > 0:
            center = pd.DataFrame([[(max(lvl) + min(lvl)) / 2 for lvl in levels]] * center_points,
                                 columns=factors)
            design = pd.concat([design, center], ignore_index=True)
        
        design.insert(0, 'StdOrder', range(1, len(design) + 1))
        if randomize:
            design = design.sample(frac=1).reset_index(drop=True)
        
        design.insert(1, 'RunOrder', range(1, len(design) + 1))
        design['Response'] = np.nan
        
        self.design_matrix = design
        return design
    
    def fractional_factorial(self,
                            factors: List[str],
                            levels: List[List[float]],
                            resolution: int = 4,
                            center_points: int = 0,
                            randomize: bool = True) -> pd.DataFrame:
        """Fractional Factorial Design."""
        n_factors = len(factors)
        
        if resolution == 3:
            runs = 2 ** (n_factors - 2)
        elif resolution == 4:
            runs = 2 ** (n_factors - 1)
        else:
            runs = 2 ** n_factors // 2
        
        k_base = int(np.log2(runs))
        coded_base_points = list(product([-1, 1], repeat=k_base))
        base_design = pd.DataFrame(coded_base_points, columns=factors[:k_base])
        
        for i in range(k_base, n_factors):
            if i == k_base: 
                base_design[factors[i]] = base_design[factors[0]]
                for j in range(1, k_base):
                    base_design[factors[i]] *= base_design[factors[j]]
            else: 
                idx1 = (i - k_base) % k_base
                idx2 = (i - k_base + 1) % k_base
                base_design[factors[i]] = base_design[factors[idx1]] * base_design[factors[idx2]]
        
        if center_points > 0:
            center = pd.DataFrame([[0.0] * n_factors] * center_points, columns=factors)
            base_design = pd.concat([base_design, center], ignore_index=True)
            
        for i, name in enumerate(factors):
            low, high = min(levels[i]), max(levels[i])
            base_design[name] = base_design[name].apply(lambda x: ((x + 1) / 2) * (high - low) + low)
        
        base_design.insert(0, 'StdOrder', range(1, len(base_design) + 1))
        if randomize:
            base_design = base_design.sample(frac=1).reset_index(drop=True)
        
        base_design.insert(1, 'RunOrder', range(1, len(base_design) + 1))
        base_design['Response'] = np.nan
        
        self.design_matrix = base_design
        self.design_type = 'fractional_factorial'
        return base_design
    
    def central_composite(self,
                         factors: List[str],
                         levels: List[List[float]],
                         alpha: str = 'orthogonal',
                         center_points: int = 6,
                         randomize: bool = True) -> pd.DataFrame:
        """Central Composite Design (CCD)."""
        n_factors = len(factors)
        cube_points = list(product([-1, 1], repeat=n_factors))
        
        if alpha == 'orthogonal':
            alpha_val = np.sqrt(n_factors)
        elif alpha == 'rotatable':
            alpha_val = (2 ** n_factors) ** 0.25
        else:
            alpha_val = 1.0
        
        axial_points = []
        for i in range(n_factors):
            point_plus = [0] * n_factors
            point_minus = [0] * n_factors
            point_plus[i] = alpha_val
            point_minus[i] = -alpha_val
            axial_points.extend([point_plus, point_minus])
        
        center = [[0] * n_factors] * center_points
        all_points = cube_points + axial_points + center
        
        design = pd.DataFrame(all_points, columns=factors)
        design.insert(0, 'StdOrder', range(1, len(design) + 1))
            
        if randomize:
            design = design.sample(frac=1).reset_index(drop=True)
            
        for i, name in enumerate(factors):
            low, high = min(levels[i]), max(levels[i])
            design[name] = design[name].apply(lambda x: ((x + 1) / 2) * (high - low) + low)
        
        design.insert(1, 'RunOrder', range(1, len(design) + 1))
        design['Response'] = np.nan
        
        self.design_matrix = design
        self.design_type = 'central_composite'
        return design
    
    def box_behnken(self,
                   factors: List[str],
                   levels: List[List[float]],
                   center_points: int = 3,
                   randomize: bool = True) -> pd.DataFrame:
        """Box-Behnken Design."""
        n_factors = len(factors)
        if n_factors < 3:
            raise ValueError("Box-Behnken design requires at least 3 factors.")
        
        design_points = []
        for i in range(n_factors):
            for j in range(i + 1, n_factors):
                for combo in product([-1, 1], repeat=2):
                    point = [0] * n_factors
                    point[i] = combo[0]
                    point[j] = combo[1]
                    design_points.append(point)
        
        center = [[0] * n_factors] * center_points
        design_points.extend(center)
        
        design = pd.DataFrame(design_points, columns=factors)
        design.insert(0, 'StdOrder', range(1, len(design) + 1))
            
        if randomize:
            design = design.sample(frac=1).reset_index(drop=True)
            
        for i, name in enumerate(factors):
            low, high = min(levels[i]), max(levels[i])
            design[name] = design[name].apply(lambda x: ((x + 1) / 2) * (high - low) + low)
            
        design.insert(1, 'RunOrder', range(1, len(design) + 1))
        design['Response'] = np.nan
        
        self.design_matrix = design
        self.design_type = 'box_behnken'
        return design

    def mixture_simplex_lattice(self,
                                components: List[str],
                                degree: int = 2,
                                randomize: bool = True) -> pd.DataFrame:
        """Simplex Lattice Design."""
        n = len(components)
        
        def generate_lattice(n, m):
            if n == 1:
                return [[m]]
            points = []
            for i in range(m + 1):
                for rest in generate_lattice(n - 1, m - i):
                    points.append([i] + rest)
            return points

        points = np.array(generate_lattice(n, degree)) / degree
        design = pd.DataFrame(points, columns=components)
        
        design.insert(0, 'StdOrder', range(1, len(design) + 1))
        if randomize:
            design = design.sample(frac=1).reset_index(drop=True)
        design.insert(1, 'RunOrder', range(1, len(design) + 1))
        design['Response'] = np.nan
        
        self.design_type = 'mixture_simplex_lattice'
        return design

    def mixture_simplex_centroid(self,
                                components: List[str],
                                randomize: bool = True) -> pd.DataFrame:
        """Simplex Centroid Design."""
        n = len(components)
        points = []
        
        from itertools import combinations
        for k in range(1, n + 1):
            for combo in combinations(range(n), k):
                point = [0.0] * n
                for idx in combo:
                    point[idx] = 1.0 / k
                points.append(point)
        
        design = pd.DataFrame(points, columns=components)
        design.insert(0, 'StdOrder', range(1, len(design) + 1))
        if randomize:
            design = design.sample(frac=1).reset_index(drop=True)
        design.insert(1, 'RunOrder', range(1, len(design) + 1))
        design['Response'] = np.nan
        
        self.design_type = 'mixture_simplex_centroid'
        return design

    _PB_GENERATORS = {
        12: '++-+++---+-',
        20: '++--++++-+-+----++-',
        24: '+++++-+-++--++--+-+----',
    }

    @staticmethod
    def _pb_matrix(n_runs: int) -> np.ndarray:
        if n_runs in (8, 16, 32):
            from scipy.linalg import hadamard
            H = hadamard(n_runs)
            return H[:, 1:].astype(int)

        gen_str = DOEDesigner._PB_GENERATORS.get(n_runs)
        if gen_str is None:
            raise ValueError(f"Unsupported Plackett-Burman runs: {n_runs}")

        first_row = np.array([1 if c == '+' else -1 for c in gen_str], dtype=int)
        rows = []
        for i in range(n_runs - 1):
            rows.append(np.roll(first_row, i))
        rows.append(-np.ones(n_runs - 1, dtype=int))
        return np.array(rows)

    def plackett_burman(self,
                        factors: List[str],
                        levels: List[List[float]],
                        runs: Optional[int] = None,
                        center_points: int = 0,
                        randomize: bool = True) -> pd.DataFrame:
        """Plackett-Burman Design."""
        n_factors = len(factors)
        if n_factors < 2:
            raise ValueError("Plackett-Burman requires at least 2 factors.")

        if runs is None:
            for r in (8, 12, 16, 20, 24):
                if r >= n_factors + 1:
                    runs = r
                    break
            if runs is None:
                raise ValueError("Plackett-Burman supports up to 23 factors.")

        H = DOEDesigner._pb_matrix(runs)
        if H.shape[1] < n_factors:
            raise ValueError(f"PB-{runs} supports up to {H.shape[1]} factors, got {n_factors}")
        coded = H[:, :n_factors]

        design = pd.DataFrame(coded, columns=factors)

        if center_points > 0:
            center = pd.DataFrame([[0.0] * n_factors] * center_points, columns=factors)
            design = pd.concat([design, center], ignore_index=True)

        design.insert(0, 'StdOrder', range(1, len(design) + 1))
        if randomize:
            design = design.sample(frac=1).reset_index(drop=True)

        for i, name in enumerate(factors):
            low, high = float(min(levels[i])), float(max(levels[i]))
            mid = (low + high) / 2.0
            design[name] = design[name].astype(float).apply(
                lambda x, lo=low, hi=high, m=mid: lo if x == -1 else (hi if x == 1 else m)
            )

        design.insert(1, 'RunOrder', range(1, len(design) + 1))
        design['Response'] = np.nan

        self.design_matrix = design
        self.design_type = 'plackett_burman'
        return design

    def definitive_screening(self,
                             factors: List[str],
                             levels: List[List[float]],
                             randomize: bool = True) -> pd.DataFrame:
        """Definitive Screening Design (DSD)."""
        m = len(factors)
        if m < 4:
            raise ValueError("DSD requires at least 4 factors.")
            
        C = np.zeros((m, m), dtype=float)
        for i in range(m):
            for j in range(m):
                if i < j:
                    C[i, j] = 1.0
                elif i > j:
                    C[i, j] = -1.0

        coded = np.vstack([C, -C, np.zeros((1, m))])
        design = pd.DataFrame(coded, columns=factors)
        design.insert(0, 'StdOrder', range(1, len(design) + 1))

        if randomize:
            design = design.sample(frac=1).reset_index(drop=True)

        for i, name in enumerate(factors):
            low, high = float(min(levels[i])), float(max(levels[i]))
            mid = (low + high) / 2.0
            design[name] = design[name].astype(float).apply(
                lambda x, lo=low, hi=high, m=mid: lo if x < -0.5 else (hi if x > 0.5 else m)
            )

        design.insert(1, 'RunOrder', range(1, len(design) + 1))
        design['Response'] = np.nan

        self.design_matrix = design
        self.design_type = 'definitive_screening'
        return design

    def mixture_process_crossed(self,
                                mixture_components: List[str],
                                process_factors: List[str],
                                process_levels: List[List[float]],
                                mixture_design: str = 'simplex_centroid',
                                mixture_degree: int = 2,
                                process_design: str = 'full_factorial',
                                randomize: bool = True) -> pd.DataFrame:
        """Mixture-Process Crossed Design."""
        if not mixture_components or not process_factors:
            raise ValueError("Mixture components and process factors cannot be empty.")

        if mixture_design == 'simplex_lattice':
            mix_df = self.mixture_simplex_lattice(mixture_components, degree=mixture_degree, randomize=False)
        elif mixture_design == 'simplex_centroid':
            mix_df = self.mixture_simplex_centroid(mixture_components, randomize=False)
        else:
            raise ValueError(f"Unsupported mixture design: {mixture_design}")
            
        mix_df = mix_df.drop(columns=['StdOrder', 'RunOrder', 'Response'], errors='ignore').reset_index(drop=True)

        if process_design == 'full_factorial':
            proc_df = self.full_factorial(process_factors, process_levels, randomize=False)
        elif process_design == 'box_behnken':
            proc_df = self.box_behnken(process_factors, process_levels, randomize=False)
        elif process_design == 'central_composite':
            proc_df = self.central_composite(process_factors, process_levels, randomize=False)
        else:
            raise ValueError(f"Unsupported process design: {process_design}")
            
        proc_df = proc_df.drop(columns=['StdOrder', 'RunOrder', 'Response'], errors='ignore').reset_index(drop=True)

        rows = []
        for _, m_row in mix_df.iterrows():
            for _, p_row in proc_df.iterrows():
                row = {**m_row.to_dict(), **p_row.to_dict()}
                rows.append(row)

        crossed = pd.DataFrame(rows)
        crossed.insert(0, 'StdOrder', range(1, len(crossed) + 1))
        if randomize:
            crossed = crossed.sample(frac=1).reset_index(drop=True)
        crossed.insert(1, 'RunOrder', range(1, len(crossed) + 1))
        crossed['Response'] = np.nan

        self.design_matrix = crossed
        self.design_type = 'mixture_process_crossed'
        return crossed

    def mixture_constrained(self,
                             components: List[str],
                             lower_bounds: List[float],
                             upper_bounds: List[float],
                             randomize: bool = True,
                             include_centroid: bool = True) -> pd.DataFrame:
        """Mixture Constrained Design."""
        n = len(components)
        if len(lower_bounds) != n or len(upper_bounds) != n:
            raise ValueError("lower/upper lengths must match number of components")
            
        L = np.array(lower_bounds, dtype=float)
        U = np.array(upper_bounds, dtype=float)
        if np.any(L < 0) or np.any(U > 1) or np.any(L > U):
            raise ValueError("Invalid constraints: 0 <= lower <= upper <= 1")
        if L.sum() > 1.0 + 1e-9 or U.sum() < 1.0 - 1e-9:
            raise ValueError("Infeasible constraints")

        vertices_set = set()
        for i in range(n):
            others = [j for j in range(n) if j != i]
            for mask in range(2 ** (n - 1)):
                pt = np.zeros(n)
                for k, j in enumerate(others):
                    pt[j] = U[j] if (mask >> k) & 1 else L[j]
                pt[i] = 1.0 - pt[others].sum()
                if L[i] - 1e-9 <= pt[i] <= U[i] + 1e-9:
                    vertices_set.add(tuple(np.round(pt, 6)))

        if not vertices_set:
            raise ValueError("No feasible vertices found.")

        vertices = [np.array(v) for v in vertices_set]
        design = pd.DataFrame(vertices, columns=components)

        if include_centroid:
            mid = (L + U) / 2.0
            mid = mid / mid.sum() if mid.sum() > 0 else mid
            design = pd.concat([design, pd.DataFrame([mid], columns=components)], ignore_index=True)

        design.insert(0, 'StdOrder', range(1, len(design) + 1))
        if randomize:
            design = design.sample(frac=1).reset_index(drop=True)
        design.insert(1, 'RunOrder', range(1, len(design) + 1))
        design['Response'] = np.nan

        self.design_matrix = design
        self.design_type = 'mixture_constrained'
        return design
