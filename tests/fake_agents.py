"""
Agen palsu untuk menguji runner turnamen (jalur gagal dan variasi metrics).
Dipasang lewat spesifikasi "alias=tests.fake_agents:Kelas", sehingga ikut terlihat
oleh proses worker multiprocessing.
"""
from types import SimpleNamespace

from src.engine.api import get_legal_moves


class FirstMoveAgent:
    """Selalu memilih lubang legal pertama. Metrics memakai nama alternatif (nodes_expanded, max_depth_reached)."""
    name = "first"

    def __init__(self):
        self.metrics = None

    def choose_move(self, state, time_limit=None, depth=None):
        moves = get_legal_moves(state)
        self.metrics = SimpleNamespace(nodes_expanded=7, cutoffs=2, max_depth_reached=3,
                                       execution_time_sec=0.001)
        return moves[0]


class IllegalAgent:
    name = "illegal"

    def choose_move(self, state, time_limit=None, depth=None):
        return 99


class NoneAgent:
    name = "none"

    def choose_move(self, state, time_limit=None, depth=None):
        return None


class RaisingAgent:
    name = "raising"

    def choose_move(self, state, time_limit=None, depth=None):
        raise RuntimeError("sengaja gagal")


class BrokenInitAgent:
    name = "broken_init"

    def __init__(self):
        raise RuntimeError("gagal dibuat")


class MutatingAgent:
    """Merusak state yang diterimanya; runner harus meneruskan salinan."""
    name = "mutating"

    def choose_move(self, state, time_limit=None, depth=None):
        move = get_legal_moves(state)[0]
        state.board[:] = 0
        state.current_player = 1 - state.current_player
        return move


class StateLogAgentA:
    """Mencatat (move_count, papan, pemain) setiap state yang diterima; memilih lubang legal pertama."""
    name = "log_a"
    seen = []

    def choose_move(self, state, time_limit=None, depth=None):
        StateLogAgentA.seen.append((int(state.move_count), state.board.tobytes(), int(state.current_player)))
        return get_legal_moves(state)[0]


class StateLogAgentB(StateLogAgentA):
    name = "log_b"


class RecordingAgent:
    """Mencatat argumen yang diterima, untuk memeriksa penerusan depth/time_limit/reset."""
    name = "recording"
    calls = []

    def __init__(self):
        self.seed = None

    def reset(self, seed=None):
        self.seed = seed

    def choose_move(self, state, time_limit=None, depth=None):
        RecordingAgent.calls.append((time_limit, depth, self.seed))
        return get_legal_moves(state)[0]
