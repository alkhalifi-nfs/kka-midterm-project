"""
Uji vektor aturan final (menabur lanjutan, pengaman, akhir game) dan perilaku API.

Format vektor: papan 16 angka, lalu giliran berikutnya. Semua vektor diturunkan
dengan tangan dari teks aturan (docs/rules.md), bukan dari keluaran engine.
"""
import numpy as np
import pytest

import src.engine.board as board_module
from src.engine.api import (
    CongklakState, MAX_GAME_MOVES, apply_move, get_initial_state, get_legal_moves,
    get_score_diff, get_scores, get_winner, is_terminal, state_key,
)


def make_state(board, player=0, move_count=0, terminal=False):
    return CongklakState(np.array(board, dtype=np.int32), player, terminal, move_count)


def as_list(state):
    return [int(x) for x in state.board]


# --- Pembuka P0 dari posisi awal ------------------------------------------------

OPENINGS = {
    0: ([0, 8, 8, 8, 8, 8, 8, 1, 7, 7, 7, 7, 7, 7, 7, 0], 0),
    1: ([8, 0, 8, 8, 8, 8, 8, 10, 0, 8, 8, 8, 8, 0, 8, 0], 1),
    2: ([8, 8, 0, 8, 8, 8, 8, 10, 8, 0, 8, 8, 0, 8, 8, 0], 1),
    3: ([8, 8, 8, 0, 8, 8, 8, 10, 8, 8, 0, 0, 8, 8, 8, 0], 1),
    4: ([8, 8, 8, 8, 0, 8, 8, 10, 8, 8, 0, 0, 8, 8, 8, 0], 1),
    5: ([8, 8, 8, 8, 8, 0, 8, 10, 8, 0, 8, 8, 0, 8, 8, 0], 1),
    6: ([8, 8, 8, 8, 8, 8, 0, 10, 0, 8, 8, 8, 8, 0, 8, 0], 1),
}


@pytest.mark.parametrize("pit", sorted(OPENINGS))
def test_opening_move_p0(pit):
    board, next_player = OPENINGS[pit]
    out = apply_move(get_initial_state(), pit)
    assert as_list(out) == board
    assert out.current_player == next_player
    assert not out.is_terminal
    assert out.move_count == 1
    assert sum(as_list(out)) == 98


def test_opening_pits_1_to_6_give_p0_store_10():
    for pit in range(1, 7):
        assert get_scores(apply_move(get_initial_state(), pit)) == (10, 0)


@pytest.mark.parametrize("k", range(7))
def test_opening_symmetry_p1_equals_rotated_p0(k):
    """Langkah P1 lubang 8+k = langkah P0 lubang k setelah papan diputar 8 slot dan pemain ditukar."""
    p0_result = apply_move(get_initial_state(), k)

    start_p1 = get_initial_state()
    start_p1.current_player = 1
    p1_result = apply_move(start_p1, 8 + k)

    rotated = [0] * 16
    for i, seeds in enumerate(as_list(p0_result)):
        rotated[(i + 8) % 16] = seeds
    assert as_list(p1_result) == rotated
    assert p1_result.current_player == 1 - p0_result.current_player


# --- Skenario: P0 melangkah (awal, lubang -> hasil, giliran berikutnya) ----------

SCENARIOS = {
    "relay lalu giliran tambahan": (
        [0, 0, 0, 1, 2, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0], 3,
        [0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0], 0),
    "relay lalu tembak": (
        [0, 1, 2, 0, 0, 0, 0, 0, 0, 4, 0, 3, 0, 0, 0, 0], 1,
        [0, 0, 0, 1, 1, 0, 0, 5, 0, 0, 0, 3, 0, 0, 0, 0], 1),
    "relay di sisi lawan": (
        [0, 0, 0, 0, 0, 0, 2, 0, 1, 0, 0, 0, 0, 5, 0, 0], 6,
        [0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 5, 0, 0], 1),
    "relay, seberang kosong (tanpa tembak)": (
        [2, 0, 1, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0], 0,
        [0, 1, 0, 1, 1, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0], 1),
    "satu putaran penuh (15 biji)": (
        [15, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0], 0,
        [0, 1, 1, 1, 1, 1, 1, 3, 1, 1, 2, 1, 1, 1, 0, 0], 1),
}


