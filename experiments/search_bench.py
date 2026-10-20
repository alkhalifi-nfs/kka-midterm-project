"""
Pengukuran pencarian untuk Bab 3.2 dan 3.3 (RQ1).

Untuk setiap posisi uji dan setiap kedalaman, semua konfigurasi pencarian
memilih langkah pada kedalaman yang sama. Dicatat: langkah, nilai, jumlah
node, pemangkasan, pemakaian TT, dan waktu. Hasilnya menjawab:
  - Bab 3.2: apakah Alpha-Beta memilih langkah (dan nilai) yang sama dengan Minimax;
  - Bab 3.3: berapa persen node yang dihemat pruning, move ordering, dan TT,
    effective branching factor (EBF), dan ukuran TT.

  python -m experiments.search_bench --depths 1-6 --out results/search_bench.csv

Keluaran (folder yang sama dengan --out):
  search_bench.csv              satu baris per (posisi, kedalaman, konfigurasi)
  search_bench.meta.json        parameter, commit, lingkungan
  search_bench_summary.csv      ringkasan per (konfigurasi, kedalaman)
  search_bench_tabel.md         tabel siap tempel (koma desimal)
  search_bench_nodes.png        grafik rata-rata node vs kedalaman (skala log)

TT dikosongkan sebelum setiap pencarian, jadi tiap baris berdiri sendiri.
Waktu (elapsed) bergantung mesin dan jumlah worker; pakai --workers 1 bila
angka waktu akan dikutip.
"""

import argparse
import csv
import datetime
import json
import os
import platform
import sys
import time
from multiprocessing import get_context
from typing import Dict, List, Optional, Sequence, Tuple

import matplotlib
matplotlib.use("Agg")  # backend tanpa layar
import matplotlib.pyplot as plt  # noqa: E402
import numpy  # noqa: E402
import pandas as pd  # noqa: E402

from experiments.positions import load_positions  # noqa: E402
from experiments.report_tables import MISSING, _table, fmt  # noqa: E402
from experiments.tournament import _git_state  # noqa: E402
from src.agents.alphabeta import AlphaBetaAgent  # noqa: E402
from src.agents.minimax import MinimaxAgent  # noqa: E402

DEFAULT_POSITIONS = "results/positions_seed42_n500.json"
DPI = 200

# nama -> (label laporan, pakai TT?, argumen AlphaBetaAgent atau None untuk Minimax)
CONFIGS: Dict[str, Tuple[str, bool, Optional[dict]]] = {
    "minimax": ("Minimax", False, None),
    "ab_polos": ("Alpha-Beta polos", False, dict(ordering=False, use_tt=False, iterative=False)),
    "ab_ordering": ("+ move ordering", False, dict(ordering=True, use_tt=False, iterative=False)),
    "ab_tt": ("+ TT (tanpa ordering)", True, dict(ordering=False, use_tt=True, iterative=False)),
    "ab_ordering_tt": ("+ ordering + TT", True, dict(ordering=True, use_tt=True, iterative=False)),
    "ab_lengkap": ("Model 2 lengkap (+ ID)", True, dict(ordering=True, use_tt=True, iterative=True)),
}

COLUMNS = ["position_id", "move_count", "current_player", "n_legal", "depth", "config",
           "move", "value", "nodes", "cutoffs", "tt_hits", "tt_entries", "depth_reached",
           "elapsed", "same_move", "same_value"]


# --- Menjalankan -------------------------------------------------------------------------

_AGENTS: Dict[Tuple[str, str], object] = {}


def _agent(config: str, heuristic: str):
    """Satu agen per (konfigurasi, heuristik) per proses; TT dikosongkan sebelum dipakai."""
    key = (config, heuristic)
    if key not in _AGENTS:
        kwargs = CONFIGS[config][2]
        _AGENTS[key] = (MinimaxAgent(heuristic=heuristic) if kwargs is None
                        else AlphaBetaAgent(heuristic=heuristic, **kwargs))
    agent = _AGENTS[key]
    agent.reset()
    return agent


