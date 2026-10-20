"""Tes skrip pengukuran pencarian Bab 3.2/3.3 (experiments/search_bench.py)."""
import argparse
import json
import os

import pandas as pd
import pytest

from experiments import search_bench
from experiments.search_bench import CONFIGS, effective_branching_factor, parse_configs, parse_depths

POSITIONS = os.path.join(os.path.dirname(__file__), "..", "results", "positions_seed42_n500.json")


@pytest.fixture(scope="module")
def bench(tmp_path_factory):
    out = str(tmp_path_factory.mktemp("bench") / "sb.csv")
    code = search_bench.main(["--positions", POSITIONS, "--limit", "6", "--depths", "1-3",
                              "--workers", "1", "--out", out])
    assert code == 0
    return out


def test_one_row_per_position_depth_config(bench):
    frame = pd.read_csv(bench)
    assert len(frame) == 6 * 3 * len(CONFIGS)
    assert set(frame.config) == set(CONFIGS)
    assert (frame.groupby(["position_id", "depth"]).size() == len(CONFIGS)).all()


def test_configs_without_tt_agree_with_minimax(bench):
    frame = pd.read_csv(bench)
    no_tt = frame[frame.config.map(lambda c: not CONFIGS[c][1])]
    assert no_tt.same_move.all() and no_tt.same_value.all()
    assert (frame[~frame.config.isin(["ab_tt", "ab_ordering_tt", "ab_lengkap"])].tt_entries == 0).all()


def test_pruning_never_visits_more_nodes_than_minimax(bench):
    frame = pd.read_csv(bench).set_index(["position_id", "depth", "config"]).nodes
    for (pos, depth, config), nodes in frame.items():
        if config in ("ab_polos", "ab_ordering"):
            assert nodes <= frame[(pos, depth, "minimax")]


def test_summary_tables_plot_and_meta(bench):
    base = os.path.splitext(bench)[0]
    summary = pd.read_csv(base + "_summary.csv")
    mm = summary[summary.config == "minimax"]
    assert (mm.nodes_vs_minimax == 1.0).all() and len(mm) == 3
    assert (summary[summary.config == "ab_polos"].same_move == 6).all()

    text = open(base + "_tabel.md", encoding="utf-8").read()
    assert "Bab 3.2" in text and "Effective branching factor" in text and "Model 2 lengkap" in text
    assert "langkah 6/6, nilai 6/6" in text
    assert os.path.getsize(base + "_nodes.png") > 0

    meta = json.load(open(base + ".meta.json", encoding="utf-8"))
    assert meta["n_positions"] == 6 and meta["depths"] == [1, 2, 3] and meta["heuristic"] == "h2"


def test_summarize_only_rebuilds_from_csv(bench):
    base = os.path.splitext(bench)[0]
    os.remove(base + "_tabel.md")
    assert search_bench.main(["--out", bench, "--summarize-only"]) == 0
    assert os.path.exists(base + "_tabel.md")


def test_effective_branching_factor():
    assert effective_branching_factor(15, 3) == pytest.approx(2.0)      # 1 + 2 + 4 + 8
    assert effective_branching_factor(1 + 7 + 49, 2) == pytest.approx(7.0)
    assert effective_branching_factor(1, 3) == 0.0
    assert effective_branching_factor(3, 4) < 1.0                        # pohon terpotong akhir game


def test_cli_parsers():
    assert parse_depths("1-3,5") == [1, 2, 3, 5]
    assert parse_configs("all") == list(CONFIGS)
    with pytest.raises(argparse.ArgumentTypeError):
        parse_depths("0-2")
    with pytest.raises(argparse.ArgumentTypeError):
        parse_configs("minimax,salah")
