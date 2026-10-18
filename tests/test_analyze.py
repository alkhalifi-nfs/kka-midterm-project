"""Tes analisis turnamen: Wilson, Bradley-Terry/Elo, bootstrap, statistik pencarian, keluaran."""
import math
import os

import numpy as np
import pandas as pd
import pytest

from experiments import analyze, tournament
from experiments.analyze import (
    Z95, bootstrap_elo, bradley_terry, elo_table, load_games, search_stats, wilson_interval,
    winrate_table, _agent_index, _points_matrix,
)


def synthetic_games(a_wins, b_wins, draws=0, a="A", b="B"):
    """Game berpasangan sintetis; sisi A/B bergantian agar tidak ada bias sisi."""
    outcomes = ["A"] * a_wins + ["B"] * b_wins + ["draw"] * draws
    rows = []
    for i, outcome in enumerate(outcomes):
        p0, p1 = (a, b) if i % 2 == 0 else (b, a)
        winner = "draw" if outcome == "draw" else (a if outcome == "A" else b)
        rows.append({"seed": 0, "opening_id": i, "agent_p0": p0, "agent_p1": p1, "winner": winner})
    return pd.DataFrame(rows)


# --- Wilson ----------------------------------------------------------------------------------

def test_wilson_matches_closed_forms():
    z2 = Z95 ** 2
    assert wilson_interval(0, 10) == pytest.approx((0.0, z2 / (10 + z2)), abs=1e-12)
    assert wilson_interval(10, 10) == pytest.approx((10 / (10 + z2), 1.0), abs=1e-12)
    low, high = wilson_interval(5, 10)  # nilai tabel: [0,2366; 0,7634]
    assert (low, high) == pytest.approx((0.2366, 0.7634), abs=1e-4)
    assert low + high == pytest.approx(1.0)


@pytest.mark.parametrize("k,n", [(1, 7), (3, 10), (30, 100), (75, 100), (5, 400), (0.5, 3), (2.5, 5)])
def test_wilson_endpoints_satisfy_the_defining_equation(k, n):
    """Ujung interval Wilson adalah p yang memenuhi (p_hat - p)^2 = z^2 p (1-p) / n."""
    p_hat = k / n
    for endpoint in wilson_interval(k, n):
        assert (p_hat - endpoint) ** 2 == pytest.approx(Z95 ** 2 * endpoint * (1 - endpoint) / n, rel=1e-9)


def test_wilson_width_shrinks_with_more_games_and_handles_n_zero():
    widths = [wilson_interval(0.75 * n, n)[1] - wilson_interval(0.75 * n, n)[0] for n in (20, 80, 320)]
    assert widths[0] > widths[1] > widths[2]
    assert math.isnan(wilson_interval(0, 0)[0])


def test_winrate_table_counts_draws_as_half():
    games = synthetic_games(a_wins=6, b_wins=2, draws=2)
    table = winrate_table(games).set_index(["agent_row", "agent_col"])
    ab = table.loc[("A", "B")]
    assert (ab.n_games, ab.wins, ab.draws, ab.losses) == (10, 6, 2, 2)
    assert ab.win_rate == pytest.approx(0.7)
    assert table.loc[("B", "A")].win_rate == pytest.approx(0.3)
    assert (ab.ci_low, ab.ci_high) == pytest.approx(wilson_interval(7, 10))
    assert ab.ci_low < ab.win_rate < ab.ci_high


# --- Bradley-Terry / Elo ----------------------------------------------------------------------

def test_elo_difference_for_75_percent_winrate_is_400_log10_3():
    games = synthetic_games(a_wins=300, b_wins=100)
    agents, ai, bi, points = _agent_index(games)
    elo, regularized, _ = bradley_terry(_points_matrix(ai, bi, points, len(agents)))
    assert not regularized
    diff = elo[0] - elo[1]
    assert diff == pytest.approx(400 * math.log10(3), abs=1e-6)
    assert diff == pytest.approx(190.8, abs=0.05)
    assert elo.mean() == pytest.approx(1500.0)


def test_elo_is_symmetric_in_agent_labels():
    first = elo_table(synthetic_games(30, 10, a="A", b="B"), resamples=20).set_index("agent")
    second = elo_table(synthetic_games(10, 30, a="B", b="A"), resamples=20).set_index("agent")
    assert first.loc["A", "elo"] == pytest.approx(second.loc["A", "elo"], abs=1e-6)