def measure(task) -> List[dict]:
    """Semua konfigurasi pada satu (posisi, kedalaman). Minimax selalu dijalankan sebagai rujukan."""
    position_id, state, depth, configs, heuristic = task
    from src.engine.api import get_legal_moves

    rows, reference = [], None
    for config in ["minimax"] + [c for c in configs if c != "minimax"]:
        agent = _agent(config, heuristic)
        started = time.perf_counter()
        value, move = agent.search(state.copy(), depth)
        elapsed = time.perf_counter() - started
        if reference is None:
            reference = (value, move)
        if config not in configs:
            continue
        m = agent.metrics
        rows.append({
            "position_id": position_id, "move_count": state.move_count,
            "current_player": state.current_player, "n_legal": len(get_legal_moves(state)),
            "depth": depth, "config": config, "move": move, "value": value,
            "nodes": m.nodes, "cutoffs": m.cutoffs,
            "tt_hits": getattr(m, "tt_hits", 0), "tt_entries": getattr(m, "tt_entries", 0),
            "depth_reached": m.depth_reached, "elapsed": round(elapsed, 6),
            "same_move": int(move == reference[1]), "same_value": int(value == reference[0]),
        })
    return rows


def run_bench(positions_path: str, depths: Sequence[int], configs: Sequence[str], heuristic: str,
              out: str, workers: int = 1, limit: Optional[int] = None, progress: bool = True) -> pd.DataFrame:
    positions = load_positions(positions_path)
    if limit:
        positions = positions[:limit]
    tasks = [(i, state, d, list(configs), heuristic) for d in depths for i, state in enumerate(positions)]

    started = time.perf_counter()
    rows: List[dict] = []

    def collect(result, done):
        rows.extend(result)
        if progress and (done % 100 == 0 or done == len(tasks)):
            sys.stderr.write(f"  {done}/{len(tasks)} (posisi x kedalaman), {time.perf_counter() - started:.0f} dtk\n")

    if workers <= 1:
        for done, task in enumerate(tasks, 1):
            collect(measure(task), done)
    else:
        with get_context("spawn").Pool(workers) as pool:
            for done, result in enumerate(pool.imap(measure, tasks, chunksize=4), 1):
                collect(result, done)

    frame = pd.DataFrame(rows, columns=COLUMNS).sort_values(["depth", "position_id", "config"])
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    frame.to_csv(out, index=False)

    commit, dirty = _git_state()
    meta = {
        "positions": positions_path, "n_positions": len(positions), "depths": list(depths),
        "configs": list(configs), "heuristic": heuristic, "workers": workers,
        "seconds": round(time.perf_counter() - started, 1),
        "date": datetime.datetime.now().isoformat(timespec="seconds"),
        "commit": commit, "dirty": dirty, "python": platform.python_version(),
        "numpy": numpy.__version__, "platform": platform.platform(),
    }
    with open(os.path.splitext(out)[0] + ".meta.json", "w", encoding="utf-8") as handle:
        json.dump(meta, handle, indent=1)
    return frame


# --- Ringkasan ----------------------------------------------------------------------------

