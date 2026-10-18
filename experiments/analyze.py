"""
Analisis hasil turnamen: win rate, rating Elo, statistik pencarian, dan grafik.

Contoh:
  python -m experiments.analyze results/tournament_a.csv results/tournament_b.csv --out-dir results

Keluaran di --out-dir (default results/):
  winrate_matrix.csv   BENTUK PANJANG: satu baris per pasangan terurut (baris, kolom)
                       dengan n game, menang/seri/kalah, win rate (seri = 0,5), dan
                       interval Wilson 95%. Pivot kolom win_rate untuk bentuk matriks.
  elo.csv              rating Bradley-Terry (MLE, iterasi MM), skala 400*log10,
                       rata-rata antar agen = 1500, interval bootstrap 95%
                       (1.000 resample per game).
  search_stats.csv     rata-rata node/langkah, waktu/langkah, kedalaman per agen.
  figures/winrate_heatmap.png, elo_bar.png, nodes_per_move.png (bila ada data node).

Catatan metode:
  * Seri dihitung 0,5. Interval Wilson memakai proporsi poin (menang + 0,5 seri) / n
    sebagai pendekatan; seri membuat interval sedikit lebih lebar dari kasus ideal.
  * Bradley-Terry: P(i mengalahkan j) = pi_i / (pi_i + pi_j). MLE hanya ada bila
    graf "i pernah menang atas j" terhubung kuat. Bila tidak (mis. satu agen kalah
    di semua game), dipakai penghalusan: tiap pasangan yang pernah bertemu diberi
    `prior` poin (default 0,5) untuk kedua arah, dan kolom `regularized` = True.
  * Bootstrap default meresampel GAME satu per satu (sesuai spesifikasi). Game yang
    berbagi pembukaan (pasangan sisi-tukar, dan antar pasangan agen) tidak independen
    penuh. Arah pengaruhnya bergantung pada agen: pada satu pengukuran random vs greedy
    (1.800 game) skor sebuah agen pada dua game satu pembukaan berkorelasi negatif
    (-0,12), sehingga interval per game justru sedikit lebih lebar (sekitar 2%) daripada
    interval per pembukaan. Itu belum tentu berlaku untuk agen lain. Periksa pada data
    sebenarnya dengan --bootstrap-unit opening, yang meresampel seluruh game dari satu
    (seed, opening_id) sekaligus.
"""

import argparse
import math
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

import matplotlib
matplotlib.use("Agg")  # backend tanpa layar; harus dipilih sebelum pyplot dipakai
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

Z95 = 1.959963984540054
ELO_MEAN = 1500.0
KEY_COLUMNS = ["seed", "opening_id", "agent_p0", "agent_p1"]
REQUIRED_COLUMNS = KEY_COLUMNS + ["winner"]
DPI = 200


# --- Pemuatan data ------------------------------------------------------------------

def load_games(paths: Sequence[str]) -> pd.DataFrame:
    """Membaca dan menggabungkan CSV turnamen; baris dengan kunci sama dibuang (yang pertama dipertahankan)."""
    frames = []
    for path in paths:
        frame = pd.read_csv(path, dtype={"agent_p0": str, "agent_p1": str, "winner": str,
                                         "forfeit": str, "error": str}, keep_default_na=False,
                            na_values=[""])
        missing = [c for c in REQUIRED_COLUMNS if c not in frame.columns]
        if missing:
            raise ValueError(f"{path}: kolom wajib tidak ada: {missing}")
        frames.append(frame)
    games = pd.concat(frames, ignore_index=True)
    before = len(games)
    games = games.drop_duplicates(subset=KEY_COLUMNS, keep="first").reset_index(drop=True)
    if len(games) != before:
        sys.stderr.write(f"[PERINGATAN] {before - len(games)} baris duplikat (kunci sama) dibuang\n")
    if games.empty:
        raise ValueError("Tidak ada game untuk dianalisis.")
    return games