def test_bradley_terry_recovers_true_ratings_from_exact_expected_counts():
    true_elo = np.array([1700.0, 1500.0, 1300.0, 1450.0])
    k = len(true_elo)
    strength = 10 ** (true_elo / 400)
    n_games = 1000.0
    points = np.array([[n_games * strength[i] / (strength[i] + strength[j]) if i != j else 0.0
                        for j in range(k)] for i in range(k)])
    elo, regularized, _ = bradley_terry(points)
    assert not regularized
    expected = true_elo - true_elo.mean() + 1500.0
    assert elo == pytest.approx(expected, abs=1e-6)


def test_all_draws_give_equal_ratings_and_zero_width_interval():
    table = elo_table(synthetic_games(0, 0, draws=40), resamples=50)
    assert table["elo"].tolist() == pytest.approx([1500.0, 1500.0])
    assert table["ci_low"].tolist() == pytest.approx([1500.0, 1500.0])
    assert table["ci_high"].tolist() == pytest.approx([1500.0, 1500.0])


def test_unbeaten_agent_gets_finite_regularized_rating_and_is_flagged():
    table = elo_table(synthetic_games(a_wins=20, b_wins=0), resamples=50).set_index("agent")
    assert table["regularized"].all()
    assert np.isfinite(table[["elo", "ci_low", "ci_high"]].to_numpy()).all()
    assert table.loc["A", "elo"] > table.loc["B", "elo"]
    assert table["elo"].mean() == pytest.approx(1500.0)


def test_disconnected_comparison_graph_is_rejected():
    points = np.zeros((4, 4))
    points[0, 1] = points[1, 0] = 3
    points[2, 3] = points[3, 2] = 3
    with pytest.raises(ValueError, match="tidak terhubung"):
        bradley_terry(points)


def test_three_agent_chain_is_ranked_consistently():
    games = pd.concat([
        synthetic_games(30, 10, a="A", b="B"),
        synthetic_games(30, 10, a="B", b="C").assign(opening_id=lambda d: d["opening_id"] + 1000),
        synthetic_games(35, 5, a="A", b="C").assign(opening_id=lambda d: d["opening_id"] + 2000),
    ], ignore_index=True)
    table = elo_table(games, resamples=100).set_index("agent")
    assert table.loc["A", "elo"] > table.loc["B", "elo"] > table.loc["C", "elo"]
    assert table["elo"].mean() == pytest.approx(1500.0)
    assert (table["ci_low"] <= table["elo"]).all() and (table["elo"] <= table["ci_high"]).all()


# --- Bootstrap ------------------------------------------------------------------------------------

def test_bootstrap_is_deterministic_for_a_seed_and_varies_between_seeds():
    games = synthetic_games(60, 20)
    first = elo_table(games, resamples=200, seed=5)
    again = elo_table(games, resamples=200, seed=5)
    other = elo_table(games, resamples=200, seed=6)
    pd.testing.assert_frame_equal(first, again)
    assert not np.allclose(first["ci_low"], other["ci_low"])


def test_bootstrap_interval_matches_analytic_standard_error_for_75_percent():
    """
    400 game, 75% menang: galat baku log-odds = sqrt(1/300 + 1/100); dalam Elo
    (400/ln10 kali itu) selisih dua agen punya galat baku ~20,06, jadi setiap agen
    (dipusatkan di 1500) punya setengah lebar interval 95% sekitar 1,96 * 20,06 / 2 = 19,66.
    """
    games = synthetic_games(300, 100)
    table = elo_table(games, resamples=1000, seed=0).set_index("agent")
    analytic_se_diff = 400 / math.log(10) * math.sqrt(1 / 300 + 1 / 100)
    assert analytic_se_diff == pytest.approx(20.06, abs=0.01)
    half_width = (table.loc["A", "ci_high"] - table.loc["A", "ci_low"]) / 2
    assert half_width == pytest.approx(Z95 * analytic_se_diff / 2, rel=0.15)
    assert table.loc["A", "ci_low"] < table.loc["A", "elo"] < table.loc["A", "ci_high"]
    assert table.loc["A", "elo"] == pytest.approx(1500 + 400 * math.log10(3) / 2, abs=1e-3)


