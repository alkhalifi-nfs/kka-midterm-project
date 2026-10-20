"""Tes Model 3: fitur evaluasi 6 fitur, operator GA, training, dan GAAgent."""
import json
import os
import random

import pytest

from experiments import ga_train
from src.agents.evaluation import (
    H2_AS_GA_WEIGHTS, TERMINAL_WEIGHT, evaluate, ga_features, weighted_evaluator,
)
from src.agents.ga import GAAgent, load_weights
from src.engine.api import get_initial_state, get_legal_moves
from tests.test_evaluation import HAND, make_state, random_positions


def test_ga_features_hand_crafted():
    # f1..f3 seperti H2; f4 = 8 (peluang tembak P0), f5 = 5 (ancaman dari P1);
    # f6 = lubang berisi P0 {0,2,3,6} - P1 {8,10,11,13,14} = 4 - 5 = -1
    assert ga_features(make_state(HAND), 0) == (13, -1, 1, 8, 5, -1)
    assert ga_features(make_state(HAND), 1) == (-13, 1, -1, 5, 8, 1)


def test_h2_is_a_point_in_ga_weight_space():
    evaluator = weighted_evaluator(H2_AS_GA_WEIGHTS)
    for state in random_positions(40, seed=9):
        for me in (0, 1):
            assert evaluator(state, me) == pytest.approx(evaluate(state, me, "h2"))


def test_weighted_evaluator_terminal_and_validation():
    board = [0] * 16
    board[7], board[15] = 50, 48
    assert weighted_evaluator([0] * 6)(make_state(board, terminal=True), 0) == 2 * TERMINAL_WEIGHT
    with pytest.raises(ValueError, match="6 bobot"):
        weighted_evaluator([1, 2, 3])


def test_operators_respect_bounds():
    rng = random.Random(0)
    a, b = [1.0, -1.0, 0.5, 0.0, 0.9, -0.9], [-1.0, 1.0, 0.4, 0.0, 1.0, -1.0]
    for _ in range(200):
        child = ga_train.mutate(rng, ga_train.blx_crossover(rng, a, b, 0.5), 1.0, 0.5)
        assert len(child) == 6 and all(-1.0 <= g <= 1.0 for g in child)
    assert ga_train.mutate(rng, a, 0.0, 0.5) == a


def test_next_generation_keeps_elites_and_size():
    rng = random.Random(1)
    population = [[i / 10] * 6 for i in range(8)]
    fitness = list(range(8))
    params = dict(ga_train.DEFAULTS, population=8, elite=2)
    new = ga_train.next_generation(rng, population, fitness, params)
    assert len(new) == 8 and new[0] == population[7] and new[1] == population[6]


def test_play_game_is_deterministic():
    task = (tuple(H2_AS_GA_WEIGHTS), "h1", 5, 0, 1, 2, 6)
    win, margin = ga_train.play_game(task)
    assert win in (0.0, 50.0, 100.0) and -98 <= margin <= 98
    assert ga_train.play_game(task) == (win, margin)


@pytest.fixture(scope="module")
def trained(tmp_path_factory):
    out = str(tmp_path_factory.mktemp("ga"))
    code = ga_train.main(["--population", "4", "--generations", "2", "--elite", "1", "--openings", "1",
                          "--validation-openings", "1", "--validation-last", "2", "--depth", "1",
                          "--workers", "1", "--out-dir", out])
    assert code == 0
    return out


def test_training_outputs(trained):
    for name in ("ga_weights.json", "ga_history.csv", "ga_population.csv", "ga_validation.csv",
                 "ga_convergence.png"):
        assert os.path.getsize(os.path.join(trained, name)) > 0
    result = json.load(open(os.path.join(trained, "ga_weights.json"), encoding="utf-8"))
    assert len(result["weights"]) == 6 and all(-1 <= w <= 1 for w in result["weights"])
    assert result["params"]["population"] == 4 and result["chosen"].startswith("terbaik generasi")
    rows = open(os.path.join(trained, "ga_population.csv"), encoding="utf-8").read().splitlines()
    assert len(rows) == 1 + 4 * 2


def test_ga_agent_uses_trained_weights(trained):
    path = os.path.join(trained, "ga_weights.json")
    agent = GAAgent(depth=2, weights_path=path)
    assert agent.weights == load_weights(path) and agent.name == "ga"
    state = get_initial_state()
    assert agent.choose_move(state) in get_legal_moves(state)
    assert agent.metrics.nodes > 0


def test_ga_agent_without_weights_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="ga_train"):
        GAAgent(weights_path=str(tmp_path / "tidak_ada.json"))
    assert GAAgent(weights=H2_AS_GA_WEIGHTS).weights == list(H2_AS_GA_WEIGHTS)
