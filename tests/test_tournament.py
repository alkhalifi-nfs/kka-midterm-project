"""Tes runner turnamen, registry agen, dan agen dasar."""
import numpy as np
import pandas as pd
import pytest

import src.engine.api as engine_api
from experiments import registry, tournament
from experiments.baseline_agents import GreedyAgent, RandomAgent
from experiments.tournament import COLUMNS, build_tasks, make_opening, play_game, run_tournament
from src.engine.api import apply_move, get_initial_state, get_legal_moves, get_score_diff

TIMING_COLUMNS = ["time_p0", "time_p1", "elapsed_p0", "elapsed_p1"]
FAKE = "tests.fake_agents"


def run(tmp_path, specs, openings=3, seeds=(42,), plies=4, depth=4, time_limit=None, workers=1,
        name="t.csv", resume=False):
    out = str(tmp_path / name)
    summary = run_tournament(list(specs), openings, list(seeds), plies, depth, time_limit,
                             workers, out, resume, progress=False)
    return out, summary


def read_rows(path):
    return pd.read_csv(path, dtype={"agent_p0": str, "agent_p1": str, "winner": str,
                                    "forfeit": str, "error": str}, keep_default_na=False,
                       na_values=[""])


def comparable(path):
    frame = read_rows(path).drop(columns=TIMING_COLUMNS)
    return frame.sort_values(["seed", "opening_id", "agent_p0", "agent_p1"]).reset_index(drop=True)


# --- Registry ----------------------------------------------------------------------------

def test_registry_builds_baseline_agents():
    assert isinstance(registry.make_agent("random"), RandomAgent)
    assert isinstance(registry.make_agent("greedy"), GreedyAgent)


def test_registry_skips_missing_agents_with_warning(capsys):
    usable = registry.usable_specs(["random", "minimax", "alphabeta", "ga", "greedy"])
    assert usable == ["random", "greedy"]
    err = capsys.readouterr().err
    for name in ("minimax", "alphabeta", "ga"):
        assert f"agen '{name}' dilewati" in err


def test_registry_default_specs_lists_only_available(capsys):
    assert registry.default_specs() == ["random", "greedy"]
    assert "dilewati" in capsys.readouterr().err


def test_registry_unknown_name_is_an_error():
    with pytest.raises(ValueError, match="tidak dikenal"):
        registry.parse_agent_spec("randon")


def test_registry_alias_and_module_specs():
    assert registry.agent_name(f"duluan={FAKE}:FirstMoveAgent") == "duluan"
    assert registry.agent_name(f"{FAKE}:FirstMoveAgent") == f"{FAKE}:FirstMoveAgent"
    assert registry.make_agent(f"duluan={FAKE}:FirstMoveAgent").name == "first"
    with pytest.raises(ValueError):
        registry.parse_agent_spec("tanpa_titik_dua=abc")


def test_registry_missing_attribute_is_reported_not_raised(capsys):
    assert registry.resolve_factory(f"x={FAKE}:TidakAda") is None
    assert "tidak punya 'TidakAda'" in capsys.readouterr().err


def test_registry_agent_that_fails_to_build_is_skipped(capsys):
    assert registry.usable_specs([f"rusak={FAKE}:BrokenInitAgent", "random"]) == ["random"]
    assert "gagal dibuat" in capsys.readouterr().err


# --- Agen dasar --------------------------------------------------------------------------

def test_random_agent_is_reproducible_after_reset():
    state = get_initial_state()
    agent = RandomAgent()
    agent.reset(5)
    first = [agent.choose_move(state) for _ in range(20)]
    agent.reset(5)
    assert [agent.choose_move(state) for _ in range(20)] == first
    assert set(first) <= set(get_legal_moves(state))


def test_greedy_picks_largest_score_diff_with_lowest_pit_on_ties():
    state = get_initial_state()
    agent = GreedyAgent()
    best = max(get_score_diff(apply_move(state, m), 0) for m in get_legal_moves(state))
    expected = min(m for m in get_legal_moves(state) if get_score_diff(apply_move(state, m), 0) == best)
    assert agent.choose_move(state) == expected == 1  # pembuka lubang 1 langsung +10, yang terkecil dari 1-6
    assert agent.metrics.nodes == 7 and agent.metrics.depth_reached == 1