def test_bootstrap_interval_shrinks_with_more_games():
    small = elo_table(synthetic_games(30, 10), resamples=300, seed=1).iloc[0]
    large = elo_table(synthetic_games(300, 100), resamples=300, seed=1).iloc[0]
    assert (large["ci_high"] - large["ci_low"]) < 0.5 * (small["ci_high"] - small["ci_low"])


def test_bootstrap_on_tiny_sample_does_not_crash_and_brackets_point_estimate():
    games = synthetic_games(3, 1)  # sebagian resample tanpa kekalahan -> penghalusan otomatis
    agents, ai, bi, points = _agent_index(games)
    elo, _, pi = bradley_terry(_points_matrix(ai, bi, points, 2))
    low, high = bootstrap_elo(ai, bi, points, 2, resamples=300, seed=0, init=pi)
    assert np.isfinite(low).all() and np.isfinite(high).all()
    assert (low < high).all()
    assert (low <= elo + 1e-9).all() and (elo <= high + 1e-9).all()


# --- Statistik pencarian ----------------------------------------------------------------------------

def test_search_stats_aggregates_per_agent():
    games = pd.DataFrame([
        {"agent_p0": "ab", "agent_p1": "rand", "decisions_p0": 10, "decisions_p1": 12, "time_p0": 1.0, "time_p1": 0.1,
         "nodes_p0": 100, "nodes_p1": np.nan, "cutoffs_p0": 30, "cutoffs_p1": np.nan,
         "depth_sum_p0": 40, "depth_sum_p1": np.nan, "elapsed_p0": 0.9, "elapsed_p1": np.nan},
        {"agent_p0": "rand", "agent_p1": "ab", "decisions_p0": 14, "decisions_p1": 20, "time_p0": 0.2, "time_p1": 3.0,
         "nodes_p0": np.nan, "nodes_p1": 300, "cutoffs_p0": np.nan, "cutoffs_p1": 70,
         "depth_sum_p0": np.nan, "depth_sum_p1": 100, "elapsed_p0": np.nan, "elapsed_p1": 2.7},
    ])
    stats = search_stats(games).set_index("agent")
    ab, rand = stats.loc["ab"], stats.loc["rand"]
    assert ab.n_games == 2 and ab.n_decisions == 30
    assert ab.nodes_per_move == pytest.approx(400 / 30)
    assert ab.cutoffs_per_move == pytest.approx(100 / 30)
    assert ab.depth_reached_mean == pytest.approx(140 / 30)
    assert ab.time_per_move_s == pytest.approx(4.0 / 30)
    assert ab.metric_elapsed_per_move_s == pytest.approx(3.6 / 30)
    assert rand.n_decisions == 26 and rand.time_per_move_s == pytest.approx(0.3 / 26)
    assert math.isnan(rand.nodes_per_move) and math.isnan(rand.depth_reached_mean)


def test_search_stats_ignores_games_without_metrics_for_per_move_ratios():
    games = pd.DataFrame([
        {"agent_p0": "x", "agent_p1": "y", "decisions_p0": 10, "decisions_p1": 10, "time_p0": 1, "time_p1": 1,
         "nodes_p0": 50, "nodes_p1": np.nan},
        {"agent_p0": "x", "agent_p1": "y", "decisions_p0": 90, "decisions_p1": 10, "time_p0": 9, "time_p1": 1,
         "nodes_p0": np.nan, "nodes_p1": np.nan},
    ])
    row = search_stats(games).set_index("agent").loc["x"]
    assert row.nodes_per_move == pytest.approx(5.0)  # 50 / 10, bukan 50 / 100
    assert row.time_per_move_s == pytest.approx(0.1)


# --- Pemuatan dan keluaran ------------------------------------------------------------------------------

def test_load_games_merges_files_and_drops_duplicate_keys(tmp_path, capsys):
    games = synthetic_games(6, 2)
    first, second = str(tmp_path / "a.csv"), str(tmp_path / "b.csv")
    games.iloc[:5].to_csv(first, index=False)
    games.iloc[3:].to_csv(second, index=False)  # tumpang tindih 2 baris
    merged = load_games([first, second])
    assert len(merged) == 8
    assert "2 baris duplikat" in capsys.readouterr().err


