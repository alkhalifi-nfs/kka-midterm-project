"""
Model 2: Alpha-Beta Pruning + move ordering + transposition table (Zobrist)
+ iterative deepening (laporan Bab 2.3).

Ringkasan perilaku:
  - Peran MAX/MIN menurut PLAYER(s), seperti Minimax (giliran tambahan:
    MAX -> MAX). Setiap langkah mengurangi sisa kedalaman satu ply.
  - Move ordering (Tabel 2): langkah dari TT/iterasi sebelumnya, lalu langkah
    giliran tambahan, lalu tembak (menurun menurut biji yang ditangkap), lalu
    sisanya (menurun menurut isi lubang asal). Seri: indeks lubang menaik.
  - Transposition table: kunci Zobrist 64-bit, entri (kunci, kedalaman, nilai,
    jenis batas, langkah terbaik), 2^tt_bits slot; saat benturan indeks entri
    yang lebih dalam dipertahankan. Entri dipakai bila kedalamannya >= sisa
    kedalaman simpul.
  - Iterative deepening: kedalaman 1, 2, ... hingga batas kedalaman atau
    batas waktu habis; iterasi yang terpotong waktu dibuang. Berhenti lebih
    awal bila satu iterasi sudah menelusuri pohon sampai akhir permainan.

Pemutus seri di akar sama dengan Minimax (lubang berindeks terkecil di antara
langkah bernilai sama), walaupun urutan ekspansinya diubah oleh move ordering.
Tanpa TT, nilai dan langkah di akar identik dengan Minimax pada kedalaman yang
sama (diuji di tests/test_alphabeta.py). Dengan TT, nilai dari entri yang lebih
dalam boleh dipakai, sehingga hasilnya dapat berbeda dari Minimax berkedalaman
tetap; inilah alasan uji kesamaan Bab 3.2 dijalankan dengan TT dimatikan.
"""

import math
import random
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple, Union

import src.engine.api as api
from src.agents.evaluation import HEURISTICS, evaluate
from src.engine.api import CongklakState, get_legal_moves, is_terminal
from src.engine.board import Board

DEFAULT_DEPTH = 4
MAX_ID_DEPTH = 64          # batas iterative deepening bila hanya dibatasi waktu
TIME_CHECK_EVERY = 256     # periksa jam setiap sekian simpul

EXACT, LOWER, UPPER = 0, 1, 2

Evaluator = Callable[[CongklakState, int], float]


# --- Zobrist hashing (Bab 2.3.3) ------------------------------------------------------

N_SLOTS = 16
MAX_SEEDS = 98


class Zobrist:
    """Tabel Z[i][k] (16 slot x 0..98 biji) dan Z_turn, bilangan acak 64-bit dari seed tetap."""

    def __init__(self, seed: int = 2026):
        rng = random.Random(seed)
        self.table = [[rng.getrandbits(64) for _ in range(MAX_SEEDS + 1)] for _ in range(N_SLOTS)]
        self.turn = rng.getrandbits(64)

    def hash(self, board: List[int], player: int) -> int:
        h = self.turn if player == 1 else 0
        for i, k in enumerate(board):
            h ^= self.table[i][k]
        return h

    def update(self, h: int, old: List[int], new: List[int], old_player: int, new_player: int) -> int:
        """Pembaruan inkremental: hanya slot yang berubah (dan giliran) yang di-XOR."""
        table = self.table
        for i in range(N_SLOTS):
            if old[i] != new[i]:
                h ^= table[i][old[i]] ^ table[i][new[i]]
        if old_player != new_player:
            h ^= self.turn
        return h


# --- Ekspansi langkah dengan info untuk move ordering ---------------------------------

class _RecordingBoard(Board):
    """Board yang mencatat jumlah biji hasil tembak pada langkah terakhir."""
    captured = 0

    def apply_capture(self, player: int, last_pit: int) -> int:
        self.captured = super().apply_capture(player, last_pit)
        return self.captured


def expand(state: CongklakState, move: int) -> Tuple[CongklakState, bool, int]:
    """
    Sama persis dengan api.apply_move (termasuk batas MAX_GAME_MOVES), ditambah
    (giliran_tambahan, biji_ditembak) untuk move ordering. Kesamaannya dengan
    apply_move diuji di tests/test_alphabeta.py.
    """
    if state.is_terminal:
        raise ValueError("State sudah terminal, tidak ada langkah yang bisa dijalankan.")
    b = _RecordingBoard(state.board)
    next_player, extra_turn, terminal = b.step(state.current_player, move)
    move_count = state.move_count + 1
    if not terminal and move_count >= api.MAX_GAME_MOVES:
        b.sweep_remaining_seeds()
        terminal = True
    child = CongklakState(board=b.state, current_player=next_player,
                          is_terminal=terminal, move_count=move_count)
    return child, extra_turn, b.captured


# --- Agen -----------------------------------------------------------------------------

