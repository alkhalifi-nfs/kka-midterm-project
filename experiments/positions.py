"""
Pengambilan sampel posisi non-terminal yang reproducible lewat playout acak.

Dipakai untuk uji kebenaran Minimax = Alpha-Beta (Ravy) dan ablation (Pisnur).

  python -m experiments.positions --n 500 --seed 42
  -> results/positions_seed42_n500.json

Setiap posisi memakai RNG sendiri yang diturunkan dari (seed, indeks), jadi
posisi ke-i tidak berubah walau n diubah (n=10 adalah awalan dari n=20).
Cara: tarik jumlah langkah target L seragam di [min_plies, max_plies], mainkan L
langkah acak dari posisi awal; bila game selesai sebelum L, ulangi dengan L baru.
Akibatnya posisi yang lebih dalam sedikit kurang sering muncul, karena game acak
berlangsung rata-rata puluhan langkah.

Format JSON: {"meta": {...}, "positions": [{"board": [16 bilangan],
"current_player": 0|1, "move_count": int}, ...]}.
"""

import argparse
import json
import os
import random
from typing import List, Optional

import numpy as np

from src.engine.api import CongklakState, apply_move, get_initial_state, get_legal_moves, is_terminal

MAX_ATTEMPTS = 10_000


def sample_positions(n: int, seed: int, min_plies: int = 4, max_plies: int = 40) -> List[CongklakState]:
    """n posisi tidak-terminal; move_count tiap posisi = jumlah langkah yang dimainkan."""
    if n < 0 or min_plies < 0 or max_plies < min_plies:
        raise ValueError("Butuh n >= 0 dan 0 <= min_plies <= max_plies.")
    positions = []
    for index in range(n):
        rng = random.Random(f"positions|{seed}|{index}")
        for _ in range(MAX_ATTEMPTS):
            target = rng.randint(min_plies, max_plies)
            state = get_initial_state()
            while state.move_count < target and not is_terminal(state):
                state = apply_move(state, rng.choice(get_legal_moves(state)))
            if state.move_count == target and not is_terminal(state):
                positions.append(state)
                break
        else:
            raise RuntimeError(f"Gagal mendapat posisi non-terminal untuk indeks {index} "
                               f"(min_plies={min_plies}, max_plies={max_plies}).")
    return positions


def positions_to_records(positions: List[CongklakState]) -> List[dict]:
    return [{"board": [int(x) for x in p.board], "current_player": int(p.current_player),
             "move_count": int(p.move_count)} for p in positions]


def save_positions(path: str, positions: List[CongklakState], meta: Optional[dict] = None) -> None:
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write('{"meta": ' + json.dumps(meta or {}, sort_keys=True) + ',\n "positions": [\n')
        records = positions_to_records(positions)
        for i, record in enumerate(records):
            handle.write("  " + json.dumps(record) + ("," if i < len(records) - 1 else "") + "\n")
        handle.write(" ]}\n")


def load_positions(path: str) -> List[CongklakState]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    records = data["positions"] if isinstance(data, dict) else data
    return [CongklakState(board=np.array(r["board"], dtype=np.int32),
                          current_player=int(r["current_player"]),
                          is_terminal=False, move_count=int(r["move_count"])) for r in records]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m experiments.positions",
        description="Membuat sampel posisi non-terminal yang reproducible dan menyimpannya sebagai JSON.",
    )
    parser.add_argument("--n", type=int, default=500, help="jumlah posisi (default 500)")
    parser.add_argument("--seed", type=int, default=42, help="seed (default 42)")
    parser.add_argument("--min-plies", type=int, default=4)
    parser.add_argument("--max-plies", type=int, default=40)
    parser.add_argument("--out", default=None, help="berkas keluaran (default results/positions_seed<seed>_n<n>.json)")
    args = parser.parse_args(argv)

    out = args.out or os.path.join("results", f"positions_seed{args.seed}_n{args.n}.json")
    positions = sample_positions(args.n, args.seed, args.min_plies, args.max_plies)
    save_positions(out, positions, {"n": args.n, "seed": args.seed,
                                    "min_plies": args.min_plies, "max_plies": args.max_plies})
    print(f"{len(positions)} posisi -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
