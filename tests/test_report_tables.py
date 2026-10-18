"""Tes pembuat tabel laporan (experiments/report_tables.py)."""
import math

import numpy as np
import pandas as pd
import pytest

from experiments import analyze, report_tables
from experiments.report_tables import build_report, fmt


def games_csv(path, a_wins, b_wins, with_nodes=False):
    rows = []
    for i in range(a_wins + b_wins):
        p0, p1 = ("alpha", "beta") if i % 2 == 0 else ("beta", "alpha")
        winner = "alpha" if i < a_wins else "beta"
        row = {"seed": 1, "opening_id": i, "agent_p0": p0, "agent_p1": p1, "winner": winner,
               "decisions_p0": 10, "decisions_p1": 10, "time_p0": 0.01, "time_p1": 0.02}
        if with_nodes:
            row["nodes_p0"] = 400 if p0 == "alpha" else np.nan
            row["nodes_p1"] = 400 if p1 == "alpha" else np.nan
            row["depth_sum_p0"] = 40 if p0 == "alpha" else np.nan
            row["depth_sum_p1"] = 40 if p1 == "alpha" else np.nan
        rows.append(row)
    pd.DataFrame(rows).to_csv(path, index=False)


def test_fmt_uses_decimal_comma_percent_and_dash_for_missing():
    assert fmt(0.925, 1, percent=True) == "92,5%"
    assert fmt(1718.24, 1) == "1718,2"
    assert fmt(3, 0) == "3"
    for missing in (None, float("nan"), np.nan, pd.NA):
        assert fmt(missing) == "-"


def test_tables_contain_exactly_the_numbers_in_the_result_files(tmp_path):
    csv = str(tmp_path / "g.csv")
    games_csv(csv, a_wins=30, b_wins=10, with_nodes=True)
    out = str(tmp_path / "res")
    result = analyze.analyze([csv], out, resamples=50)
    text = build_report(out)

    elo = result["elo"].set_index("agent")
    rate = result["winrate"].set_index(["agent_row", "agent_col"])
    assert fmt(elo.loc["alpha", "elo"], 1) in text and fmt(elo.loc["beta", "elo"], 1) in text
    assert "75,0%" in text and "25,0%" in text
    assert fmt(rate.loc[("alpha", "beta"), "ci_low"], 1, percent=True) in text
    assert "30 / 0 / 10" in text  # menang / seri / kalah untuk alpha
    assert "<!-- Dihasilkan otomatis" in text
    assert "50 resample per game" in text
    assert all("." not in line for line in text.splitlines() if line.startswith("|")), "tabel tidak boleh memuat titik desimal"


def test_matrix_has_dash_on_diagonal_and_rows_follow_elo_order(tmp_path):
    csv = str(tmp_path / "g.csv")
    games_csv(csv, a_wins=5, b_wins=35)  # beta lebih kuat -> beta harus di baris pertama
    out = str(tmp_path / "res")
    analyze.analyze([csv], out, resamples=30)
    lines = [l for l in build_report(out).splitlines() if l.startswith("| **")]
    assert lines[0].startswith("| **beta**") and lines[1].startswith("| **alpha**")
    assert lines[0].split("|")[2].strip() == "-"  # diagonal beta x beta
    assert lines[0].split("|")[3].strip() == "87,5%"  # baris beta melawan kolom alpha: 35 dari 40
    assert lines[1].split("|")[2].strip() == "12,5%"  # baris alpha melawan kolom beta: 5 dari 40


def test_search_table_is_included_only_when_the_file_exists_and_blank_metrics_become_dash(tmp_path):
    csv = str(tmp_path / "g.csv")
    games_csv(csv, a_wins=20, b_wins=20, with_nodes=True)
    out = str(tmp_path / "res")
    analyze.analyze([csv], out, resamples=30)
    text = build_report(out)
    assert "Beban pencarian per langkah" in text
    alpha_row = next(l for l in text.splitlines() if l.startswith("| alpha |") and "Peringkat" not in l and l.count("|") == 8)
    beta_row = next(l for l in text.splitlines() if l.startswith("| beta |") and l.count("|") == 8)
    assert "40,0" in alpha_row            # 400 node / 10 keputusan
    assert beta_row.split("|")[4].strip() == "-"   # beta tanpa data node
    (tmp_path / "res" / "search_stats.csv").unlink()
    assert "Beban pencarian" not in build_report(out)


def test_regularization_note_appears_when_an_agent_never_wins(tmp_path):
    csv = str(tmp_path / "g.csv")
    games_csv(csv, a_wins=20, b_wins=0)
    out = str(tmp_path / "res")
    analyze.analyze([csv], out, resamples=30)
    assert "penghalusan" in build_report(out)


def test_opening_bootstrap_unit_is_named_in_the_caption(tmp_path):
    csv = str(tmp_path / "g.csv")
    games_csv(csv, a_wins=10, b_wins=10)
    out = str(tmp_path / "res")
    analyze.analyze([csv], out, resamples=30, unit="opening")
    assert "30 resample per pembukaan" in build_report(out)


def test_missing_required_files_give_a_clear_error_and_nothing_is_written(tmp_path, capsys):
    with pytest.raises(FileNotFoundError, match="winrate_matrix.csv"):
        build_report(str(tmp_path))
    target = tmp_path / "out.md"
    with pytest.raises(SystemExit, match="analyze"):
        report_tables.main(["--results-dir", str(tmp_path), "--out", str(target)])
    assert not target.exists()


def test_cli_writes_the_markdown_file(tmp_path, capsys):
    csv = str(tmp_path / "g.csv")
    games_csv(csv, a_wins=12, b_wins=8)
    out = str(tmp_path / "res")
    analyze.analyze([csv], out, resamples=30)
    target = str(tmp_path / "sub" / "tabel.md")
    assert report_tables.main(["--results-dir", out, "--out", target]) == 0
    assert open(target, encoding="utf-8").read() == build_report(out)
    assert report_tables.main(["--results-dir", out]) == 0
    assert "Rating Elo" in capsys.readouterr().out