@pytest.mark.parametrize("name", list(SCENARIOS))
def test_scenarios_p0(name):
    start, pit, expected, next_player = SCENARIOS[name]
    out = apply_move(make_state(start, 0), pit)
    assert as_list(out) == expected
    assert out.current_player == next_player
    assert not out.is_terminal
    assert sum(as_list(out)) == sum(start)


# --- Batas putaran tabur ---------------------------------------------------------

def test_sow_round_cap_one_stops_after_first_round(monkeypatch):
    monkeypatch.setattr(board_module, "MAX_SOW_ROUNDS", 1)
    out = apply_move(get_initial_state(), 1)
    assert as_list(out) == [7, 0, 8, 8, 8, 8, 8, 1, 8, 7, 7, 7, 7, 7, 7, 0]
    assert out.current_player == 1


def test_cap_round_ending_on_filled_own_pit_passes_turn_without_capture(monkeypatch):
    start = [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0]
    # Tanpa batas efektif: lubang 0 -> lubang 1 (sudah berisi, jadi 2) -> relay 2 biji ke 2 dan 3.
    full = apply_move(make_state(start, 0), 0)
    assert as_list(full) == [0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0]
    assert full.current_player == 1

    # Batas 1 putaran: berhenti di lubang 1 yang berisi, giliran pindah, tidak ada tembak.
    monkeypatch.setattr(board_module, "MAX_SOW_ROUNDS", 1)
    capped = apply_move(make_state(start, 0), 0)
    assert as_list(capped) == [0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0]
    assert capped.current_player == 1


# --- Akhir game ------------------------------------------------------------------

def test_side_empty_does_not_end_game_when_next_player_has_moves():
    out = apply_move(make_state([0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 3, 0], 0), 6)
    assert as_list(out) == [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 3, 0]
    assert out.current_player == 1
    assert not out.is_terminal
    assert not is_terminal(out)


def test_game_ends_when_next_player_has_no_moves_and_leftovers_are_swept():
    out = apply_move(make_state([1, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 4], 0), 0)
    assert as_list(out) == [0, 0, 0, 0, 0, 0, 0, 6, 0, 0, 0, 0, 0, 0, 0, 4]
    assert out.is_terminal and is_terminal(out)
    assert get_legal_moves(out) == []
    assert get_scores(out) == (6, 4)
    assert get_winner(out) == 0


def test_extra_turn_with_empty_own_side_ends_game():
    # P0 menaruh biji terakhir di lumbung sendiri tetapi tak punya lubang berisi lagi.
    out = apply_move(make_state([0, 0, 0, 0, 0, 0, 1, 0, 4, 5, 0, 0, 0, 0, 0, 0], 0), 6)
    assert out.is_terminal
    assert get_scores(out) == (1, 9)
    assert as_list(out) == [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 9]


@pytest.mark.parametrize("player,pit", [(0, 3), (1, 10)])
def test_move_cap_300_forces_terminal(player, pit):
    start = get_initial_state()
    start.current_player = player
    start.move_count = MAX_GAME_MOVES - 1
    out = apply_move(start, pit)
    assert out.is_terminal
    assert out.move_count == MAX_GAME_MOVES
    assert all(int(out.board[i]) == 0 for i in list(range(0, 7)) + list(range(8, 15)))
    assert int(out.board.sum()) == 98
    assert sum(get_scores(out)) == 98


