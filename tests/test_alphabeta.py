"""Tes Model 2 Alpha-Beta + move ordering + TT + iterative deepening (src/agents/alphabeta.py)."""
import random
from pathlib import Path

import numpy as np
import pytest

import src.engine.api as engine_api
from experiments import registry
from experiments.positions import load_positions
from src.agents.alphabeta import AlphaBetaAgent, AlphaBetaH1Agent, Zobrist, expand
from src.agents.evaluation import h1
from src.agents.minimax import MinimaxAgent
from src.engine.api import apply_move, get_initial_state, get_legal_moves, get_scores, is_terminal

POSITIONS = load_positions(str(Path(__file__).resolve().parent.parent / "results" / "positions_seed42_n500.json"))


def random_walk_states(n, seed):
    rng = random.Random(seed)
    out = []
    while len(out) < n:
        state = get_initial_state()
        for _ in range(rng.randint(0, 60)):
            if is_terminal(state):
                break
            out.append(state)
            state = apply_move(state, rng.choice(get_legal_moves(state)))
    return out[:n]


# --- expand() harus identik dengan apply_move -------------------------------------------------

def assert_same_state(a, b):
    assert np.array_equal(a.board, b.board)
    assert (a.current_player, a.is_terminal, a.move_count) == (b.current_player, b.is_terminal, b.move_count)


def test_expand_matches_apply_move():
    captures = extras = 0
    for state in random_walk_states(400, seed=1):
        for a in get_legal_moves(state):
            child, extra, captured = expand(state, a)
            assert_same_state(child, apply_move(state, a))
            assert extra == (child.current_player == state.current_player)
            store = 7 if state.current_player == 0 else 15
            assert child.board[store] - state.board[store] >= captured
            captures += captured > 0
            extras += extra
    assert captures > 0 and extras > 0


def test_expand_respects_move_cap(monkeypatch):
    monkeypatch.setattr(engine_api, "MAX_GAME_MOVES", 3)
    state = get_initial_state()
    state = apply_move(apply_move(state, 0), get_legal_moves(apply_move(state, 0))[0])
    for a in get_legal_moves(state):
        assert_same_state(expand(state, a)[0], apply_move(state, a))


# --- Zobrist ------------------------------------------------------------------------------------

def test_zobrist_incremental_equals_full():
    z = Zobrist()
    for state in random_walk_states(150, seed=2):
        h = z.hash(state.board.tolist(), state.current_player)
        for a in get_legal_moves(state):
            child = apply_move(state, a)
            full = z.hash(child.board.tolist(), child.current_player)
            assert z.update(h, state.board.tolist(), child.board.tolist(),
                            state.current_player, child.current_player) == full


def test_zobrist_includes_player_and_is_reproducible():
    board = get_initial_state().board.tolist()
    assert Zobrist().hash(board, 0) != Zobrist().hash(board, 1)
    assert Zobrist().hash(board, 1) == Zobrist().hash(board, 1)


# --- Kesamaan dengan Minimax (RQ1, Bab 3.2) -----------------------------------------------------

@pytest.mark.parametrize("heuristic", ["h1", "h2"])
@pytest.mark.parametrize("ordering,iterative", [(False, False), (True, False), (True, True)])
def test_same_value_and_move_as_minimax_without_tt(heuristic, ordering, iterative):
    mm = MinimaxAgent(heuristic=heuristic)
    ab = AlphaBetaAgent(heuristic=heuristic, ordering=ordering, use_tt=False, iterative=iterative)
    for i, state in enumerate(POSITIONS[:24]):
        depth = 1 + i % 4
        assert ab.search(state, depth) == mm.search(state, depth), f"posisi {i}, depth {depth}"


def test_pruning_and_ordering_save_nodes():
    totals = {}
    configs = {
        "minimax": MinimaxAgent(),
        "ab": AlphaBetaAgent(ordering=False, use_tt=False, iterative=False),
        "ab_order": AlphaBetaAgent(ordering=True, use_tt=False, iterative=False),
    }
    for name, agent in configs.items():
        totals[name] = 0
        for state in POSITIONS[:20]:
            agent.search(state, 4)
            totals[name] += agent.metrics.nodes
    assert totals["ab"] < totals["minimax"]
    assert totals["ab_order"] < totals["ab"]


def test_tt_reduces_nodes_and_counts_hits():
    with_tt = AlphaBetaAgent(use_tt=True, iterative=False)
    without = AlphaBetaAgent(use_tt=False, iterative=False)
    nodes_tt = nodes_no = hits = 0
    for state in POSITIONS[:20]:
        with_tt.reset()
        with_tt.search(state, 5)
        nodes_tt += with_tt.metrics.nodes
        hits += with_tt.metrics.tt_hits
        without.search(state, 5)
        nodes_no += without.metrics.nodes
    assert hits > 0 and nodes_tt < nodes_no
    assert with_tt.metrics.tt_entries > 0 and without.metrics.tt_entries == 0


