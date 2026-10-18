"""
Uji silang engine terhadap oracle independen (tests/reference_engine.py).

Oracle ditulis dari teks aturan, bukan dari board.py. Tiga kelompok uji:
  1. 1.000 game acak penuh (seed tetap), dicocokkan langkah demi langkah.
  2. Posisi acak sembarang (termasuk lubang besar) untuk rantai relay panjang.
  3. Pengaman MAX_SOW_ROUNDS diperkecil (1, 2, 3) agar cabang batas tabur teruji.
"""
import random

import numpy as np
import pytest

import src.engine
import src.engine.api
import src.engine.board as board_module
from src.engine.api import (
    CongklakState, MAX_GAME_MOVES, apply_move, get_initial_state, get_legal_moves,
)
from tests import reference_engine as ref

N_RANDOM_GAMES = 1000


def _to_list(state: CongklakState):
    return [int(x) for x in state.board]


def test_oracle_and_engine_share_the_same_constants():
    assert ref.MAX_ROUNDS == board_module.MAX_SOW_ROUNDS == 200
    assert ref.MAX_MOVES == MAX_GAME_MOVES == 300


def test_engine_package_reexports_same_class():
    assert src.engine.CongklakState is src.engine.api.CongklakState
    for name in src.engine.__all__:
        assert getattr(src.engine, name) is getattr(src.engine.api, name), name


def test_1000_random_games_match_oracle_step_by_step():
    relay_moves = extra_turn_moves = capture_moves = total_moves = 0
    lengths = []

    for game in range(N_RANDOM_GAMES):
        rng = random.Random(20261021 + game)
        state = get_initial_state()
        board = ref.initial_board()
        player, move_count, terminal = 0, 0, False

        while not terminal:
            assert sum(board) == 98
            assert _to_list(state) == board
            assert state.current_player == player
            assert state.move_count == move_count
            assert not state.is_terminal

            legal = ref.legal_moves(board, player)
            assert get_legal_moves(state) == legal

            pit = rng.choice(legal)
            res, terminal, move_count = ref.apply(board, player, move_count, pit)
            state = apply_move(state, pit)
            board, player = res.board, res.next_player

            total_moves += 1
            relay_moves += res.rounds >= 2
            extra_turn_moves += res.extra_turn
            capture_moves += res.captured > 0

            assert _to_list(state) == board, f"game {game}, langkah {move_count}"
            assert state.current_player == player
            assert state.move_count == move_count
            assert state.is_terminal == terminal

        # Game selesai secara normal, bukan karena pengaman 300 langkah
        assert sum(board) == 98
        assert move_count < MAX_GAME_MOVES, f"game {game} kena batas 300 langkah"
        assert get_legal_moves(state) == []
        lengths.append(move_count)

    # Pastikan perbandingan tidak kosong: semua mekanisme benar-benar terpakai
    assert relay_moves > 0 and extra_turn_moves > 0 and capture_moves > 0
    assert max(lengths) < MAX_GAME_MOVES
    assert total_moves == sum(lengths)


def _random_position(rng: random.Random):
    """Papan acak dengan total 98 biji; lumbung boleh terisi. Pastikan pemain punya langkah."""
    while True:
        board = [0] * 16
        for _ in range(98):
            board[rng.randrange(16)] += 1
        player = rng.randrange(2)
        if ref.legal_moves(board, player):
            return board, player


def test_random_arbitrary_positions_match_oracle():
    rng = random.Random(7)
    max_rounds_seen = 0
    for _ in range(3000):
        board, player = _random_position(rng)
        pit = rng.choice(ref.legal_moves(board, player))
        move_count = rng.randrange(0, MAX_GAME_MOVES)

        res, terminal, new_count = ref.apply(board, player, move_count, pit)
        state = CongklakState(np.array(board, dtype=np.int32), player, False, move_count)
        out = apply_move(state, pit)
        max_rounds_seen = max(max_rounds_seen, res.rounds)

        assert _to_list(out) == res.board, (board, player, pit)
        assert out.current_player == res.next_player
        assert out.is_terminal == terminal
        assert out.move_count == new_count
        assert _to_list(state) == board, "state masukan tidak boleh berubah"
    assert max_rounds_seen >= 3, "posisi acak seharusnya menghasilkan rantai relay"


@pytest.mark.parametrize("cap", [1, 2, 3])
def test_reduced_sow_round_cap_matches_oracle(monkeypatch, cap):
    """Cabang batas putaran tabur (hampir tak pernah tercapai di 200) diuji dengan batas kecil."""
    monkeypatch.setattr(board_module, "MAX_SOW_ROUNDS", cap)
    capped_moves = 0
    for game in range(150):
        rng = random.Random(555 + game)
        state = get_initial_state()
        board = ref.initial_board()
        player, move_count, terminal = 0, 0, False
        while not terminal:
            pit = rng.choice(ref.legal_moves(board, player))
            res, terminal, move_count = ref.apply(board, player, move_count, pit, max_rounds=cap)
            state = apply_move(state, pit)
            board, player = res.board, res.next_player
            capped_moves += res.rounds == cap and not res.extra_turn
            assert _to_list(state) == board
            assert state.current_player == player
            assert state.is_terminal == terminal
    assert capped_moves > 0, "batas putaran seharusnya tercapai pada sebagian langkah"
