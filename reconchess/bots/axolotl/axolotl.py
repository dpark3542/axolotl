import math
import random
from reconchess import *


def sense_board(board: chess.Board, square: Square):
    builder = []
    for i in range(square - 9, square + 15, 8):
        for j in range(3):
            piece = board.piece_at(i + j)
            if not piece:
                builder.append(" ")
            else:
                builder.append(piece.symbol())
    return "".join(builder)

# Call a move partially legal if the move is not legal by normal chess rules, but does not result in a pass.
# Example: A move by a queen that is blocked by an opponent piece. The move is not a pass as the queen takes the opponent piece.
#
# Suppose we have hypotheses f_1,f_2,...,f_n occuring with probability p_1,p_2,...,p_n.
# When handling a sense result, move result, or opponent move result, we receive some info.
# P(true board = f_i | info) = P(info | true board = f_i) P(true board = f) / P(info)
# P(info | true board = f_i) is always 0 or 1 for this game.
# Then remove all hypotheses f_i where info does not hold and normalize the remaining probabilities.
class AxolotlBot(Player):
    def __init__(self):
        self.color = None
        self.hypotheses = None
        self.sense = None
        self.move = None

    def handle_game_start(self, color: Color, board: chess.Board, opponent_name: str):
        self.color = color
        # TODO: move to handle opponent move result
        if color == board.turn:
            self.hypotheses = {board.fen(shredder=True): 1}
        else:
            # assume opponent realizes they initially have perfect information and thus does not play partially legal moves
            # remove case where opponent passes on normal starting board?
            opponent_moves = list(board.pseudo_legal_moves)
            n = len(opponent_moves) + 1
            self.hypotheses = {board.fen(shredder=True): 1 / n}
            for move in opponent_moves:
                board.push(move)
                self.hypotheses[board.fen(shredder=True)] = 1 / n
                board.pop()

    def handle_opponent_move_result(self, captured_my_piece: bool, capture_square: Optional[Square]):
        if captured_my_piece:
            # calculate next hypotheses and their probabilities of the board after opponent's turn
            # calculate new hypotheses and probabilities using information about capture
            pass
        else:
            # calculate next hypotheses and their probabilities of the board after opponent's turn
            # calculate new hypotheses and probabilities using information about capture
            pass

    def choose_sense(self, sense_actions: List[Square], move_actions: List[chess.Move], seconds_left: float) -> Optional[Square]:
        distributions = {} # maps square to distribution of number of hypotheses remaining after sense
        for i in range(1, 7):
            for j in range(1, 7):
                square = 8 * i + j
                sense_dist = {} # maps sense result to (probability, count)
                num_dist = {} # maps number of remaining hypotheses to probability
                for h, p in self.hypotheses:
                    result = sense_board(h, square)
                    if result in sense_dist:
                        sense_dist[result] += (p, 1)
                    else:
                        sense_dist[result] = (p, 1)
                for p, c in sense_dist.values():
                    if c in num_dist:
                        num_dist[c] += p
                    else:
                        num_dist[c] = p
                distributions[square] = num_dist
        # choose which square by minimizing some function f
        min = math.inf
        self.sense = None
        for square, dist in distributions:
            # f = maximum number of hypotheses remaining
            f = max(dist, key=dist.get)

            # f = expected value of number of hypotheses remaining
            # f = 0
            # for n, p in dist:
            #     f += n * p

            # take min
            if f < min:
                min = f
                self.sense = square
        return self.sense

    def handle_sense_result(self, sense_result: List[Tuple[Square, Optional[chess.Piece]]]):
        # parse sense result
        board = chess.Board(None)
        for square, piece in sense_result:
            if piece is not None:
                board.set_piece_at(square, piece)
        result = sense_board(board, self.sense)

        # remove hypotheses with different sense result
        tot = 0
        for h, p in self.hypotheses:
            if result != sense_board(h, self.sense):
                tot += p
                del self.hypotheses[h]

        # normalize probabilities
        for h, p in self.hypotheses:
            self.hypotheses[h] = p / (1 - tot)

    def choose_move(self, move_actions: List[chess.Move], seconds_left: float) -> Optional[chess.Move]:
        return random.choice(move_actions + [None])

    def handle_move_result(self, requested_move: Optional[chess.Move], taken_move: Optional[chess.Move], captured_opponent_piece: bool, capture_square: Optional[Square]):
        pass

    def handle_game_end(self, winner_color: Optional[Color], win_reason: Optional[WinReason], game_history: GameHistory):
        pass