def effective_branching_factor(nodes: float, depth: int) -> float:
    """b* yang memenuhi nodes = 1 + b* + b*^2 + ... + b*^depth (Russell & Norvig; nodes termasuk akar)."""
    if depth < 1 or nodes <= 1:
        return 0.0

    def total(b):
        return sum(b ** i for i in range(depth + 1))

    low, high = 0.0, max(2.0, nodes)
    for _ in range(200):
        mid = (low + high) / 2
        if total(mid) < nodes:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def summarize(frame: pd.DataFrame) -> pd.DataFrame:
    """Satu baris per (konfigurasi, kedalaman)."""
    minimax_nodes = frame[frame.config == "minimax"].groupby("depth").nodes.sum()
    rows = []
    for (config, depth), g in frame.groupby(["config", "depth"], sort=False):
        nodes_mean = g.nodes.mean()
        rows.append({
            "config": config, "label": CONFIGS[config][0], "depth": depth, "n": len(g),
            "nodes_total": int(g.nodes.sum()), "nodes_mean": nodes_mean,
            "nodes_vs_minimax": g.nodes.sum() / minimax_nodes[depth] if depth in minimax_nodes else float("nan"),
            "ebf": effective_branching_factor(nodes_mean, depth),
            "cutoffs_mean": g.cutoffs.mean(), "tt_hits_mean": g.tt_hits.mean(),
            "tt_entries_mean": g.tt_entries.mean(), "tt_entries_max": int(g.tt_entries.max()),
            "elapsed_mean": g.elapsed.mean(),
            "same_move": int(g.same_move.sum()), "same_value": int(g.same_value.sum()),
        })
    order = {name: i for i, name in enumerate(CONFIGS)}
    return (pd.DataFrame(rows).sort_values(["depth", "config"], key=lambda c: c.map(order) if c.name == "config" else c)
            .reset_index(drop=True))


def tables_md(summary: pd.DataFrame, meta: dict) -> str:
    configs = [c for c in CONFIGS if c in set(summary.config)]
    depths = sorted(summary.depth.unique())
    cell = {(r.config, r.depth): r for r in summary.itertuples()}
    label = {c: CONFIGS[c][0] for c in configs}
    others = [c for c in configs if c != "minimax"]

    def get(config, depth):
        return cell.get((config, depth))

    parts = [f"<!-- dibuat oleh experiments/search_bench.py dari {meta.get('positions', '?')}; "
             f"heuristik {meta.get('heuristic', '?')}; commit {str(meta.get('commit'))[:7]} -->", ""]

    # Bab 3.2: kesamaan dengan Minimax
    parts += ["**Kesamaan langkah dan nilai dengan Minimax (Bab 3.2)**", ""]
    header = ["Kedalaman", "Posisi"] + [label[c] for c in others]
    rows = []
    for d in depths:
        n = get("minimax", d).n if get("minimax", d) else (get(others[0], d).n if others else 0)
        row = [str(d), str(n)]
        for c in others:
            r = get(c, d)
            row.append(MISSING if r is None else
                       f"langkah {r.same_move}/{r.n}, nilai {r.same_value}/{r.n}")
        rows.append(row)
    parts += [_table(header, rows), "",
              "Konfigurasi bertanda TT boleh berbeda dari Minimax karena entri TT dari pencarian yang "
              "lebih dalam dipakai ulang (lihat src/agents/alphabeta.py).", ""]

    # Bab 3.3: node relatif dan EBF
    parts += ["**Rata-rata node per posisi (persentase terhadap Minimax pada kedalaman yang sama)**", ""]
    header = ["Kedalaman"] + [label[c] for c in configs]
    rows = [[str(d)] + [MISSING if get(c, d) is None else
                        f"{fmt(get(c, d).nodes_mean, 0)} ({fmt(get(c, d).nodes_vs_minimax, 1, percent=True)})"
                        for c in configs] for d in depths]
    parts += [_table(header, rows), ""]

    parts += ["**Effective branching factor (EBF)**", ""]
    rows = [[str(d)] + [MISSING if get(c, d) is None else fmt(get(c, d).ebf, 2) for c in configs]
            for d in depths]
    parts += [_table(header, rows), ""]

    # Bab 3.3: TT dan waktu
    tt_configs = [c for c in configs if CONFIGS[c][1]]
    if tt_configs:
        parts += ["**Transposition table: rata-rata TT hit dan isi TT per pencarian (maksimum)**", ""]
        header = ["Kedalaman"] + [label[c] for c in tt_configs]
        rows = [[str(d)] + [MISSING if get(c, d) is None else
                            f"{fmt(get(c, d).tt_hits_mean, 1)} hit, {fmt(get(c, d).tt_entries_mean, 0)} "
                            f"entri ({get(c, d).tt_entries_max})" for c in tt_configs] for d in depths]
        parts += [_table(header, rows), ""]

    parts += [f"**Rata-rata waktu per pencarian (milidetik; {meta.get('workers', '?')} worker, "
              f"{meta.get('platform', '?')})**", ""]
    header = ["Kedalaman"] + [label[c] for c in configs]
    rows = [[str(d)] + [MISSING if get(c, d) is None else fmt(get(c, d).elapsed_mean * 1000, 2)
                        for c in configs] for d in depths]
    parts += [_table(header, rows), ""]
    return "\n".join(parts)


