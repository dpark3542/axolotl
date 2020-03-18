import chess.engine
import math
import os
from reconchess import *

STOCKFISH_ENV_VAR = "STOCKFISH_EXECUTABLE"


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
        self.friendly_board = None  # chess.Board object of our pieces
        self.hypotheses = None  # dictionary mapping fen strings to probability
        self.sense = None
        self.move = None
        self.engine = None

    def start_engine(self):
        if STOCKFISH_ENV_VAR not in os.environ:
            raise Exception("No environment variable for Stockfish executable")
        stockfish_path = os.environ[STOCKFISH_ENV_VAR]
        if not os.path.exists(stockfish_path):
            raise Exception("Stockfish executable not found at " + stockfish_path)
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path, setpgrp=True)

    def handle_game_start(self, color: Color, board: chess.Board, opponent_name: str):
        self.color = color
        self.friendly_board = board.copy(stack=False)

        # friendly board
        for square in range(64):
            if board.color_at(square) != color:
                self.friendly_board.remove_piece_at(square)
        if color:
            self.friendly_board.castling_rights &= chess.BB_A1 | chess.BB_H1
        else:
            self.friendly_board.castling_rights &= chess.BB_A8 | chess.BB_H8
        self.hypotheses = {board.fen(shredder=True): 1}

        # engine
        self.start_engine()

    def handle_opponent_move_result(self, captured_my_piece: bool, capture_square: Optional[Square]):
        self.friendly_board.push(chess.Move.null())
        # Calculate next hypotheses and their probabilities of the board after opponent's turn.
        # Assume opponent is equally likely to choose any valid move.
        # In practice, opponents do not seem to play invalid moves such as invalid pawn captures.
        # Then assume the probability the opponent plays an invalid move/pass is equal to the probability of any valid move.
        new_hypotheses = {}
        for h, p in self.hypotheses.items():
            board = chess.Board(h)
            if captured_my_piece:
                moves = list(board.generate_pseudo_legal_captures(to_mask=chess.BB_SQUARES[capture_square]))
            else:
                moves = set(board.pseudo_legal_moves) - set(board.generate_pseudo_legal_captures())
                moves.add(chess.Move.null())
                # castling
                if board.has_kingside_castling_rights(not self.color):
                    if self.color == chess.BLACK and board.color_at(chess.F1) is None and board.color_at(
                            chess.G1) is None:
                        moves.add(chess.Move.from_uci("e1g1"))
                    if self.color == chess.WHITE and board.color_at(chess.F8) is None and board.color_at(
                            chess.G8) is None:
                        moves.add(chess.Move.from_uci("e8g8"))
                if board.has_queenside_castling_rights(not self.color):
                    if self.color == chess.BLACK and board.color_at(chess.D1) is None and board.color_at(
                            chess.C1) is None and board.color_at(chess.B1) is None:
                        moves.add(chess.Move.from_uci("e1c1"))
                    if self.color == chess.WHITE and board.color_at(chess.D8) is None and board.color_at(
                            chess.C8) is None and board.color_at(chess.B8) is None:
                        moves.add(chess.Move.from_uci("e8c8"))
            for move in moves:
                board.push(move)
                fen = board.fen(shredder=True)
                if fen in new_hypotheses:
                    new_hypotheses[fen] += p / len(moves)
                else:
                    new_hypotheses[fen] = p / len(moves)
                board.pop()
        self.hypotheses = new_hypotheses

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
        fmin = math.inf
        self.sense = None
        for square, dist in distributions.items():
            # f = maximum number of hypotheses remaining
            f = max(dist, key=dist.get)

            # f = expected value of number of hypotheses remaining
            # f = 0
            # for n, p in dist:
            #     f += n * p

            # take min
            if f < fmin:
                fmin = f
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

    def generate_submove_graph(self):
        """
        Returns a directed graph of chess moves in the form of a dictionary.
        u -> v is an edge if the path a piece travels when performing move v is the maximum proper subset of the path for u.
        For example, Bc1e3 -> Bc1d2 and f2f4 -> f2f3 are edges.
        Only paths taken by pawns, bishops, rooks, queens, and kings are included.
        Castling is included.
        The null move is considered a valid move.
        :return: directed graph of submoves
        """
        g = {}
        root = chess.Move.null()

        # slide moves
        for a in range(64):
            # move to the right
            for d in [-7, 1, 9]:
                b = a + d
                if 0 <= b < 64 and b % 8 != 0:
                    g[chess.Move(a, b)] = root
                b = a + 2 * d
                while 0 <= b < 64 and b % 8 != 0:
                    g[chess.Move(a, b)] = chess.Move(a, b - d)
                    b += d
            # move to the left
            for d in [-9, 1, 7]:
                b = a + d
                if 0 <= b < 64 and b % 8 != 7:
                    g[chess.Move(a, b)] = root
                b = a + 2 * d
                while 0 <= b < 64 and b % 8 != 7:
                    g[chess.Move(a, b)] = chess.Move(a, b - d)
                    b += d
            # move vertically
            for d in [-8, 8]:
                b = a + d
                if 0 <= b < 64:
                    g[chess.Move(a, b)] = root
                b = a + 2 * d
                while 0 <= b < 64:
                    g[chess.Move(a, b)] = chess.Move(a, b - d)
                    b += d

        # castling
        if self.friendly_board.has_kingside_castling_rights(self.color):
            if self.color:
                g[chess.Move.from_uci("e1g1")] = root
            else:
                g[chess.Move.from_uci("e8g8")] = root
        if self.friendly_board.has_queenside_castling_rights(self.color):
            if self.color:
                g[chess.Move.from_uci("e1c1")] = root
            else:
                g[chess.Move.from_uci("e8c8")] = root

        return g

    def choose_move(self, move_actions: List[chess.Move], seconds_left: float) -> Optional[chess.Move]:
        distributions = {chess.Move.null(): []}  # maps move to (unsorted) distribution of scores
        for move in move_actions:
            distributions[move] = []
        graph = self.generate_submove_graph()  # see generate_submove_graph for details
        # sort move_actions so that if the moves in move_actions are processed in order and u -> v is an edge in the submove graph, then v will be processed before u
        move_actions.sort(key=lambda x: (x.from_square, abs(x.from_square - x.to_square) % 8 + abs(x.from_square - x.to_square) // 8))
        time = (seconds_left - 0.1) / (len(self.hypotheses) * (len(move_actions) + 1))

        # find distributions
        for h, p in self.hypotheses.items():
            board = chess.Board(h)

            # first check if we are in checkmate
            if board.is_checkmate():
                for move in move_actions:
                    distributions[move] = 0
                continue

            # next check if we can take their king
            if board.is_attacked_by(self.color, board.king(not self.color)):
                for move in move_actions:
                    if move.to_square == board.king(not self.color):
                        distributions[move].append(math.inf)
                    else:
                        distributions[move].append(-math.inf)
                continue

            legal_moves = set(board.pseudo_legal_moves)

            # process null move (root) first
            board.push(chess.Move.null())
            try:
                info = self.engine.analyse(board, chess.engine.Limit(time=time))
                score = info["score"].pov(self.color)
                if score.is_mate():
                    distributions[chess.Move.null()].append(score.mate() * math.inf)
                else:
                    distributions[chess.Move.null()].append(score.score())
            except chess.engine.EngineTerminatedError:
                distributions[chess.Move.null()].append(0)
                print("Stockfish crashed.")
                print("Time: " + str(time) + "s")
                print("Board: ")
                print(board)
                print(str(board.fen(shredder=True)))
                self.start_engine()
            board.pop()

            # process rest of moves
            for move in move_actions:
                # legal move
                if move in legal_moves:
                    try:
                        info = self.engine.analyse(board, chess.engine.Limit(time=time), root_moves=[move])
                        score = info["score"].pov(self.color)
                        if score.is_mate():
                            distributions[move].append(score.mate() * math.inf)
                        else:
                            distributions[move].append(score.score())
                    except chess.engine.EngineTerminatedError:
                        distributions[move].append(0)
                        print("Stockfish crashed.")
                        print("Time: " + str(time) + "s")
                        print("Move: " + move.uci())
                        print("Board: ")
                        print(board)
                        print(str(board.fen(shredder=True)))
                        self.start_engine()
                # blocked move
                else:
                    distributions[move].append(distributions[graph[move]][-1])

        # sort distributions
        # for move, dist in distributions.items():
        #     dist.sort()

        # choose move by maximizing some function f
        fmax = -math.inf
        self.move = None
        for move, dist in distributions.items():
            # f is min score
            f = min(dist)

            # take max
            if f > fmax:
                fmax = f
                self.move = move

        if self.move == chess.Move.null():
            return None
        return self.move

    @staticmethod
    def check_move(board, move, color, capture=None, capture_square=None):
        """
        Returns if move is legal on the board according to rbmc rules.
        For example, castling has stricter requirements on rbmc.
        Pseudo legal moves such as blocked slide moves and blocked pawn pushes are not considered legal.
        If capture info is provided, will further check if move is a legal capture/quiet move on a particular capture square.
        :param board: board
        :param move: move
        :param color: color of player performing move
        :param capture: if move results in a capture
        :param capture_square: capture square
        :return: boolean if move is legal and matches capture info
        """
        # null move
        if move is None:
            if capture is None:
                return True
            else:
                return not capture
        # kingside castle
        elif board.is_kingside_castling(move):
            if not board.has_kingside_castling_rights(color):
                return False
            if capture is None:
                return True
            else:
                return not capture
        # queenside castle
        elif board.is_queenside_castling(move):
            if not board.has_queenside_castling_rights(color):
                return False
            if capture is None:
                return True
            else:
                return not capture
        # all other moves (board.pseudo_legal_moves)
        else:
            if capture is None:
                return move in board.pseudo_legal_moves
            elif capture:
                return move in board.generate_pseudo_legal_captures(to_mask=chess.BB_SQUARES[capture_square])
            else:
                return move in set(board.pseudo_legal_moves) - set(board.generate_pseudo_legal_captures())

    def handle_move_result(self, requested_move: Optional[chess.Move], taken_move: Optional[chess.Move], captured_opponent_piece: bool, capture_square: Optional[Square]):
        # update friendly_board
        if taken_move is None:
            self.friendly_board.push(chess.Move.null())
        else:
            self.friendly_board.push(taken_move)

        # update hypotheses
        # taken_move is equal to requested_move, is a blocked sliding capture move, or is a blocked pawn push, pawn capture, or castle.
        new_hypotheses = {}
        tot = 0
        for h, p in self.hypotheses.items():
            board = chess.Board(h)
            # flag if current hypothesis matches given info
            if requested_move == taken_move:
                # make sure requested_move = taken_move is legal in board and matches capture info
                flag = self.check_move(board, requested_move, self.color, captured_opponent_piece, capture_square)
            else:
                # make sure requested_move is not legal, taken_move is legal, and taken_move matches capture info
                flag = not self.check_move(board, requested_move, self.color)
                flag &= self.check_move(board, taken_move, self.color, captured_opponent_piece, capture_square)
            if flag:
                board.push(taken_move)
                new_hypotheses[board.fen(shredder=True)] = p
            else:
                tot += p

        # normalize probabilities
        self.hypotheses = new_hypotheses
        for h, p in self.hypotheses.items():
            self.hypotheses[h] = p / (1 - tot)

    def handle_game_end(self, winner_color: Optional[Color], win_reason: Optional[WinReason], game_history: GameHistory):
        self.color = None
        self.hypotheses = None
        self.sense = None
        self.move = None
        try:
            self.engine.quit()
            self.engine = None
        except chess.engine.EngineTerminatedError:
            pass
