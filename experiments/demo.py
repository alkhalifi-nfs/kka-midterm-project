"""
Demo: tonton dua agen bermain congklak, atau lawan sendiri agen AI.

  python -m experiments.demo                              # alphabeta vs greedy
  python -m experiments.demo --p0 minimax --p1 ga
  python -m experiments.demo --p0 manusia --p1 alphabeta  # Anda melawan AI

Nama agen sama dengan di turnamen: random, greedy, minimax, minimax_h1,
alphabeta, alphabeta_h1, ga, ditambah "manusia" untuk bermain lewat keyboard.

Papan dicetak dari sudut pandang Pemain 0 (baris bawah). Biji ditabur
berlawanan arah jarum jam: lubang Pemain 0 dari kiri ke kanan, lalu lumbung
Pemain 0 (kanan), lalu lubang Pemain 1 dari kanan ke kiri, lalu lumbung Pemain 1 (kiri).
Lubang setiap pemain diberi nomor 1 sampai 7 sesuai arah taburnya.
"""

import argparse
import sys
from typing import Callable, Optional

from experiments import registry
from src.engine.api import (
    P0_PITS, P1_PITS, P0_STORE, P1_STORE, apply_move, get_initial_state, get_legal_moves,
    get_scores, is_terminal,
)

HUMAN = "manusia"
PITS = (P0_PITS, P1_PITS)


def pit_number(index: int) -> int:
    """Indeks papan (0..6 atau 8..14) -> nomor lubang 1..7 milik pemiliknya."""
    return index % 8 + 1


def render(board) -> str:
    b = [int(x) for x in board]
    top = " ".join(f"{b[i]:2d}" for i in reversed(P1_PITS))
    bottom = " ".join(f"{b[i]:2d}" for i in P0_PITS)
    return "\n".join([
        "            nomor:  7  6  5  4  3  2  1",
        f"         Pemain 1: {top}",
        f"  [lumbung P1 {b[P1_STORE]:2d}]                       [lumbung P0 {b[P0_STORE]:2d}]",
        f"         Pemain 0: {bottom}",
        "            nomor:  1  2  3  4  5  6  7",
    ])


def ask_human(state, read: Callable[[str], str] = input) -> int:
    legal = {pit_number(i): i for i in get_legal_moves(state)}
    while True:
        text = read(f"Pilih lubang ({', '.join(str(n) for n in sorted(legal))}): ").strip()
        if text.isdigit() and int(text) in legal:
            return legal[int(text)]
        print("  Lubang tidak valid atau kosong, coba lagi.")


def play(p0: str, p1: str, depth: int, time_limit: Optional[float], quiet: bool = False,
         read: Callable[[str], str] = input, out=sys.stdout) -> tuple:
    names = (p0, p1)
    agents = [None if name == HUMAN else registry.make_agent(name) for name in names]
    for agent in agents:
        if agent is not None and hasattr(agent, "reset"):
            agent.reset(0)

    def say(text=""):
        if not quiet:
            print(text, file=out)

    state = get_initial_state()
    say(render(state.board))
    turn = 0
    while not is_terminal(state):
        player = state.current_player
        if agents[player] is None:
            move = ask_human(state, read)
        else:
            move = agents[player].choose_move(state.copy(), time_limit=time_limit, depth=depth)
        before = int(state.board[P0_STORE if player == 0 else P1_STORE])
        state = apply_move(state, move)
        turn += 1
        gained = int(state.board[P0_STORE if player == 0 else P1_STORE]) - before
        note = " -> giliran tambahan!" if state.current_player == player and not state.is_terminal else ""
        say(f"\nLangkah {turn}: Pemain {player} ({names[player]}) memilih lubang {pit_number(move)}, "
            f"lumbung +{gained}{note}")
        say(render(state.board))

    s0, s1 = get_scores(state)
    result = "SERI" if s0 == s1 else f"Pemain {0 if s0 > s1 else 1} ({names[0 if s0 > s1 else 1]}) MENANG"
    print(f"\nPermainan selesai setelah {turn} langkah. Skor {s0} - {s1}. {result}", file=out)
    return s0, s1, turn


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Tonton atau mainkan congklak melawan agen AI.")
    parser.add_argument("--p0", default="alphabeta", help="agen Pemain 0 (jalan pertama) atau 'manusia'")
    parser.add_argument("--p1", default="greedy", help="agen Pemain 1 atau 'manusia'")
    parser.add_argument("--depth", type=int, default=4, help="kedalaman pencarian agen (default 4)")
    parser.add_argument("--time-limit", type=float, default=0.0,
                        help="batas waktu per langkah dalam detik; 0 = hanya kedalaman")
    parser.add_argument("--quiet", action="store_true", help="hanya tampilkan hasil akhir")
    args = parser.parse_args(argv)
    for name in (args.p0, args.p1):
        if name != HUMAN and name not in registry.AGENT_SPECS:
            raise SystemExit(f"Agen tidak dikenal: {name}. Pilihan: {', '.join(registry.AGENT_SPECS)}, {HUMAN}")
    play(args.p0, args.p1, args.depth, args.time_limit or None, quiet=args.quiet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
