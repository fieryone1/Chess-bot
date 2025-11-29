import random
import math
import random
import time
from extension.board_utils import list_legal_moves_for, take_notes,copy_piece_move
class SearchTimeout(Exception):
    pass
PIECE_VALUES = {
    "king": 10_000,
    "queen": 900,
    "right": 550,
    "rook": 500,   
    "bishop": 330,
    "knight": 320,
    "pawn": 100,
}

nodes_visited=0
TRANSPOSITION_TABLE = {}

def get_state_key(board):


    pieces_data = tuple(
        (p.name, p.player.name) 
        for p in board.get_pieces()
    )
    
    return (pieces_data, board.current_player.name)


def order_moves(legal):
    return sorted(legal, key= lambda pm: len(getattr(pm[1], "captures", []) or []), reverse=True)


def agent(board, player, var):  

    """"
    This is an example of your designed Agent

    Parameters
    ----------
    board: the current chess board
    player: your assigned player role (white or black)
    var:  [ply, THINKING_TIME_BUDGET] a list cotaining the ply ID and the thinking_time_budget (secs)

    Returns
    -------
    piece: your selected chess piece
    move_opt: your selected move of your selected chess piece
    
    Hints:
    -----
    - List of players on the current board game: list(board.players) - default list: [Player (white), Player (black)]
    - board.players[0].name = "white" and board.players[1].name = "black"
    - Name of the player assigned to the Agent (either "white" or "black"): player.name
    - list of pieces of the current player: list(board.get_player_pieces(player))
    - List of pieces and corresponding moves for each pieces of the player: piece, move_opt = list_legal_moves_for(board, player)
    - From var: ply ID = var[0], timeout = var[1]
    - Use the timeout variable together with time.perf_counter()
    to ensure the agent returns its best move before the time limit expires.
    """

    start_time = time.perf_counter()
    thinking_time = var[1]
    deadline = start_time + thinking_time - 0.05
    legal = list_legal_moves_for(board, player)
    legal = order_moves(legal)
    if not legal:
        return None, None

    
    best_move_so_far = random.choice(legal)
    

    for current_depth in range(1, 50): 
        try:
            best_score_this_depth = -math.inf
            best_move_this_depth = None
         
            for piece, move_opt in legal:
                board_clone = board.clone()
                _, piece_on_clone, move_on_clone = copy_piece_move(board_clone, piece, move_opt)
                
                if piece_on_clone and move_on_clone:
                    piece_on_clone.move(move_on_clone)
                    
                   
                    score = minimax(
                        board_clone, 
                        current_depth - 1, 
                        False, 
                        player, 
                        -math.inf, 
                        math.inf, 
                        deadline
                    )
                    
                    if score > best_score_this_depth:
                        best_score_this_depth = score
                        best_move_this_depth = (piece, move_opt)
         
            if best_move_this_depth:
                best_move_so_far = best_move_this_depth
             
        except SearchTimeout:
           
            break
            
    return best_move_so_far

    # TRANSPOSITION_TABLE.clear()
    # SEARCH_DEPTH=3
    # legal=list_legal_moves_for(board,player)
    # legal=order_moves(legal)
    # best=-math.inf
    # best_move=(None,None)
    # for piece, move_opt in legal:
    #     board_copy=board.clone()
    #     _, piece_on_clone, move_on_clone = copy_piece_move(board_copy, piece, move_opt)
    #     if piece_on_clone and move_on_clone:
    #         piece_on_clone.move(move_on_clone)
    #         score=minimax(board_copy,SEARCH_DEPTH-1,False,player,-math.inf,math.inf)
    #         if score> best:
    #             best=score
    #             best_move=(piece,move_opt)
    # return best_move


def minimax(board,depth,is_max_player,root_player,alpha,beta,deadline):
    if time.perf_counter() >= deadline:
        raise SearchTimeout()

    state_key = get_state_key(board)
    if state_key in TRANSPOSITION_TABLE:
 
        tt_depth, tt_score, tt_flag = TRANSPOSITION_TABLE[state_key]

    
        if tt_depth >= depth:
   
            if tt_flag == 0:   
                return tt_score
            elif tt_flag == 1: 
                alpha = max(alpha, tt_score)
            elif tt_flag == 2:
                beta = min(beta, tt_score)

           
            if alpha >= beta:
                return tt_score
    original_alpha = alpha
    current_player=board.current_player
    legal = list_legal_moves_for(board,current_player)
    legal=order_moves(legal)
    if depth==0 or not legal:
        return evaluate(board,root_player)
    if is_max_player:
        best=-math.inf
        for pc,mv in legal:
            board_clone=board.clone()
            _, piece_on_clone,move_on_clone = copy_piece_move(board_clone,pc,mv)
            if piece_on_clone and move_on_clone:
                piece_on_clone.move(move_on_clone)
                score=minimax(board_clone,depth-1,False,root_player,alpha,beta,deadline)
                best=max(best,score)
                alpha=max(alpha,score)
                if beta<=alpha:
              
                    break
        tt_flag = 0
        if best <= original_alpha:
            tt_flag = 2 # Upper Bound (Fail Low)
        elif best >= beta:
            tt_flag = 1 # Lower Bound (Fail High)
        
        TRANSPOSITION_TABLE[state_key] = (depth, best, tt_flag)
        return best
    else:
        best=math.inf
        for pc,mv in legal:
            board_clone=board.clone()
            _, piece_on_clone,move_on_clone = copy_piece_move(board_clone,pc,mv)
            if piece_on_clone and move_on_clone:
                piece_on_clone.move(move_on_clone)
                score=minimax(board_clone,depth-1,True,root_player,alpha,beta,deadline)
                best=min(best,score)
                beta=min(beta,score)
                if beta<=alpha:
                 
                    break
        tt_flag = 0
        if best <= original_alpha:
            tt_flag = 2 # Upper Bound
        elif best >= beta:
            tt_flag = 1 # Lower Bound
            
        TRANSPOSITION_TABLE[state_key] = (depth, best, tt_flag)
        return best
    

def evaluate(board,root_player):
    current_player = board.current_player
    if not list_legal_moves_for(board, current_player):
        if current_player.name == root_player.name:
            return -1_000_000 
        else:
            return 1_000_000 
    score = 0
    opponent_player = board.players[0] if board.players[1].name ==root_player.name  else board.players[1]
    for piece in board.get_pieces():
        piece_value=PIECE_VALUES.get(piece.name.lower(),0)
        if piece.player.name==root_player.name:
            score+=piece_value
        elif piece.player.name == opponent_player.name:
            score-=piece_value

    return score


