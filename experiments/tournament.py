"""
Runner turnamen round-robin Congklak-Master.

Contoh:
  python -m experiments.tournament --agents random,greedy --openings 100 \\
      --seeds 42,123,2026 --opening-plies 4 --depth 4 --time-limit 0 \\
      --workers 8 --out results/tournament_uji.csv --resume

Desain (alasan tiap keputusan):
  * Agen deterministik akan memainkan game yang sama berulang. Karena itu tiap
    game dimulai dengan `opening-plies` langkah ACAK yang diturunkan HANYA dari
    (seed, opening_id). Pembukaan yang sama dipakai kedua game dalam sebuah
    pasangan dan oleh semua pasangan agen.
  * Tiap pembukaan dimainkan DUA kali dengan sisi ditukar (game berpasangan):
    keunggulan P0 besar (pembuka lubang 1-6 langsung +10), jadi penukaran sisi
    wajib. Jumlah game per pasangan agen = openings x 2 x jumlah seed.
  * Round-robin atas semua pasangan unik (tanpa self-play).
  * Reproducible: seed acak tiap agen diturunkan dari (seed, opening_id, sisi,
    nama agen) dengan hash stabil (bukan hash() Python yang berubah per proses).
  * CSV ditulis bertahap (flush per game); --resume melewati game yang sudah ada
    (kunci: seed, opening_id, agent_p0, agent_p1).
  * Agen yang mengembalikan langkah ilegal atau melempar exception dicatat
    sebagai KALAH (forfeit) disertai peringatan; run tidak berhenti.
  * Runner tidak menegakkan time_limit: nilainya hanya diteruskan ke agen.

Kolom CSV: seed, opening_id, agent_p0, agent_p1, winner (nama atau "draw"),
score_p0, score_p1, moves (semua langkah termasuk pembukaan), hit_move_cap
(1 bila move_count akhir >= 300), forfeit (nama agen yang kalah forfeit),
error, opening_plies, depth, time_limit (parameter run), lalu per sisi (p0/p1):
decisions (jumlah pemanggilan choose_move), time (detik dinding yang diukur
runner), serta nodes, cutoffs, depth_sum, elapsed yang dijumlahkan dari
`agent.metrics` (kosong bila agen tidak punya metrics).
"""

import argparse
import csv
import hashlib
import itertools
import multiprocessing
import os
import random
import sys
import time
from typing import Dict, Iterable, List, NamedTuple, Optional, Set, Tuple

from experiments import registry
from src.engine.api import (
    CongklakState, MAX_GAME_MOVES, apply_move, get_initial_state, get_legal_moves,
    get_scores, get_winner, is_terminal,
)

COLUMNS = [
    "seed", "opening_id", "agent_p0", "agent_p1", "winner", "score_p0", "score_p1",
    "moves", "hit_move_cap", "forfeit", "error", "opening_plies", "depth", "time_limit",
    "decisions_p0", "decisions_p1", "time_p0", "time_p1",
    "nodes_p0", "nodes_p1", "cutoffs_p0", "cutoffs_p1",
    "depth_sum_p0", "depth_sum_p1", "elapsed_p0", "elapsed_p1",
]

# kunci metrik -> nama atribut yang dikenali pada agent.metrics (urut prioritas)
_METRIC_NAMES = {
    "nodes": ("nodes", "nodes_expanded"),
    "cutoffs": ("cutoffs",),
    "depth": ("depth_reached", "max_depth_reached"),
    "elapsed": ("elapsed", "execution_time_sec"),
}


class GameTask(NamedTuple):
    seed: int
    opening_id: int
    spec_p0: str
    spec_p1: str
    opening_plies: int
    depth: Optional[int]
    time_limit: Optional[float]


# --- Reproducibility -----------------------------------------------------------

def make_opening(seed: int, opening_id: int, plies: int) -> CongklakState:
    """
    Posisi setelah `plies` langkah acak, diturunkan hanya dari (seed, opening_id).
    Bila game selesai lebih awal, pembukaan berhenti di posisi terminal itu.
    """
    rng = random.Random(f"opening|{seed}|{opening_id}")
    state = get_initial_state()
    for _ in range(plies):
        if is_terminal(state):
            break
        state = apply_move(state, rng.choice(get_legal_moves(state)))
    return state


