"""
Fungsi evaluasi H1 dan H2 (laporan Bab 2.2.3 dan 2.2.4) beserta skor terminal.

Semua nilai dihitung dari sudut pandang pemain `me` (pemain agen di akar pohon),
sehingga berlaku antisimetri: evaluate(s, me) == -evaluate(s, 1 - me).

    H1(s) = lumbung(me) - lumbung(lawan)
    H2(s) = 1,0*f1 + 0,3*f2 + 0,5*f3 + 0,2*f4      (Tabel 1 laporan)

Pada state terminal, skor = TERMINAL_WEIGHT * selisih lumbung akhir
(Pseudocode SKOR), agar hasil akhir permainan selalu lebih menentukan daripada
nilai heuristik yang hanya berkisar puluhan.
"""

from typing import Sequence, Tuple

from src.engine.api import (
    CongklakState, P0_PITS, P0_STORE, P1_PITS, P1_STORE, PLAYER_0, PLAYER_1, is_terminal,
)

TERMINAL_WEIGHT = 1000

# Bobot manual H2 (Tabel 1 laporan); baseline pembanding bobot hasil GA.
H2_WEIGHTS: Tuple[float, float, float, float] = (1.0, 0.3, 0.5, 0.2)

HEURISTICS = ("h1", "h2")

_PITS = (P0_PITS, P1_PITS)
_STORES = (P0_STORE, P1_STORE)


def _check_player(me: int) -> None:
    if me not in (PLAYER_0, PLAYER_1):
        raise ValueError(f"Pemain harus 0 atau 1, bukan {me!r}.")


def terminal_score(state: CongklakState, me: int) -> int:
    """
    TERMINAL_WEIGHT * selisih lumbung akhir dari sudut pandang `me`.
    Sisa biji di lubang ikut dihitung ke pemilik sisinya (setara sweep), jadi
    hasilnya benar baik state sudah disapu engine maupun belum.
    """
    _check_player(me)
    b = state.board.tolist()
    final = [b[_STORES[p]] + sum(b[i] for i in _PITS[p]) for p in (PLAYER_0, PLAYER_1)]
    return TERMINAL_WEIGHT * (final[me] - final[1 - me])


def h1(state: CongklakState, me: int) -> int:
    """H1: selisih isi lumbung, b[Store(me)] - b[Store(lawan)]."""
    _check_player(me)
    b = state.board
    return int(b[_STORES[me]]) - int(b[_STORES[1 - me]])


def _side_features(b: Sequence[int], p: int) -> Tuple[int, int, int, int]:
    """Nilai mentah keempat fitur untuk satu sisi (belum dikurangi lawan)."""
    pits = _PITS[p]
    store = _STORES[p]
    # f3: lubang yang isinya tepat sama dengan jaraknya ke lumbung sendiri,
    # sehingga putaran tabur pertama berakhir di lumbung (giliran tambahan).
    extra_turns = sum(1 for i in pits if b[i] == store - i)
    # f4: biji lawan di seberang lubang kosong sendiri (peluang tembak, optimistis).
    capturable = sum(b[14 - i] for i in pits if b[i] == 0)
    return b[store], sum(b[i] for i in pits), extra_turns, capturable


def h2_features(state: CongklakState, me: int) -> Tuple[int, int, int, int]:
    """
    (f1, f2, f3, f4), masing-masing berupa nilai agen dikurangi nilai lawan:
      f1 selisih lumbung, f2 selisih biji di sisi, f3 peluang giliran tambahan,
      f4 peluang tembak.
    """
    _check_player(me)
    b = state.board.tolist()
    mine = _side_features(b, me)
    theirs = _side_features(b, 1 - me)
    return tuple(m - t for m, t in zip(mine, theirs))


def h2(state: CongklakState, me: int, weights: Sequence[float] = H2_WEIGHTS) -> float:
    """H2: kombinasi linear berbobot dari h2_features."""
    if len(weights) != 4:
        raise ValueError(f"H2 butuh 4 bobot, bukan {len(weights)}.")
    return float(sum(w * f for w, f in zip(weights, h2_features(state, me))))


def evaluate(state: CongklakState, me: int, heuristic: str = "h2") -> float:
    """
    SKOR(s) pada Pseudocode SKOR: skor terminal bila permainan selesai,
    selain itu H1 atau H2 dari sudut pandang `me`.
    """
    if is_terminal(state):
        return float(terminal_score(state, me))
    if heuristic == "h1":
        return float(h1(state, me))
    if heuristic == "h2":
        return h2(state, me)
    raise ValueError(f"Heuristik tidak dikenal: {heuristic!r} (pilihan: {', '.join(HEURISTICS)}).")


# --- Fungsi evaluasi 6 fitur untuk Model 3 (laporan Bab 2.4.1) -----------------------------

GA_FEATURES = ("f1 selisih lumbung", "f2 selisih biji di sisi", "f3 selisih peluang giliran tambahan",
               "f4 peluang tembak agen", "f5 ancaman tembak lawan", "f6 selisih lubang aktif")

# H2 sebagai titik di ruang 6 fitur: f4_H2 = f4 - f5 dan f6 tidak dipakai.
# Karena itu bobot hasil GA dapat dibandingkan langsung dengan bobot manual H2 (RQ2).
H2_AS_GA_WEIGHTS: Tuple[float, ...] = (1.0, 0.3, 0.5, 0.2, -0.2, 0.0)


def ga_features(state: CongklakState, me: int) -> Tuple[int, int, int, int, int, int]:
    """
    (f1, ..., f6) dari sudut pandang `me`:
      f1, f2, f3 sama dengan H2 (selisih agen - lawan);
      f4 biji lawan di seberang lubang kosong agen (peluang tembak agen, agresif);
      f5 biji agen di seberang lubang kosong lawan (ancaman tembak lawan, defensif);
      f6 selisih jumlah lubang berisi (mobilitas).
    """
    _check_player(me)
    b = state.board.tolist()
    mine = _side_features(b, me)
    theirs = _side_features(b, 1 - me)
    active_mine = sum(1 for i in _PITS[me] if b[i] > 0)
    active_theirs = sum(1 for i in _PITS[1 - me] if b[i] > 0)
    return (mine[0] - theirs[0], mine[1] - theirs[1], mine[2] - theirs[2],
            mine[3], theirs[3], active_mine - active_theirs)


def weighted_evaluator(weights: Sequence[float]):
    """Evaluator(state, me) untuk Alpha-Beta: skor terminal, selain itu sum(w_k * f_k)."""
    weights = tuple(float(w) for w in weights)
    if len(weights) != len(GA_FEATURES):
        raise ValueError(f"Butuh {len(GA_FEATURES)} bobot, bukan {len(weights)}.")

    def evaluator(state: CongklakState, me: int) -> float:
        if is_terminal(state):
            return float(terminal_score(state, me))
        return float(sum(w * f for w, f in zip(weights, ga_features(state, me))))

    return evaluator