# --- Pembukaan dan penjadwalan -------------------------------------------------------------

def test_opening_is_deterministic_and_has_requested_plies():
    a, b = make_opening(42, 7, 4), make_opening(42, 7, 4)
    assert a == b and a.move_count == 4
    assert make_opening(42, 8, 4) != a or make_opening(43, 7, 4) != a
    assert make_opening(1, 1, 0) == get_initial_state()


@pytest.mark.parametrize("plies", [0, 4, 7])
def test_both_games_of_a_pair_start_from_the_same_opening_position(tmp_path, plies):
    from tests.fake_agents import StateLogAgentA
    StateLogAgentA.seen.clear()
    run(tmp_path, [f"a={FAKE}:StateLogAgentA", f"b={FAKE}:StateLogAgentB"], openings=5, seeds=(3,), plies=plies)
    # tepat satu state tercatat per game pada move_count == plies (posisi pembukaan itu sendiri)
    opening_calls = [call for call in StateLogAgentA.seen if call[0] == plies]
    assert len(opening_calls) == 5 * 2
    for opening_id in range(5):
        expected = make_opening(3, opening_id, plies)
        wanted = (expected.board.tobytes(), expected.current_player)
        found = [(board, player) for count, board, player in opening_calls if (board, player) == wanted]
        assert len(found) >= 2, f"opening {opening_id}: kedua game harus mulai dari posisi yang sama"
    # pembukaan berbeda antar opening_id (bukan satu posisi yang sama untuk semua)
    assert len({(board, player) for _, board, player in opening_calls}) > 1 or plies == 0


def test_tasks_are_paired_with_swapped_sides_and_count_matches_formula():
    tasks = build_tasks(["a", "b", "c"], openings=5, seeds=[1, 2], opening_plies=4, depth=4, time_limit=None)
    assert len(tasks) == 3 * 5 * 2 * 2  # pasangan x opening x 2 sisi x seed
    sides = {(t.seed, t.opening_id, t.spec_p0, t.spec_p1) for t in tasks}
    for seed, opening, p0, p1 in sides:
        assert (seed, opening, p1, p0) in sides


def test_tournament_row_count_columns_and_pairing(tmp_path):
    out, summary = run(tmp_path, ["random", "greedy"], openings=4, seeds=(42, 7))
    frame = read_rows(out)
    assert summary == {"total": 16, "skipped": 0, "played": 16, "forfeits": 0}
    assert list(frame.columns) == COLUMNS
    assert len(frame) == 1 * 4 * 2 * 2
    assert frame.groupby(["seed", "opening_id"]).size().eq(2).all()
    assert (frame["score_p0"] + frame["score_p1"] == 98).all()
    assert set(frame["winner"]) <= {"random", "greedy", "draw"}
    assert (frame["moves"] >= 4).all() and (frame["hit_move_cap"] == 0).all()
    swapped = frame.groupby(["seed", "opening_id"])["agent_p0"].apply(lambda s: set(s) == {"random", "greedy"})
    assert swapped.all()


def test_three_agents_play_every_unique_pair(tmp_path):
    out, _ = run(tmp_path, ["random", "greedy", f"first={FAKE}:FirstMoveAgent"], openings=2)
    frame = read_rows(out)
    assert len(frame) == 3 * 2 * 2
    pairs = {frozenset((a, b)) for a, b in zip(frame["agent_p0"], frame["agent_p1"])}
    assert pairs == {frozenset(p) for p in [("random", "greedy"), ("random", "first"), ("greedy", "first")]}


def test_results_are_reproducible_across_runs(tmp_path):
    first, _ = run(tmp_path, ["random", "greedy"], openings=5, name="a.csv")
    second, _ = run(tmp_path, ["random", "greedy"], openings=5, name="b.csv")
    pd.testing.assert_frame_equal(comparable(first), comparable(second))


