"""
Smoke Test Integrasi Agen (Random, Greedy, Minimax, Alpha-Beta) pada Core Engine (T21).
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import numpy as np
from src.engine.api import (
    get_initial_state, get_legal_moves, apply_move, is_terminal, get_scores, PLAYER_0
)
from src.agents.baseline_and_search import (
    RandomAgent, GreedyAgent, MinimaxAgent, AlphaBetaAgent
)


def play_full_game(agent_p0, agent_p1, max_turns: int = 400):
    """Menjalankan simulasi penuh 1 pertandingan antara 2 agen."""
    state = get_initial_state()
    turns = 0

    while not is_terminal(state) and turns < max_turns:
        # Invariant check: jumlah total biji harus selalu 98
        assert int(np.sum(state.board)) == 98, f"Biji berubah di turn {turns}: {state.board}"

        legal = get_legal_moves(state)
        assert len(legal) > 0, "State belum terminal tetapi tidak ada langkah legal."

        active_agent = agent_p0 if state.current_player == PLAYER_0 else agent_p1
        move = active_agent.select_move(state)

        assert move in legal, f"Agen memilih langkah ilegal: {move} (legal: {legal})"
        state = apply_move(state, move)
        turns += 1

    assert is_terminal(state), "Permainan melebihi batas langkah maksimum (infinite loop)."
    s0, s1 = get_scores(state)
    assert s0 + s1 == 98, f"Skor akhir tidak berjumlah 98: {s0} + {s1}"
    return s0, s1, turns


def test_smoke_01_random_vs_random():
    """Uji tanding Random vs Random hingga selesai."""
    s0, s1, turns = play_full_game(RandomAgent(seed=1), RandomAgent(seed=2))
    assert turns > 0 and (s0 + s1 == 98)


def test_smoke_02_greedy_vs_random():
    """Uji tanding Greedy vs Random hingga selesai."""
    s0, s1, _ = play_full_game(GreedyAgent(), RandomAgent(seed=42))
    assert s0 + s1 == 98


def test_smoke_03_minimax_vs_greedy():
    """Uji tanding Minimax (depth 3) vs Greedy hingga selesai."""
    s0, s1, _ = play_full_game(MinimaxAgent(max_depth=3), GreedyAgent())
    assert s0 + s1 == 98


def test_smoke_04_alphabeta_vs_minimax():
    """Uji tanding Alpha-Beta (depth 3) vs Minimax (depth 3) hingga selesai."""
    s0, s1, _ = play_full_game(AlphaBetaAgent(max_depth=3), MinimaxAgent(max_depth=3))
    assert s0 + s1 == 98


def test_smoke_05_minimax_alphabeta_decision_equivalence():
    """
    Sanity Check Kritis: Keputusan Minimax dan Alpha-Beta pada depth yang sama
    harus 100% identik, dan Alpha-Beta harus memeriksa node <= Minimax.
    """
    state = get_initial_state()
    rng = RandomAgent(seed=99)

    # Uji pada 10 state berurutan termasuk saat terjadi extra-turn
    for _ in range(10):
        if is_terminal(state):
            break
        mm = MinimaxAgent(max_depth=4)
        ab = AlphaBetaAgent(max_depth=4)

        move_mm = mm.select_move(state)
        move_ab = ab.select_move(state)

        assert move_mm == move_ab, f"Keputusan berbeda! Minimax={move_mm}, AlphaBeta={move_ab}"
        assert ab.nodes_expanded <= mm.nodes_expanded
        assert ab.cutoffs > 0

        state = apply_move(state, rng.select_move(state))


def test_smoke_06_state_immutability_during_search():
    """Memastikan pencarian pohon Minimax/Alpha-Beta tidak merusak array state asli."""
    state = get_initial_state()
    board_before = state.board.copy()
    player_before = state.current_player

    ab = AlphaBetaAgent(max_depth=4)
    _ = ab.select_move(state)

    assert np.array_equal(state.board, board_before), "State papan berubah akibat efek samping pencarian!"
    assert state.current_player == player_before


if __name__ == "__main__":
    pytest.main(["-v", __file__])