def plant_tt_entry(agent, state, move, depth, value):
    """Menanam entri EXACT palsu untuk anak `move` dari `state` di TT agen."""
    child = apply_move(state, move)
    h = agent.zobrist.hash(child.board.tolist(), child.current_player)
    agent._tt_me = state.current_player
    agent._tt[h & (agent.tt_size - 1)] = (h, depth, value, 0, None)


def test_tt_entry_used_only_when_deep_enough():
    # Pada depth 2 hanya simpul sisa-kedalaman 1 yang memeriksa TT, jadi tanpa entri
    # tanaman hasilnya identik dengan Minimax.
    state = POSITIONS[5]
    move = get_legal_moves(state)[-1]
    expected = MinimaxAgent().search(state, 2)

    shallow = AlphaBetaAgent(iterative=False)
    plant_tt_entry(shallow, state, move, depth=0, value=1e9)  # terlalu dangkal: harus diabaikan
    assert shallow.search(state, 2) == expected

    deep = AlphaBetaAgent(iterative=False)
    plant_tt_entry(deep, state, move, depth=5, value=1e9)  # cukup dalam: harus dipakai
    assert deep.search(state, 2) == (1e9, move)
    assert deep.metrics.tt_hits >= 1


def test_full_model_plays_legal_moves():
    agent = AlphaBetaAgent()
    for state in POSITIONS[:20]:
        agent.reset()
        assert agent.choose_move(state.copy(), depth=4) in get_legal_moves(state)


# --- Waktu dan kontrak agen -------------------------------------------------------------------

@pytest.mark.parametrize("make", [AlphaBetaAgent, MinimaxAgent])
def test_time_limit_iterative_deepening(make):
    agent = make()
    state = get_initial_state()
    move = agent.choose_move(state, time_limit=0.2, depth=0)
    assert move in get_legal_moves(state)
    assert agent.metrics.depth_reached >= 2
    assert agent.metrics.elapsed < 1.5

    agent.choose_move(state, time_limit=5.0, depth=2)  # depth tetap menjadi batas atas
    assert agent.metrics.depth_reached == 2

    with pytest.raises(ValueError):
        agent.choose_move(state, depth=0)  # tanpa batas waktu maupun kedalaman


@pytest.mark.parametrize("make", [AlphaBetaAgent, MinimaxAgent])
def test_iterative_deepening_stops_when_tree_is_exhausted(make):
    # Pemain 0 hanya punya 1 biji di lubang 6: satu langkah, masuk lumbung, sisi kosong -> selesai.
    board = np.zeros(16, dtype=np.int32)
    board[6], board[7], board[8], board[15] = 1, 40, 10, 47
    state = engine_api.CongklakState(board=board, current_player=0)
    agent = make()
    assert agent.choose_move(state, time_limit=5.0, depth=0) == 6
    assert agent.metrics.depth_reached == 1


def test_agent_contract():
    state = get_initial_state()
    before = state.board.copy()
    agent = registry.make_agent("alphabeta")
    assert isinstance(agent, AlphaBetaAgent) and agent.name == "alphabeta"
    assert isinstance(registry.make_agent("alphabeta_h1"), AlphaBetaH1Agent)
    move = agent.choose_move(state, depth=3)
    assert move in get_legal_moves(state) and np.array_equal(state.board, before)
    m = agent.metrics
    assert m.nodes > 0 and m.cutoffs > 0 and m.depth_reached == 3 and m.elapsed > 0
    agent.reset(1)
    assert agent.metrics.nodes == 0 and agent._tt == {}


def test_custom_evaluator_for_model_3():
    calls = []

    def store_diff(state, me):
        calls.append(me)
        return float(h1(state, me))

    agent = AlphaBetaAgent(heuristic=store_diff, name="ga")
    assert agent.choose_move(get_initial_state(), depth=2) in range(7)
    assert calls and set(calls) == {0} and agent.name == "ga"


def test_plays_full_game_against_minimax():
    state = get_initial_state()
    agents = (AlphaBetaAgent(depth=3), MinimaxAgent(depth=2))
    while not is_terminal(state):
        state = apply_move(state, agents[state.current_player].choose_move(state))
    assert sum(get_scores(state)) == 98


def test_bad_arguments():
    with pytest.raises(ValueError, match="Kedalaman"):
        AlphaBetaAgent(depth=0)
    with pytest.raises(ValueError, match="Heuristik"):
        AlphaBetaAgent(heuristic="h3")
