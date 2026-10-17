"""
Modul Utilitas Metrik Kinerja Pencarian (T23).
Digunakan untuk mengukur nodes expanded, alpha-beta cutoff, kedalaman, dan waktu eksekusi.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class SearchMetrics:
    nodes_expanded: int = 0
    cutoffs: int = 0
    max_depth_reached: int = 0
    execution_time_sec: float = 0.0
    extra_data: Dict[str, Any] = field(default_factory=dict)

    def reset(self):
        """Mereset seluruh metrik ke nilai awal."""
        self.nodes_expanded = 0
        self.cutoffs = 0
        self.max_depth_reached = 0
        self.execution_time_sec = 0.0
        self.extra_data.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Mengubah metrik ke dalam bentuk dictionary untuk logging CSV."""
        return {
            "nodes_expanded": self.nodes_expanded,
            "cutoffs": self.cutoffs,
            "max_depth_reached": self.max_depth_reached,
            "execution_time_sec": round(self.execution_time_sec, 5),
            **self.extra_data
        }


class MetricsTimer:
    """Context manager untuk mengukur waktu eksekusi suatu blok kode / fungsi pencarian langkah."""
    def __init__(self, metrics: SearchMetrics):
        self.metrics = metrics
        self.start_time = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.perf_counter()
        self.metrics.execution_time_sec = end_time - self.start_time