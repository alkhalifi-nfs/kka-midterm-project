"""
Unit Tests untuk Core Engine Congklak-Master (T13).
Mencakup 16 kasus uji: inisialisasi, sowing, skip lumbung lawan,
extra-turn, capture (tembak), kondisi akhir (terminal sweep), dan konservasi biji.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
import numpy as np
from src.engine.board import (
    Board, PLAYER_0, PLAYER_1, P0_PITS, P0_STORE, P1_PITS, P1_STORE
)
from src.engine.api import (
    get_initial_state, get_legal_moves, apply_move, is_terminal, get_scores
)


# 1. Uji kondisi awal papan
def test_01_initial_board_setup():
    b = Board()
    assert sum(b.state) == 98
    assert b.state[P0_STORE] == 0
    assert b.state[P1_STORE] == 0
    assert all(b.state[p] == 7 for p in P0_PITS)
    assert all(b.state[p] == 7 for p in P1_PITS)


# 2. Uji langkah legal di awal permainan
def test_02_initial_valid_moves():
    state = get_initial_state()
    assert get_legal_moves(state) == [0, 1, 2, 3, 4, 5, 6]


# 3. Uji penaburan dasar (sowing) tanpa melewati lumbung
def test_03_basic_sowing():
    b = Board(np.zeros(16, dtype=np.int32))
    b.state[0] = 3
    b.state[8] = 5  # Agar sisi P1 tidak kosong
    last_pit, extra = b.sow(PLAYER_0, 0)
    assert last_pit == 3
    assert not extra
    assert list(b.state[0:4]) == [0, 1, 1, 1]


# 4. Uji Giliran Tambahan (Extra-Turn) untuk Pemain 0
def test_04_extra_turn_player_0():
    state = get_initial_state()
    next_state = apply_move(state, 0)  # 7 biji dari lubang 0 jatuh tepat di lumbung 7
    assert next_state.current_player == PLAYER_0
    assert next_state.board[P0_STORE] == 1


# 5. Uji Giliran Tambahan (Extra-Turn) untuk Pemain 1
def test_05_extra_turn_player_1():
    state = get_initial_state()
    state.current_player = PLAYER_1
    next_state = apply_move(state, 8)  # 7 biji dari lubang 8 jatuh tepat di lumbung 15
    assert next_state.current_player == PLAYER_1
    assert next_state.board[P1_STORE] == 1


# 6. Uji pergantian giliran normal (tidak jatuh di lumbung)
def test_06_normal_turn_switch():
    state = get_initial_state()
    next_state = apply_move(state, 1)  # Jatuh di lubang 8
    assert next_state.current_player == PLAYER_1


# 7. Uji lumbung lawan dilewati (Skip Opponent Store) oleh Pemain 0
def test_07_skip_opponent_store_p0():
    b = Board(np.zeros(16, dtype=np.int32))
    b.state[6] = 9   # 9 biji dari 6: masuk ke 7..14 (8 biji), skip 15, biji ke-9 jatuh di 0
    b.state[8] = 1
    last_pit, _ = b.sow(PLAYER_0, 6)
    assert b.state[P1_STORE] == 0
    assert last_pit == 0
    assert b.state[0] == 1


# 8. Uji lumbung lawan dilewati (Skip Opponent Store) oleh Pemain 1
def test_08_skip_opponent_store_p1():
    b = Board(np.zeros(16, dtype=np.int32))
    b.state[14] = 9  # 9 biji dari 14: masuk ke 15, 0..6 (8 biji), skip 7, biji ke-9 jatuh di 8
    b.state[0] = 1
    last_pit, _ = b.sow(PLAYER_1, 14)
    assert b.state[P0_STORE] == 0
    assert last_pit == 8
    assert b.state[8] == 1


# 9. Uji aturan Tembak (Capture) berhasil untuk Pemain 0
def test_09_capture_success_p0():
    b = Board(np.zeros(16, dtype=np.int32))
    b.state[2] = 1
    b.state[3] = 0      # Target jatuh kosong
    b.state[11] = 6     # Seberang lubang 3 adalah 14 - 3 = 11
    b.state[0] = 1      # Sisa biji agar tidak terminal
    b.state[8] = 1
    next_p, extra, term = b.step(PLAYER_0, 2)
    assert not extra
    assert not term
    assert next_p == PLAYER_1
    assert b.state[3] == 0
    assert b.state[11] == 0
    assert b.state[P0_STORE] == 7  # 1 + 6 biji


# 10. Uji aturan Tembak (Capture) berhasil untuk Pemain 1
def test_10_capture_success_p1():
    b = Board(np.zeros(16, dtype=np.int32))
    b.state[9] = 1
    b.state[10] = 0     # Target jatuh kosong
    b.state[4] = 5      # Seberang lubang 10 adalah 14 - 10 = 4
    b.state[0] = 1
    b.state[8] = 1
    b.step(PLAYER_1, 9)
    assert b.state[10] == 0
    assert b.state[4] == 0
    assert b.state[P1_STORE] == 6  # 1 + 5 biji


# 11. Uji Capture gagal jika lubang seberang milik lawan kosong
def test_11_capture_fail_when_opposite_empty():
    b = Board(np.zeros(16, dtype=np.int32))
    b.state[2] = 1
    b.state[3] = 0
    b.state[11] = 0     # Seberang kosong -> tidak boleh tembak
    b.state[0] = 1
    b.state[8] = 1
    b.step(PLAYER_0, 2)
    assert b.state[3] == 1
    assert b.state[P0_STORE] == 0


# 12. Uji Capture tidak aktif jika mendarat di lubang kosong milik lawan
def test_12_no_capture_on_opponent_side():
    b = Board(np.zeros(16, dtype=np.int32))
    b.state[6] = 2      # Lewati 7 (lumbung), jatuh di 8 (lubang lawan yang kosong)
    b.state[8] = 0
    b.state[6] = 2
    b.state[0] = 2      # Seberang lubang 8 adalah 6
    b.state[9] = 1
    b.step(PLAYER_0, 6)
    assert b.state[8] == 1
    assert b.state[P0_STORE] == 1  # Hanya 1 biji dari lewat lumbung


# 13. Uji Kondisi Akhir (Terminal State) dan sapu bersih sisa biji (Sweep)
def test_13_terminal_condition_and_sweep():
    b = Board(np.zeros(16, dtype=np.int32))
    b.state[6] = 1      # Biji terakhir P0 masuk ke lumbung 7 -> sisi P0 habis
    b.state[8] = 4
    b.state[9] = 5
    _, _, terminal = b.step(PLAYER_0, 6)
    assert terminal
    assert b.state[P0_STORE] == 1
    assert b.state[P1_STORE] == 9  # 4 + 5 disapu ke lumbung P1
    assert sum(b.state[P1_PITS]) == 0


# 14. Uji penentuan pemenang dan kondisi seri (Draw)
def test_14_winner_and_draw_detection():
    b = Board(np.zeros(16, dtype=np.int32))
    b.state[P0_STORE] = 50
    b.state[P1_STORE] = 48
    assert b.get_winner() == PLAYER_0

    b.state[P0_STORE] = 49
    b.state[P1_STORE] = 49
    assert b.get_winner() == -1


# 15. Uji Error Handling saat memilih lubang kosong atau lubang lawan
def test_15_illegal_move_raises_error():
    b = Board(np.zeros(16, dtype=np.int32))
    b.state[0] = 0
    with pytest.raises(ValueError):
        b.sow(PLAYER_0, 0)
    with pytest.raises(ValueError):
        b.sow(PLAYER_0, 8)  # Lubang milik P1


# 16. Uji Konservasi 98 Biji selama simulasi permainan penuh
def test_16_total_seed_conservation_full_game():
    state = get_initial_state()
    steps = 0
    while not is_terminal(state) and steps < 500:
        assert int(np.sum(state.board)) == 98
        moves = get_legal_moves(state)
        state = apply_move(state, moves[0])
        steps += 1
    assert is_terminal(state)
    s0, s1 = get_scores(state)
    assert s0 + s1 == 98

    if __name__ == "__main__":
        pytest.main(["-v", __file__])