def test_load_games_rejects_missing_columns_and_bad_winner(tmp_path):
    bad = str(tmp_path / "bad.csv")
    pd.DataFrame({"seed": [1]}).to_csv(bad, index=False)
    with pytest.raises(ValueError, match="kolom wajib"):
        load_games([bad])
    games = synthetic_games(2, 2)
    games.loc[0, "winner"] = "orang_lain"
    with pytest.raises(ValueError, match="bukan agen_p0"):
        winrate_table(games)


def test_agent_named_like_numbers_stays_text(tmp_path):
    games = synthetic_games(4, 4, a="123", b="007")
    path = str(tmp_path / "num.csv")
    games.to_csv(path, index=False)
    loaded = load_games([path])
    assert set(loaded["agent_p0"]) == {"123", "007"}
    assert set(winrate_table(loaded)["agent_row"]) == {"123", "007"}


def test_end_to_end_from_real_tournament_produces_every_file(tmp_path):
    csv_path = str(tmp_path / "games.csv")
    summary = tournament.run_tournament(["random", "greedy"], 15, [42], 4, 1, None, 1, csv_path,
                                        progress=False)
    assert summary["played"] == 30
    out_dir = str(tmp_path / "out")
    result = analyze.analyze([csv_path], out_dir, resamples=100, seed=0)

    expected = ["winrate_matrix.csv", "elo.csv", "search_stats.csv",
                "figures/winrate_heatmap.png", "figures/elo_bar.png", "figures/nodes_per_move.png"]
    for name in expected:
        path = os.path.join(out_dir, name)
        assert os.path.getsize(path) > 0, name
        if name.endswith(".png"):
            assert open(path, "rb").read(8) == b"\x89PNG\r\n\x1a\n"

    rate = pd.read_csv(os.path.join(out_dir, "winrate_matrix.csv"))
    assert set(rate.columns) == {"agent_row", "agent_col", "n_games", "wins", "draws", "losses",
                                 "win_rate", "ci_low", "ci_high"}
    assert len(rate) == 2 and (rate["n_games"] == 30).all()
    assert rate["win_rate"].sum() == pytest.approx(1.0)
    elo = pd.read_csv(os.path.join(out_dir, "elo.csv"))
    assert elo["elo"].mean() == pytest.approx(1500.0, abs=0.01)
    stats = pd.read_csv(os.path.join(out_dir, "search_stats.csv")).set_index("agent")
    assert stats.loc["greedy", "nodes_per_move"] > 0 and stats.loc["greedy", "depth_reached_mean"] == 1
    assert math.isnan(stats.loc["random", "nodes_per_move"])
    assert result["nodes_figure"]


def test_nodes_figure_is_skipped_when_no_agent_has_node_data(tmp_path):
    games = synthetic_games(10, 10)
    path = str(tmp_path / "g.csv")
    games.to_csv(path, index=False)
    out_dir = str(tmp_path / "o")
    result = analyze.analyze([path], out_dir, resamples=20)
    assert not result["nodes_figure"]
    assert not os.path.exists(os.path.join(out_dir, "figures", "nodes_per_move.png"))
    assert os.path.exists(os.path.join(out_dir, "figures", "elo_bar.png"))


def test_cli_main_prints_tables(tmp_path, capsys):
    path = str(tmp_path / "g.csv")
    synthetic_games(30, 10).to_csv(path, index=False)
    assert analyze.main([path, "--out-dir", str(tmp_path / "o"), "--bootstrap", "30"]) == 0
    out = capsys.readouterr().out
    assert "Win rate" in out and "Elo" in out


# --- Bootstrap per pembukaan (cluster) ---------------------------------------------------------

def openings_games(outcomes):
    """
    Dua game per pembukaan (A pegang P0 di game pertama, B di game kedua).
    `outcomes[i]` = (pemenang game 1, pemenang game 2), masing-masing "A" atau "B".
    """
    rows = []
    for i, (first, second) in enumerate(outcomes):
        rows.append({"seed": 7, "opening_id": i, "agent_p0": "A", "agent_p1": "B", "winner": first})
        rows.append({"seed": 7, "opening_id": i, "agent_p0": "B", "agent_p1": "A", "winner": second})
    return pd.DataFrame(rows)


