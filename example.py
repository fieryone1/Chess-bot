import math
import random
import time
from extension.board_utils import list_legal_moves_for, copy_piece_move

# Piece weights tuned for the 5x5 variant
PIECE_VALUES = {
    "king": 10_000,
    "queen": 900,
    "right": 550,
    "rook": 500,   # not used in samples but kept for completeness
    "bishop": 330,
    "knight": 320,
    "pawn": 100,
}

CENTER = (2, 2)


def agent(board, player, var):
    """
    Iterative-deepening alpha–beta agent with a simple heuristic eval.
    board: cloned board handed in by the runner
    player: Player object ("white" or "black")
    var: [ply_id, THINKING_TIME_BUDGET]
    """
    start = time.perf_counter()
    deadline = start + max(var[1] - 0.15, 0.05)  # small buffer before timeout

    root_player = player

    def other_player(b, p):
        for pl in b.players:
            if pl != p:
                return pl
        return p  # fallback, should not happen

    def evaluate(b):
        """Material + centralization + mobility; very fast to compute."""
        opp = other_player(b, root_player)
        own_king, opp_king = False, False
        score = 0.0

        for pc in b.get_pieces():
            name = str(pc.name).lower()
            val = PIECE_VALUES.get(name, 120)
            sign = 1 if pc.player == root_player else -1
            score += sign * val

            # Central squares are strong in 5x5
            dist_center = abs(pc.position.x - CENTER[0]) + abs(pc.position.y - CENTER[1])
            score += sign * (4 - dist_center) * 3  # Manhattan distance bonus

            if name == "king":
                if pc.player == root_player:
                    own_king = True
                else:
                    opp_king = True

        if not own_king:
            return -1e6
        if not opp_king:
            return 1e6

        try:
            own_mob = len(list_legal_moves_for(b, root_player))
            opp_mob = len(list_legal_moves_for(b, opp))
            score += (own_mob - opp_mob) * 4.0
        except Exception:
            pass  # in case move gen fails for some reason

        return score

    def order_moves(move_list):
        """Prefer captures to help pruning."""
        return sorted(
            move_list,
            key=lambda pm: len(getattr(pm[1], "captures", []) or []),
            reverse=True,
        )

    def search(b, to_move, depth, alpha, beta):
        if time.perf_counter() >= deadline:
            raise TimeoutError

        legal = list_legal_moves_for(b, to_move)
        if depth == 0 or not legal:
            if not legal:
                # No legal move: current mover loses in this ruleset
                return (-1e5 if to_move == root_player else 1e5), None
            return evaluate(b), None

        maximizing = to_move == root_player
        best_move = None

        if maximizing:
            value = -math.inf
            for pc, mv in order_moves(legal):
                child = b.clone()
                child, c_pc, c_mv = copy_piece_move(child, pc, mv)
                if not c_pc or not c_mv:
                    continue
                c_pc.move(c_mv)
                score, _ = search(child, other_player(child, to_move), depth - 1, alpha, beta)
                if score > value:
                    value = score
                    best_move = (pc, mv)
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            return value, best_move
        else:
            value = math.inf
            for pc, mv in order_moves(legal):
                child = b.clone()
                child, c_pc, c_mv = copy_piece_move(child, pc, mv)
                if not c_pc or not c_mv:
                    continue
                c_pc.move(c_mv)
                score, _ = search(child, other_player(child, to_move), depth - 1, alpha, beta)
                if score < value:
                    value = score
                    best_move = (pc, mv)
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value, best_move

    legal_root_moves = list_legal_moves_for(board, root_player)
    if not legal_root_moves:
        return None, None

    # Fallback in case search times out early
    best_piece, best_move = random.choice(legal_root_moves)

    depth = 1
    # Shallow by default; the small board often allows going deeper quickly
    max_depth = 4 if len(list(board.get_pieces())) > 12 else 5

    while depth <= max_depth:
        try:
            _, move = search(board, root_player, depth, -math.inf, math.inf)
            if move:
                best_piece, best_move = move
        except TimeoutError:
            break
        if time.perf_counter() >= deadline:
            break
        depth += 1

    return best_piece, best_move
