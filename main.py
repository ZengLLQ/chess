#!/usr/bin/env python3
"""
Single-File Full Chess Game & AI Coach
Palette strictly restricted to:
  - Deep Chocolate Brown (#3B2314)
  - Soft Sage            (#9CAF88)
  - Warm Cream           (#F5EFE6)
"""

from __future__ import annotations

import copy
import os
import threading
import tkinter as tk
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

# Optional Google GenAI SDK (gemini-skills-suite compliant)
try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


# ============================================================================
# 1. STRICT 3-COLOR PALETTE CONSTANTS
# ============================================================================
CHOCOLATE: str = "#3B2314"  # Deep chocolate brown
SAGE: str = "#9CAF88"       # Soft sage
CREAM: str = "#F5EFE6"      # Warm cream


# ============================================================================
# 2. DOMAIN MODELS & CHESS CONSTANTS
# ============================================================================
class Color(str, Enum):
    WHITE = "w"
    BLACK = "b"

    @property
    def opposite(self) -> Color:
        return Color.BLACK if self == Color.WHITE else Color.WHITE

    @property
    def label(self) -> str:
        return "White" if self == Color.WHITE else "Black"


class PieceType(str, Enum):
    PAWN = "P"
    KNIGHT = "N"
    BISHOP = "B"
    ROOK = "R"
    QUEEN = "Q"
    KING = "K"


UNICODE_GLYPHS: dict[tuple[Color, PieceType], str] = {
    (Color.WHITE, PieceType.KING): "♚",
    (Color.WHITE, PieceType.QUEEN): "♛",
    (Color.WHITE, PieceType.ROOK): "♜",
    (Color.WHITE, PieceType.BISHOP): "♝",
    (Color.WHITE, PieceType.KNIGHT): "♞",
    (Color.WHITE, PieceType.PAWN): "♟",
    (Color.BLACK, PieceType.KING): "♚",
    (Color.BLACK, PieceType.QUEEN): "♛",
    (Color.BLACK, PieceType.ROOK): "♜",
    (Color.BLACK, PieceType.BISHOP): "♝",
    (Color.BLACK, PieceType.KNIGHT): "♞",
    (Color.BLACK, PieceType.PAWN): "♟",
}

OUTLINE_GLYPHS: dict[PieceType, str] = {
    PieceType.KING: "♔",
    PieceType.QUEEN: "♕",
    PieceType.ROOK: "♖",
    PieceType.BISHOP: "♗",
    PieceType.KNIGHT: "♘",
    PieceType.PAWN: "♙",
}

PIECE_VALUES: dict[PieceType, int] = {
    PieceType.PAWN: 100,
    PieceType.KNIGHT: 320,
    PieceType.BISHOP: 330,
    PieceType.ROOK: 500,
    PieceType.QUEEN: 900,
    PieceType.KING: 20000,
}

# Positional Piece-Square Tables (from White's perspective, row 0 = rank 8)
PST: dict[PieceType, list[list[int]]] = {
    PieceType.PAWN: [
        [0,  0,  0,  0,  0,  0,  0,  0],
        [50, 50, 50, 50, 50, 50, 50, 50],
        [10, 10, 20, 30, 30, 20, 10, 10],
        [5,  5, 10, 25, 25, 10,  5,  5],
        [0,  0,  0, 20, 20,  0,  0,  0],
        [5, -5,-10,  0,  0,-10, -5,  5],
        [5, 10, 10,-20,-20, 10, 10,  5],
        [0,  0,  0,  0,  0,  0,  0,  0],
    ],
    PieceType.KNIGHT: [
        [-50,-40,-30,-30,-30,-30,-40,-50],
        [-40,-20,  0,  0,  0,  0,-20,-40],
        [-30,  0, 10, 15, 15, 10,  0,-30],
        [-30,  5, 15, 20, 20, 15,  5,-30],
        [-30,  0, 15, 20, 20, 15,  0,-30],
        [-30,  5, 10, 15, 15, 10,  5,-30],
        [-40,-20,  0,  5,  5,  0,-20,-40],
        [-50,-40,-30,-30,-30,-30,-40,-50],
    ],
    PieceType.BISHOP: [
        [-20,-10,-10,-10,-10,-10,-10,-20],
        [-10,  0,  0,  0,  0,  0,  0,-10],
        [-10,  0,  5, 10, 10,  5,  0,-10],
        [-10,  5,  5, 10, 10,  5,  5,-10],
        [-10,  0, 10, 10, 10, 10,  0,-10],
        [-10, 10, 10, 10, 10, 10, 10,-10],
        [-10,  5,  0,  0,  0,  0,  5,-10],
        [-20,-10,-10,-10,-10,-10,-10,-20],
    ],
    PieceType.ROOK: [
        [0,  0,  0,  0,  0,  0,  0,  0],
        [5, 10, 10, 10, 10, 10, 10,  5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [0,  0,  0,  5,  5,  0,  0,  0],
    ],
    PieceType.QUEEN: [
        [-20,-10,-10, -5, -5,-10,-10,-20],
        [-10,  0,  0,  0,  0,  0,  0,-10],
        [-10,  0,  5,  5,  5,  5,  0,-10],
        [-5,  0,  5,  5,  5,  5,  0, -5],
        [0,  0,  5,  5,  5,  5,  0, -5],
        [-10,  5,  5,  5,  5,  5,  0,-10],
        [-10,  0,  5,  0,  0,  0,  0,-10],
        [-20,-10,-10, -5, -5,-10,-10,-20],
    ],
    PieceType.KING: [
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-20,-30,-30,-40,-40,-30,-30,-20],
        [-10,-20,-20,-20,-20,-20,-20,-10],
        [20, 20,  0,  0,  0,  0, 20, 20],
        [20, 30, 10,  0,  0, 10, 30, 20],
    ],
}


