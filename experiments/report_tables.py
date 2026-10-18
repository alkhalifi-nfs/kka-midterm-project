"""
Merender tabel Markdown untuk laporan dari file hasil di results/.

Semua angka di laporan harus berasal dari file di results/. Modul ini mengubah
keluaran experiments.analyze menjadi tabel siap tempel (koma desimal), sehingga
tidak ada angka yang diketik tangan.

  python -m experiments.report_tables --results-dir results --out report/tabel_hasil.md

Masukan (di --results-dir): winrate_matrix.csv, elo.csv (wajib) dan
search_stats.csv (opsional). Dengan --meta <berkas .meta.json dari turnamen>,
ditambahkan tabel parameter protokol. Sel tanpa data ditulis "-".
"""

import argparse
import json
import math
import os
from typing import List, Optional

import pandas as pd

MISSING = "-"


def fmt(value, digits: int = 1, percent: bool = False) -> str:
    """Angka dengan koma desimal; NaN/None menjadi '-'. percent=True mengalikan 100 dan menambah '%'."""
    if value is None or (isinstance(value, float) and math.isnan(value)) or pd.isna(value):
        return MISSING
    number = float(value) * (100.0 if percent else 1.0)
    text = f"{number:.{digits}f}".replace(".", ",")
    return text + "%" if percent else text


def _table(header: List[str], rows: List[List[str]], align: Optional[List[str]] = None) -> str:
    align = align or ["---"] * len(header)
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(align) + " |"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def winrate_matrix_md(winrate: pd.DataFrame, order: List[str]) -> str:
    """Matriks win rate (%) baris melawan kolom; diagonal dan pasangan tanpa game ditulis '-'."""
    cell = {(r.agent_row, r.agent_col): fmt(r.win_rate, 1, percent=True) for r in winrate.itertuples()}
    rows = [[f"**{row}**"] + [cell.get((row, col), MISSING) for col in order] for row in order]
    return _table(["Baris \\ Kolom"] + order, rows, ["---"] + [":---:"] * len(order))


def winrate_pairs_md(winrate: pd.DataFrame, order: List[str]) -> str:
    position = {name: i for i, name in enumerate(order)}
    ordered = winrate.assign(_r=winrate["agent_row"].map(position), _c=winrate["agent_col"].map(position))
    ordered = ordered.sort_values(["_r", "_c"])
    rows = [[r.agent_row, r.agent_col, str(int(r.n_games)), f"{int(r.wins)} / {int(r.draws)} / {int(r.losses)}",
             fmt(r.win_rate, 1, percent=True), f"[{fmt(r.ci_low, 1, percent=True)}; {fmt(r.ci_high, 1, percent=True)}]"]
            for r in ordered.itertuples()]
    return _table(["Agen (baris)", "Lawan (kolom)", "Game", "Menang / Seri / Kalah", "Win rate", "Wilson 95%"],
                  rows, ["---", "---", "---:", ":---:", "---:", ":---:"])


def elo_md(elo: pd.DataFrame) -> str:
    rows = []
    for rank, r in enumerate(elo.itertuples(), start=1):
        rows.append([str(rank), r.agent, fmt(r.elo, 1), f"[{fmt(r.ci_low, 1)}; {fmt(r.ci_high, 1)}]",
                     str(int(r.n_games)), fmt(r.score_rate, 1, percent=True)])
    return _table(["Peringkat", "Agen", "Elo", "CI bootstrap 95%", "Game", "Skor"], rows,
                  ["---:", "---", "---:", ":---:", "---:", "---:"])


def search_md(stats: pd.DataFrame) -> str:
    rows = [[r.agent, str(int(r.n_games)), str(int(r.n_decisions)), fmt(r.nodes_per_move, 1),
             fmt(r.cutoffs_per_move, 1), fmt(r.depth_reached_mean, 2), fmt(r.time_per_move_s * 1000, 3)]
            for r in stats.itertuples()]
    return _table(["Agen", "Game", "Keputusan", "Node/langkah", "Cutoff/langkah", "Kedalaman rata-rata", "Waktu/langkah (ms)"],
                  rows, ["---", "---:", "---:", "---:", "---:", "---:", "---:"])


