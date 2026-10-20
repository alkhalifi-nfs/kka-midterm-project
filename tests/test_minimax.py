"""Tes Model 1 Minimax (src/agents/minimax.py)."""
import random

import numpy as np
import pytest

from src.agents.alphabeta import AlphaBetaAgent
from src.agents.evaluation import evaluate
from src.agents.minimax import MinimaxAgent, MinimaxH1Agent
from src.engine.api import (
    CongklakState, apply_move, get_initial_state, get_legal_moves, get_scores, is_terminal,
)


def random_positions(n, seed):
    rng = random.Random(seed)
    out = []
    while len(out) < n:
        state = get_initial_state()
        for _ in range(rng.randint(0, 50)):
            if is_terminal(state):
                break
            state = apply_move(state, rng.choice(get_legal_moves(state)))
        if not is_terminal(state):
            out.append(state)
    return out


def reference_value(state, depth, me, heuristic):
    """Minimax rujukan, ditulis langsung dari rumus V(s, d) Bab 2.2.2."""
    if depth == 0 or is_terminal(state):
        return evaluate(state, me, heuristic)
    values = [reference_value(apply_move(state, a), depth - 1, me, heuristic)
              for a in get_legal_moves(state)]
    return max(values) if state.current_player == me else min(values)


def reference_choice(state, depth, heuristic):
    me = state.current_player
    scored = [(reference_value(apply_move(state, a), depth - 1, me, heuristic), a)
              for a in get_legal_moves(state)]
    best = max(v for v, _ in scored)
    return best, next(a for v, a in scored if v == best)  # seri -> lubang pertama


@pytest.mark.parametrize("heuristic", ["h1", "h2"])
def test_matches_reference_formula(heuristic):
    agent = MinimaxAgent(heuristic=heuristic)
    extra_turns_seen = 0
    for i, state in enumerate(random_positions(25, seed=11)):
        depth = 1 + i % 3
        assert agent.search(state, depth) == reference_choice(state, depth, heuristic)
        extra_turns_seen += sum(apply_move(state, a).current_player == state.current_player
                                for a in get_legal_moves(state))
    assert extra_turns_seen > 0, "sampel harus memuat giliran tambahan (MAX -> MAX)"


def test_extra_turn_child_is_max_node():
    """Setelah giliran tambahan, simpul anak tetap milik agen sehingga diambil nilai terbesar."""
    for state in random_positions(40, seed=3):
        for a in get_legal_moves(state):
            child = apply_move(state, a)
            if child.current_player != state.current_player or is_terminal(child):
                continue
            me = state.current_player
            leaves = [evaluate(apply_move(child, b), me, "h2") for b in get_legal_moves(child)]
            if max(leaves) == min(leaves):
                continue  # tidak bisa membedakan MAX dari MIN
            agent = MinimaxAgent()
            agent._me, agent._nodes = me, 0
            assert agent._value(child, 1) == max(leaves)
            return
    pytest.fail("tidak menemukan posisi dengan giliran tambahan")


def test_depth_one_is_greedy_on_evaluation():
    for state in random_positions(15, seed=5):
        me = state.current_player
        moves = get_legal_moves(state)
        scores = [evaluate(apply_move(state, a), me, "h2") for a in moves]
        expected = moves[scores.index(max(scores))]
        assert MinimaxAgent(depth=1).choose_move(state) == expected


def test_same_decision_as_alphabeta_with_h1():
    for state in random_positions(15, seed=21):
        mm = MinimaxH1Agent(depth=3)
        ab = AlphaBetaAgent(depth=3, heuristic="h1", use_tt=False, iterative=False)
        assert mm.choose_move(state) == ab.choose_move(state)
        assert ab.metrics.nodes <= mm.metrics.nodes


def test_agent_contract_and_metrics():
    state = get_initial_state()
    board_before = state.board.copy()
    agent = MinimaxAgent(depth=2)
    agent.reset(123)
    move = agent.choose_move(state, time_limit=0.5)
    assert move in get_legal_moves(state)
    assert np.array_equal(state.board, board_before) and state.current_player == 0
    m = agent.metrics
    assert m.nodes > len(get_legal_moves(state)) and m.cutoffs == 0 and m.depth_reached == 2
    assert m.elapsed >= 0
    nodes_d2 = m.nodes

    agent.choose_move(state, depth=3)  # depth dari runner menimpa default
    assert agent.metrics.depth_reached == 3 and agent.metrics.nodes > nodes_d2

    assert agent.name == "minimax" and MinimaxH1Agent().name == "minimax_h1"


def test_plays_full_game_against_itself():
    state = get_initial_state()
    agents = (MinimaxAgent(depth=2), MinimaxH1Agent(depth=2))
    while not is_terminal(state):
        state = apply_move(state, agents[state.current_player].choose_move(state))
    assert sum(get_scores(state)) == 98


def test_bad_arguments():
    with pytest.raises(ValueError, match="Kedalaman"):
        MinimaxAgent(depth=0)
    with pytest.raises(ValueError, match="Heuristik"):
        MinimaxAgent(heuristic="h3")
    board = np.zeros(16, dtype=np.int32)
    board[7], board[8], board[15] = 40, 10, 48
    with pytest.raises(ValueError, match="legal"):
        MinimaxAgent().choose_move(CongklakState(board=board, current_player=0))
