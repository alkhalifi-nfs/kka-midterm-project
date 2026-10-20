"""Tes program demo (experiments/demo.py)."""
import io

import pytest

from experiments import demo
from src.engine.api import get_initial_state


def test_pit_numbers_follow_sowing_direction():
    assert [demo.pit_number(i) for i in range(7)] == [1, 2, 3, 4, 5, 6, 7]
    assert [demo.pit_number(i) for i in range(8, 15)] == [1, 2, 3, 4, 5, 6, 7]


def test_render_initial_board():
    text = demo.render(get_initial_state().board)
    assert "Pemain 0:  7  7  7  7  7  7  7" in text and "[lumbung P0  0]" in text


def test_agents_play_full_game_quietly():
    out = io.StringIO()
    s0, s1, turns = demo.play("alphabeta", "greedy", depth=2, time_limit=None, quiet=True, out=out)
    assert s0 + s1 == 98 and turns > 0
    assert "Permainan selesai" in out.getvalue()


def test_human_input_is_validated():
    answers = iter(["9", "abc", "1"] + ["1", "2", "3", "4", "5", "6", "7"] * 40)
    out = io.StringIO()
    s0, s1, _ = demo.play("manusia", "greedy", depth=1, time_limit=None, quiet=True,
                          read=lambda prompt: next(answers), out=out)
    assert s0 + s1 == 98


def test_unknown_agent_is_rejected():
    with pytest.raises(SystemExit, match="tidak dikenal"):
        demo.main(["--p0", "salah"])