def agent_seed(seed: int, opening_id: int, side: int, name: str) -> int:
    """Seed untuk agent.reset(), stabil lintas proses dan lintas mesin."""
    digest = hashlib.sha256(f"agent|{seed}|{opening_id}|{side}|{name}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


# --- Satu game -----------------------------------------------------------------

def _read_metrics(agent) -> Optional[Dict[str, float]]:
    metrics = getattr(agent, "metrics", None)
    if metrics is None:
        return None
    out = {}
    for key, names in _METRIC_NAMES.items():
        for attr in names:
            value = metrics.get(attr) if isinstance(metrics, dict) else getattr(metrics, attr, None)
            if value is not None:
                try:
                    out[key] = float(value)
                except (TypeError, ValueError):
                    pass
                break
    return out or None


class _SeatStats:
    """Akumulator per sisi: jumlah keputusan, waktu dinding, dan jumlah metrik."""

    def __init__(self):
        self.decisions = 0
        self.time = 0.0
        self.sums: Dict[str, Optional[float]] = {key: None for key in _METRIC_NAMES}

    def add_metrics(self, metrics: Optional[Dict[str, float]]) -> None:
        for key, value in (metrics or {}).items():
            self.sums[key] = (self.sums[key] or 0.0) + value


def _fmt_number(value: Optional[float]) -> object:
    if value is None:
        return ""
    return int(value) if float(value).is_integer() else round(value, 6)


def _param_text(value) -> str:
    return "0" if value is None else f"{value:g}"


def play_game(task: GameTask) -> Dict[str, object]:
    """Memainkan satu game dan mengembalikan satu baris CSV (dict menurut COLUMNS)."""
    seed, opening_id = task.seed, task.opening_id
    names = (registry.agent_name(task.spec_p0), registry.agent_name(task.spec_p1))
    stats = (_SeatStats(), _SeatStats())
    forfeit_seat: Optional[int] = None
    error = ""

    state = make_opening(seed, opening_id, task.opening_plies)

    agents = [None, None]
    for seat, spec in enumerate((task.spec_p0, task.spec_p1)):
        try:
            agents[seat] = registry.make_agent(spec)
            reset = getattr(agents[seat], "reset", None)
            if callable(reset):
                reset(agent_seed(seed, opening_id, seat, names[seat]))
        except Exception as exc:  # noqa: BLE001 - kegagalan agen apa pun berarti kalah
            forfeit_seat, error = seat, f"init_exception:{type(exc).__name__}"
            registry.warn(f"{names[seat]} gagal dibuat ({type(exc).__name__}: {exc}); "
                          f"game seed={seed} opening={opening_id} dicatat kalah")
            break

    while forfeit_seat is None and not is_terminal(state):
        seat = state.current_player
        legal = get_legal_moves(state)
        started = time.perf_counter()
        try:
            move = agents[seat].choose_move(state.copy(), time_limit=task.time_limit, depth=task.depth)
        except Exception as exc:  # noqa: BLE001
            forfeit_seat, error = seat, f"exception:{type(exc).__name__}"
            registry.warn(f"{names[seat]} melempar {type(exc).__name__}: {exc}; "
                          f"game seed={seed} opening={opening_id} dicatat kalah")
            break
        stats[seat].time += time.perf_counter() - started
        stats[seat].decisions += 1

        try:
            move = int(move)
        except (TypeError, ValueError):
            move = None
        if move not in legal:
            forfeit_seat, error = seat, f"illegal_move:{move}"
            registry.warn(f"{names[seat]} memilih langkah ilegal {move!r} (legal: {legal}); "
                          f"game seed={seed} opening={opening_id} dicatat kalah")
            break

        stats[seat].add_metrics(_read_metrics(agents[seat]))
        state = apply_move(state, move)

    score_p0, score_p1 = get_scores(state)
    if forfeit_seat is not None:
        winner = names[1 - forfeit_seat]
    else:
        result = get_winner(state)
        winner = "draw" if result == -1 else names[result]

    row: Dict[str, object] = {
        "seed": seed, "opening_id": opening_id,
        "agent_p0": names[0], "agent_p1": names[1], "winner": winner,
        "score_p0": score_p0, "score_p1": score_p1,
        "moves": state.move_count,
        "hit_move_cap": int(state.is_terminal and state.move_count >= MAX_GAME_MOVES),
        "forfeit": names[forfeit_seat] if forfeit_seat is not None else "",
        "error": error,
        "opening_plies": task.opening_plies,
        "depth": "" if task.depth is None else task.depth,
        "time_limit": _param_text(task.time_limit),
    }
    for side in (0, 1):
        s = stats[side]
        row[f"decisions_p{side}"] = s.decisions
        row[f"time_p{side}"] = round(s.time, 6)
        row[f"nodes_p{side}"] = _fmt_number(s.sums["nodes"])
        row[f"cutoffs_p{side}"] = _fmt_number(s.sums["cutoffs"])
        row[f"depth_sum_p{side}"] = _fmt_number(s.sums["depth"])
        row[f"elapsed_p{side}"] = _fmt_number(s.sums["elapsed"])
    return row


# --- Penjadwalan -----------------------------------------------------------------

def build_tasks(specs: List[str], openings: int, seeds: List[int], opening_plies: int,
                depth: Optional[int], time_limit: Optional[float]) -> List[GameTask]:
    """Semua game: seed x opening x pasangan unik x dua sisi (game berpasangan)."""
    tasks = []
    for seed in seeds:
        for opening_id in range(openings):
            for a, b in itertools.combinations(specs, 2):
                tasks.append(GameTask(seed, opening_id, a, b, opening_plies, depth, time_limit))
                tasks.append(GameTask(seed, opening_id, b, a, opening_plies, depth, time_limit))
    return tasks


def _task_key(task: GameTask) -> Tuple[str, str, str, str]:
    return (str(task.seed), str(task.opening_id),
            registry.agent_name(task.spec_p0), registry.agent_name(task.spec_p1))


def read_existing(path: str, params: Tuple[str, str, str]) -> Set[Tuple[str, str, str, str]]:
    """
    Kunci game yang sudah ada di CSV. Baris terakhir yang terpotong (proses
    dihentikan saat menulis) dibuang dari berkas. Melempar SystemExit bila header
    atau parameter run (opening_plies, depth, time_limit) tidak cocok.
    """
    with open(path, "r", newline="", encoding="utf-8") as handle:
        lines = handle.read().splitlines(keepends=True)
    if not lines:
        return set()

    header = next(csv.reader([lines[0]]))
    if header != COLUMNS:
        raise SystemExit(f"Header {path} berbeda dari yang diharapkan; tidak bisa --resume.")

    valid = [lines[0]]
    keys = set()
    seen_params = set()
    for index, line in enumerate(lines[1:], start=1):
        complete = line.endswith("\n")
        fields = next(csv.reader([line]), [])
        if not complete or len(fields) != len(COLUMNS):
            if index == len(lines) - 1:
                registry.warn(f"baris terakhir {path} terpotong, dibuang dan akan dimainkan ulang")
                continue
            raise SystemExit(f"{path} baris {index + 1} rusak; periksa berkas sebelum --resume.")
        valid.append(line)
        row = dict(zip(COLUMNS, fields))
        keys.add((row["seed"], row["opening_id"], row["agent_p0"], row["agent_p1"]))
        seen_params.add((row["opening_plies"], row["depth"], row["time_limit"]))

    if len(valid) != len(lines):
        temp_path = path + ".tmp"
        with open(temp_path, "w", newline="", encoding="utf-8") as handle:
            handle.writelines(valid)
        os.replace(temp_path, path)

    mismatched = seen_params - {params}
    if mismatched:
        raise SystemExit(
            f"--resume ditolak: {path} berisi game dengan parameter (opening_plies, depth, time_limit) "
            f"{sorted(mismatched)}, sedangkan run ini {params}. Pakai --out lain."
        )
    return keys


def run_tournament(specs: List[str], openings: int, seeds: List[int], opening_plies: int,
                   depth: Optional[int], time_limit: Optional[float], workers: int,
                   out_path: str, resume: bool = False, progress: bool = True) -> Dict[str, int]:
    """Menjalankan turnamen dan menulis CSV bertahap. Mengembalikan ringkasan jumlah game."""
    names = [registry.agent_name(spec) for spec in specs]
    if len(set(names)) != len(names):
        raise ValueError(f"Nama agen harus unik: {names}")
    if len(specs) < 2:
        raise ValueError("Turnamen membutuhkan minimal 2 agen.")

    tasks = build_tasks(specs, openings, seeds, opening_plies, depth, time_limit)
    total = len(tasks)

    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    exists = os.path.exists(out_path) and os.path.getsize(out_path) > 0
    done_keys: Set[Tuple[str, str, str, str]] = set()
    if exists:
        if not resume:
            raise SystemExit(f"{out_path} sudah ada. Pakai --resume untuk melanjutkan atau --out lain.")
        done_keys = read_existing(out_path, (str(opening_plies), "" if depth is None else str(depth),
                                             _param_text(time_limit)))

    pending = [task for task in tasks if _task_key(task) not in done_keys]
    skipped = total - len(pending)
    if progress:
        sys.stderr.write(f"Turnamen: {len(specs)} agen ({', '.join(names)}), {total} game, "
                         f"{skipped} sudah ada, {len(pending)} akan dimainkan, {max(1, workers)} worker\n")

    written = forfeits = 0
    started = time.perf_counter()
    with open(out_path, "a" if exists else "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        if not exists:
            writer.writeheader()
            handle.flush()

        def consume(rows: Iterable[Dict[str, object]]) -> None:
            nonlocal written, forfeits
            step = max(1, len(pending) // 20)
            for row in rows:
                writer.writerow(row)
                handle.flush()
                written += 1
                forfeits += bool(row["forfeit"])
                if progress and (written % step == 0 or written == len(pending)):
                    spent = time.perf_counter() - started
                    eta = spent / written * (len(pending) - written)
                    sys.stderr.write(f"  {written}/{len(pending)} game ({spent:.0f} dtk, sisa ~{eta:.0f} dtk)\n")

        if pending and workers <= 1:
            consume(map(play_game, pending))
        elif pending:
            # Referensi fungsi lewat nama modul penuh (bukan __main__) agar bisa di-pickle
            # pada metode start 'spawn'. Spawn dipilih supaya perilakunya sama di semua OS.
            from experiments.tournament import play_game as worker_fn
            context = multiprocessing.get_context("spawn")
            chunk = max(1, min(16, len(pending) // (workers * 4)))
            with context.Pool(workers) as pool:
                consume(pool.imap_unordered(worker_fn, pending, chunksize=chunk))

    return {"total": total, "skipped": skipped, "played": written, "forfeits": forfeits}


# --- CLI -------------------------------------------------------------------------

def _parse_seeds(text: str) -> List[int]:
    try:
        seeds = [int(part) for part in text.split(",") if part.strip()]
    except ValueError:
        raise argparse.ArgumentTypeError(f"--seeds harus daftar bilangan bulat dipisah koma: {text!r}")
    if not seeds or len(set(seeds)) != len(seeds):
        raise argparse.ArgumentTypeError("--seeds tidak boleh kosong atau berulang")
    return seeds


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m experiments.tournament",
        description="Turnamen round-robin Congklak-Master dengan pembukaan acak berpasangan (sisi ditukar).",
    )
    parser.add_argument("--agents", default="all",
                        help="daftar spesifikasi dipisah koma (nama terdaftar atau alias=modul:Kelas); "
                             "'all' = semua nama terdaftar yang tersedia (default)")
    parser.add_argument("--openings", type=int, default=100, help="jumlah pembukaan per seed (default 100)")
    parser.add_argument("--seeds", type=_parse_seeds, default=[42, 123, 2026],
                        help="daftar seed dipisah koma (default 42,123,2026)")
    parser.add_argument("--opening-plies", type=int, default=4, help="jumlah langkah acak pembukaan (default 4)")
    parser.add_argument("--depth", type=int, default=4, help="batas kedalaman yang diteruskan ke agen (default 4)")
    parser.add_argument("--time-limit", type=float, default=0.0,
                        help="batas waktu per langkah (detik) yang diteruskan ke agen; 0 = tanpa batas")
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1),
                        help="jumlah proses paralel (default: jumlah CPU - 1; 1 = tanpa multiprocessing)")
    parser.add_argument("--out", required=True, help="berkas CSV keluaran, mis. results/tournament_<tag>.csv")
    parser.add_argument("--resume", action="store_true", help="lanjutkan run: lewati game yang sudah ada di --out")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.openings < 1 or args.opening_plies < 0 or args.workers < 1:
        raise SystemExit("--openings >= 1, --opening-plies >= 0, --workers >= 1")

    if args.agents == "all":
        specs = registry.default_specs()
    else:
        try:
            specs = registry.usable_specs([part for part in args.agents.split(",") if part.strip()])
        except ValueError as exc:
            raise SystemExit(str(exc))
    if len(specs) < 2:
        raise SystemExit(f"Hanya {len(specs)} agen tersedia ({', '.join(registry.agent_name(s) for s in specs)}); "
                         f"turnamen butuh minimal 2.")

    summary = run_tournament(
        specs, args.openings, args.seeds, args.opening_plies, args.depth,
        args.time_limit if args.time_limit > 0 else None, args.workers, args.out, args.resume,
    )
    sys.stderr.write(f"Selesai: {summary['played']} game dimainkan, {summary['skipped']} dilewati (resume), "
                     f"{summary['forfeits']} kalah forfeit -> {args.out}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
