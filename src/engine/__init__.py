"""
API Interface & Board State untuk Congklak-Master.
Terintegrasi langsung dengan modul Board v1.
"""

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
from src.engine.board import (
    Board, PLAYER_0, PLAYER_1, P0_PITS, P0_STORE, P1_PITS, P1_STORE
)


@dataclass
class CongklakState:
    board: np.ndarray
    current_player: int
    is_terminal: bool = False

    def copy(self) -> 'CongklakState':
        return CongklakState(
            board=self.board.copy(),
            current_player=self.current_player,
            is_terminal=self.is_terminal
        )


def get_initial_state() -> CongklakState:
    b = Board()
    return CongklakState(board=b.state, current_player=PLAYER_0, is_terminal=False)


def get_legal_moves(state: CongklakState) -> List[int]:
    if state.is_terminal:
        return []
    b = Board(state.board)
    return b.get_valid_moves(state.current_player)


def is_terminal(state: CongklakState) -> bool:
    return state.is_terminal or len(get_legal_moves(state)) == 0


def get_scores(state: CongklakState) -> Tuple[int, int]:
    return int(state.board[P0_STORE]), int(state.board[P1_STORE])


def apply_move(state: CongklakState, pit_index: int) -> CongklakState:
    b = Board(state.board)
    next_player, _, terminal = b.step(state.current_player, pit_index)
    return CongklakState(
        board=b.state,
        current_player=next_player,
        is_terminal=terminal
    )