"""
Training Algoritma Genetika untuk bobot evaluasi 6 fitur Model 3 (laporan Bab 2.4, 3.4).

  python -m experiments.ga_train --out-dir results

Ringkasan (nilai bawaan; semua bisa diubah lewat argumen):
  - Kromosom: 6 bobot real [w1..w6] untuk f1..f6 (src/agents/evaluation.py, ga_features),
    inisialisasi acak seragam [-1, 1], dibatasi ke [-1, 1] setelah mutasi.
  - Fitness: rata-rata per game dari Win_Score (menang 100, seri 50, kalah 0) +
    Margin_Biji (lumbung agen - lumbung lawan), melawan Alpha-Beta H2 dan Alpha-Beta
    H1 pada kedalaman yang sama, dari `openings` pembukaan acak per lawan, sisi bertukar.
    Semua individu dalam satu generasi memakai pembukaan yang sama (adil), dan
    pembukaan berganti tiap generasi (mengurangi overfitting).
  - Seleksi turnamen (k=3), crossover BLX-alpha (alpha=0,5, peluang 0,9), mutasi
    Gaussian per gen (peluang 0,2, sigma 0,15), elitisme 2 individu.
  - Validasi: kandidat terbaik dari 10 generasi terakhir dan bobot setara H2 dimainkan
    pada pembukaan validasi terpisah; kandidat dengan fitness validasi tertinggi
    disimpan sebagai results/ga_weights.json (dibaca src/agents/ga.py).

Keluaran di --out-dir: ga_weights.json, ga_history.csv (per generasi),
ga_population.csv (semua individu), ga_validation.csv, ga_convergence.png.
"""

import argparse
import csv
import datetime
import json
import os
import platform
import random
import sys
import time
from multiprocessing import get_context
from typing import Dict, List, Optional, Sequence, Tuple

import matplotlib
matplotlib.use("Agg")  # backend tanpa layar
import matplotlib.pyplot as plt  # noqa: E402
import numpy  # noqa: E402

from experiments.tournament import _git_state, make_opening  # noqa: E402
from src.agents.alphabeta import AlphaBetaAgent  # noqa: E402
from src.agents.evaluation import GA_FEATURES, H2_AS_GA_WEIGHTS, weighted_evaluator  # noqa: E402
from src.engine.api import apply_move, get_scores, is_terminal  # noqa: E402

N_GENES = len(GA_FEATURES)
BOUND = 1.0
DPI = 200

DEFAULTS = dict(population=20, generations=30, elite=2, tournament_k=3, crossover_rate=0.9,
                blx_alpha=0.5, mutation_rate=0.2, mutation_sigma=0.15, depth=4, openings=8,
                opening_plies=6, opponents=("h2", "h1"), validation_openings=50,
                validation_last=10, seed=2026)

WIN, DRAW, LOSS = 100.0, 50.0, 0.0


# --- Satu game ------------------------------------------------------------------------------

def play_game(task) -> Tuple[float, float]:
    """(Win_Score, Margin_Biji) untuk kromosom `weights` melawan heuristik `opponent`."""
    weights, opponent, opening_seed, opening_id, side, depth, plies = task
    state = make_opening(opening_seed, opening_id, plies)
    agents = [None, None]
    agents[side] = AlphaBetaAgent(depth=depth, heuristic=weighted_evaluator(weights), iterative=False)
    agents[1 - side] = AlphaBetaAgent(depth=depth, heuristic=opponent, iterative=False)
    while not is_terminal(state):
        state = apply_move(state, agents[state.current_player].choose_move(state))
    scores = get_scores(state)
    margin = scores[side] - scores[1 - side]
    return (WIN if margin > 0 else DRAW if margin == 0 else LOSS), float(margin)


def fitness_tasks(weights: Sequence[float], opponents: Sequence[str], opening_seed: int,
                  openings: int, depth: int, plies: int) -> list:
    return [(tuple(weights), opp, opening_seed, oid, side, depth, plies)
            for opp in opponents for oid in range(openings) for side in (0, 1)]


