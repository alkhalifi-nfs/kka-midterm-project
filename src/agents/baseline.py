"""
Agen pembanding dasar: Random dan Greedy.

Keduanya tidak melakukan pencarian dan dipakai sebagai batas bawah kekuatan di
turnamen. Agen di sini mengikuti kontrak agen (lihat experiments/__init__.py).
"""

import random
import time
from dataclasses import dataclass

from src.engine.api import apply_move, get_legal_moves, get_score_diff


@dataclass
class MoveMetrics:
    """Metrik pemanggilan choose_move terakhir (nama atribut mengikuti kontrak agen)."""
    nodes: int = 0
    cutoffs: int = 0
    depth_reached: int = 0
    elapsed: float = 0.0


class RandomAgent:
    """Memilih langkah legal secara acak seragam. Tidak punya metrics (kasus 'tanpa metrik')."""
    name = "random"

    def __init__(self, seed: int = 0):
        self._rng = random.Random(seed)

    def reset(self, seed=None) -> None:
        self._rng = random.Random(seed)

    def choose_move(self, state, time_limit=None, depth=None) -> int:
        moves = get_legal_moves(state)
        if not moves:
            raise ValueError("Tidak ada langkah legal pada state ini.")
        return self._rng.choice(moves)


class GreedyAgent:
    """
    Greedy 1-ply: pilih langkah dengan get_score_diff terbesar (dari sudut pandang
    pemain yang melangkah) setelah satu langkah. Seri dipecah deterministik dengan
    lubang berindeks terkecil. Deterministik, tidak memakai time_limit maupun depth.
    """
    name = "greedy"

    def __init__(self):
        self.metrics = MoveMetrics()

    def reset(self, seed=None) -> None:
        self.metrics = MoveMetrics()

    def choose_move(self, state, time_limit=None, depth=None) -> int:
        start = time.perf_counter()
        moves = get_legal_moves(state)  # urut menaik, sehingga seri jatuh ke indeks terkecil
        if not moves:
            raise ValueError("Tidak ada langkah legal pada state ini.")

        player = state.current_player
        best_move, best_diff = None, None
        for move in moves:
            diff = get_score_diff(apply_move(state, move), player)
            if best_diff is None or diff > best_diff:
                best_move, best_diff = move, diff

        # node = jumlah posisi yang dibangkitkan (satu per langkah legal), kedalaman 1
        self.metrics = MoveMetrics(
            nodes=len(moves), cutoffs=0, depth_reached=1,
            elapsed=time.perf_counter() - start,
        )
        return best_move
