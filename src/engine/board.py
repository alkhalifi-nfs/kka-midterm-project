"""
Logika Papan Congklak (Board & Sowing Mechanism).
Mengatur representasi slot papan, aturan penaburan biji, dan logika giliran tambahan.
"""

from typing import List, Tuple
import numpy as np

# Definisi Pemain
PLAYER_0 = 0
PLAYER_1 = 1

# Pemetaan Indeks Papan (16 Slot)
# Sisi Pemain 0 (Bawah / Selatan): lubang 0-6, lumbung 7
# Sisi Pemain 1 (Atas / Utara): lubang 8-14, lumbung 15
P0_PITS = list(range(0, 7))
P0_STORE = 7
P1_PITS = list(range(8, 15))
P1_STORE = 15

TOTAL_SLOTS = 16
SEEDS_PER_PIT = 7


class Board:
    def __init__(self, state: np.ndarray = None):
        """
        Inisialisasi papan. Jika state kosong, papan diisi default 7 biji per lubang.
        """
        if state is not None:
            self.state = state.copy()
        else:
            self.state = np.zeros(TOTAL_SLOTS, dtype=np.int32)
            for pit in P0_PITS + P1_PITS:
                self.state[pit] = SEEDS_PER_PIT

    def copy(self) -> 'Board':
        """Membuat salinan independen dari papan."""
        return Board(self.state)

    @staticmethod
    def get_player_pits(player: int) -> List[int]:
        """Mengembalikan daftar indeks lubang kecil milik pemain."""
        return P0_PITS if player == PLAYER_0 else P1_PITS

    @staticmethod
    def get_player_store(player: int) -> int:
        """Mengembalikan indeks lumbung milik pemain."""
        return P0_STORE if player == PLAYER_0 else P1_STORE

    @staticmethod
    def get_opponent_store(player: int) -> int:
        """Mengembalikan indeks lumbung milik lawan."""
        return P1_STORE if player == PLAYER_0 else P0_STORE

    def get_valid_moves(self, player: int) -> List[int]:
        """
        Mengembalikan lubang legal milik pemain yang memiliki minimal 1 biji.
        """
        pits = self.get_player_pits(player)
        return [p for p in pits if self.state[p] > 0]

    def sow(self, player: int, start_pit: int) -> Tuple[int, bool]:
        """
        Menjalankan proses penaburan biji (sowing) dari lubang yang dipilih.
        
        Aturan:
        1. Ambil semua biji dari start_pit.
        2. Tabur 1 biji ke setiap lubang berikutnya berlawanan arah jarum jam.
        3. Lumbung lawan dilewati (skip).
        4. Cek giliran tambahan: jika biji terakhir mendarat di lumbung sendiri.

        Returns:
            last_pit (int): Indeks tempat biji terakhir mendarat.
            has_extra_turn (bool): True jika pemain mendapatkan giliran tambahan.
        """
        seeds = self.state[start_pit]
        if seeds <= 0:
            raise ValueError(f"Lubang {start_pit} kosong, tidak bisa melangkah.")

        # Ambil biji dari lubang awal
        self.state[start_pit] = 0

        curr_pit = start_pit
        opp_store = self.get_opponent_store(player)
        my_store = self.get_player_store(player)

        # Tabur biji satu per satu
        while seeds > 0:
            curr_pit = (curr_pit + 1) % TOTAL_SLOTS
            
            # Lewati lumbung lawan
            if curr_pit == opp_store:
                continue

            self.state[curr_pit] += 1
            seeds -= 1

        # Cek apakah biji terakhir jatuh di lumbung sendiri (Extra Turn)
        has_extra_turn = (curr_pit == my_store)

        return curr_pit, has_extra_turn


def execute_turn(board: Board, player: int, move: int) -> Tuple[int, int, bool]:
    """
    Fungsi bantuan transisi langkah untuk pemain.
    
    Returns:
        next_player (int): Pemain yang berhak melangkah selanjutnya (0 atau 1).
        last_pit (int): Indeks lubang tempat biji terakhir jatuh.
        has_extra_turn (bool): Status apakah pemain mendapat giliran tambahan.
    """
    last_pit, has_extra_turn = board.sow(player, move)

    if has_extra_turn:
        next_player = player
    else:
        next_player = 1 - player

    return next_player, last_pit, has_extra_turn


if __name__ == "__main__":
    # Pengujian mandiri (Sanity Check)
    b = Board()
    print("--- State Awal Papan ---")
    print("P1 (Atas) :", b.state[8:15][::-1], f"| Lumbung P1 [15]: {b.state[15]}")
    print("P0 (Bawah):", b.state[0:7], f"| Lumbung P0 [7] : {b.state[7]}")

    # Contoh Player 0 melangkah dari lubang 0 (7 biji)
    # Biji akan jatuh ke: 1, 2, 3, 4, 5, 6, 7 (Lumbung P0) -> Harusnya Extra Turn!
    next_p, last_slot, extra = execute_turn(b, PLAYER_0, 0)
    print("\n--- Setelah P0 melangkah dari lubang 0 ---")
    print(f"Biji terakhir jatuh di slot: {last_slot}")
    print(f"Dapat giliran tambahan? {extra}")
    print(f"Giliran berikutnya: Pemain {next_p}")
    print("Lumbung P0 sekarang:", b.state[P0_STORE])