def test_every_legal_move_at_move_count_299_is_terminal():
    start = get_initial_state()
    start.move_count = 299
    for pit in get_legal_moves(start):
        out = apply_move(start, pit)
        assert out.is_terminal and out.move_count == 300
        assert int(out.board.sum()) == 98


def test_move_count_increments_and_survives_copy():
    s = get_initial_state()
    assert s.move_count == 0
    s1 = apply_move(s, 0)          # giliran tambahan tetap dihitung sebagai 1 langkah
    s2 = apply_move(s1, 3)
    assert (s1.move_count, s2.move_count) == (1, 2)
    assert s2.copy().move_count == 2
    assert s.move_count == 0


# --- state_key / == / hash ---------------------------------------------------------

def test_equal_states_have_equal_hash_and_work_as_dict_keys():
    a, b = get_initial_state(), get_initial_state()
    assert a == b and hash(a) == hash(b)
    assert state_key(a) == state_key(b)
    table = {a: "awal"}
    assert table[b] == "awal"
    assert len({a, b}) == 1


def test_different_player_means_different_state():
    a = get_initial_state()
    b = get_initial_state()
    b.current_player = 1
    assert a != b
    assert state_key(a) != state_key(b)
    assert len({a, b}) == 2


def test_different_board_means_different_state():
    assert apply_move(get_initial_state(), 1) != apply_move(get_initial_state(), 2)


def test_move_count_is_not_part_of_state_key():
    a = get_initial_state()
    b = get_initial_state()
    b.move_count = 17
    assert a == b and hash(a) == hash(b)


def test_state_key_ignores_array_dtype():
    a = get_initial_state()
    b = CongklakState(a.board.astype(np.int64), 0)
    assert a == b and hash(a) == hash(b)


def test_state_is_not_equal_to_other_types():
    assert get_initial_state() != "bukan state"
    assert get_initial_state() != None  # noqa: E711


# --- get_winner / get_score_diff ---------------------------------------------------

def test_get_winner_and_score_diff():
    board = [0] * 16
    board[7], board[15] = 50, 48
    s = make_state(board, 0, terminal=True)
    assert get_winner(s) == 0
    assert get_score_diff(s, 0) == 2
    assert get_score_diff(s, 1) == -2

    board[7], board[15] = 47, 51
    s = make_state(board, 1, terminal=True)
    assert get_winner(s) == 1
    assert get_score_diff(s, 0) == -4
    assert get_score_diff(s, 1) == 4

    board[7], board[15] = 49, 49
    s = make_state(board, 0, terminal=True)
    assert get_winner(s) == -1
    assert get_score_diff(s, 0) == get_score_diff(s, 1) == 0


def test_get_score_diff_rejects_invalid_player():
    with pytest.raises(ValueError):
        get_score_diff(get_initial_state(), 2)


# --- Perilaku API umum -------------------------------------------------------------

def test_apply_move_does_not_mutate_input_state():
    s = get_initial_state()
    before = s.board.copy()
    out = apply_move(s, 1)
    assert np.array_equal(s.board, before)
    assert s.current_player == 0 and s.move_count == 0
    assert out.board is not s.board


@pytest.mark.parametrize("pit", [7, 8, 15, 20])
def test_apply_move_rejects_pit_not_owned_by_current_player(pit):
    with pytest.raises(ValueError):
        apply_move(get_initial_state(), pit)


def test_apply_move_rejects_empty_pit_and_terminal_state():
    s = make_state([0, 3, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0], 0)
    with pytest.raises(ValueError):
        apply_move(s, 0)
    done = apply_move(make_state([1, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 4], 0), 0)
    with pytest.raises(ValueError):
        apply_move(done, 0)


def test_game_scores_always_sum_to_98_at_end():
    s = get_initial_state()
    while not is_terminal(s):
        s = apply_move(s, get_legal_moves(s)[-1])
    assert sum(get_scores(s)) == 98
    assert s.move_count < MAX_GAME_MOVES