def _agent_index(games: pd.DataFrame) -> Tuple[List[str], np.ndarray, np.ndarray, np.ndarray]:
    """Daftar agen terurut abjad, indeks p0/p1 per game, dan poin sisi P0 (1, 0,5, atau 0)."""
    agents = sorted(set(games["agent_p0"]) | set(games["agent_p1"]))
    index = {name: i for i, name in enumerate(agents)}
    ai = games["agent_p0"].map(index).to_numpy(dtype=np.int64)
    bi = games["agent_p1"].map(index).to_numpy(dtype=np.int64)
    winner = games["winner"].to_numpy()
    points_p0 = np.where(winner == games["agent_p0"].to_numpy(), 1.0,
                         np.where(winner == "draw", 0.5,
                                  np.where(winner == games["agent_p1"].to_numpy(), 0.0, np.nan)))
    if np.isnan(points_p0).any():
        bad = games.loc[np.isnan(points_p0), "winner"].unique()[:5]
        raise ValueError(f"Kolom winner berisi nilai yang bukan agen_p0/agen_p1/draw: {list(bad)}")
    return agents, ai, bi, points_p0


def _points_matrix(ai: np.ndarray, bi: np.ndarray, points_p0: np.ndarray, k: int,
                   sample: Optional[np.ndarray] = None) -> np.ndarray:
    """Matriks k x k: P[i, j] = poin yang dikumpulkan i dalam game melawan j."""
    if sample is not None:
        ai, bi, points_p0 = ai[sample], bi[sample], points_p0[sample]
    flat = np.bincount(ai * k + bi, weights=points_p0, minlength=k * k)
    flat = flat + np.bincount(bi * k + ai, weights=1.0 - points_p0, minlength=k * k)
    return flat.reshape(k, k)


# --- Win rate dengan interval Wilson ---------------------------------------------------

def wilson_interval(successes: float, n: float, z: float = Z95) -> Tuple[float, float]:
    """Interval Wilson untuk proporsi successes/n (successes boleh pecahan untuk seri = 0,5)."""
    if n <= 0:
        return float("nan"), float("nan")
    p = successes / n
    z2 = z * z
    denominator = 1.0 + z2 / n
    center = (p + z2 / (2.0 * n)) / denominator
    half = z * math.sqrt(p * (1.0 - p) / n + z2 / (4.0 * n * n)) / denominator
    return max(0.0, center - half), min(1.0, center + half)


def winrate_table(games: pd.DataFrame) -> pd.DataFrame:
    """Tabel panjang win rate baris-melawan-kolom (seri = 0,5) dengan interval Wilson 95%."""
    agents, ai, bi, points_p0 = _agent_index(games)
    k = len(agents)
    wins = np.zeros((k, k))
    draws = np.zeros((k, k))
    np.add.at(wins, (ai[points_p0 == 1.0], bi[points_p0 == 1.0]), 1)
    np.add.at(wins, (bi[points_p0 == 0.0], ai[points_p0 == 0.0]), 1)
    np.add.at(draws, (ai[points_p0 == 0.5], bi[points_p0 == 0.5]), 1)
    np.add.at(draws, (bi[points_p0 == 0.5], ai[points_p0 == 0.5]), 1)

    rows = []
    for i in range(k):
        for j in range(k):
            if i == j:
                continue
            n = wins[i, j] + wins[j, i] + draws[i, j]
            if n == 0:
                continue
            score = wins[i, j] + 0.5 * draws[i, j]
            low, high = wilson_interval(score, n)
            rows.append({
                "agent_row": agents[i], "agent_col": agents[j], "n_games": int(n),
                "wins": int(wins[i, j]), "draws": int(draws[i, j]), "losses": int(wins[j, i]),
                "win_rate": score / n, "ci_low": low, "ci_high": high,
            })
    return pd.DataFrame(rows)


# --- Bradley-Terry / Elo -------------------------------------------------------------------

