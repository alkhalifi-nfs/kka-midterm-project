"""
Model 3: Alpha-Beta (Model 2) dengan fungsi evaluasi 6 fitur berbobot hasil
Algoritma Genetika (laporan Bab 2.4).

Bobot dibaca dari results/ga_weights.json yang ditulis experiments/ga_train.py.
Bila berkas belum ada, agen gagal dibuat dan turnamen melewatinya dengan peringatan.
"""

import json
import os
from typing import Optional, Sequence

from src.agents.alphabeta import DEFAULT_DEPTH, AlphaBetaAgent
from src.agents.evaluation import GA_FEATURES, weighted_evaluator

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_WEIGHTS = os.path.join(REPO_ROOT, "results", "ga_weights.json")


def load_weights(path: str = DEFAULT_WEIGHTS) -> list:
    """Bobot terbaik dari berkas hasil training (kunci "weights")."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Bobot GA belum ada: {path}. Jalankan python -m experiments.ga_train dulu.")
    with open(path, "r", encoding="utf-8") as handle:
        weights = json.load(handle)["weights"]
    if len(weights) != len(GA_FEATURES):
        raise ValueError(f"{path}: butuh {len(GA_FEATURES)} bobot, bukan {len(weights)}.")
    return [float(w) for w in weights]


class GAAgent(AlphaBetaAgent):
    """Model 2 lengkap (ordering, TT, iterative deepening) dengan evaluator bobot GA."""

    def __init__(self, depth: int = DEFAULT_DEPTH, weights: Optional[Sequence[float]] = None,
                 weights_path: str = DEFAULT_WEIGHTS, name: str = "ga", **kwargs):
        self.weights = list(weights) if weights is not None else load_weights(weights_path)
        super().__init__(depth=depth, heuristic=weighted_evaluator(self.weights), name=name, **kwargs)
