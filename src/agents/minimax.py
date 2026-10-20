"""
Model 1: Depth-Limited Minimax untuk congklak (laporan Bab 2.2).

Peran MAX/MIN ditentukan oleh PLAYER(s), bukan oleh paritas kedalaman, karena
giliran tambahan membuat pemain yang sama bisa jalan lagi (MAX -> MAX,
MIN -> MIN). Setiap langkah, termasuk yang menghasilkan giliran tambahan,
mengurangi sisa kedalaman sebanyak satu ply.

Pemutus seri: langkah dicoba dalam urutan indeks lubang menaik dan pembaruan
memakai pembanding ketat, sehingga di antara langkah bernilai sama dipilih
yang pertama (Pseudocode PILIH_LANGKAH). Alpha-Beta harus memakai aturan yang
sama agar uji kesamaan keputusan (Bab 3.2) bermakna.

Agen memenuhi kontrak agen turnamen (experiments/__init__.py).
"""

import math
import time
from dataclasses import dataclass
from typing import Optional, Tuple

from src.agents.evaluation import HEURISTICS, evaluate
from src.engine.api import CongklakState, apply_move, get_legal_moves, is_terminal

DEFAULT_DEPTH = 4
MAX_ID_DEPTH = 64          # batas kedalaman bila hanya dibatasi waktu
TIME_CHECK_EVERY = 256     # periksa jam setiap sekian simpul


class _Timeout(Exception):
    pass


@dataclass
class SearchStats:
    """Metrik pemanggilan choose_move terakhir (nama atribut mengikuti kontrak agen)."""
    nodes: int = 0          # jumlah state yang dikunjungi, termasuk akar dan daun
    cutoffs: int = 0        # Minimax tidak memangkas, selalu 0
    depth_reached: int = 0
    elapsed: float = 0.0    # detik


class MinimaxAgent:
    """
    Minimax berkedalaman terbatas. `heuristic` adalah "h1" atau "h2".

    Tanpa time_limit: satu pencarian pada kedalaman `depth` (Bab 2.2).
    Dengan time_limit (untuk RQ3, perbandingan pada batas waktu yang sama):
    kedalaman 1, 2, ... diulang hingga waktu habis, tanpa ordering maupun TT;
    iterasi yang terpotong dibuang dan kedalaman 1 selalu diselesaikan;
    berhenti lebih awal bila pohon sudah habis sampai akhir permainan.
    depth <= 0 bersama time_limit berarti hanya dibatasi waktu.
    """

    def __init__(self, depth: int = DEFAULT_DEPTH, heuristic: str = "h2"):
        if depth < 1:
            raise ValueError(f"Kedalaman minimal 1, bukan {depth}.")
        if heuristic not in HEURISTICS:
            raise ValueError(f"Heuristik tidak dikenal: {heuristic!r} (pilihan: {', '.join(HEURISTICS)}).")
        self.depth = depth
        self.heuristic = heuristic
        self.name = "minimax" if heuristic == "h2" else f"minimax_{heuristic}"  # = nama di registry
        self.metrics = SearchStats()
        self._me = 0
        self._nodes = 0
        self._deadline: Optional[float] = None
        self._hit_horizon = False

    def reset(self, seed=None) -> None:
        """Agen deterministik; seed diabaikan."""
        self.metrics = SearchStats()

    def choose_move(self, state: CongklakState, time_limit=None, depth=None) -> int:
        """Langkah terbaik pada kedalaman `depth` (default: self.depth), lihat docstring kelas."""
        started = time.perf_counter()
        max_depth = self.depth if depth is None else int(depth)
        if not time_limit:
            _, move = self.search(state, max_depth)
            self.metrics.elapsed = time.perf_counter() - started
            return move

        if max_depth <= 0:
            max_depth = MAX_ID_DEPTH
        move, completed, nodes = None, 0, 0
        for d in range(1, max_depth + 1):
            self._deadline = started + time_limit if d > 1 else None
            try:
                _, move = self.search(state, d)
            except _Timeout:
                nodes += self._nodes
                break
            finally:
                self._deadline = None
            completed = d
            nodes += self.metrics.nodes
            if not self._hit_horizon:
                break  # seluruh pohon sampai akhir permainan sudah ditelusuri
            if time.perf_counter() >= started + time_limit:
                break
        self.metrics = SearchStats(nodes=nodes, cutoffs=0, depth_reached=completed,
                                   elapsed=time.perf_counter() - started)
        return move

    def search(self, state: CongklakState, depth: int) -> Tuple[float, int]:
        """
        (nilai akar, langkah terbaik) dari sudut pandang pemain yang sedang jalan.
        Mengisi self.metrics kecuali `elapsed`.
        """
        if depth < 1:
            raise ValueError(f"Kedalaman minimal 1, bukan {depth}.")
        moves = get_legal_moves(state)
        if not moves:
            raise ValueError("Tidak ada langkah legal pada state ini.")

        self._me = state.current_player
        self._nodes = 1  # akar
        self._hit_horizon = False
        best_v, best_a = -math.inf, moves[0]
        for a in moves:
            v = self._value(apply_move(state, a), depth - 1)
            if v > best_v:
                best_v, best_a = v, a

        self.metrics = SearchStats(nodes=self._nodes, cutoffs=0, depth_reached=depth)
        return best_v, best_a

    def _value(self, state: CongklakState, depth: int) -> float:
        """NILAI(s, d) pada Pseudocode NILAI."""
        self._nodes += 1
        if (self._deadline is not None and self._nodes % TIME_CHECK_EVERY == 0
                and time.perf_counter() >= self._deadline):
            raise _Timeout
        if is_terminal(state):
            return evaluate(state, self._me, self.heuristic)
        if depth == 0:
            self._hit_horizon = True
            return evaluate(state, self._me, self.heuristic)

        children = (self._value(apply_move(state, a), depth - 1) for a in get_legal_moves(state))
        return max(children) if state.current_player == self._me else min(children)


class MinimaxH1Agent(MinimaxAgent):
    """Minimax dengan H1, untuk perbandingan H1 vs H2 di turnamen."""

    def __init__(self, depth: int = DEFAULT_DEPTH):
        super().__init__(depth=depth, heuristic="h1")