def _strongly_connected(adjacent: np.ndarray) -> bool:
    reach = adjacent.copy() | np.eye(len(adjacent), dtype=bool)
    for m in range(len(adjacent)):  # Warshall
        reach |= reach[:, [m]] & reach[[m], :]
    return bool(reach.all())


def bradley_terry(points: np.ndarray, prior: float = 0.5, max_iter: int = 200_000,
                  tol: float = 1e-12, init: Optional[np.ndarray] = None
                  ) -> Tuple[np.ndarray, bool, np.ndarray]:
    """
    MLE Bradley-Terry dengan iterasi MM (Hunter 2004):
        pi_i <- W_i / sum_j n_ij / (pi_i + pi_j)
    `points[i, j]` = poin i melawan j (menang = 1, seri = 0,5). Hasil dinormalkan agar
    rata-rata geometrik pi = 1, sehingga Elo = 1500 + 400*log10(pi) berrata-rata 1500.

    Returns: (elo, regularized, pi). regularized=True bila MLE tidak ada dan dipakai
    penghalusan `prior` poin per arah pada setiap pasangan yang pernah bertemu.
    """
    points = np.array(points, dtype=float)
    np.fill_diagonal(points, 0.0)
    played = (points + points.T) > 0
    if (~played[~np.eye(len(points), dtype=bool)]).all():
        raise ValueError("Tidak ada pasangan agen yang pernah bertemu.")

    regularized = not _strongly_connected(points > 0)
    if regularized:
        points = points + prior * played
        if not _strongly_connected(points > 0):
            raise ValueError("Graf pertandingan tidak terhubung: rating antar agen tidak dapat dibandingkan.")

    n = points + points.T
    total_points = points.sum(axis=1)
    log_pi = np.zeros(len(points)) if init is None else np.log(init)
    for _ in range(max_iter):
        pi = np.exp(log_pi)
        denominator = (n / (pi[:, None] + pi[None, :])).sum(axis=1)
        new_log = np.log(total_points / denominator)
        new_log -= new_log.mean()
        done = np.max(np.abs(new_log - log_pi)) < tol
        log_pi = new_log
        if done:
            break
    pi = np.exp(log_pi)
    elo = ELO_MEAN + 400.0 * log_pi / math.log(10.0)
    return elo, regularized, pi