@dataclass(frozen=True)
class Piece:
    color: Color
    kind: PieceType

    @property
    def glyph(self) -> str:
        return UNICODE_GLYPHS[(self.color, self.kind)]


@dataclass(frozen=True)
class Move:
    start: tuple[int, int]
    end: tuple[int, int]
    piece: Piece
    captured: Optional[Piece] = None
    promotion: Optional[PieceType] = None
    is_en_passant: bool = False
    is_castling: bool = False
    san: str = ""

    @property
    def uci(self) -> str:
        files = "abcdefgh"
        s_r, s_c = self.start
        e_r, e_c = self.end
        promo = self.promotion.value.lower() if self.promotion else ""
        return f"{files[s_c]}{8 - s_r}{files[e_c]}{8 - e_r}{promo}"


# ============================================================================
# 3. CHESS STATE & FULL LEGAL MOVE ENGINE
# ============================================================================
@dataclass
class CastlingRights:
    wk: bool = True
    wq: bool = True
    bk: bool = True
    bq: bool = True

    def copy(self) -> CastlingRights:
        return CastlingRights(self.wk, self.wq, self.bk, self.bq)


class ChessState:
    def __init__(self) -> None:
        self.board: list[list[Optional[Piece]]] = [[None] * 8 for _ in range(8)]
        self.turn: Color = Color.WHITE
        self.castling: CastlingRights = CastlingRights()
        self.en_passant_target: Optional[tuple[int, int]] = None
        self.halfmove_clock: int = 0
        self.fullmove_number: int = 1
        self.move_history: list[Move] = []
        self.position_counts: dict[str, int] = {}
        self.captured_white: list[Piece] = []
        self.captured_black: list[Piece] = []
        self._setup_starting_board()
        self._record_position()

    def _setup_starting_board(self) -> None:
        back_rank = [
            PieceType.ROOK, PieceType.KNIGHT, PieceType.BISHOP, PieceType.QUEEN,
            PieceType.KING, PieceType.BISHOP, PieceType.KNIGHT, PieceType.ROOK,
        ]
        for c in range(8):
            self.board[0][c] = Piece(Color.BLACK, back_rank[c])
            self.board[1][c] = Piece(Color.BLACK, PieceType.PAWN)
            self.board[6][c] = Piece(Color.WHITE, PieceType.PAWN)
            self.board[7][c] = Piece(Color.WHITE, back_rank[c])

    def clone(self) -> ChessState:
        state = ChessState.__new__(ChessState)
        state.board = [row[:] for row in self.board]
        state.turn = self.turn
        state.castling = self.castling.copy()
        state.en_passant_target = self.en_passant_target
        state.halfmove_clock = self.halfmove_clock
        state.fullmove_number = self.fullmove_number
        state.move_history = self.move_history[:]
        state.position_counts = self.position_counts.copy()
        state.captured_white = self.captured_white[:]
        state.captured_black = self.captured_black[:]
        return state

    def position_key(self) -> str:
        rows = []
        for r in range(8):
            empty = 0
            row_str = ""
            for c in range(8):
                p = self.board[r][c]
                if p is None:
                    empty += 1
                else:
                    if empty:
                        row_str += str(empty)
                        empty = 0
                    ch = p.kind.value
                    row_str += ch if p.color == Color.WHITE else ch.lower()
            if empty:
                row_str += str(empty)
            rows.append(row_str)
        c_str = (
                        ("K" if self.castling.wk else "")
                        + ("Q" if self.castling.wq else "")
                        + ("k" if self.castling.bk else "")
                        + ("q" if self.castling.bq else "")
                ) or "-"
        ep_str = "-"
        if self.en_passant_target:
            er, ec = self.en_passant_target
            ep_str = f"{'abcdefgh'[ec]}{8 - er}"
        return f"{'/'.join(rows)} {self.turn.value} {c_str} {ep_str}"

    def to_fen(self) -> str:
        return f"{self.position_key()} {self.halfmove_clock} {self.fullmove_number}"

    def _record_position(self) -> None:
        key = self.position_key()
        self.position_counts[key] = self.position_counts.get(key, 0) + 1

    def find_king(self, color: Color) -> Optional[tuple[int, int]]:
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p and p.color == color and p.kind == PieceType.KING:
                    return (r, c)
        return None

    def is_square_attacked(self, square: tuple[int, int], by_color: Color) -> bool:
        tr, tc = square
        # 1. Pawn attacks
        pawn_dir = 1 if by_color == Color.WHITE else -1
        pr = tr + pawn_dir
        if 0 <= pr < 8:
            for pc in (tc - 1, tc + 1):
                if 0 <= pc < 8:
                    p = self.board[pr][pc]
                    if p and p.color == by_color and p.kind == PieceType.PAWN:
                        return True

        # 2. Knight attacks
        knight_offsets = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1),
        ]
        for dr, dc in knight_offsets:
            nr, nc = tr + dr, tc + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                p = self.board[nr][nc]
                if p and p.color == by_color and p.kind == PieceType.KNIGHT:
                    return True

        # 3. King attacks
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                kr, kc = tr + dr, tc + dc
                if 0 <= kr < 8 and 0 <= kc < 8:
                    p = self.board[kr][kc]
                    if p and p.color == by_color and p.kind == PieceType.KING:
                        return True

        # 4. Orthogonal sliders (Rook / Queen)
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = tr + dr, tc + dc
            while 0 <= nr < 8 and 0 <= nc < 8:
                p = self.board[nr][nc]
                if p:
                    if p.color == by_color and p.kind in (PieceType.ROOK, PieceType.QUEEN):
                        return True
                    break
                nr += dr
                nc += dc

        # 5. Diagonal sliders (Bishop / Queen)
        for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            nr, nc = tr + dr, tc + dc
            while 0 <= nr < 8 and 0 <= nc < 8:
                p = self.board[nr][nc]
                if p:
                    if p.color == by_color and p.kind in (PieceType.BISHOP, PieceType.QUEEN):
                        return True
                    break
                nr += dr
                nc += dc

        return False

    def in_check(self, color: Color) -> bool:
        king_sq = self.find_king(color)
        if not king_sq:
            return False
        return self.is_square_attacked(king_sq, color.opposite)

    def generate_pseudo_moves(self, color: Color) -> list[Move]:
        moves: list[Move] = []
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if not p or p.color != color:
                    continue
                if p.kind == PieceType.PAWN:
                    self._gen_pawn_moves(r, c, p, moves)
                elif p.kind == PieceType.KNIGHT:
                    self._gen_knight_moves(r, c, p, moves)
                elif p.kind == PieceType.BISHOP:
                    self._gen_slider_moves(r, c, p, [(-1, -1), (-1, 1), (1, -1), (1, 1)], moves)
                elif p.kind == PieceType.ROOK:
                    self._gen_slider_moves(r, c, p, [(-1, 0), (1, 0), (0, -1), (0, 1)], moves)
                elif p.kind == PieceType.QUEEN:
                    self._gen_slider_moves(
                        r, c, p,
                        [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)],
                        moves,
                    )
                elif p.kind == PieceType.KING:
                    self._gen_king_moves(r, c, p, moves)
        return moves

    def _gen_pawn_moves(self, r: int, c: int, p: Piece, moves: list[Move]) -> None:
        step = -1 if p.color == Color.WHITE else 1
        start_row = 6 if p.color == Color.WHITE else 1
        promo_row = 0 if p.color == Color.WHITE else 7
        promo_types = (PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT)

        # Single step forward
        nr = r + step
        if 0 <= nr < 8 and self.board[nr][c] is None:
            if nr == promo_row:
                for pt in promo_types:
                    moves.append(Move((r, c), (nr, c), p, promotion=pt))
            else:
                moves.append(Move((r, c), (nr, c), p))
                # Double step from starting rank
                nnr = r + 2 * step
                if r == start_row and self.board[nnr][c] is None:
                    moves.append(Move((r, c), (nnr, c), p))

        # Captures (diagonal + en passant)
        for dc in (-1, 1):
            nc = c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                target = self.board[nr][nc]
                if target and target.color != p.color:
                    if nr == promo_row:
                        for pt in promo_types:
                            moves.append(Move((r, c), (nr, nc), p, captured=target, promotion=pt))
                    else:
                        moves.append(Move((r, c), (nr, nc), p, captured=target))
                elif self.en_passant_target == (nr, nc):
                    ep_captured = self.board[r][nc]
                    if ep_captured and ep_captured.color != p.color:
                        moves.append(
                            Move((r, c), (nr, nc), p, captured=ep_captured, is_en_passant=True)
                        )

    def _gen_knight_moves(self, r: int, c: int, p: Piece, moves: list[Move]) -> None:
        offsets = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1),
        ]
        for dr, dc in offsets:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                target = self.board[nr][nc]
                if target is None or target.color != p.color:
                    moves.append(Move((r, c), (nr, nc), p, captured=target))

    def _gen_slider_moves(
            self,
            r: int,
            c: int,
            p: Piece,
            directions: list[tuple[int, int]],
            moves: list[Move],
    ) -> None:
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 8 and 0 <= nc < 8:
                target = self.board[nr][nc]
                if target is None:
                    moves.append(Move((r, c), (nr, nc), p))
                else:
                    if target.color != p.color:
                        moves.append(Move((r, c), (nr, nc), p, captured=target))
                    break
                nr += dr
                nc += dc

    def _gen_king_moves(self, r: int, c: int, p: Piece, moves: list[Move]) -> None:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    target = self.board[nr][nc]
                    if target is None or target.color != p.color:
                        moves.append(Move((r, c), (nr, nc), p, captured=target))

        # Castling
        if self.in_check(p.color):
            return
        opp = p.color.opposite
        if p.color == Color.WHITE and r == 7 and c == 4:
            if (
                    self.castling.wk
                    and self.board[7][5] is None
                    and self.board[7][6] is None
                    and not self.is_square_attacked((7, 5), opp)
                    and not self.is_square_attacked((7, 6), opp)
            ):
                moves.append(Move((7, 4), (7, 6), p, is_castling=True))
            if (
                    self.castling.wq
                    and self.board[7][3] is None
                    and self.board[7][2] is None
                    and self.board[7][1] is None
                    and not self.is_square_attacked((7, 3), opp)
                    and not self.is_square_attacked((7, 2), opp)
            ):
                moves.append(Move((7, 4), (7, 2), p, is_castling=True))
        elif p.color == Color.BLACK and r == 0 and c == 4:
            if (
                    self.castling.bk
                    and self.board[0][5] is None
                    and self.board[0][6] is None
                    and not self.is_square_attacked((0, 5), opp)
                    and not self.is_square_attacked((0, 6), opp)
            ):
                moves.append(Move((0, 4), (0, 6), p, is_castling=True))
            if (
                    self.castling.bq
                    and self.board[0][3] is None
                    and self.board[0][2] is None
                    and self.board[0][1] is None
                    and not self.is_square_attacked((0, 3), opp)
                    and not self.is_square_attacked((0, 2), opp)
            ):
                moves.append(Move((0, 4), (0, 2), p, is_castling=True))

    def apply_move_unverified(self, move: Move) -> None:
        sr, sc = move.start
        er, ec = move.end
        p = move.piece

        # Remove piece from start
        self.board[sr][sc] = None

        # Handle en passant capture removal
        if move.is_en_passant:
            self.board[sr][ec] = None

        # Handle castling rook movement
        if move.is_castling:
            if ec == 6:  # Kingside
                rook = self.board[sr][7]
                self.board[sr][7] = None
                self.board[sr][5] = rook
            elif ec == 2:  # Queenside
                rook = self.board[sr][0]
                self.board[sr][0] = None
                self.board[sr][3] = rook

        # Place piece at destination (with optional promotion)
        placed_piece = Piece(p.color, move.promotion) if move.promotion else p
        self.board[er][ec] = placed_piece

        # Track captured pieces
        if move.captured:
            if move.captured.color == Color.WHITE:
                self.captured_white.append(move.captured)
            else:
                self.captured_black.append(move.captured)

        # Update castling rights
        if p.kind == PieceType.KING:
            if p.color == Color.WHITE:
                self.castling.wk = False
                self.castling.wq = False
            else:
                self.castling.bk = False
                self.castling.bq = False
        if (sr, sc) == (7, 0) or (er, ec) == (7, 0):
            self.castling.wq = False
        if (sr, sc) == (7, 7) or (er, ec) == (7, 7):
            self.castling.wk = False
        if (sr, sc) == (0, 0) or (er, ec) == (0, 0):
            self.castling.bq = False
        if (sr, sc) == (0, 7) or (er, ec) == (0, 7):
            self.castling.bk = False

        # Update en passant target
        if p.kind == PieceType.PAWN and abs(er - sr) == 2:
            self.en_passant_target = ((sr + er) // 2, sc)
        else:
            self.en_passant_target = None

        # Halfmove & fullmove counters
        if p.kind == PieceType.PAWN or move.captured is not None:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        if self.turn == Color.BLACK:
            self.fullmove_number += 1

        self.turn = self.turn.opposite

    def generate_legal_moves(self, color: Optional[Color] = None) -> list[Move]:
        side = color or self.turn
        legal: list[Move] = []
        for m in self.generate_pseudo_moves(side):
            sim = self.clone()
            sim.apply_move_unverified(m)
            if not sim.in_check(side):
                legal.append(m)
        return legal

    def format_san(self, move: Move, legal_moves: list[Move]) -> str:
        if move.is_castling:
            base = "O-O" if move.end[1] == 6 else "O-O-O"
        else:
            files = "abcdefgh"
            sr, sc = move.start
            er, ec = move.end
            dest = f"{files[ec]}{8 - er}"

            if move.piece.kind == PieceType.PAWN:
                base = f"{files[sc]}x{dest}" if move.captured else dest
                if move.promotion:
                    base += f"={move.promotion.value}"
            else:
                ambiguous = [
                    m for m in legal_moves
                    if m.end == move.end
                       and m.piece.kind == move.piece.kind
                       and m.start != move.start
                ]
                disambig = ""
                if ambiguous:
                    same_file = any(m.start[1] == sc for m in ambiguous)
                    same_rank = any(m.start[0] == sr for m in ambiguous)
                    if not same_file:
                        disambig = files[sc]
                    elif not same_rank:
                        disambig = str(8 - sr)
                    else:
                        disambig = f"{files[sc]}{8 - sr}"
                cap = "x" if move.captured else ""
                base = f"{move.piece.kind.value}{disambig}{cap}{dest}"

        sim = self.clone()
        sim.apply_move_unverified(move)
        opp_legal = sim.generate_legal_moves(sim.turn)
        if sim.in_check(sim.turn):
            base += "#" if not opp_legal else "+"
        return base

    def make_move(self, move: Move) -> Move:
        legal = self.generate_legal_moves(self.turn)
        san_str = self.format_san(move, legal)
        recorded = Move(
            start=move.start,
            end=move.end,
            piece=move.piece,
            captured=move.captured,
            promotion=move.promotion,
            is_en_passant=move.is_en_passant,
            is_castling=move.is_castling,
            san=san_str,
        )
        self.apply_move_unverified(recorded)
        self.move_history.append(recorded)
        self._record_position()
        return recorded

    def is_insufficient_material(self) -> bool:
        pieces: list[Piece] = []
        bishops_sq_colors: list[int] = []
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p and p.kind != PieceType.KING:
                    pieces.append(p)
                    if p.kind == PieceType.BISHOP:
                        bishops_sq_colors.append((r + c) % 2)
        if not pieces:
            return True
        if len(pieces) == 1 and pieces[0].kind in (PieceType.KNIGHT, PieceType.BISHOP):
            return True
        if len(pieces) == 2 and all(p.kind == PieceType.BISHOP for p in pieces):
            return bishops_sq_colors[0] == bishops_sq_colors[1]
        return False

    def game_status(self) -> tuple[bool, str]:
        legal = self.generate_legal_moves(self.turn)
        if not legal:
            if self.in_check(self.turn):
                winner = self.turn.opposite.label
                return True, f"Checkmate — {winner} wins!"
            return True, "Draw by Stalemate"
        if self.halfmove_clock >= 100:
            return True, "Draw by 50-Move Rule"
        if self.position_counts.get(self.position_key(), 0) >= 3:
            return True, "Draw by Threefold Repetition"
        if self.is_insufficient_material():
            return True, "Draw by Insufficient Material"
        if self.in_check(self.turn):
            return False, f"{self.turn.label} to move (Check!)"
        return False, f"{self.turn.label} to move"


# ============================================================================
# 4. MINIMAX + ALPHA-BETA PRUNING ENGINE & GEMINI AI COACH
# ============================================================================
class ChessEngine:
    @staticmethod
    def evaluate(state: ChessState) -> int:
        score = 0
        for r in range(8):
            for c in range(8):
                p = state.board[r][c]
                if not p:
                    continue
                base = PIECE_VALUES[p.kind]
                table_r = r if p.color == Color.WHITE else (7 - r)
                positional = PST[p.kind][table_r][c]
                if p.color == Color.WHITE:
                    score += base + positional
                else:
                    score -= base + positional
        return score

    @classmethod
    def choose_move(cls, state: ChessState, depth: int = 3) -> Optional[Move]:
        legal = state.generate_legal_moves(state.turn)
        if not legal:
            return None

        # Move ordering: captures and promotions first for faster pruning
        def move_priority(m: Move) -> int:
            val = 0
            if m.captured:
                val += 10 * PIECE_VALUES[m.captured.kind] - PIECE_VALUES[m.piece.kind]
            if m.promotion:
                val += PIECE_VALUES[m.promotion]
            return val

        legal.sort(key=move_priority, reverse=True)
        maximizing = state.turn == Color.WHITE
        best_move = legal[0]
        alpha = -999_999
        beta = 999_999

        if maximizing:
            best_val = -999_999
            for m in legal:
                child = state.clone()
                child.apply_move_unverified(m)
                val = cls._alphabeta(child, depth - 1, alpha, beta, False)
                if val > best_val:
                    best_val = val
                    best_move = m
                alpha = max(alpha, val)
        else:
            best_val = 999_999
            for m in legal:
                child = state.clone()
                child.apply_move_unverified(m)
                val = cls._alphabeta(child, depth - 1, alpha, beta, True)
                if val < best_val:
                    best_val = val
                    best_move = m
                beta = min(beta, val)

        return best_move

    @classmethod
    def _alphabeta(
            cls,
            state: ChessState,
            depth: int,
            alpha: int,
            beta: int,
            maximizing: bool,
    ) -> int:
        legal = state.generate_legal_moves(state.turn)
        if depth == 0 or not legal:
            if not legal:
                if state.in_check(state.turn):
                    return -100_000 - depth if maximizing else 100_000 + depth
                return 0
            return cls.evaluate(state)

        if maximizing:
            value = -999_999
            for m in legal:
                child = state.clone()
                child.apply_move_unverified(m)
                value = max(value, cls._alphabeta(child, depth - 1, alpha, beta, False))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = 999_999
            for m in legal:
                child = state.clone()
                child.apply_move_unverified(m)
                value = min(value, cls._alphabeta(child, depth - 1, alpha, beta, True))
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value


class GeminiChessCoach:
    """
    Stateful chess coach powered by google-genai Interactions API (gemini-3.8-flash).
    Automatically falls back to built-in positional analysis if no API key is configured.
    """

    def __init__(self) -> None:
        self.previous_interaction_id: Optional[str] = None
        self.client = None
        if HAS_GENAI and (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
            try:
                self.client = genai.Client()
            except Exception:
                self.client = None

    def advise(self, state: ChessState) -> str:
        best_local = ChessEngine.choose_move(state, depth=3)
        eval_cp = ChessEngine.evaluate(state) / 100.0
        local_san = state.format_san(best_local, state.generate_legal_moves()) if best_local else "None"

        if self.client is not None:
            try:
                prompt = (
                    f"You are a concise Grandmaster Chess Coach. Current FEN: {state.to_fen()}. "
                    f"Turn: {state.turn.label}. Engine candidate: {local_san} (eval {eval_cp:+.2f}). "
                    "In 2 short sentences, explain the best tactical or strategic plan here."
                )
                kwargs: dict[str, object] = {
                    "model": "gemini-3.8-flash",
                    "input": prompt,
                }
                if self.previous_interaction_id:
                    kwargs["previous_interaction_id"] = self.previous_interaction_id

                interaction = self.client.interactions.create(**kwargs)
                self.previous_interaction_id = interaction.id
                if getattr(interaction, "output_text", None):
                    return f"Gemini 3.8 Coach: {interaction.output_text.strip()}"
            except Exception:
                pass

        # Fallback deterministic grandmaster coach insight
        phase = "Opening" if state.fullmove_number <= 10 else ("Endgame" if len(state.captured_white) + len(state.captured_black) >= 18 else "Middlegame")
        sign = "White" if eval_cp > 0.25 else ("Black" if eval_cp < -0.25 else "Balanced")
        return (
            f"[{phase} | Eval {eval_cp:+.2f} ({sign})] "
            f"Recommended move for {state.turn.label}: {local_san}."
        )


# ============================================================================
# 5. TKINTER GUI (STRICTLY 3 COLORS: CHOCOLATE, SAGE, CREAM)
# ============================================================================
class ChessApp:
    BOARD_PX = 600
    SQ_PX = BOARD_PX // 8

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Royal Sage Chess — Deep Chocolate • Soft Sage • Warm Cream")
        self.root.configure(bg=CHOCOLATE)
        self.root.resizable(False, False)

        self.state = ChessState()
        self.snapshots: list[ChessState] = []
        self.coach = GeminiChessCoach()

        self.selected_sq: Optional[tuple[int, int]] = None
        self.valid_moves_for_selected: list[Move] = []
        self.pending_promotion_moves: list[Move] = []
        self.flipped: bool = False
        self.vs_ai: bool = True
        self.ai_thinking: bool = False

        self._build_layout()
        self._render_all()

    def _build_layout(self) -> None:
        main_frame = tk.Frame(self.root, bg=CHOCOLATE, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left column: Board + Coordinate Margin
        board_container = tk.Frame(
            main_frame,
            bg=CHOCOLATE,
            highlightbackground=SAGE,
            highlightthickness=3,
            padx=14,
            pady=14,
        )
        board_container.pack(side=tk.LEFT, padx=(0, 20))

        self.canvas = tk.Canvas(
            board_container,
            width=self.BOARD_PX,
            height=self.BOARD_PX,
            bg=CHOCOLATE,
            highlightthickness=0,
            cursor="hand2",
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # Right column: Sidebar Controls, Status, Captured & Move Log
        sidebar = tk.Frame(main_frame, bg=CHOCOLATE, width=320)
        sidebar.pack(side=tk.RIGHT, fill=tk.BOTH)
        sidebar.pack_propagate(False)

        # Title Header
        header = tk.Label(
            sidebar,
            text="ROYAL SAGE CHESS",
            font=("Georgia", 18, "bold"),
            bg=CHOCOLATE,
            fg=CREAM,
            anchor="w",
        )
        header.pack(fill=tk.X, pady=(0, 2))

        sub = tk.Label(
            sidebar,
            text="CHOCOLATE • SAGE • CREAM",
            font=("Consolas", 9, "bold"),
            bg=CHOCOLATE,
            fg=SAGE,
            anchor="w",
        )
        sub.pack(fill=tk.X, pady=(0, 12))

        # Status Banner
        self.status_label = tk.Label(
            sidebar,
            text="White to move",
            font=("Georgia", 12, "bold"),
            bg=SAGE,
            fg=CHOCOLATE,
            padx=10,
            pady=8,
            anchor="center",
        )
        self.status_label.pack(fill=tk.X, pady=(0, 10))

        # Captured Pieces Card
        cap_card = tk.Frame(
            sidebar,
            bg=CREAM,
            highlightbackground=SAGE,
            highlightthickness=2,
            padx=10,
            pady=8,
        )
        cap_card.pack(fill=tk.X, pady=(0, 10))

        self.cap_black_label = tk.Label(
            cap_card,
            text="White captured: —",
            font=("Segoe UI Symbol", 11),
            bg=CREAM,
            fg=CHOCOLATE,
            anchor="w",
        )
        self.cap_black_label.pack(fill=tk.X)

        self.cap_white_label = tk.Label(
            cap_card,
            text="Black captured: —",
            font=("Segoe UI Symbol", 11),
            bg=CREAM,
            fg=CHOCOLATE,
            anchor="w",
        )
        self.cap_white_label.pack(fill=tk.X)

        # Move History Log
        log_header = tk.Label(
            sidebar,
            text="MOVE NOTATION (SAN)",
            font=("Consolas", 10, "bold"),
            bg=CHOCOLATE,
            fg=SAGE,
            anchor="w",
        )
        log_header.pack(fill=tk.X, pady=(2, 4))

        log_frame = tk.Frame(
            sidebar,
            bg=CREAM,
            highlightbackground=SAGE,
            highlightthickness=2,
        )
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.move_text = tk.Text(
            log_frame,
            bg=CREAM,
            fg=CHOCOLATE,
            font=("Consolas", 11),
            relief=tk.FLAT,
            padx=8,
            pady=6,
            state=tk.DISABLED,
            wrap=tk.WORD,
            height=9,
            selectbackground=SAGE,
            selectforeground=CHOCOLATE,
        )
        self.move_text.pack(fill=tk.BOTH, expand=True)

        # Coach Output Box
        self.coach_label = tk.Label(
            sidebar,
            text="Click 'Coach Hint' for tactical advice.",
            font=("Georgia", 9, "italic"),
            bg=CREAM,
            fg=CHOCOLATE,
            wraplength=295,
            justify=tk.LEFT,
            padx=8,
            pady=6,
            highlightbackground=SAGE,
            highlightthickness=1,
        )
        self.coach_label.pack(fill=tk.X, pady=(0, 10))

        # Action Buttons Grid
        btn_grid = tk.Frame(sidebar, bg=CHOCOLATE)
        btn_grid.pack(fill=tk.X)

        self.mode_btn = self._make_button(btn_grid, "Mode: vs AI", self._toggle_mode)
        self.mode_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=3)

        self.flip_btn = self._make_button(btn_grid, "Flip Board", self._flip_board)
        self.flip_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=3)

        self.undo_btn = self._make_button(btn_grid, "Undo Move", self._undo_move)
        self.undo_btn.grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=3)

        self.coach_btn = self._make_button(btn_grid, "Coach Hint", self._ask_coach)
        self.coach_btn.grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=3)

        self.new_btn = self._make_button(
            sidebar, "New Game", self._new_game, primary=True
        )
        self.new_btn.pack(fill=tk.X, pady=(6, 0))

        btn_grid.columnconfigure(0, weight=1)
        btn_grid.columnconfigure(1, weight=1)

    def _make_button(
            self,
            parent: tk.Widget,
            text: str,
            command: Callable[[], None],
            primary: bool = False,
    ) -> tk.Button:
        bg_col = CREAM if primary else SAGE
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Georgia", 10, "bold"),
            bg=bg_col,
            fg=CHOCOLATE,
            activebackground=CHOCOLATE,
            activeforeground=CREAM,
            relief=tk.FLAT,
            bd=0,
            padx=10,
            pady=7,
            cursor="hand2",
        )

    # ------------------------------------------------------------------------
    # BOARD COORDINATE CONVERSIONS
    # ------------------------------------------------------------------------
    def _board_to_display(self, r: int, c: int) -> tuple[int, int]:
        if self.flipped:
            return (7 - r, 7 - c)
        return (r, c)

    def _display_to_board(self, dr: int, dc: int) -> tuple[int, int]:
        if self.flipped:
            return (7 - dr, 7 - dc)
        return (dr, dc)

    # ------------------------------------------------------------------------
    # RENDERING (STRICTLY 3 COLORS)
    # ------------------------------------------------------------------------
    def _render_all(self) -> None:
        self.canvas.delete("all")
        last_move = self.state.move_history[-1] if self.state.move_history else None
        legal_targets = {m.end: m for m in self.valid_moves_for_selected}

        for dr in range(8):
            for dc in range(8):
                r, c = self._display_to_board(dr, dc)
                x1 = dc * self.SQ_PX
                y1 = dr * self.SQ_PX
                x2 = x1 + self.SQ_PX
                y2 = y1 + self.SQ_PX

                is_light = (r + c) % 2 == 0
                sq_color = CREAM if is_light else SAGE
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=sq_color, outline="")

                # Highlight selected square or last move with inset border
                if self.selected_sq == (r, c):
                    self.canvas.create_rectangle(
                        x1 + 3, y1 + 3, x2 - 3, y2 - 3,
                        outline=CHOCOLATE, width=4,
                        )
                elif last_move and (r, c) in (last_move.start, last_move.end):
                    self.canvas.create_rectangle(
                        x1 + 4, y1 + 4, x2 - 4, y2 - 4,
                        outline=CHOCOLATE, width=2, dash=(4, 3),
                        )

                # Coordinate labels along left rank and bottom file
                if dc == 0:
                    rank_lbl = str(8 - r)
                    lbl_col = CHOCOLATE
                    self.canvas.create_text(
                        x1 + 10, y1 + 12,
                        text=rank_lbl,
                        fill=lbl_col,
                        font=("Consolas", 9, "bold"),
                        )
                if dr == 7:
                    file_lbl = "abcdefgh"[c]
                    lbl_col = CHOCOLATE
                    self.canvas.create_text(
                        x2 - 10, y2 - 10,
                        text=file_lbl,
                        fill=lbl_col,
                        font=("Consolas", 9, "bold"),
                        )

                # Draw piece with high-contrast dual-layer silhouette
                piece = self.state.board[r][c]
                if piece:
                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2
                    self._draw_piece(cx, cy, piece)

                # Draw legal move indicators
                if (r, c) in legal_targets:
                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2
                    if self.state.board[r][c] is not None or legal_targets[(r, c)].is_en_passant:
                        # Capture ring
                        rad = self.SQ_PX // 2 - 7
                        self.canvas.create_oval(
                            cx - rad, cy - rad, cx + rad, cy + rad,
                            outline=CHOCOLATE, width=4,
                            )
                    else:
                        # Quiet move dot
                        rad = 9
                        self.canvas.create_oval(
                            cx - rad, cy - rad, cx + rad, cy + rad,
                            fill=CHOCOLATE, outline=CREAM, width=2,
                            )

        # If a pawn promotion choice is pending, draw modal overlay on canvas
        if self.pending_promotion_moves:
            self._draw_promotion_overlay()

        self._update_sidebar()

    def _draw_piece(self, cx: int, cy: int, piece: Piece) -> None:
        font_spec = ("Segoe UI Symbol", 36, "bold")
        glyph = piece.glyph
        if piece.color == Color.WHITE:
            # Chocolate outline + Warm Cream interior + subtle Sage pedestal
            for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, -2), (-2, 2), (2, 2)):
                self.canvas.create_text(cx + ox, cy + oy, text=glyph, fill=CHOCOLATE, font=font_spec)
            self.canvas.create_text(cx, cy, text=glyph, fill=CREAM, font=font_spec)
            self.canvas.create_text(cx, cy, text=OUTLINE_GLYPHS[piece.kind], fill=CHOCOLATE, font=font_spec)
        else:
            # Warm Cream halo + Deep Chocolate interior
            for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)):
                self.canvas.create_text(cx + ox, cy + oy, text=glyph, fill=CREAM, font=font_spec)
            self.canvas.create_text(cx, cy, text=glyph, fill=CHOCOLATE, font=font_spec)

    def _draw_promotion_overlay(self) -> None:
        bx1, by1, bx2, by2 = 90, 220, 510, 380
        self.canvas.create_rectangle(
            bx1, by1, bx2, by2,
            fill=CHOCOLATE, outline=CREAM, width=4,
        )
        self.canvas.create_text(
            (bx1 + bx2) // 2, by1 + 32,
            text="SELECT PAWN PROMOTION PIECE",
            fill=CREAM,
            font=("Georgia", 13, "bold"),
            )
        box_w = 84
        gap = 14
        start_x = bx1 + 22
        y_top = by1 + 62
        for idx, m in enumerate(self.pending_promotion_moves):
            px1 = start_x + idx * (box_w + gap)
            px2 = px1 + box_w
            py2 = y_top + 80
            self.canvas.create_rectangle(
                px1, y_top, px2, py2,
                fill=SAGE, outline=CREAM, width=2,
            )
            promo_piece = Piece(m.piece.color, m.promotion or PieceType.QUEEN)
            self._draw_piece((px1 + px2) // 2, (y_top + py2) // 2, promo_piece)

    def _update_sidebar(self) -> None:
        over, status_msg = self.state.game_status()
        if self.ai_thinking and not over:
            status_msg = "AI Engine thinking..."
        self.status_label.config(
            text=status_msg,
            bg=CREAM if over else SAGE,
            fg=CHOCOLATE,
        )

        w_caps = "".join(p.glyph for p in self.state.captured_black) or "—"
        b_caps = "".join(p.glyph for p in self.state.captured_white) or "—"
        self.cap_black_label.config(text=f"White captured: {w_caps}")
        self.cap_white_label.config(text=f"Black captured: {b_caps}")

        # Format SAN move list in pairs
        self.move_text.config(state=tk.NORMAL)
        self.move_text.delete("1.0", tk.END)
        history = self.state.move_history
        lines: list[str] = []
        for i in range(0, len(history), 2):
            move_num = (i // 2) + 1
            w_san = history[i].san
            b_san = history[i + 1].san if i + 1 < len(history) else ""
            lines.append(f"{move_num:>2}. {w_san:<8} {b_san:<8}")
        self.move_text.insert(tk.END, "\n".join(lines))
        self.move_text.see(tk.END)
        self.move_text.config(state=tk.DISABLED)

    # ------------------------------------------------------------------------
    # INTERACTION HANDLERS
    # ------------------------------------------------------------------------
    def _on_canvas_click(self, event: tk.Event) -> None:
        if self.ai_thinking:
            return

        # Handle promotion modal click if active
        if self.pending_promotion_moves:
            bx1, by1 = 90, 220
            box_w, gap = 84, 14
            start_x = bx1 + 22
            y_top = by1 + 62
            py2 = y_top + 80
            for idx, m in enumerate(self.pending_promotion_moves):
                px1 = start_x + idx * (box_w + gap)
                px2 = px1 + box_w
                if px1 <= event.x <= px2 and y_top <= event.y <= py2:
                    self.pending_promotion_moves.clear()
                    self._execute_move(m)
                    return
            # Clicked outside promotion buttons -> cancel promotion selection
            self.pending_promotion_moves.clear()
            self._render_all()
            return

        over, _ = self.state.game_status()
        if over:
            return

        dc = event.x // self.SQ_PX
        dr = event.y // self.SQ_PX
        if not (0 <= dr < 8 and 0 <= dc < 8):
            return
        r, c = self._display_to_board(dr, dc)

        # Check if user clicked a valid destination square for the selected piece
        matching = [m for m in self.valid_moves_for_selected if m.end == (r, c)]
        if matching:
            if len(matching) > 1 and matching[0].promotion is not None:
                self.pending_promotion_moves = matching
                self._render_all()
                return
            self._execute_move(matching[0])
            return

        # Otherwise select friendly piece
        clicked_piece = self.state.board[r][c]
        if clicked_piece and clicked_piece.color == self.state.turn:
            self.selected_sq = (r, c)
            all_legal = self.state.generate_legal_moves(self.state.turn)
            self.valid_moves_for_selected = [m for m in all_legal if m.start == (r, c)]
        else:
            self.selected_sq = None
            self.valid_moves_for_selected = []

        self._render_all()

    def _execute_move(self, move: Move) -> None:
        self.snapshots.append(self.state.clone())
        self.state.make_move(move)
        self.selected_sq = None
        self.valid_moves_for_selected = []
        self._render_all()

        over, _ = self.state.game_status()
        if not over and self.vs_ai and self.state.turn == Color.BLACK:
            self.ai_thinking = True
            self._update_sidebar()
            threading.Thread(target=self._run_ai_turn, daemon=True).start()

    def _run_ai_turn(self) -> None:
        ai_move = ChessEngine.choose_move(self.state, depth=3)
        self.root.after(0, lambda: self._finish_ai_turn(ai_move))

    def _finish_ai_turn(self, ai_move: Optional[Move]) -> None:
        self.ai_thinking = False
        if ai_move:
            self.snapshots.append(self.state.clone())
            self.state.make_move(ai_move)
        self._render_all()

    # ------------------------------------------------------------------------
    # SIDEBAR ACTIONS
    # ------------------------------------------------------------------------
    def _toggle_mode(self) -> None:
        if self.ai_thinking:
            return
        self.vs_ai = not self.vs_ai
        self.mode_btn.config(text="Mode: vs AI" if self.vs_ai else "Mode: 2-Player")
        if self.vs_ai and self.state.turn == Color.BLACK:
            over, _ = self.state.game_status()
            if not over:
                self.ai_thinking = True
                self._update_sidebar()
                threading.Thread(target=self._run_ai_turn, daemon=True).start()

    def _flip_board(self) -> None:
        self.flipped = not self.flipped
        self._render_all()

    def _undo_move(self) -> None:
        if self.ai_thinking or not self.snapshots:
            return
        if self.vs_ai and len(self.snapshots) >= 2 and self.state.turn == Color.WHITE:
            self.snapshots.pop()
            self.state = self.snapshots.pop()
        else:
            self.state = self.snapshots.pop()
        self.selected_sq = None
        self.valid_moves_for_selected = []
        self.pending_promotion_moves.clear()
        self._render_all()

    def _ask_coach(self) -> None:
        if self.ai_thinking:
            return
        self.coach_label.config(text="Analyzing position...")
        state_copy = self.state.clone()

        def worker() -> None:
            advice = self.coach.advise(state_copy)
            self.root.after(0, lambda: self.coach_label.config(text=advice))

        threading.Thread(target=worker, daemon=True).start()

    def _new_game(self) -> None:
        if self.ai_thinking:
            return
        self.state = ChessState()
        self.snapshots.clear()
        self.selected_sq = None
        self.valid_moves_for_selected = []
        self.pending_promotion_moves.clear()
        self.coach.previous_interaction_id = None
        self.coach_label.config(text="New game started. Click 'Coach Hint' anytime.")
        self._render_all()


def main() -> None:
    root = tk.Tk()
    ChessApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()