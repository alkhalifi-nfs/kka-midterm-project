"""Tes fungsi evaluasi H1/H2 dan skor terminal (src/agents/evaluation.py)."""
import random

import numpy as np
import pytest

from src.agents.evaluation import (
    H2_WEIGHTS, TERMINAL_WEIGHT, evaluate, h1, h2, h2_features, terminal_score,
)
from src.engine.api import CongklakState, apply_move, get_initial_state, get_legal_moves, is_terminal


def make_state(board, player=0, terminal=False):
    board = np.array(board, dtype=np.int32)
    assert board.sum() == 98
    return CongklakState(board=board, current_player=player, is_terminal=terminal)


# Posisi buatan tangan, fitur dihitung manual (sudut pandang Pemain 0):
#   f1 = 40 - 27 = 13
#   f2 = (7+5+1+2) - (4+2+3+6+1) = 15 - 16 = -1
#   f3 = P0 {lubang 0: 7 biji, lubang 2: 5 biji} - P1 {lubang 14: 1 biji} = 2 - 1 = 1
#   f4 = P0 kosong 1,4,5 -> seberang 13,10,9 = 6+2+0 = 8
#        P1 kosong 9,12 -> seberang 5,2 = 0+5 = 5          -> 8 - 5 = 3
#            0  1  2  3  4  5  6  S0  8  9 10 11 12 13 14  S1
HAND = [7, 0, 5, 1, 0, 0, 2, 40, 4, 0, 2, 3, 0, 6, 1, 27]


def random_positions(n=60, seed=7):
    rng = random.Random(seed)
    out = []
    while len(out) < n:
        state = get_initial_state()
        for _ in range(rng.randint(0, 40)):
            if is_terminal(state):
                break
            state = apply_move(state, rng.choice(get_legal_moves(state)))
        out.append(state)
    return out


def test_initial_position_is_balanced():
    s = get_initial_state()
    assert h1(s, 0) == 0
    assert h2_features(s, 0) == (0, 0, 0, 0)
    assert h2(s, 0) == 0.0


def test_hand_crafted_features():
    s = make_state(HAND)
    assert h1(s, 0) == 13
    assert h2_features(s, 0) == (13, -1, 1, 3)
    assert h2(s, 0) == pytest.approx(1.0 * 13 + 0.3 * -1 + 0.5 * 1 + 0.2 * 3)
    assert h2_features(s, 1) == (-13, 1, -1, -3)


def test_default_weights_match_report_table_1():
    assert H2_WEIGHTS == (1.0, 0.3, 0.5, 0.2)


def test_custom_weights():
    s = make_state(HAND)
    assert h2(s, 0, weights=(0, 0, 0, 1)) == 3.0
    with pytest.raises(ValueError, match="4 bobot"):
        h2(s, 0, weights=(1, 2, 3))


@pytest.mark.parametrize("heuristic", ["h1", "h2"])
def test_antisymmetric(heuristic):
    for s in random_positions():
        assert evaluate(s, 0, heuristic) == pytest.approx(-evaluate(s, 1, heuristic))


def test_terminal_score_after_sweep():
    board = [0] * 16
    board[7], board[15] = 50, 48
    s = make_state(board, terminal=True)
    assert evaluate(s, 0, "h1") == 2 * TERMINAL_WEIGHT
    assert evaluate(s, 1, "h2") == -2 * TERMINAL_WEIGHT


def test_terminal_score_counts_unswept_seeds():
    # Pemain 0 giliran tetapi sisinya kosong: terminal, 10 biji di sisi P1 milik P1.
    board = [0] * 16
    board[7], board[8], board[15] = 40, 10, 48
    s = make_state(board, player=0)
    assert is_terminal(s)
    assert terminal_score(s, 0) == (40 - 58) * TERMINAL_WEIGHT
    assert evaluate(s, 0, "h2") == (40 - 58) * TERMINAL_WEIGHT


def test_draw_is_zero():
    board = [0] * 16
    board[7] = board[15] = 49
    assert evaluate(make_state(board, terminal=True), 0) == 0


def test_bad_arguments():
    s = get_initial_state()
    with pytest.raises(ValueError, match="Heuristik"):
        evaluate(s, 0, "h3")
    with pytest.raises(ValueError, match="Pemain"):
        h1(s, 2)