def test_results_do_not_depend_on_number_of_workers(tmp_path):
    single, _ = run(tmp_path, ["random", "greedy"], openings=6, workers=1, name="w1.csv")
    multi, _ = run(tmp_path, ["random", "greedy"], openings=6, workers=2, name="w2.csv")
    pd.testing.assert_frame_equal(comparable(single), comparable(multi))


def test_different_seeds_change_the_games(tmp_path):
    a, _ = run(tmp_path, ["random", "greedy"], openings=6, seeds=(1,), name="s1.csv")
    b, _ = run(tmp_path, ["random", "greedy"], openings=6, seeds=(2,), name="s2.csv")
    assert not np.array_equal(read_rows(a)["moves"].to_numpy(), read_rows(b)["moves"].to_numpy())


# --- Metrik --------------------------------------------------------------------------------

def test_metrics_columns_are_filled_only_when_agent_has_metrics(tmp_path):
    out, _ = run(tmp_path, ["random", "greedy"], openings=2)
    frame = read_rows(out)
    random_p0 = frame[frame["agent_p0"] == "random"]
    greedy_p0 = frame[frame["agent_p0"] == "greedy"]
    assert random_p0["nodes_p0"].isna().all() and random_p0["nodes_p1"].notna().all()
    assert greedy_p0["nodes_p0"].notna().all() and greedy_p0["nodes_p1"].isna().all()
    assert (greedy_p0["depth_sum_p0"] == greedy_p0["decisions_p0"]).all()  # kedalaman 1 per langkah
    assert (frame["time_p0"] >= 0).all() and (frame["decisions_p0"] > 0).all()


def test_alternative_metric_names_are_recognised(tmp_path):
    out, _ = run(tmp_path, ["random", f"first={FAKE}:FirstMoveAgent"], openings=1)
    row = read_rows(out).query("agent_p0 == 'first'").iloc[0]
    assert row["nodes_p0"] == 7 * row["decisions_p0"]
    assert row["cutoffs_p0"] == 2 * row["decisions_p0"]
    assert row["depth_sum_p0"] == 3 * row["decisions_p0"]
    assert row["elapsed_p0"] == pytest.approx(0.001 * row["decisions_p0"])


def test_depth_time_limit_and_reset_seed_are_forwarded(tmp_path):
    from tests.fake_agents import RecordingAgent
    RecordingAgent.calls.clear()
    run(tmp_path, ["random", f"rec={FAKE}:RecordingAgent"], openings=1, depth=6, time_limit=0.5)
    assert RecordingAgent.calls
    assert all(call[0] == 0.5 and call[1] == 6 for call in RecordingAgent.calls)
    assert all(isinstance(call[2], int) for call in RecordingAgent.calls)
    assert len({call[2] for call in RecordingAgent.calls}) == 2  # satu seed per game (sisi berbeda)


# --- Kegagalan agen ----------------------------------------------------------------------------

@pytest.mark.parametrize("cls,error_prefix", [
    ("IllegalAgent", "illegal_move:99"),
    ("NoneAgent", "illegal_move:None"),
    ("RaisingAgent", "exception:RuntimeError"),
    ("BrokenInitAgent", "init_exception:RuntimeError"),
])
@pytest.mark.parametrize("workers", [1, 2])
def test_bad_agent_forfeits_but_run_continues(tmp_path, capsys, cls, error_prefix, workers):
    out, summary = run(tmp_path, ["random", f"bad={FAKE}:{cls}"], openings=2, workers=workers)
    frame = read_rows(out)
    assert len(frame) == 4 and summary["forfeits"] == 4
    assert (frame["forfeit"] == "bad").all() and (frame["winner"] == "random").all()
    assert frame["error"].str.startswith(error_prefix).all()
    if workers == 1:
        assert "dicatat kalah" in capsys.readouterr().err