class Evaluator:
    """Memainkan banyak game, serial atau dengan multiprocessing (urutan hasil tetap)."""

    def __init__(self, workers: int):
        self.workers = workers
        self.pool = get_context("spawn").Pool(workers) if workers > 1 else None

    def run(self, tasks: list) -> List[Tuple[float, float]]:
        if self.pool is None:
            return [play_game(t) for t in tasks]
        return self.pool.map(play_game, tasks, chunksize=max(1, len(tasks) // (self.workers * 4)))

    def fitness(self, population: Sequence[Sequence[float]], per_individual) -> List[dict]:
        """per_individual(weights) -> daftar tugas. Mengembalikan statistik per individu."""
        tasks, spans = [], []
        for weights in population:
            own = per_individual(weights)
            spans.append((len(tasks), len(tasks) + len(own)))
            tasks += own
        results = self.run(tasks)
        out = []
        for start, end in spans:
            games = results[start:end]
            n = len(games)
            out.append({
                "fitness": sum(w + m for w, m in games) / n,
                "win_rate": sum(1.0 for w, _ in games if w == WIN) / n,
                "draw_rate": sum(1.0 for w, _ in games if w == DRAW) / n,
                "margin": sum(m for _, m in games) / n,
                "games": n,
            })
        return out

    def close(self):
        if self.pool is not None:
            self.pool.close()
            self.pool.join()


# --- Operator genetika ------------------------------------------------------------------------

def clip(x: float) -> float:
    return max(-BOUND, min(BOUND, x))


def tournament_select(rng: random.Random, population, fitness, k: int):
    picks = rng.sample(range(len(population)), k)
    return population[max(picks, key=lambda i: fitness[i])]


def blx_crossover(rng: random.Random, a, b, alpha: float) -> List[float]:
    child = []
    for x, y in zip(a, b):
        low, high = min(x, y), max(x, y)
        span = high - low
        child.append(clip(rng.uniform(low - alpha * span, high + alpha * span)))
    return child


def mutate(rng: random.Random, genes, rate: float, sigma: float) -> List[float]:
    return [clip(g + rng.gauss(0.0, sigma)) if rng.random() < rate else g for g in genes]


def next_generation(rng: random.Random, population, fitness, p: dict) -> List[List[float]]:
    order = sorted(range(len(population)), key=lambda i: fitness[i], reverse=True)
    new = [list(population[i]) for i in order[:p["elite"]]]
    while len(new) < p["population"]:
        a = tournament_select(rng, population, fitness, p["tournament_k"])
        b = tournament_select(rng, population, fitness, p["tournament_k"])
        child = blx_crossover(rng, a, b, p["blx_alpha"]) if rng.random() < p["crossover_rate"] else list(a)
        new.append(mutate(rng, child, p["mutation_rate"], p["mutation_sigma"]))
    return new


# --- Training -------------------------------------------------------------------------------

def generation_seed(seed: int, generation: int) -> int:
    return seed * 1000 + generation


def validation_seed(seed: int) -> int:
    return seed * 1000 + 999


def train(p: dict, out_dir: str, workers: int = 1, progress: bool = True) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    rng = random.Random(p["seed"])
    population = [[rng.uniform(-BOUND, BOUND) for _ in range(N_GENES)] for _ in range(p["population"])]
    evaluator = Evaluator(workers)
    started = time.perf_counter()
    history, everyone = [], []

    try:
        for gen in range(p["generations"]):
            seed = generation_seed(p["seed"], gen)
            stats = evaluator.fitness(population, lambda w: fitness_tasks(
                w, p["opponents"], seed, p["openings"], p["depth"], p["opening_plies"]))
            fitness = [s["fitness"] for s in stats]
            best = max(range(len(population)), key=lambda i: fitness[i])
            mean = sum(fitness) / len(fitness)
            std = (sum((f - mean) ** 2 for f in fitness) / len(fitness)) ** 0.5
            history.append({"generation": gen, "best_fitness": fitness[best], "mean_fitness": mean,
                            "std_fitness": std, "best_win_rate": stats[best]["win_rate"],
                            "best_margin": stats[best]["margin"],
                            **{f"w{k + 1}": population[best][k] for k in range(N_GENES)},
                            "seconds": round(time.perf_counter() - started, 1)})
            for i, (w, s) in enumerate(zip(population, stats)):
                everyone.append({"generation": gen, "individual": i, **s,
                                 **{f"w{k + 1}": w[k] for k in range(N_GENES)}})
            if progress:
                sys.stderr.write(f"  generasi {gen + 1}/{p['generations']}: terbaik {fitness[best]:.1f}, "
                                 f"rata-rata {mean:.1f} ({time.perf_counter() - started:.0f} dtk)\n")
            if gen < p["generations"] - 1:
                population = next_generation(rng, population, fitness, p)

        # Validasi: terbaik dari N generasi terakhir + bobot setara H2 sebagai rujukan.
        candidates, labels = [], []
        for row in history[-p["validation_last"]:]:
            weights = [row[f"w{k + 1}"] for k in range(N_GENES)]
            if weights not in candidates:
                candidates.append(weights)
                labels.append(f"terbaik generasi {row['generation']}")
        candidates.append(list(H2_AS_GA_WEIGHTS))
        labels.append("H2 (bobot manual, rujukan)")
        vseed = validation_seed(p["seed"])
        validation = evaluator.fitness(candidates, lambda w: fitness_tasks(
            w, p["opponents"], vseed, p["validation_openings"], p["depth"], p["opening_plies"]))
    finally:
        evaluator.close()

    val_rows = [{"candidate": label, **stats, **{f"w{k + 1}": w[k] for k in range(N_GENES)}}
                for label, w, stats in zip(labels, candidates, validation)]
    ga_rows = val_rows[:-1]
    chosen = max(ga_rows, key=lambda r: r["fitness"])
    commit, dirty = _git_state()
    result = {
        "weights": [chosen[f"w{k + 1}"] for k in range(N_GENES)],
        "features": list(GA_FEATURES),
        "chosen": chosen["candidate"],
        "validation_fitness": chosen["fitness"],
        "h2_validation_fitness": val_rows[-1]["fitness"],
        "params": {**p, "opponents": list(p["opponents"])},
        "seconds": round(time.perf_counter() - started, 1), "workers": workers,
        "date": datetime.datetime.now().isoformat(timespec="seconds"),
        "commit": commit, "dirty": dirty, "python": platform.python_version(),
        "numpy": numpy.__version__, "platform": platform.platform(),
    }

    _write_csv(os.path.join(out_dir, "ga_history.csv"), history)
    _write_csv(os.path.join(out_dir, "ga_population.csv"), everyone)
    _write_csv(os.path.join(out_dir, "ga_validation.csv"), val_rows)
    with open(os.path.join(out_dir, "ga_weights.json"), "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=1)
    plot_convergence(history, os.path.join(out_dir, "ga_convergence.png"))
    return result


def _write_csv(path: str, rows: List[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def plot_convergence(history: List[dict], path: str) -> None:
    gens = [r["generation"] + 1 for r in history]
    mean = [r["mean_fitness"] for r in history]
    std = [r["std_fitness"] for r in history]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(gens, [r["best_fitness"] for r in history], marker="o", markersize=3, label="Fitness terbaik")
    ax.plot(gens, mean, marker="s", markersize=3, label="Fitness rata-rata populasi")
    ax.fill_between(gens, [m - s for m, s in zip(mean, std)], [m + s for m, s in zip(mean, std)],
                    alpha=0.15, label="Rata-rata ± simpangan baku")
    ax.set_xlabel("Generasi")
    ax.set_ylabel("Fitness (Win_Score + Margin_Biji per game)")
    ax.set_title("Kurva konvergensi Algoritma Genetika")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)


# --- CLI ------------------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    d = DEFAULTS
    parser.add_argument("--population", type=int, default=d["population"])
    parser.add_argument("--generations", type=int, default=d["generations"])
    parser.add_argument("--elite", type=int, default=d["elite"])
    parser.add_argument("--tournament-k", type=int, default=d["tournament_k"])
    parser.add_argument("--crossover-rate", type=float, default=d["crossover_rate"])
    parser.add_argument("--blx-alpha", type=float, default=d["blx_alpha"])
    parser.add_argument("--mutation-rate", type=float, default=d["mutation_rate"])
    parser.add_argument("--mutation-sigma", type=float, default=d["mutation_sigma"])
    parser.add_argument("--depth", type=int, default=d["depth"], help="kedalaman Alpha-Beta saat training")
    parser.add_argument("--openings", type=int, default=d["openings"], help="pembukaan per lawan per generasi")
    parser.add_argument("--opening-plies", type=int, default=d["opening_plies"])
    parser.add_argument("--opponents", default=",".join(d["opponents"]), help="heuristik lawan, mis. h2,h1")
    parser.add_argument("--validation-openings", type=int, default=d["validation_openings"])
    parser.add_argument("--validation-last", type=int, default=d["validation_last"])
    parser.add_argument("--seed", type=int, default=d["seed"])
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    parser.add_argument("--out-dir", default="results")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    p = {key: getattr(args, key) for key in DEFAULTS}
    p["opponents"] = tuple(o.strip() for o in args.opponents.split(",") if o.strip())
    if p["population"] < 2 or p["elite"] >= p["population"] or p["tournament_k"] > p["population"]:
        raise SystemExit("butuh population >= 2, elite < population, tournament-k <= population")
    if p["generations"] < 1 or p["depth"] < 1 or p["openings"] < 1 or p["validation_openings"] < 1:
        raise SystemExit("generations, depth, openings, validation-openings minimal 1")
    result = train(p, args.out_dir, workers=args.workers)
    sys.stderr.write(f"Selesai: bobot {['%.3f' % w for w in result['weights']]} ({result['chosen']}), "
                     f"fitness validasi {result['validation_fitness']:.1f} vs H2 {result['h2_validation_fitness']:.1f} "
                     f"-> {os.path.join(args.out_dir, 'ga_weights.json')}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
