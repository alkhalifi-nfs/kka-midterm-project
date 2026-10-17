"""
Unit Test untuk Modul SearchMetrics & MetricsTimer (T23).
"""

import time
import pytest
from src.utils.metrics import SearchMetrics, MetricsTimer


def test_metrics_initialization():
    m = SearchMetrics()
    assert m.nodes_expanded == 0
    assert m.cutoffs == 0
    assert m.max_depth_reached == 0
    assert m.execution_time_sec == 0.0


def test_metrics_timer_context():
    m = SearchMetrics()
    with MetricsTimer(m):
        time.sleep(0.05)  # Simulasi proses pencarian

    assert m.execution_time_sec >= 0.04


def test_metrics_to_dict():
    m = SearchMetrics(nodes_expanded=150, cutoffs=25, max_depth_reached=4)
    m.extra_data["branching_factor"] = 3.5
    
    d = m.to_dict()
    assert d["nodes_expanded"] == 150
    assert d["cutoffs"] == 25
    assert d["max_depth_reached"] == 4
    assert d["branching_factor"] == 3.5


def test_metrics_reset():
    m = SearchMetrics(nodes_expanded=50, cutoffs=10)
    m.reset()
    assert m.nodes_expanded == 0
    assert m.cutoffs == 0