def bootstrap_elo(ai: np.ndarray, bi: np.ndarray, points_p0: np.ndarray, k: int,
                  resamples: int = 1000, seed: int = 0, prior: float = 0.5,
                  init: Optional[np.ndarray] = None,
                  blocks: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Interval persentil 95% bootstrap. Tanpa `blocks`: resample per game dengan
    pengembalian. Dengan `blocks` (id blok per game, mis. pembukaan): resample BLOK
    dengan pengembalian, tiap blok membawa seluruh game di dalamnya.
    """
    rng = np.random.default_rng(seed)
    n_games = len(ai)
    samples = np.empty((resamples, k))

    if blocks is not None:
        _, blocks = np.unique(blocks, return_inverse=True)
        n_blocks = int(blocks.max()) + 1
        per_block = np.zeros((n_blocks, k, k))
        np.add.at(per_block, (blocks, ai, bi), points_p0)
        np.add.at(per_block, (blocks, bi, ai), 1.0 - points_p0)

    for r in range(resamples):
        if blocks is None:
            matrix = _points_matrix(ai, bi, points_p0, k, rng.integers(0, n_games, n_games))
        else:
            counts = np.bincount(rng.integers(0, n_blocks, n_blocks), minlength=n_blocks)
            matrix = np.tensordot(counts, per_block, axes=1)
        # toleransi lebih longgar (1e-9 pada log-rating, setara ~2e-7 poin Elo) karena warm start
        samples[r], _, _ = bradley_terry(matrix, prior, tol=1e-9, init=init)
    low, high = np.percentile(samples, [2.5, 97.5], axis=0)
    return low, high


def elo_table(games: pd.DataFrame, resamples: int = 1000, seed: int = 0,
              prior: float = 0.5, unit: str = "game") -> pd.DataFrame:
    """Tabel Elo. unit="game": bootstrap per game (default); unit="opening": per (seed, opening_id)."""
    if unit not in ("game", "opening"):
        raise ValueError(f"unit harus 'game' atau 'opening', bukan {unit!r}")
    agents, ai, bi, points_p0 = _agent_index(games)
    k = len(agents)
    points = _points_matrix(ai, bi, points_p0, k)
    elo, regularized, pi = bradley_terry(points, prior)
    blocks = games.groupby(["seed", "opening_id"]).ngroup().to_numpy() if unit == "opening" else None
    low, high = bootstrap_elo(ai, bi, points_p0, k, resamples, seed, prior, init=pi, blocks=blocks)
    n_games = (points + points.T).sum(axis=1)
    return pd.DataFrame({
        "agent": agents, "elo": elo, "ci_low": low, "ci_high": high,
        "n_games": n_games.astype(int), "score_rate": points.sum(axis=1) / n_games,
        "regularized": regularized, "bootstrap_resamples": resamples, "bootstrap_unit": unit,
    }).sort_values("elo", ascending=False, kind="stable").reset_index(drop=True)


# --- Statistik pencarian ---------------------------------------------------------------------

def _long_by_agent(games: pd.DataFrame) -> pd.DataFrame:
    """Satu baris per (game, sisi) dengan kolom metrik tanpa akhiran _p0/_p1."""
    parts = []
    for side in (0, 1):
        part = pd.DataFrame({"agent": games[f"agent_p{side}"]})
        for column in ("decisions", "time", "nodes", "cutoffs", "depth_sum", "elapsed"):
            name = f"{column}_p{side}"
            part[column] = pd.to_numeric(games[name], errors="coerce") if name in games.columns else np.nan
        parts.append(part)
    return pd.concat(parts, ignore_index=True)


def _ratio(frame: pd.DataFrame, numerator: str) -> float:
    """sum(numerator) / sum(decisions) hanya pada baris yang memiliki metrik tsb; NaN bila tidak ada."""
    valid = frame[frame[numerator].notna() & (frame["decisions"] > 0)]
    decisions = valid["decisions"].sum()
    return float(valid[numerator].sum() / decisions) if decisions > 0 else float("nan")


def search_stats(games: pd.DataFrame) -> pd.DataFrame:
    long = _long_by_agent(games)
    rows = []
    for agent, frame in long.groupby("agent", sort=True):
        decisions = frame["decisions"].sum()
        rows.append({
            "agent": agent,
            "n_games": len(frame),
            "n_decisions": int(decisions),
            "nodes_per_move": _ratio(frame, "nodes"),
            "cutoffs_per_move": _ratio(frame, "cutoffs"),
            "depth_reached_mean": _ratio(frame, "depth_sum"),
            "time_per_move_s": float(frame["time"].sum() / decisions) if decisions > 0 else float("nan"),
            "metric_elapsed_per_move_s": _ratio(frame, "elapsed"),
        })
    return pd.DataFrame(rows)


def nodes_per_move_by_game(games: pd.DataFrame) -> Dict[str, np.ndarray]:
    """Node per langkah di tiap game (hanya yang punya data node), per agen."""
    long = _long_by_agent(games)
    valid = long[long["nodes"].notna() & (long["decisions"] > 0)].copy()
    valid["nodes_per_move"] = valid["nodes"] / valid["decisions"]
    return {agent: frame["nodes_per_move"].to_numpy() for agent, frame in valid.groupby("agent", sort=True)}


# --- Grafik ------------------------------------------------------------------------------------

def _id(value: float, digits: int = 1) -> str:
    """Format angka dengan koma desimal (gaya Indonesia)."""
    return f"{value:.{digits}f}".replace(".", ",")


def plot_winrate_heatmap(table: pd.DataFrame, order: List[str], path: str) -> None:
    k = len(order)
    matrix = np.full((k, k), np.nan)
    counts = np.zeros((k, k), dtype=int)
    index = {name: i for i, name in enumerate(order)}
    for row in table.itertuples():
        matrix[index[row.agent_row], index[row.agent_col]] = row.win_rate * 100.0
        counts[index[row.agent_row], index[row.agent_col]] = row.n_games

    fig, ax = plt.subplots(figsize=(1.3 * k + 3.2, 1.1 * k + 2.6))
    image = ax.imshow(np.ma.masked_invalid(matrix), cmap="RdYlBu", vmin=0, vmax=100)
    for i in range(k):
        for j in range(k):
            if i == j:
                ax.text(j, i, "-", ha="center", va="center", color="gray")
            elif counts[i, j] > 0:
                value = matrix[i, j]
                color = "white" if value < 20 or value > 80 else "black"
                ax.text(j, i, f"{_id(value, 1)}%\n(n={counts[i, j]})", ha="center", va="center",
                        fontsize=9, color=color)
    ax.set_xticks(range(k), labels=order, rotation=30, ha="right")
    ax.set_yticks(range(k), labels=order)
    ax.set_xlabel("Lawan (kolom)")
    ax.set_ylabel("Agen (baris)")
    ax.set_title("Win rate baris melawan kolom (seri dihitung 0,5)")
    colorbar = fig.colorbar(image, ax=ax)
    colorbar.set_label("Win rate (%)")
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)


def plot_elo_bar(elo: pd.DataFrame, path: str) -> None:
    # Nol pada skala Elo bersifat sembarang, jadi batang digambar sebagai simpangan
    # dari rata-rata 1500 (bukan dari 0) agar tinggi batang tidak menyesatkan.
    fig, ax = plt.subplots(figsize=(max(6.5, 1.1 * len(elo) + 3.5), 5))
    positions = np.arange(len(elo))
    values = elo["elo"].to_numpy()
    lower = np.clip(values - elo["ci_low"].to_numpy(), 0, None)
    upper = np.clip(elo["ci_high"].to_numpy() - values, 0, None)
    ax.bar(positions, values - ELO_MEAN, bottom=ELO_MEAN, color="#4C72B0")
    ax.errorbar(positions, values, yerr=[lower, upper], fmt="none", ecolor="black", elinewidth=1.3,
                capsize=5)
    ax.axhline(ELO_MEAN, color="gray", linestyle="--", linewidth=1, label="Rata-rata 1500")
    for x, value, up in zip(positions, values, upper):
        ax.annotate(_id(value, 0), (x, value + up), xytext=(0, 4), textcoords="offset points",
                    ha="center", va="bottom", fontsize=9)
    ax.set_xticks(positions, labels=list(elo["agent"]))
    ax.margins(y=0.15)
    ax.set_xlabel("Agen")
    ax.set_ylabel("Rating Elo (poin; rata-rata antar agen = 1500)")
    ax.set_title("Rating Elo Bradley-Terry dengan interval bootstrap 95%")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)


def plot_nodes_per_move(per_game: Dict[str, np.ndarray], path: str) -> None:
    agents = list(per_game)
    means = np.array([values.mean() for values in per_game.values()])
    errors = np.array([1.96 * values.std(ddof=1) / math.sqrt(len(values)) if len(values) > 1 else 0.0
                       for values in per_game.values()])
    fig, ax = plt.subplots(figsize=(max(6.5, 1.1 * len(agents) + 3.5), 5))
    ax.bar(agents, means, yerr=errors, capsize=5, color="#55A868", error_kw={"elinewidth": 1.3})
    if means.max() > 50 * max(means.min(), 1e-9) and means.min() > 0:
        ax.set_yscale("log")
    ax.set_xlabel("Agen")
    ax.set_ylabel("Rata-rata node per langkah (jumlah simpul)")
    ax.set_title("Beban pencarian per langkah\n(error bar: interval 95% antar game)")
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)


# --- CLI ---------------------------------------------------------------------------------------

def _write_csv(frame: pd.DataFrame, path: str, float_digits: int = 6) -> None:
    frame.to_csv(path, index=False, float_format=f"%.{float_digits}f")


def analyze(paths: Sequence[str], out_dir: str = "results", resamples: int = 1000,
            seed: int = 0, prior: float = 0.5, unit: str = "game") -> Dict[str, object]:
    games = load_games(paths)
    figures_dir = os.path.join(out_dir, "figures")
    os.makedirs(figures_dir, exist_ok=True)

    table = winrate_table(games)
    _write_csv(table, os.path.join(out_dir, "winrate_matrix.csv"), 6)

    elo = elo_table(games, resamples, seed, prior, unit)
    # Rating dan batas interval dibulatkan ke 0,01 poin Elo; kolom lain (mis. score_rate) tetap presisi penuh.
    rounded = elo.copy()
    rounded[["elo", "ci_low", "ci_high"]] = rounded[["elo", "ci_low", "ci_high"]].round(2)
    rounded["score_rate"] = rounded["score_rate"].round(6)
    rounded.to_csv(os.path.join(out_dir, "elo.csv"), index=False)

    stats = search_stats(games)
    _write_csv(stats, os.path.join(out_dir, "search_stats.csv"), 6)

    order = list(elo["agent"])
    plot_winrate_heatmap(table, order, os.path.join(figures_dir, "winrate_heatmap.png"))
    plot_elo_bar(elo, os.path.join(figures_dir, "elo_bar.png"))
    per_game = nodes_per_move_by_game(games)
    if per_game:
        plot_nodes_per_move(per_game, os.path.join(figures_dir, "nodes_per_move.png"))

    return {"games": games, "winrate": table, "elo": elo, "search_stats": stats,
            "nodes_figure": bool(per_game)}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m experiments.analyze",
        description="Analisis CSV turnamen: win rate (Wilson), Elo Bradley-Terry (bootstrap), statistik pencarian, grafik.",
    )
    parser.add_argument("inputs", nargs="+", help="satu atau beberapa CSV hasil experiments.tournament")
    parser.add_argument("--out-dir", default="results", help="folder keluaran (default results)")
    parser.add_argument("--bootstrap", type=int, default=1000, help="jumlah resample bootstrap (default 1000)")
    parser.add_argument("--seed", type=int, default=0, help="seed bootstrap (default 0)")
    parser.add_argument("--prior", type=float, default=0.5,
                        help="poin penghalusan per arah bila MLE tidak ada (default 0,5)")
    parser.add_argument("--bootstrap-unit", choices=["game", "opening"], default="game",
                        help="satuan resample bootstrap: 'game' (default, sesuai spesifikasi) atau "
                             "'opening' (seluruh game dari satu seed+opening_id sekaligus)")
    args = parser.parse_args(argv)

    result = analyze(args.inputs, args.out_dir, args.bootstrap, args.seed, args.prior, args.bootstrap_unit)
    games, table, elo = result["games"], result["winrate"], result["elo"]
    print(f"{len(games)} game dari {len(args.inputs)} berkas -> {args.out_dir}")
    print("\nWin rate (baris melawan kolom, seri = 0,5):")
    print(table.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print("\nElo (Bradley-Terry, bootstrap 95%):")
    print(elo.to_string(index=False, float_format=lambda x: f"{x:.1f}"))
    if bool(elo["regularized"].iloc[0]):
        print("\nCATATAN: MLE tidak ada pada data ini (ada agen tanpa kemenangan/kekalahan); "
              "Elo dihitung dengan penghalusan dan nilainya bergantung pada --prior.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