def plot_nodes(summary: pd.DataFrame, path: str) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for config in CONFIGS:
        g = summary[summary.config == config]
        if len(g):
            ax.plot(g.depth, g.nodes_mean, marker="o", label=CONFIGS[config][0])
    ax.set_yscale("log")
    ax.set_xlabel("Kedalaman (ply)")
    ax.set_ylabel("Rata-rata node per posisi (skala log)")
    ax.set_title("Jumlah node yang dikunjungi per kedalaman")
    ax.set_xticks(sorted(summary.depth.unique()))
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)


def write_outputs(csv_path: str) -> Dict[str, str]:
    frame = pd.read_csv(csv_path)
    meta_file = os.path.splitext(csv_path)[0] + ".meta.json"
    meta = {}
    if os.path.exists(meta_file):
        with open(meta_file, "r", encoding="utf-8") as handle:
            meta = json.load(handle)
    base = os.path.splitext(csv_path)[0]
    paths = {"summary": base + "_summary.csv", "tables": base + "_tabel.md", "plot": base + "_nodes.png"}
    summary = summarize(frame)
    summary.to_csv(paths["summary"], index=False)
    with open(paths["tables"], "w", encoding="utf-8") as handle:
        handle.write(tables_md(summary, meta))
    plot_nodes(summary, paths["plot"])
    return paths


# --- CLI ------------------------------------------------------------------------------------

def parse_depths(text: str) -> List[int]:
    depths = []
    for part in text.split(","):
        if "-" in part:
            low, high = part.split("-")
            depths += list(range(int(low), int(high) + 1))
        elif part.strip():
            depths.append(int(part))
    if not depths or min(depths) < 1:
        raise argparse.ArgumentTypeError("kedalaman minimal 1, contoh: 1-6 atau 2,4,6")
    return sorted(set(depths))


def parse_configs(text: str) -> List[str]:
    configs = list(CONFIGS) if text == "all" else [c.strip() for c in text.split(",") if c.strip()]
    unknown = [c for c in configs if c not in CONFIGS]
    if unknown:
        raise argparse.ArgumentTypeError(f"konfigurasi tidak dikenal: {', '.join(unknown)} "
                                         f"(pilihan: {', '.join(CONFIGS)})")
    return configs


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--positions", default=DEFAULT_POSITIONS, help=f"berkas posisi (default {DEFAULT_POSITIONS})")
    parser.add_argument("--depths", type=parse_depths, default=parse_depths("1-6"), help="mis. 1-6 atau 2,4,6")
    parser.add_argument("--configs", type=parse_configs, default=list(CONFIGS),
                        help=f"dipisah koma atau 'all' (default all: {', '.join(CONFIGS)})")
    parser.add_argument("--heuristic", choices=["h1", "h2"], default="h2")
    parser.add_argument("--limit", type=int, default=None, help="hanya N posisi pertama (untuk uji cepat)")
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    parser.add_argument("--out", default="results/search_bench.csv")
    parser.add_argument("--summarize-only", action="store_true", help="hanya buat ulang ringkasan dari --out")
    args = parser.parse_args(argv)

    if not args.summarize_only:
        run_bench(args.positions, args.depths, args.configs, args.heuristic, args.out,
                  workers=args.workers, limit=args.limit)
    paths = write_outputs(args.out)
    sys.stderr.write("Selesai -> " + ", ".join([args.out] + list(paths.values())) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