@dataclass
class SearchStats:
    """Metrik pemanggilan choose_move terakhir (nama atribut mengikuti kontrak agen)."""
    nodes: int = 0          # state yang dikunjungi, seluruh iterasi (termasuk yang dibuang)
    cutoffs: int = 0        # pemangkasan alpha/beta di dalam loop anak
    depth_reached: int = 0  # kedalaman iterasi terakhir yang selesai
    elapsed: float = 0.0    # detik
    tt_hits: int = 0        # entri TT yang cukup dalam dan langsung mengakhiri simpul
    tt_entries: int = 0     # isi TT setelah pencarian (indikator memori)


class _Timeout(Exception):
    pass


class AlphaBetaAgent:
    """
    Model 2. `heuristic` adalah "h1", "h2", atau fungsi evaluator(state, me) -> float
    (dipakai Model 3 untuk bobot hasil GA). Komponen bisa dimatikan untuk ablasi
    Bab 3.3: ordering, use_tt, iterative.

    Kedalaman dan waktu:
      - choose_move(depth=d): batas kedalaman d (default self.depth). depth <= 0
        atau None bersama time_limit berarti hanya dibatasi waktu.
      - time_limit (detik): iterative deepening berhenti saat waktu habis; iterasi
        kedalaman 1 selalu diselesaikan agar selalu ada langkah legal.
    """

    def __init__(self, depth: int = DEFAULT_DEPTH, heuristic: Union[str, Evaluator] = "h2",
                 ordering: bool = True, use_tt: bool = True, iterative: bool = True,
                 tt_bits: int = 20, name: Optional[str] = None):
        if depth < 1:
            raise ValueError(f"Kedalaman minimal 1, bukan {depth}.")
        if callable(heuristic):
            self._evaluate = heuristic
        elif heuristic in HEURISTICS:
            self._evaluate = lambda s, me, h=heuristic: evaluate(s, me, h)
        else:
            raise ValueError(f"Heuristik tidak dikenal: {heuristic!r} (pilihan: {', '.join(HEURISTICS)}).")
        self.depth = depth
        self.heuristic = heuristic
        self.ordering = ordering
        self.use_tt = use_tt
        self.iterative = iterative
        self.tt_size = 1 << tt_bits
        self.name = name or ("alphabeta" if heuristic == "h2" else f"alphabeta_{heuristic}")
        self.zobrist = Zobrist()
        self.metrics = SearchStats()
        self._tt: Dict[int, tuple] = {}
        self._tt_me: Optional[int] = None
        self._me = 0
        self._deadline: Optional[float] = None
        self._hit_horizon = False

    def reset(self, seed=None) -> None:
        """Mengosongkan TT di awal game. Agen deterministik; seed diabaikan."""
        self._tt.clear()
        self._tt_me = None
        self.metrics = SearchStats()

    # --- Antarmuka ---------------------------------------------------------------------

    def choose_move(self, state: CongklakState, time_limit=None, depth=None) -> int:
        started = time.perf_counter()
        max_depth = self.depth if depth is None else int(depth)
        if max_depth <= 0:
            if not time_limit:
                raise ValueError("Butuh depth >= 1 atau time_limit.")
            max_depth = MAX_ID_DEPTH
        self._deadline = started + time_limit if time_limit else None

        _, move = self.search(state, max_depth)
        self.metrics.elapsed = time.perf_counter() - started
        self._deadline = None
        return move

    def search(self, state: CongklakState, depth: int) -> Tuple[float, int]:
        """
        (nilai akar, langkah terbaik) dari sudut pandang pemain yang sedang jalan,
        dari iterasi terdalam yang selesai. Mengisi self.metrics kecuali `elapsed`.
        """
        if depth < 1:
            raise ValueError(f"Kedalaman minimal 1, bukan {depth}.")
        if not get_legal_moves(state):
            raise ValueError("Tidak ada langkah legal pada state ini.")

        self._me = state.current_player
        if self._tt_me != self._me:  # nilai di TT dari sudut pandang pemain agen
            self._tt.clear()
            self._tt_me = self._me
        self.metrics = SearchStats()

        root_hash = self.zobrist.hash(state.board.tolist(), state.current_player)
        result: Optional[Tuple[float, int]] = None
        pv_move: Optional[int] = None
        for d in (range(1, depth + 1) if self.iterative else [depth]):
            self._hit_horizon = False
            try:
                result = self._root(state, root_hash, d, pv_move)
            except _Timeout:
                break
            pv_move = result[1]
            self.metrics.depth_reached = d
            if not self._hit_horizon:
                break  # seluruh pohon sampai akhir permainan sudah ditelusuri
            if self._deadline is not None and time.perf_counter() >= self._deadline:
                break

        self.metrics.tt_entries = len(self._tt)
        return result

    # --- Pencarian ---------------------------------------------------------------------

    def _children(self, state: CongklakState, tt_move: Optional[int]):
        """Daftar (langkah, anak), diurutkan menurut Tabel 2 bila ordering aktif."""
        moves = get_legal_moves(state)
        if not self.ordering:
            return [(a, expand(state, a)[0]) for a in moves]

        board = state.board
        keyed = []
        for a in moves:
            child, extra, captured = expand(state, a)
            if a == tt_move:
                key = (0, 0)
            elif extra:
                key = (1, 0)
            elif captured:
                key = (2, -captured)
            else:
                key = (3, -int(board[a]))
            keyed.append((key, a, child))
        keyed.sort(key=lambda item: (item[0], item[1]))  # seri -> indeks menaik
        return [(a, child) for _, a, child in keyed]

    def _child_hash(self, h: int, state: CongklakState, child: CongklakState) -> int:
        return self.zobrist.update(h, state.board.tolist(), child.board.tolist(),
                                   state.current_player, child.current_player)

    def _tick(self) -> None:
        self.metrics.nodes += 1
        if (self._deadline is not None and self.metrics.depth_reached >= 1
                and self.metrics.nodes % TIME_CHECK_EVERY == 0
                and time.perf_counter() >= self._deadline):
            raise _Timeout

    def _root(self, state: CongklakState, h: int, depth: int,
              pv_move: Optional[int]) -> Tuple[float, int]:
        """
        Akar selalu simpul MAX. Langkah berindeks lebih kecil dari langkah terbaik
        sementara dicari dengan alpha tepat di bawah nilai terbaik, sehingga
        nilai yang sama terdeteksi dan pemutus seri sama dengan Minimax.
        """
        self._tick()
        tt_move = pv_move
        if tt_move is None and self.use_tt:
            entry = self._tt.get(h & (self.tt_size - 1))
            if entry is not None and entry[0] == h:
                tt_move = entry[4]

        best_v, best_a = -math.inf, None
        for a, child in self._children(state, tt_move):
            if best_a is None:
                alpha = -math.inf
            elif a < best_a:
                alpha = math.nextafter(best_v, -math.inf)
            else:
                alpha = best_v
            v = self._alphabeta(child, self._child_hash(h, state, child), depth - 1, alpha, math.inf)
            if v > best_v or (v == best_v and a < best_a):
                best_v, best_a = v, a

        self._store(h, depth, best_v, EXACT, best_a)
        return best_v, best_a

    def _alphabeta(self, state: CongklakState, h: int, depth: int, alpha: float, beta: float) -> float:
        """Alpha-Beta fail-soft dengan TT (Pseudocode Alpha-Beta Bab 2.3.1 + 2.3.4)."""
        self._tick()
        if is_terminal(state):
            return self._evaluate(state, self._me)
        if depth == 0:
            self._hit_horizon = True
            return self._evaluate(state, self._me)

        alpha0, beta0 = alpha, beta
        tt_move = None
        if self.use_tt:
            entry = self._tt.get(h & (self.tt_size - 1))
            if entry is not None and entry[0] == h:
                _, e_depth, e_value, e_flag, tt_move = entry
                if e_depth >= depth:
                    self._hit_horizon = True  # konservatif: subpohon entri tidak diketahui
                    if e_flag == EXACT:
                        self.metrics.tt_hits += 1
                        return e_value
                    if e_flag == LOWER:
                        alpha = max(alpha, e_value)
                    else:
                        beta = min(beta, e_value)
                    if alpha >= beta:
                        self.metrics.tt_hits += 1
                        return e_value

        maximizing = state.current_player == self._me
        best_v = -math.inf if maximizing else math.inf
        best_a = None
        for a, child in self._children(state, tt_move):
            v = self._alphabeta(child, self._child_hash(h, state, child), depth - 1, alpha, beta)
            if maximizing:
                if v > best_v:
                    best_v, best_a = v, a
                alpha = max(alpha, best_v)
            else:
                if v < best_v:
                    best_v, best_a = v, a
                beta = min(beta, best_v)
            if alpha >= beta:
                self.metrics.cutoffs += 1
                break

        if best_v <= alpha0:
            flag = UPPER
        elif best_v >= beta0:
            flag = LOWER
        else:
            flag = EXACT
        self._store(h, depth, best_v, flag, best_a)
        return best_v

    def _store(self, h: int, depth: int, value: float, flag: int, move: Optional[int]) -> None:
        if not self.use_tt:
            return
        index = h & (self.tt_size - 1)
        old = self._tt.get(index)
        if old is not None and old[0] != h and old[1] > depth:
            return  # benturan indeks: pertahankan entri yang lebih dalam
        self._tt[index] = (h, depth, value, flag, move)


class AlphaBetaH1Agent(AlphaBetaAgent):
    """Model 2 dengan H1."""

    def __init__(self, depth: int = DEFAULT_DEPTH):
        super().__init__(depth=depth, heuristic="h1")