def meta_md(meta: dict) -> str:
    """Tabel parameter protokol turnamen dari berkas <csv>.meta.json."""
    time_limit = meta.get("time_limit")
    runs = meta.get("runs", [])
    commits = []
    for r in runs:
        commit = r.get("git_commit")
        label = commit[:10] if commit else "tidak tersedia"
        commits.append(label + (" (ada perubahan belum di-commit)" if r.get("git_dirty") else ""))
    rows = [
        ["Agen", ", ".join(meta["agents"])],
        ["Pasangan agen (round-robin tanpa self-play)", str(meta["pairs"])],
        ["Pembukaan per seed", str(meta["openings"])],
        ["Seed", ", ".join(str(s) for s in meta["seeds"])],
        ["Langkah acak pembukaan", str(meta["opening_plies"])],
        ["Game per pasangan agen (pembukaan x 2 sisi x seed)", str(meta["openings"] * 2 * len(meta["seeds"]))],
        ["Total game yang direncanakan", str(meta["games_expected"])],
        ["Pembukaan berbeda dari yang diminta", f'{meta["distinct_openings"]} dari {meta["requested_openings"]}'],
        ["Batas kedalaman yang diteruskan ke agen", str(meta["depth"]) if meta.get("depth") is not None else MISSING],
        ["Batas waktu per langkah (detik)", "tanpa batas" if not time_limit else fmt(time_limit, 2)],
        ["Batas langkah per game / putaran tabur per giliran", f'{meta["max_game_moves"]} / {meta["max_sow_rounds"]}'],
        ["Jumlah pemanggilan (termasuk --resume)", str(len(runs))],
        ["Game dimainkan (jumlah semua pemanggilan)", str(sum(int(r.get("played", 0)) for r in runs))],
        ["Kalah forfeit (jumlah semua pemanggilan)", str(sum(int(r.get("forfeits", 0)) for r in runs))],
        ["Commit kode per pemanggilan", "; ".join(commits) if commits else MISSING],
        ["Lingkungan", f'Python {meta.get("python", "?")}, numpy {meta.get("numpy", "?")}'],
    ]
    return _table(["Parameter", "Nilai"], rows, ["---", "---"])


def build_report(results_dir: str, meta_file: Optional[str] = None) -> str:
    """Seluruh tabel sebagai satu dokumen Markdown."""
    def path(name: str) -> str:
        return os.path.join(results_dir, name)

    missing = [name for name in ("winrate_matrix.csv", "elo.csv") if not os.path.exists(path(name))]
    if missing:
        raise FileNotFoundError(f"File wajib tidak ada di {results_dir}: {', '.join(missing)}. "
                                f"Jalankan python -m experiments.analyze terlebih dahulu.")

    winrate = pd.read_csv(path("winrate_matrix.csv"), dtype={"agent_row": str, "agent_col": str})
    elo = pd.read_csv(path("elo.csv"), dtype={"agent": str})
    order = list(elo["agent"])  # urut Elo menurun

    unit = str(elo["bootstrap_unit"].iloc[0]) if "bootstrap_unit" in elo.columns else "game"
    resamples = int(elo["bootstrap_resamples"].iloc[0]) if "bootstrap_resamples" in elo.columns else None
    notes = []
    if "regularized" in elo.columns and bool(elo["regularized"].astype(str).str.lower().eq("true").any()):
        notes.append("**Catatan:** MLE Bradley-Terry tidak ada pada data ini (ada agen tanpa kemenangan atau tanpa "
                     "kekalahan), sehingga Elo dihitung dengan penghalusan dan batas interval bergantung pada nilai prior.")

    parts = [
        f"<!-- Dihasilkan otomatis oleh experiments.report_tables dari {results_dir}; jangan disunting tangan. -->",
        "",
        "**Win rate baris melawan kolom (seri dihitung 0,5)**",
        "",
        winrate_matrix_md(winrate, order),
        "",
        "**Rincian pasangan agen (interval Wilson 95%)**",
        "",
        winrate_pairs_md(winrate, order),
        "",
        f"**Rating Elo Bradley-Terry (rata-rata antar agen 1500; CI bootstrap 95%, "
        f"{resamples if resamples else '?'} resample per {'pembukaan' if unit == 'opening' else 'game'})**",
        "",
        elo_md(elo),
    ]
    parts += [""] + notes if notes else []

    if meta_file:
        with open(meta_file, "r", encoding="utf-8") as handle:
            parts += ["", "**Parameter protokol turnamen**", "", meta_md(json.load(handle))]

    if os.path.exists(path("search_stats.csv")):
        stats = pd.read_csv(path("search_stats.csv"), dtype={"agent": str})
        stats = stats.set_index("agent").loc[[a for a in order if a in set(stats["agent"])]].reset_index()
        parts += ["", "**Beban pencarian per langkah**", "", search_md(stats)]
    return "\n".join(parts) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m experiments.report_tables",
                                     description="Tabel Markdown untuk laporan dari file di results/.")
    parser.add_argument("--results-dir", default="results", help="folder keluaran experiments.analyze (default results)")
    parser.add_argument("--meta", default=None, help="berkas <csv>.meta.json dari turnamen untuk tabel parameter")
    parser.add_argument("--out", default=None, help="berkas keluaran (default: cetak ke layar)")
    args = parser.parse_args(argv)
    try:
        text = build_report(args.results_dir, args.meta)
    except FileNotFoundError as exc:
        raise SystemExit(str(exc))
    if args.out:
        folder = os.path.dirname(args.out)
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(text)
        print(f"Tabel ditulis ke {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