def test_opening_bootstrap_has_zero_width_when_each_opening_gives_exactly_one_point_each():
    """Pemegang giliran pertama selalu menang: skor tiap agen per pembukaan selalu 1 dari 2."""
    games = openings_games([("A", "B")] * 40)  # game 1: P0=A menang; game 2: P0=B menang
    per_opening = elo_table(games, resamples=200, unit="opening")
    per_game = elo_table(games, resamples=200, unit="game")
    assert per_opening["elo"].tolist() == pytest.approx([1500.0, 1500.0])
    assert (per_opening["ci_high"] - per_opening["ci_low"]).tolist() == pytest.approx([0.0, 0.0], abs=1e-6)
    assert (per_game["ci_high"] - per_game["ci_low"]).min() > 10  # per game mengabaikan struktur itu


def test_opening_bootstrap_is_wider_when_one_agent_wins_both_games_of_an_opening():
    """Korelasi positif dalam pembukaan: lebar interval per pembukaan ~ sqrt(2) kali per game."""
    games = openings_games([("A", "A")] * 25 + [("B", "B")] * 25)
    width = lambda unit: elo_table(games, resamples=1000, seed=3, unit=unit).set_index("agent").pipe(
        lambda t: t.loc["A", "ci_high"] - t.loc["A", "ci_low"])
    ratio = width("opening") / width("game")
    assert ratio == pytest.approx(math.sqrt(2), rel=0.15)


def test_opening_blocks_of_size_one_reproduce_the_per_game_bootstrap():
    games = synthetic_games(30, 10)  # tiap game punya opening_id sendiri, seed sama
    by_game = elo_table(games, resamples=100, seed=2, unit="game")
    by_block = elo_table(games, resamples=100, seed=2, unit="opening")
    assert by_block["ci_low"].tolist() == pytest.approx(by_game["ci_low"].tolist())
    assert by_block["ci_high"].tolist() == pytest.approx(by_game["ci_high"].tolist())
    assert set(by_game["bootstrap_unit"]) == {"game"} and set(by_block["bootstrap_unit"]) == {"opening"}


def test_opening_blocks_treat_same_opening_id_in_different_seeds_as_different_blocks():
    """
    Seed 7: A menang di kedua game tiap pembukaan; seed 8 (opening_id sama): B menang di kedua game.
    Dikelompokkan per (seed, opening_id) -> 20 blok bernilai 2 atau 0 poin, sehingga interval > 0.
    Bila keliru dikelompokkan hanya per opening_id, tiap blok berisi 2 poin tetap dan interval jadi 0.
    """
    won_by_a = openings_games([("A", "A")] * 10)
    won_by_b = openings_games([("B", "B")] * 10).assign(seed=8)
    table = elo_table(pd.concat([won_by_a, won_by_b], ignore_index=True), resamples=300, unit="opening")
    assert (table["ci_high"] - table["ci_low"]).min() > 50


def test_invalid_bootstrap_unit_is_rejected_and_cli_accepts_the_option(tmp_path):
    with pytest.raises(ValueError, match="unit"):
        elo_table(synthetic_games(5, 5), resamples=10, unit="seed")
    path = str(tmp_path / "g.csv")
    openings_games([("A", "A")] * 10 + [("B", "B")] * 10).to_csv(path, index=False)
    assert analyze.main([path, "--out-dir", str(tmp_path / "o"), "--bootstrap", "30",
                         "--bootstrap-unit", "opening"]) == 0
    assert set(pd.read_csv(tmp_path / "o" / "elo.csv")["bootstrap_unit"]) == {"opening"}


def test_elo_csv_keeps_precision_of_score_rate_and_rounds_ratings_to_two_decimals(tmp_path):
    games = synthetic_games(a_wins=5, b_wins=1)  # skor A = 5/6, bukan 0,83
    path = str(tmp_path / "g.csv")
    games.to_csv(path, index=False)
    out = str(tmp_path / "o")
    result = analyze.analyze([path], out, resamples=30)
    written = pd.read_csv(os.path.join(out, "elo.csv")).set_index("agent")
    assert written.loc["A", "score_rate"] == pytest.approx(5 / 6, abs=1e-6)
    assert written.loc["A", "score_rate"] != pytest.approx(0.83, abs=1e-4)
    in_memory = result["elo"].set_index("agent")
    for column in ("elo", "ci_low", "ci_high"):
        assert written.loc["A", column] == pytest.approx(in_memory.loc["A", column], abs=0.005)
        assert round(written.loc["A", column], 2) == written.loc["A", column]
