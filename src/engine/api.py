"""
API Interface & Board State untuk Congklak-Master.
Menjadi kontrak standar untuk implementasi Agen AI (Minimax, AlphaBeta, GA)
dan satu-satunya sumber logika publik: seluruh fungsi mendelegasikan ke Board
(src/engine/board.py). Aturan lengkap ada di docs/rules.md.
"""

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
from src.engine.board import (
    Board, MAX_SOW_ROUNDS, PLAYER_0, PLAYER_1,
    P0_PITS, P0_STORE, P1_PITS, P1_STORE,
)

# Pengaman: game dipaksa selesai bila jumlah langkah (pemanggilan apply_move,
# termasuk giliran tambahan) mencapai nilai ini; sisa biji disapu seperti akhir normal.
MAX_GAME_MOVES = 300


@dataclass(eq=False)
class CongklakState:
    board: np.ndarray        # Array 1D int32 panjang 16
    current_player: int      # 0 atau 1
    is_terminal: bool = False
    move_count: int = 0      # jumlah apply_move sejak posisi awal (tidak ikut state_key)

    def copy(self) -> 'CongklakState':
        return CongklakState(
            board=self.board.copy(),
            current_player=self.current_player,
            is_terminal=self.is_terminal,
            move_count=self.move_count
        )

    # Kesamaan dan hash memakai state_key(): (isi papan, pemain giliran).
    # PERINGATAN: jangan memutasi board/current_player pada state yang sudah
    # dipakai sebagai key (dict/set/tabel transposisi), karena hash-nya ikut berubah.
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CongklakState):
            return NotImplemented
        return state_key(self) == state_key(other)

    def __hash__(self) -> int:
        return hash(state_key(self))


def state_key(state: CongklakState) -> Tuple[bytes, int]:
    """Kunci state yang hashable: (isi papan sebagai bytes, pemain giliran). move_count tidak ikut."""
    return state.board.astype(np.int32, copy=False).tobytes(), int(state.current_player)


def get_initial_state() -> CongklakState:
    """Mengembalikan kondisi awal papan (7 biji per lubang kecil, lumbung 0)."""
    b = Board()
    return CongklakState(board=b.state, current_player=PLAYER_0, is_terminal=False, move_count=0)


def get_legal_moves(state: CongklakState) -> List[int]:
    """Mengembalikan daftar indeks lubang legal yang bisa dipilih pemain aktif."""
    if state.is_terminal:
        return []
    return Board(state.board, copy=False).get_valid_moves(state.current_player)


def is_terminal(state: CongklakState) -> bool:
    """Mengecek apakah permainan sudah selesai."""
    return state.is_terminal or len(get_legal_moves(state)) == 0


def get_scores(state: CongklakState) -> Tuple[int, int]:
    """Mengembalikan skor saat ini (skor_player_0, skor_player_1)."""
    return Board(state.board, copy=False).get_scores()


def get_winner(state: CongklakState) -> int:
    """
    Pemenang berdasarkan isi lumbung: 0 (Player 0), 1 (Player 1), atau -1 (seri).
    Bermakna pada state terminal (setelah sisa biji disapu).
    """
    return Board(state.board, copy=False).get_winner()


def get_score_diff(state: CongklakState, player: int) -> int:
    """Selisih lumbung dari sudut pandang `player`: lumbung player dikurangi lumbung lawan."""
    if player not in (PLAYER_0, PLAYER_1):
        raise ValueError(f"Pemain harus 0 atau 1, bukan {player!r}.")
    s0, s1 = get_scores(state)
    return (s0 - s1) if player == PLAYER_0 else (s1 - s0)


def apply_move(state: CongklakState, pit_index: int) -> CongklakState:
    """
    Eksekusi langkah pada lubang yang dipilih dan kembalikan state baru
    (state masukan tidak diubah). Seluruh aturan (tabur, lumbung lawan dilompati,
    menabur lanjutan, giliran tambahan, tembak, sweep saat terminal) dijalankan
    oleh Board.step. Di sini ditambah pengaman MAX_GAME_MOVES.
    Melempar ValueError bila state sudah terminal atau lubang tidak legal.
    """
    if state.is_terminal:
        raise ValueError("State sudah terminal, tidak ada langkah yang bisa dijalankan.")

    b = Board(state.board)  # salinan: board milik state masukan tidak tersentuh
    next_player, _, terminal = b.step(state.current_player, pit_index)
    move_count = state.move_count + 1

    if not terminal and move_count >= MAX_GAME_MOVES:
        b.sweep_remaining_seeds()
        terminal = True

    return CongklakState(
        board=b.state,
        current_player=next_player,
        is_terminal=terminal,
        move_count=move_count
    )