def test_state_passed_to_agent_is_a_copy(tmp_path):
    out, _ = run(tmp_path, ["random", f"mut={FAKE}:MutatingAgent"], openings=2)
    frame = read_rows(out)
    assert frame["forfeit"].isna().all()
    assert (frame["score_p0"] + frame["score_p1"] == 98).all()


# --- Resume ----------------------------------------------------------------------------------------

def test_resume_plays_only_missing_games_and_matches_full_run(tmp_path):
    full, _ = run(tmp_path, ["random", "greedy"], openings=6, name="full.csv")
    part, first = run(tmp_path, ["random", "greedy"], openings=2, name="part.csv")
    assert first["played"] == 4
    _, second = run(tmp_path, ["random", "greedy"], openings=6, name="part.csv", resume=True)
    assert second["skipped"] == 4 and second["played"] == 8
    pd.testing.assert_frame_equal(comparable(full), comparable(part))
    assert not read_rows(part).duplicated(["seed", "opening_id", "agent_p0", "agent_p1"]).any()


def test_resume_with_everything_done_plays_nothing(tmp_path):
    _, _ = run(tmp_path, ["random", "greedy"], openings=2, name="x.csv")
    _, summary = run(tmp_path, ["random", "greedy"], openings=2, name="x.csv", resume=True)
    assert summary["played"] == 0 and summary["skipped"] == 4


def test_resume_drops_truncated_last_line(tmp_path):
    out, _ = run(tmp_path, ["random", "greedy"], openings=3, name="trunc.csv")
    with open(out, "a", encoding="utf-8") as handle:
        handle.write("42,2,random,gre")  # proses mati saat menulis
    _, summary = run(tmp_path, ["random", "greedy"], openings=3, name="trunc.csv", resume=True)
    assert summary["played"] == 0
    assert len(read_rows(out)) == 6


def test_existing_output_without_resume_is_refused_and_untouched(tmp_path):
    out, _ = run(tmp_path, ["random", "greedy"], openings=2, name="keep.csv")
    before = open(out, encoding="utf-8").read()
    with pytest.raises(SystemExit, match="sudah ada"):
        run(tmp_path, ["random", "greedy"], openings=2, name="keep.csv")
    assert open(out, encoding="utf-8").read() == before


def test_resume_refuses_different_run_parameters(tmp_path):
    run(tmp_path, ["random", "greedy"], openings=2, plies=4, name="p.csv")
    with pytest.raises(SystemExit, match="parameter"):
        run(tmp_path, ["random", "greedy"], openings=2, plies=6, name="p.csv", resume=True)


# --- Batas langkah ----------------------------------------------------------------------------------------

def test_hit_move_cap_is_recorded(tmp_path, monkeypatch):
    monkeypatch.setattr(engine_api, "MAX_GAME_MOVES", 20)
    monkeypatch.setattr(tournament, "MAX_GAME_MOVES", 20)
    out, _ = run(tmp_path, ["random", "greedy"], openings=10)
    frame = read_rows(out)
    assert frame["moves"].max() == 20
    capped = frame["hit_move_cap"] == 1
    assert capped.any() and (frame.loc[capped, "moves"] == 20).all()
    assert (frame.loc[~capped, "moves"] < 20).all()
    assert (frame["score_p0"] + frame["score_p1"] == 98).all()


# --- CLI -----------------------------------------------------------------------------------------------------

def test_cli_main_runs_and_reports(tmp_path, capsys):
    out = str(tmp_path / "cli.csv")
    code = tournament.main(["--agents", "random,greedy,minimax", "--openings", "2", "--seeds", "1,2",
                            "--workers", "1", "--out", out])
    assert code == 0
    assert len(read_rows(out)) == 8
    assert "agen 'minimax' dilewati" in capsys.readouterr().err


def test_cli_needs_two_agents(tmp_path):
    with pytest.raises(SystemExit, match="minimal 2"):
        tournament.main(["--agents", "random,minimax", "--openings", "1", "--out", str(tmp_path / "x.csv")])


