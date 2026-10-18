"""
Implementasi referensi (oracle) aturan Congklak-Master untuk pengujian.

Ditulis ulang langsung dari teks aturan (docs/rules.md, bagian "Aturan
Permainan"), BUKAN dari src/engine/board.py, memakai list Python biasa tanpa
numpy. Strukturnya sengaja berbeda dari engine: penaburan berjalan di atas
"cincin" 15 slot (semua slot kecuali lumbung lawan), jadi tidak ada penanganan
lompat lumbung secara terpisah.

Ringkasan aturan yang dipakai:
  - Papan 16 slot: 0-6 lubang P0, 7 lumbung P0, 8-14 lubang P1, 15 lumbung P1.
    Lubang seberang dari i adalah 14 - i.
  - Satu langkah: ambil semua biji sebuah lubang sendiri, tabur satu per satu ke
    indeks naik; lumbung lawan dilompati. Biji terakhir jatuh di:
      a) lumbung sendiri            -> pemain yang sama jalan lagi;
      b) lubang yang sebelumnya berisi (sisi mana pun) -> ambil seluruh isinya
         (termasuk biji terakhir) dan tabur lagi mulai lubang berikutnya (relay);
      c) lubang sendiri yang sebelumnya kosong -> tembak bila seberang berisi;
         giliran pindah;
      d) lubang lawan yang sebelumnya kosong -> berhenti, giliran pindah.
  - Maksimal 200 putaran tabur per giliran (putaran pertama dihitung); bila
    putaran terakhir berakhir di lubang berisi, giliran pindah tanpa tembak.
  - Setelah langkah, bila pemain yang berhak jalan tidak punya lubang berisi,
    game selesai dan sisa biji di lubang kecil disapu ke lumbung pemilik sisi.
  - Game dipaksa selesai bila jumlah langkah mencapai 300 (sisa biji disapu).
"""

from typing import List, NamedTuple, Tuple

MAX_ROUNDS = 200
MAX_MOVES = 300


def own_pits(player: int) -> List[int]:
    return list(range(0, 7)) if player == 0 else list(range(8, 15))


def store_of(player: int) -> int:
    return 7 if player == 0 else 15


def initial_board() -> List[int]:
    board = [7] * 16
    board[7] = 0
    board[15] = 0
    return board


def legal_moves(board: List[int], player: int) -> List[int]:
    return [i for i in own_pits(player) if board[i] > 0]


def _ring(player: int) -> List[int]:
    """Urutan slot yang dilalui penaburan pemain: indeks naik tanpa lumbung lawan."""
    skip = store_of(1 - player)
    return [i for i in range(16) if i != skip]


class MoveResult(NamedTuple):
    board: List[int]
    next_player: int
    rounds: int        # jumlah putaran tabur yang dijalankan
    extra_turn: bool
    captured: int      # jumlah biji yang masuk lumbung lewat tembak (0 bila tidak ada)


def play_move(board: List[int], player: int, pit: int, max_rounds: int = MAX_ROUNDS) -> MoveResult:
    """Satu langkah penuh menurut aturan (tanpa pemeriksaan akhir game)."""
    assert pit in own_pits(player) and board[pit] > 0, "langkah ilegal"
    b = list(board)
    ring = _ring(player)
    start = pit
    rounds = 0
    while True:
        rounds += 1
        seeds = b[start]
        b[start] = 0
        pos = ring.index(start)
        for _ in range(seeds):
            pos = (pos + 1) % len(ring)
            b[ring[pos]] += 1
        last = ring[pos]

        if last == store_of(player):                 # (a) giliran tambahan
            return MoveResult(b, player, rounds, True, 0)

        seeds_before_drop = b[last] - 1
        if seeds_before_drop > 0:                    # (b) lubang sudah berisi
            if rounds >= max_rounds:                 # pengaman: pindah giliran tanpa tembak
                return MoveResult(b, 1 - player, rounds, False, 0)
            start = last                             # menabur lanjutan dari lubang itu
            continue

        captured = 0                                 # lubang tadinya kosong
        if last in own_pits(player):                 # (c) sisi sendiri
            opposite = 14 - last
            if b[opposite] > 0:
                captured = b[last] + b[opposite]
                b[store_of(player)] += captured
                b[last] = 0
                b[opposite] = 0
        # (d) sisi lawan: tidak terjadi apa-apa
        return MoveResult(b, 1 - player, rounds, False, captured)


def apply(board: List[int], player: int, move_count: int, pit: int,
          max_rounds: int = MAX_ROUNDS) -> Tuple[MoveResult, bool, int]:
    """
    Satu langkah + pemeriksaan akhir game.
    Returns: (hasil_langkah dengan papan sudah disapu bila terminal, terminal, move_count baru)
    """
    res = play_move(board, player, pit, max_rounds)
    b = res.board
    move_count += 1
    terminal = not legal_moves(b, res.next_player)
    if not terminal and move_count >= MAX_MOVES:
        terminal = True
    if terminal:
        for p in (0, 1):
            for i in own_pits(p):
                b[store_of(p)] += b[i]
                b[i] = 0
    return res, terminal, move_count
