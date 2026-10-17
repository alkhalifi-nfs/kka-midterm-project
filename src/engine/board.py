"""
Logika Papan Congklak (Engine v1 Lengkap).
Mencakup: Sowing, Extra-Turn, Capture (Tembak), dan Kondisi Akhir (Sweep).
"""

from typing import List, Tuple
import numpy as np

PLAYER_0 = 0
PLAYER_1 = 1

P0_PITS = list(range(0, 7))      # 0..6
P0_STORE = 7
P1_PITS = list(range(8, 15))     # 8..14
P1_STORE = 15

TOTAL_SLOTS = 16
SEEDS_PER_PIT = 7


class Board:
    def __init__(self, state: np.ndarray = None):
        if state is not None:
            self.state = np.array(state, dtype=np.int32).copy()
        else:
            self.state = np.zeros(TOTAL_SLOTS, dtype=np.int32)
            for pit in P0_PITS + P1_PITS:
                self.state[pit] = SEEDS_PER_PIT

    def copy(self) -> 'Board':
        return Board(self.state)

    @staticmethod
    def get_player_pits(player: int) -> List[int]:
        return P0_PITS if player == PLAYER_0 else P1_PITS

    @staticmethod
    def get_player_store(player: int) -> int:
        return P0_STORE if player == PLAYER_0 else P1_STORE

    @staticmethod
    def get_opponent_store(player: int) -> int:
        return P1_STORE if player == PLAYER_0 else P0_STORE

    @staticmethod
    def get_opposite_pit(pit: int) -> int:
        """Mengembalikan indeks lubang seberang milik lawan (0<->14, 1<->13, ..., 6<->8)."""
        return 14 - pit

    def get_valid_moves(self, player: int) -> List[int]:
        pits = self.get_player_pits(player)
        return [p for p in pits if self.state[p] > 0]

    def is_side_empty(self, player: int) -> bool:
        """Mengecek apakah seluruh lubang kecil milik pemain kosong."""
        pits = self.get_player_pits(player)
        return all(self.state[p] == 0 for p in pits)

    def sweep_remaining_seeds(self) -> None:
        """Memindahkan seluruh sisa biji di lubang kecil ke lumbung pemiliknya masing-masing."""
        for p in P0_PITS:
            self.state[P0_STORE] += self.state[p]
            self.state[p] = 0
        for p in P1_PITS:
            self.state[P1_STORE] += self.state[p]
            self.state[p] = 0

    def sow(self, player: int, start_pit: int) -> Tuple[int, bool]:
        """Menabur biji dari start_pit, melewati lumbung lawan."""
        my_pits = self.get_player_pits(player)
        if start_pit not in my_pits:
            raise ValueError(f"Lubang {start_pit} bukan milik Pemain {player}.")

        seeds = self.state[start_pit]
        if seeds <= 0:
            raise ValueError(f"Lubang {start_pit} kosong, tidak bisa melangkah.")

        self.state[start_pit] = 0
        curr_pit = start_pit
        opp_store = self.get_opponent_store(player)
        my_store = self.get_player_store(player)

        while seeds > 0:
            curr_pit = (curr_pit + 1) % TOTAL_SLOTS
            if curr_pit == opp_store:
                continue
            self.state[curr_pit] += 1
            seeds -= 1

        has_extra_turn = (curr_pit == my_store)
        return curr_pit, has_extra_turn

    def apply_capture(self, player: int, last_pit: int) -> int:
        """
        Mengecek dan mengeksekusi aturan Tembak (Capture).
        Syarat:
        1. Biji terakhir mendarat di lubang kecil sisi sendiri.
        2. Lubang tersebut tadinya kosong (sekarang berisi tepat 1 biji).
        3. Lubang lawan di seberangnya berisi >= 1 biji.
        Returns:
            Jumlah biji yang berhasil ditembak (0 jika tidak terjadi capture).
        """
        my_pits = self.get_player_pits(player)
        my_store = self.get_player_store(player)

        if last_pit in my_pits and self.state[last_pit] == 1:
            opposite_pit = self.get_opposite_pit(last_pit)
            if self.state[opposite_pit] > 0:
                captured = self.state[last_pit] + self.state[opposite_pit]
                self.state[last_pit] = 0
                self.state[opposite_pit] = 0
                self.state[my_store] += captured
                return int(captured)
        return 0

    def step(self, player: int, move: int) -> Tuple[int, bool, bool]:
        """
        Menjalankan 1 langkah penuh: Sow -> Cek Extra-Turn / Capture -> Cek Kondisi Akhir.
        Returns:
            next_player (int): Pemain berikutnya.
            has_extra_turn (bool): Apakah mendapat giliran tambahan.
            is_terminal (bool): Apakah permainan berakhir setelah langkah ini.
        """
        last_pit, has_extra_turn = self.sow(player, move)

        if has_extra_turn:
            next_player = player
        else:
            self.apply_capture(player, last_pit)
            next_player = 1 - player

        # Kondisi Akhir: jika salah satu sisi kosong atau pemain berikutnya tidak punya langkah
        is_terminal = False
        if self.is_side_empty(PLAYER_0) or self.is_side_empty(PLAYER_1) or len(self.get_valid_moves(next_player)) == 0:
            self.sweep_remaining_seeds()
            is_terminal = True

        return next_player, has_extra_turn, is_terminal

    def get_scores(self) -> Tuple[int, int]:
        return int(self.state[P0_STORE]), int(self.state[P1_STORE])

    def get_winner(self) -> int:
        """Mengembalikan pemenang: 0 (Player 0), 1 (Player 1), atau -1 (Draw)."""
        s0, s1 = self.get_scores()
        if s0 > s1:
            return PLAYER_0
        elif s1 > s0:
            return PLAYER_1
        return -1