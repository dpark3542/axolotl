import math
import random
from reconchess import *

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
        self.hypotheses = {board.fen(shredder=True): 1}
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

    @staticmethod
    def expand_fen(fen):
        """
        Converts a FEN string to a different form where numbers are replaced by dots and backslashes are removed.
        :param fen: FEN string
        :return: Expanded FEN string
        """
        builder = []
        lines = fen.split(' ', 1)[0].split('/')
        lines.reverse()
        for line in lines:
            for char in line:
                if char.isdigit():
                    builder.append('.' * int(char))
                elif char != '/':
                    builder.append(char)
        s = "".join(builder)
        return s

    @staticmethod
    def sense_expanded_fen(s, square):
        """
        Returns a 9 character long subsequence of an expanded FEN string representing a 3 x 3 sense result.
        :param s: expanded FEN string
        :param square: center square to sense
        :return: sense result
        """
        return s[square - 9:square - 6] + s[square - 1:square + 2] + s[square + 7:square + 10]

    def choose_sense(self, sense_actions: List[Square], move_actions: List[chess.Move], seconds_left: float) -> Optional[Square]:
        # distributions will be a map from square to some distribution
        # initialize distributions
        distributions = {}
        for i in range(1, 7):
            for j in range(1, 7):
                distributions[8 * i + j] = {}

        for h, p in self.hypotheses.items():
            # create simple string representation of each board for easy sensing
            s = self.expand_fen(h)
            # sense each square of the board and tally up results in distributions
            for i in range(1, 7):
                for j in range(1, 7):
                    square = 8 * i + j
                    dist = distributions[square]
                    result = self.sense_expanded_fen(s, square)
                    if result in dist:
                        (q, c) = dist[result]
                        dist[result] = (p + q, c + 1)
                    else:
                        dist[result] = (p, 1)

        # each value in distributions is a map from sense result to (probability, count)
        # modify distributions in place so that each value is a map from number of hypotheses remaining to probability
        for square, dist in distributions.items():
            for h, (p, c) in list(dist.items()):
                if c in dist:
                    dist[c] += p
                else:
                    dist[c] = p
                del dist[h]

        # choose which square by minimizing some function f
        min = math.inf
        self.sense = None
        for square, dist in distributions.items():
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
        result = ""
        sense_result.sort(key=lambda x: x[0])
        for square, piece in sense_result:
            if piece is not None:
                result += piece.symbol()
            else:
                result += '.'

        # remove hypotheses with different sense result
        tot = 0
        for h, p in list(self.hypotheses.items()):
            s = self.expand_fen(h)
            if result != self.sense_expanded_fen(s, self.sense):
                tot += p
                del self.hypotheses[h]

        # normalize probabilities
        for h, p in self.hypotheses.items():
            self.hypotheses[h] = p / (1 - tot)

    def choose_move(self, move_actions: List[chess.Move], seconds_left: float) -> Optional[chess.Move]:
        return random.choice(move_actions + [None])

    def handle_move_result(self, requested_move: Optional[chess.Move], taken_move: Optional[chess.Move], captured_opponent_piece: bool, capture_square: Optional[Square]):
        pass

    def handle_game_end(self, winner_color: Optional[Color], win_reason: Optional[WinReason], game_history: GameHistory):
        pass
