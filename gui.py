import tkinter as tk
from tkinter import font
import threading
import queue
import time
import sys
from itertools import cycle

# --- Import User Modules ---
try:
    from chessmaker.chess.base import Board
    from extension.board_utils import print_board_ascii, copy_piece_move
    from extension.board_rules import get_result, thinking_with_timeout, THINKING_TIME_BUDGET, GAME_TIME_BUDGET
    from samples import white, black, sample0, sample1
    from agent import agent
    from opponent import opponent
except ImportError as e:
    print(f"Error importing game modules: {e}")
    print("Ensure this file is placed in the root of the 'CW-COMP2321-fullgame' folder.")
    sys.exit(1)

# --- Configuration ---
CELL_SIZE = 80
BOARD_SIZE = 5
COLORS = {"light": "#F0D9B5", "dark": "#B58863"}
PIECE_UNICODE = {
    "white": {"king": "♔", "queen": "♕", "rook": "♖", "bishop": "♗", "knight": "♘", "pawn": "♙", "right": "R"},
    "black": {"king": "♚", "queen": "♛", "rook": "♜", "bishop": "♝", "knight": "♞", "pawn": "♟", "right": "r"}
}

class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("COMP2321 Chess Fragments GUI")
        self.root.geometry("1000x700")

        self.msg_queue = queue.Queue()

        # Layout
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left: Board
        self.canvas_frame = tk.Frame(self.main_frame)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, width=CELL_SIZE*BOARD_SIZE, height=CELL_SIZE*BOARD_SIZE)
        self.canvas.pack(pady=20)

        # Right: Log
        self.log_frame = tk.Frame(self.main_frame, width=350)
        self.log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.log_label = tk.Label(self.log_frame, text="Game Log", font=("Arial", 12, "bold"))
        self.log_label.pack(side=tk.TOP, anchor="w")

        self.log_text = tk.Text(self.log_frame, state='disabled', wrap='word', height=20, width=40)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.scrollbar = tk.Scrollbar(self.log_frame, command=self.log_text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=self.scrollbar.set)

        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready to start.")
        self.status_bar = tk.Label(root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W, font=("Arial", 10))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Controls
        self.control_frame = tk.Frame(self.canvas_frame)
        self.control_frame.pack(side=tk.BOTTOM, pady=10)
        
        self.btn_start = tk.Button(self.control_frame, text="Start Game", command=self.start_game_thread, bg="#4CAF50", fg="white", font=("Arial", 12))
        self.btn_start.pack()

        self.draw_board_grid()
        self.root.after(100, self.process_queue)

    def draw_board_grid(self):
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                color = COLORS["light"] if (r + c) % 2 == 0 else COLORS["dark"]
                x1 = c * CELL_SIZE
                y1 = r * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black")
                if c == 0: self.canvas.create_text(x1 + 5, y1 + 10, text=str(r), anchor="nw")
                if r == BOARD_SIZE - 1: self.canvas.create_text(x2 - 5, y2 - 5, text=str(c), anchor="se")

    def update_board_visuals(self, board):
        self.canvas.delete("piece")
        for piece in board.get_pieces():
            pos = piece.position
            # Fix for pieces with None position (captured but not cleaned)
            if pos is None: continue

            p_name = piece.name.lower()
            p_color = piece.player.name.lower()
            char = PIECE_UNICODE[p_color].get(p_name, "?")
            if p_name == "right": char = "R" if p_color == "white" else "r"

            x = pos.x * CELL_SIZE + CELL_SIZE // 2
            y = pos.y * CELL_SIZE + CELL_SIZE // 2
            text_color = "black" 
            
            self.canvas.create_text(x, y, text=char, fill=text_color, font=("Arial", 36), tags="piece")

    def log(self, message):
        self.msg_queue.put(("log", message))

    def set_status(self, message):
        self.msg_queue.put(("status", message))

    def process_queue(self):
        try:
            while True:
                msg_type, data = self.msg_queue.get_nowait()
                if msg_type == "log":
                    print(data)
                    self.log_text.config(state='normal')
                    self.log_text.insert(tk.END, data + "\n")
                    self.log_text.see(tk.END)
                    self.log_text.config(state='disabled')
                elif msg_type == "board_update":
                    self.update_board_visuals(data)
                elif msg_type == "status":
                    self.status_var.set(data)
                elif msg_type == "game_over":
                    self.btn_start.config(state="normal", text="Restart")
                    self.status_var.set("Game Over.")
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)

    def start_game_thread(self):
        self.btn_start.config(state="disabled")
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
        t = threading.Thread(target=self.run_game_logic)
        t.daemon = True
        t.start()

    def make_custom_board(self, board_sample):
        # Local import/re-creation to ensure clean state
        players = [white, black]
        board = Board(squares=board_sample, players=players, turn_iterator=cycle(players))
        return board, players

    def run_game_logic(self):
        try:
            p_white = agent
            p_black = opponent
            board_sample = sample0
            
            board, players = self.make_custom_board(board_sample)
            turn_order = cycle(players)
            
            self.log(f"Time budget: {THINKING_TIME_BUDGET}s / Move")
            self.log("=== Initial position ===")
            self.msg_queue.put(("board_update", board.clone()))
            
            t_start = time.perf_counter()
            t_game = t_start + GAME_TIME_BUDGET
            ply = 1
            
            while True:
                if time.perf_counter() > t_game:
                    self.log("Draw - game timeout")
                    break
                
                player = next(turn_order)
                temp_board = board.clone()
                
                # UPDATE STATUS: Who is thinking?
                self.set_status(f"Ply {ply}: {player.name} is thinking...")
                
                func = p_white if player.name == "white" else p_black
                
                # Measure thinking time
                move_start = time.perf_counter()
                
                p_piece, p_move_opt = thinking_with_timeout(
                    func=func, 
                    thinking_time=THINKING_TIME_BUDGET, 
                    board=temp_board, 
                    player=player, 
                    var=[ply, THINKING_TIME_BUDGET]
                )
                
                move_duration = time.perf_counter() - move_start
                self.log(f"({player.name}) took {move_duration:.2f}s")

                board, piece, move_opt = copy_piece_move(board, p_piece, p_move_opt)

                if (not piece) or (not move_opt):
                    res = get_result(board)
                    if res: self.log(f"Game Ended: {res}")
                    elif p_piece == 99: self.log(f"Game Ended: {player.name} timed out")
                    else: self.log(f"Game Ended: {player.name} no legal move")
                    break
                else:
                    try:
                        piece.move(move_opt)
                        ply += 1
                        self.log(f"{piece} -> ({move_opt.position.x}, {move_opt.position.y})")
                        self.msg_queue.put(("board_update", board.clone()))
                    except Exception as e:
                        self.log(f"Error executing move: {e}")
                        break

                res = get_result(board)
                if res:
                    self.log(f"Game Ended: {res}")
                    break
                    
        except Exception as e:
            self.log(f"CRITICAL ERROR: {e}")
        finally:
            self.msg_queue.put(("game_over", None))

if __name__ == "__main__":
    root = tk.Tk()
    app = ChessGUI(root)
    root.mainloop()