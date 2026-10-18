"""
Logika Papan Congklak (Engine v2).
Mencakup: penaburan (sowing), giliran tambahan (extra-turn), menabur lanjutan
(relay), tembak (capture), pengaman putaran tabur, dan kondisi akhir (sweep).
Aturan lengkap ada di docs/rules.md.
"""

from typing import List, Optional, Tuple
import numpy as np

PLAYER_0 = 0
PLAYER_1 = 1

P0_PITS = list(range(0, 7))      # 0..6
P0_STORE = 7
P1_PITS = list(range(8, 15))     # 8..14
P1_STORE = 15

TOTAL_SLOTS = 16
SEEDS_PER_PIT = 7

# Pengaman: jumlah maksimum putaran tabur dalam satu giliran (putaran pertama
# ikut dihitung). Sengaja berupa konstanta tingkat modul agar bisa di-monkeypatch
# di tes; step() membacanya saat dipanggil.
MAX_SOW_ROUNDS = 200

# Irisan array untuk lubang kecil tiap pemain (dipakai pemeriksaan cepat).
_PIT_SLICES = (slice(0, 7), slice(8, 15))


class Board:
    def __init__(self, state: Optional[np.ndarray] = None, copy: bool = True):
        """
        Membuat papan. Tanpa `state` berarti posisi awal (7 biji per lubang kecil).
        Dengan `state`, array disalin secara default; `copy=False` hanya membungkus
        array tanpa menyalin (untuk pembacaan saja, jangan dipakai untuk step/sow
        pada array milik pihak lain).
        """
        if state is None:
            self.state = np.zeros(TOTAL_SLOTS, dtype=np.int32)
            for pit in P0_PITS + P1_PITS:
                self.state[pit] = SEEDS_PER_PIT
        elif copy:
            self.state = np.array(state, dtype=np.int32)
        else:
            self.state = np.asarray(state, dtype=np.int32)

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

    def has_valid_moves(self, player: int) -> bool:
        """True bila pemain punya minimal satu lubang kecil berisi (tanpa membuat daftar)."""
        return bool(self.state[_PIT_SLICES[player]].any())

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

    def _sow_from(self, player: int, pit: int) -> Tuple[int, bool]:
        """
        Primitif satu putaran tabur: ambil semua biji di `pit`, tabur satu per satu
        ke indeks naik (modulo 16) sambil melompati lumbung lawan.

        TIDAK memeriksa kepemilikan lubang maupun apakah lubang kosong, karena
        menabur lanjutan boleh berawal dari lubang di sisi lawan. Pemanggil yang
        menerima masukan dari luar harus memakai `sow()`.

        Returns:
            (lubang_terakhir, jatuh_di_lumbung_sendiri)
        """
        state = self.state
        seeds = int(state[pit])
        state[pit] = 0
        curr_pit = pit
        opp_store = self.get_opponent_store(player)
        my_store = self.get_player_store(player)

        while seeds > 0:
            curr_pit = (curr_pit + 1) % TOTAL_SLOTS
            if curr_pit == opp_store:
                continue
            state[curr_pit] += 1
            seeds -= 1

        return curr_pit, curr_pit == my_store

    def sow(self, player: int, start_pit: int) -> Tuple[int, bool]:
        """
        Satu putaran tabur dari start_pit (melewati lumbung lawan), dengan validasi:
        lubang harus milik pemain dan tidak kosong, jika tidak ValueError.
        """
        my_pits = self.get_player_pits(player)
        if start_pit not in my_pits:
            raise ValueError(f"Lubang {start_pit} bukan milik Pemain {player}.")

        if self.state[start_pit] <= 0:
            raise ValueError(f"Lubang {start_pit} kosong, tidak bisa melangkah.")

        return self._sow_from(player, start_pit)

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
        Menjalankan 1 langkah penuh:
          1. Putaran tabur pertama dari `move` (divalidasi oleh sow()).
          2. Selama biji terakhir jatuh di lubang yang sebelumnya sudah berisi
             (sisi mana pun): MENABUR LANJUTAN dari lubang itu, maksimal
             MAX_SOW_ROUNDS putaran per giliran.
          3. Biji terakhir di lumbung sendiri -> giliran tambahan. Selain itu cek
             Tembak, lalu giliran pindah ke lawan.
          4. Terminal bila pemain yang berhak jalan berikutnya tidak punya lubang
             berisi; sisa biji disapu ke lumbung pemilik sisinya.
        Bila putaran terakhir (ke-MAX_SOW_ROUNDS) berakhir di lubang berisi,
        giliran langsung pindah tanpa tembak.

        Returns:
            next_player (int): Pemain berikutnya.
            has_extra_turn (bool): Apakah mendapat giliran tambahan.
            is_terminal (bool): Apakah permainan berakhir setelah langkah ini.
        """
        last_pit, has_extra_turn = self.sow(player, move)
        rounds = 1

        # state[last_pit] > 1 berarti lubang itu sudah berisi sebelum biji terakhir jatuh.
        while (not has_extra_turn
               and self.state[last_pit] > 1
               and rounds < MAX_SOW_ROUNDS):
            last_pit, has_extra_turn = self._sow_from(player, last_pit)
            rounds += 1

        if has_extra_turn:
            next_player = player
        else:
            # Tembak hanya terjadi bila lubang terakhir tadinya kosong (isi == 1);
            # pada putaran terakhir yang berakhir di lubang berisi, apply_capture tidak berlaku.
            self.apply_capture(player, last_pit)
            next_player = 1 - player

        is_terminal = False
        if not self.has_valid_moves(next_player):
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
