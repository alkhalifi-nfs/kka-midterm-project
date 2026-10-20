"""
Implementasi Agen Random, Greedy, Minimax, dan Alpha-Beta
untuk integrasi dan Smoke Testing di Engine Congklak-Master (T21).
"""

import random
import math
from typing import Tuple, Optional
from src.engine.api import (
    CongklakState, get_legal_moves, apply_move, is_terminal, get_scores,
    PLAYER_0
)
from src.agents.evaluation import evaluate
from src.agents.minimax import MinimaxAgent as _Minimax


def evaluate_state(state: CongklakState, perspective_player: int) -> int:
    """
    Heuristik H1 (Selisih Lumbung) dari sudut pandang `perspective_player`.
    """
    s0, s1 = get_scores(state)
    return (s0 - s1) if perspective_player == PLAYER_0 else (s1 - s0)


class RandomAgent:
    """Agen yang memilih langkah legal secara acak dengan seed terkontrol."""
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def select_move(self, state: CongklakState) -> int:
        moves = get_legal_moves(state)
        if not moves:
            raise ValueError("Tidak ada langkah legal pada state terminal.")
        return self.rng.choice(moves)


class GreedyAgent:
    """
    Agen Greedy 1-ply: Memprioritaskan langkah yang menghasilkan giliran tambahan,
    atau memaksimalkan selisih lumbung langsung dalam 1 langkah.
    """
    def select_move(self, state: CongklakState) -> int:
        moves = get_legal_moves(state)
        if not moves:
            raise ValueError("Tidak ada langkah legal pada state terminal.")

        player = state.current_player
        best_move = moves[0]
        best_score = -math.inf

        for move in moves:
            next_state = apply_move(state, move)
            score = evaluate_state(next_state, player)
            # Bonus prioritas jika mendapat giliran tambahan (extra-turn)
            if next_state.current_player == player and not next_state.is_terminal:
                score += 0.5
            if score > best_score:
                best_score = score
                best_move = move

        return best_move


class MinimaxAgent(_Minimax):
    """
    Model 1 dengan H1 dan antarmuka lama smoke test (select_move, nodes_expanded).
    Implementasinya ada di src/agents/minimax.py.
    """
    def __init__(self, max_depth: int = 3):
        super().__init__(depth=max_depth, heuristic="h1")
        self.max_depth = max_depth

    @property
    def nodes_expanded(self) -> int:
        return self.metrics.nodes

    def select_move(self, state: CongklakState) -> int:
        return self.choose_move(state)


class AlphaBetaAgent:
    """
    Model 2 Dasar: Alpha-Beta Pruning pada pohon Non-Alternating Turn.
    Menjamin keputusan identik dengan Minimax dengan jumlah node lebih sedikit.
    """
    def __init__(self, max_depth: int = 3):
        self.max_depth = max_depth
        self.nodes_expanded = 0
        self.cutoffs = 0

    def select_move(self, state: CongklakState) -> int:
        self.nodes_expanded = 0
        self.cutoffs = 0
        _, best_move = self._alphabeta(
            state, self.max_depth, -math.inf, math.inf, state.current_player
        )
        return best_move

    def _alphabeta(
        self,
        state: CongklakState,
        depth: int,
        alpha: float,
        beta: float,
        root_player: int
    ) -> Tuple[float, Optional[int]]:
        self.nodes_expanded += 1
        moves = get_legal_moves(state)

        if depth == 0 or is_terminal(state) or not moves:
            # Skor sama dengan Minimax (H1, terminal x1000) agar keputusan bisa dibandingkan.
            return evaluate(state, root_player, "h1"), None

        is_maximizing = (state.current_player == root_player)
        best_move = moves[0]

        if is_maximizing:
            max_eval = -math.inf
            for move in moves:
                next_state = apply_move(state, move)
                eval_val, _ = self._alphabeta(
                    next_state, depth - 1, alpha, beta, root_player
                )
                if eval_val > max_eval:
                    max_eval = eval_val
                    best_move = move
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    self.cutoffs += 1
                    break
            return max_eval, best_move
        else:
            min_eval = math.inf
            for move in moves:
                next_state = apply_move(state, move)
                eval_val, _ = self._alphabeta(
                    next_state, depth - 1, alpha, beta, root_player
                )
                if eval_val < min_eval:
                    min_eval = eval_val
                    best_move = move
                beta = min(beta, eval_val)
                if beta <= alpha:
                    self.cutoffs += 1
                    break
            return min_eval, best_move