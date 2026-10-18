"""
Paket engine Congklak-Master.
Hanya me-re-export dari src.engine.api (satu-satunya sumber logika publik),
sehingga `from src.engine import CongklakState` adalah kelas yang sama dengan
`from src.engine.api import CongklakState`.
"""

from src.engine.api import (
    Board,
    CongklakState,
    MAX_GAME_MOVES,
    MAX_SOW_ROUNDS,
    PLAYER_0,
    PLAYER_1,
    P0_PITS,
    P0_STORE,
    P1_PITS,
    P1_STORE,
    apply_move,
    get_initial_state,
    get_legal_moves,
    get_score_diff,
    get_scores,
    get_winner,
    is_terminal,
    state_key,
)

__all__ = [
    "Board",
    "CongklakState",
    "MAX_GAME_MOVES",
    "MAX_SOW_ROUNDS",
    "PLAYER_0",
    "PLAYER_1",
    "P0_PITS",
    "P0_STORE",
    "P1_PITS",
    "P1_STORE",
    "apply_move",
    "get_initial_state",
    "get_legal_moves",
    "get_score_diff",
    "get_scores",
    "get_winner",
    "is_terminal",
    "state_key",
]