def test_cli_unknown_agent_is_a_clear_error(tmp_path):
    with pytest.raises(SystemExit, match="tidak dikenal"):
        tournament.main(["--agents", "random,grdy", "--out", str(tmp_path / "x.csv")])


def test_play_game_returns_exactly_the_csv_columns():
    task = build_tasks(["random", "greedy"], 1, [1], 4, 4, None)[0]
    row = play_game(task)
    assert set(row) == set(COLUMNS)
    assert row["agent_p0"] == "random" and row["agent_p1"] == "greedy"
    assert row["winner"] in {"random", "greedy", "draw"}


# --- Peringatan pembukaan berulang -----------------------------------------------------------------

def test_count_distinct_openings_respects_the_reachable_position_bound():
    distinct, requested = tournament.count_distinct_openings([42, 123, 2026], 100, 2)
    assert requested == 300
    assert 1 < distinct <= 36  # batas keras: hanya 36 posisi berbeda yang bisa dicapai dalam 2 langkah
    assert tournament.count_distinct_openings([42], 50, 0) == (1, 50)  # tanpa langkah acak: satu posisi awal
    distinct8, requested8 = tournament.count_distinct_openings([42, 123, 2026], 100, 8)
    assert distinct8 == requested8 == 300


def test_duplicate_openings_trigger_a_warning_but_unique_ones_do_not(tmp_path, capsys):
    run(tmp_path, ["random", "greedy"], openings=40, plies=2, name="dup.csv")
    assert "pembukaan yang berbeda" in capsys.readouterr().err
    run(tmp_path, ["random", "greedy"], openings=5, plies=8, name="uniq.csv")
    assert "pembukaan yang berbeda" not in capsys.readouterr().err


# --- Berkas meta -----------------------------------------------------------------------------------------

def read_meta(csv_path):
    import json
    return json.load(open(tournament.meta_path(csv_path), encoding="utf-8"))


def test_meta_file_records_parameters_counts_and_provenance(tmp_path):
    out, summary = run(tmp_path, ["random", "greedy"], openings=3, seeds=(42, 7), plies=6, depth=5,
                       time_limit=0.25, name="m.csv")
    assert tournament.meta_path(out).endswith("m.meta.json")
    meta = read_meta(out)
    assert meta["agents"] == ["random", "greedy"] and meta["pairs"] == 1
    assert (meta["openings"], meta["seeds"], meta["opening_plies"]) == (3, [42, 7], 6)
    assert (meta["depth"], meta["time_limit"]) == (5, 0.25)
    assert meta["games_expected"] == 12 == summary["total"]
    assert meta["requested_openings"] == 6 and 1 <= meta["distinct_openings"] <= 6
    assert meta["max_game_moves"] == 300 and meta["max_sow_rounds"] == 200
    assert meta["python"] and meta["numpy"]
    assert len(meta["runs"]) == 1
    run0 = meta["runs"][0]
    assert (run0["played"], run0["skipped"], run0["forfeits"]) == (12, 0, 0)
    assert run0["finished_at_utc"].endswith("+00:00")
    # hash commit: 40 heksadesimal bila git tersedia di mesin ini; bila tidak, None (keduanya sah)
    assert run0["git_commit"] is None or len(run0["git_commit"]) == 40


def test_resume_appends_a_run_entry_instead_of_overwriting_history(tmp_path):
    out, _ = run(tmp_path, ["random", "greedy"], openings=2, name="r.csv")
    run(tmp_path, ["random", "greedy"], openings=4, name="r.csv", resume=True)
    runs = read_meta(out)["runs"]
    assert [(r["played"], r["skipped"]) for r in runs] == [(4, 0), (4, 4)]
    assert read_meta(out)["games_expected"] == 8  # parameter statis mengikuti pemanggilan terakhir


def test_forfeits_are_counted_in_meta(tmp_path):
    out, _ = run(tmp_path, ["random", f"bad={FAKE}:IllegalAgent"], openings=2, name="f.csv")
    assert read_meta(out)["runs"][0]["forfeits"] == 4
