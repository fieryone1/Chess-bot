import random
import math
import random
import time
from extension.board_utils import list_legal_moves_for, take_notes,copy_piece_move
class SearchTimeout(Exception):
    pass

PST_GENERIC = [
    [ 5,  5,  5,  5,  5],
    [ 5, 10, 10, 10,  5],
    [ 5, 15, 20, 15,  5],
    [ 5, 10, 10, 10,  5],
    [ 5,  5,  5,  5,  5]
]


PST_PAWN = [
    [50, 50, 50, 50, 50], 
    [30, 30, 30, 30, 30], 
    [10, 10, 20, 10, 10], 
    [ 5,  5, 10,  5,  5], 
    [ 0,  0,  0,  0,  0]  
]


PST_KNIGHT = [
    [-10, -5, -5, -5, -10],
    [ -5, 10, 10, 10,  -5],
    [ -5, 10, 20, 10,  -5],
    [ -5, 10, 10, 10,  -5],
    [-10, -5, -5, -5, -10]
]

PST_KING = [
    [-10, -10, -10, -10, -10],
    [-10, -10, -10, -10, -10],
    [-10, -10, -10, -10, -10],
    [ -5,  -5,  -5,  -5,  -5],
    [ 10,  15,   5,  15,  10]
]
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
        (p.name, p.player.name, p.position.x, p.position.y) 
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
    deadline = start_time + (thinking_time*0.9)
    legal = list_legal_moves_for(board, player)
    legal = order_moves(legal)
    if not legal:
        return None, None

    
    best_move_so_far = random.choice(legal)
    

    for current_depth in range(1, 50): 
        print(current_depth)
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
                    if best_score_this_depth >= 900_000:
                        return best_move_this_depth
            if best_move_this_depth:
                best_move_so_far = best_move_this_depth
             
        except SearchTimeout:
           
            break
            
    return best_move_so_far




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
    

def evaluate(board, root_player):

    current_player = board.current_player
    opponent = board.players[0] if board.players[1].name == root_player.name else board.players[1]
    
    # 2. TERMINAL STATE CHECK (Win/Loss)
    current_legal_moves = list_legal_moves_for(board, current_player)
    if not current_legal_moves:
        if current_player.name == root_player.name:
            return -1_000_000 
        else:
            return 1_000_000  

    score = 0
    
  
    for piece in board.get_pieces():
        p_name = piece.name.lower()
        val = PIECE_VALUES.get(p_name, 0)
        
  
        x, y = piece.position.x, piece.position.y
       
        if p_name == "pawn":
            table = PST_PAWN
        elif p_name == "knight" or p_name == "right":
            table = PST_KNIGHT
        elif p_name == "king":
            table = PST_KING
        else:
            table = PST_GENERIC


        pst_val = 0
        if piece.player.name == "white":
            pst_val = table[y][x]
        else:
            pst_val = table[4-y][x] # Mirror row for Black

        if piece.player.name == root_player.name:
            score += (val + pst_val)
        else:
            score -= (val + pst_val)

    # B. Mobility Bonus 

    if root_player.name == current_player.name:
        root_moves = len(current_legal_moves)
        opp_moves = len(list_legal_moves_for(board, opponent))
    else:
        opp_moves = len(current_legal_moves)
        root_moves = len(list_legal_moves_for(board, root_player))

    score += (root_moves - opp_moves) * 5

    return score


