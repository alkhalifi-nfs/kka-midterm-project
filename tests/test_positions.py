"""Tes pengambilan sampel posisi (experiments/positions.py)."""
import json

import numpy as np
import pytest

from experiments.positions import load_positions, sample_positions, save_positions, main
from src.engine.api import get_legal_moves, is_terminal


def boards(positions):
    return [(p.board.tolist(), p.current_player, p.move_count) for p in positions]


def test_sampling_is_reproducible():
    assert boards(sample_positions(30, seed=42)) == boards(sample_positions(30, seed=42))


def test_different_seeds_give_different_positions():
    assert boards(sample_positions(30, seed=42)) != boards(sample_positions(30, seed=43))


def test_position_i_does_not_depend_on_n():
    assert boards(sample_positions(10, seed=7)) == boards(sample_positions(25, seed=7))[:10]


def test_positions_are_non_terminal_with_98_seeds_and_valid_state():
    positions = sample_positions(200, seed=42)
    assert len(positions) == 200
    for p in positions:
        assert not p.is_terminal and not is_terminal(p)
        assert int(p.board.sum()) == 98
        assert p.current_player in (0, 1)
        assert len(get_legal_moves(p)) > 0
        assert 4 <= p.move_count <= 40
        assert p.board.dtype == np.int32 and len(p.board) == 16


def test_ply_range_is_respected_and_covers_the_range():
    counts = [p.move_count for p in sample_positions(300, seed=1, min_plies=6, max_plies=12)]
    assert min(counts) == 6 and max(counts) == 12


def test_json_roundtrip_preserves_positions(tmp_path):
    original = sample_positions(40, seed=3)
    path = str(tmp_path / "p.json")
    save_positions(path, original, {"seed": 3})
    loaded = load_positions(path)
    assert boards(loaded) == boards(original)
    raw = json.load(open(path, encoding="utf-8"))
    assert raw["meta"] == {"seed": 3}
    assert set(raw["positions"][0]) == {"board", "current_player", "move_count"}


def test_impossible_ply_range_fails_instead_of_looping(monkeypatch):
    import experiments.positions as module
    monkeypatch.setattr(module, "MAX_ATTEMPTS", 20)
    with pytest.raises(RuntimeError, match="Gagal"):
        sample_positions(1, seed=1, min_plies=500, max_plies=500)


def test_invalid_arguments_are_rejected():
    with pytest.raises(ValueError):
        sample_positions(5, seed=1, min_plies=10, max_plies=5)


def test_cli_writes_the_default_named_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["--n", "12", "--seed", "9"]) == 0
    loaded = load_positions(str(tmp_path / "results" / "positions_seed9_n12.json"))
    assert boards(loaded) == boards(sample_positions(12, seed=9))
