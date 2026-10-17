"""
API Interface & Board State untuk Congklak-Master.
Menjadi kontrak standar untuk implementasi Agen AI (Minimax, AlphaBeta, GA)
dan Core Engine.
"""

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np

# Definisi Pemain
PLAYER_0 = 0  # Sisi bawah (Selatan)
PLAYER_1 = 1  # Sisi atas (Utara)

# Pemetaan Indeks Papan (Total 16 Slot)
P0_PITS = list(range(0, 7))      # Lubang kecil Player 0: 0 s.d. 6
P0_STORE = 7                     # Lumbung Player 0
P1_PITS = list(range(8, 15))     # Lubang kecil Player 1: 8 s.d. 14
P1_STORE = 15                    # Lumbung Player 1


@dataclass
class CongklakState:
    board: np.ndarray        # Array 1D int32 panjang 16
    current_player: int      # 0 atau 1
    is_terminal: bool = False

    def copy(self) -> 'CongklakState':
        return CongklakState(
            board=self.board.copy(),
            current_player=self.current_player,
            is_terminal=self.is_terminal
        )


def get_initial_state() -> CongklakState:
    """Mengembalikan kondisi awal papan (7 biji per lubang kecil, lumbung 0)."""
    board = np.zeros(16, dtype=np.int32)
    for p in P0_PITS + P1_PITS:
        board[p] = 7
    return CongklakState(board=board, current_player=PLAYER_0, is_terminal=False)


def get_legal_moves(state: CongklakState) -> List[int]:
    """Mengembalikan daftar indeks lubang legal yang bisa dipilih pemain aktif."""
    if state.is_terminal:
        return []
    pits = P0_PITS if state.current_player == PLAYER_0 else P1_PITS
    return [i for i in pits if state.board[i] > 0]


def is_terminal(state: CongklakState) -> bool:
    """Mengecek apakah permainan sudah selesai."""
    return state.is_terminal or len(get_legal_moves(state)) == 0


def get_scores(state: CongklakState) -> Tuple[int, int]:
    """Mengembalikan skor saat ini (skor_player_0, skor_player_1)."""
    return int(state.board[P0_STORE]), int(state.board[P1_STORE])


def apply_move(state: CongklakState, pit_index: int) -> CongklakState:
    """
    Eksekusi langkah pada lubang yang dipilih dan kembalikan state baru.
    Mencakup aturan: lumbung lawan diskip, ekstra turn, tembak (capture),
    dan sweep biji jika terminal.
    """
    next_state = state.copy()
    board = next_state.board
    player = next_state.current_player

    seeds = board[pit_index]
    board[pit_index] = 0

    curr = pit_index
    opponent_store = P1_STORE if player == PLAYER_0 else P0_STORE
    my_store = P0_STORE if player == PLAYER_0 else P1_STORE
    my_pits = P0_PITS if player == PLAYER_0 else P1_PITS

    # Tabur biji satu per satu
    while seeds > 0:
        curr = (curr + 1) % 16
        if curr == opponent_store:
            continue
        board[curr] += 1
        seeds -= 1

    # Cek Giliran Tambahan (Extra-Turn)
    if curr == my_store:
        next_player = player
    else:
        # Cek Tembak (Capture)
        if curr in my_pits and board[curr] == 1:
            opposite = 14 - curr
            if board[opposite] > 0:
                captured = board[opposite] + board[curr]
                board[curr] = 0
                board[opposite] = 0
                board[my_store] += captured
        next_player = 1 - player

    next_state.current_player = next_player

    # Cek apakah pemain berikutnya punya langkah legal
    if len(get_legal_moves(next_state)) == 0:
        # Bersihkan sisa biji ke lumbung masing-masing jika permainan buntu
        for p in P0_PITS:
            board[P0_STORE] += board[p]
            board[p] = 0
        for p in P1_PITS:
            board[P1_STORE] += board[p]
            board[p] = 0
        next_state.is_terminal = True

    return next_state