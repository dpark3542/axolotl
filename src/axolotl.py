import chess.engine
import math
import os
import re
from reconchess import *

STOCKFISH_ENV_VAR = "STOCKFISH_EXECUTABLE"
STOCKFISH_THREADS = 6


class AxolotlBot(Player):
    def __init__(self):
        self.color = None
        self.friendly_board = None  # chess.Board object of our pieces
        self.hypotheses = None  # dictionary mapping fen strings to probability
        self.sense = None
        self.move = None
        self.engine = None

    def start_engine(self):
        print("Starting new engine")

        if STOCKFISH_ENV_VAR not in os.environ:
            raise Exception("No environment variable for Stockfish executable")
        stockfish_path = os.environ[STOCKFISH_ENV_VAR]
        if not os.path.exists(stockfish_path):
            raise Exception("Stockfish executable not found at " + stockfish_path)
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path, setpgrp=True)
        self.engine.configure({"Threads": STOCKFISH_THREADS})
        
        print("PID: " + re.findall(r'\d+', repr(self.engine))[0])

    def handle_game_start(self, color: Color, board: chess.Board, opponent_name: str):
        print("Game started against " + opponent_name)

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
        self.hypotheses = {board.fen(shredder=True): 1.0}

        # engine
        self.start_engine()

    def check_friendly_pieces(self):
        """
        Checks if all hypotheses have the same friendly pieces in the same positions as self.friendly_board.
        Also checks our castling rights.
        """
        for h in self.hypotheses.keys():
            board = chess.Board(h)
            for square in range(64):
                piece = self.friendly_board.piece_at(square)
                h_piece = board.piece_at(square)
                if piece is None:
                    if h_piece is not None and h_piece.color == self.color:
                        raise Exception("hypothesis does not match friendly board")
                else:
                    if h_piece != piece:
                        raise Exception("hypothesis does not match friendly board")

    def check_hypotheses(self, board):
        if board.fen(shredder=True) not in self.hypotheses:
            raise Exception("board not in hypotheses")

    def handle_opponent_move_result(self, captured_my_piece: bool, capture_square: Optional[Square]):
        print("Turn " + str(self.friendly_board.fullmove_number))
        print("Handling opponent move result")
        if self.friendly_board.turn == self.color:
            print("It is our turn, opponent did not make a move.")
            return
        print("Hypotheses count (before): " + str(len(self.hypotheses)))

        # update friendly board
        self.friendly_board.push(chess.Move.null())
        if captured_my_piece:
            self.friendly_board.remove_piece_at(capture_square)

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
                    if self.color == chess.BLACK and board.color_at(chess.F1) is None and board.color_at(chess.G1) is None:
                        moves.add(chess.Move.from_uci("e1g1"))
                    if self.color == chess.WHITE and board.color_at(chess.F8) is None and board.color_at(chess.G8) is None:
                        moves.add(chess.Move.from_uci("e8g8"))
                if board.has_queenside_castling_rights(not self.color):
                    if self.color == chess.BLACK and board.color_at(chess.D1) is None and board.color_at(chess.C1) is None and board.color_at(chess.B1) is None:
                        moves.add(chess.Move.from_uci("e1c1"))
                    if self.color == chess.WHITE and board.color_at(chess.D8) is None and board.color_at(chess.C8) is None and board.color_at(chess.B8) is None:
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

        print("Hypotheses count (after): " + str(len(self.hypotheses)))

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
        print("Choosing sense")

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
        f_min = math.inf
        self.sense = None
        for square, dist in distributions.items():
            # f = maximum number of hypotheses remaining
            f = max(dist, key=dist.get)

            # f = expected value of number of hypotheses remaining
            # f = 0
            # for n, p in dist:
            #     f += n * p

            # take min
            if f < f_min:
                f_min = f
                self.sense = square

        print("Sensed square " + chess.SQUARE_NAMES[self.sense])

        return self.sense

    def handle_sense_result(self, sense_result: List[Tuple[Square, Optional[chess.Piece]]]):
        print("Handling sense result")
        print("Hypotheses count (before): " + str(len(self.hypotheses)))

        if self.sense is None:
            return

        # parse sense result
        result = ""
        sense_result.sort(key=lambda x: x[0])
        for square, piece in sense_result:
            if piece is not None:
                result += piece.symbol()
            else:
                result += '.'

        # remove hypotheses with different sense result
        for h, p in list(self.hypotheses.items()):
            s = self.expand_fen(h)
            if result != self.sense_expanded_fen(s, self.sense):
                del self.hypotheses[h]

        # normalize probabilities
        tot = sum(self.hypotheses.values())
        for h, p in self.hypotheses.items():
            self.hypotheses[h] = p / tot

        print("Hypotheses count (after): " + str(len(self.hypotheses)))

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
            for d in [-9, -1, 7]:
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
        print("Choosing move")

        distributions = {chess.Move.null(): {}}  # maps move to a distribution, each distribution is a map from score to probability
        graph = self.generate_submove_graph()  # see generate_submove_graph for details
        # sort move_actions in topological order according to graph
        move_actions.sort(key=lambda x: (x.from_square, abs(x.from_square % 8 - x.to_square % 8) + abs(x.from_square // 8 - x.to_square // 8)))
        for move in move_actions:
            distributions[move] = {}

        target_time = 30
        time = (target_time - 0.1) / (len(self.hypotheses) * (len(move_actions) + 1))

        def add(dictionary, key, value):
            if key in dictionary:
                dictionary[key] += value
            else:
                dictionary[key] = value

        def sigmoid(x):
            return 1 / (1 + math.pow(10, -x / 400))

        # find distributions
        for h, p in self.hypotheses.items():
            board = chess.Board(h)

            # first check if we are in checkmate
            if board.is_checkmate():
                for move in move_actions:
                    add(distributions[move], 0.5, p)
                continue

            # next check if we can take their king
            if board.is_attacked_by(self.color, board.king(not self.color)):
                for move in move_actions:
                    if move.to_square == board.king(not self.color):
                        add(distributions[move], 1.0, p)
                    else:
                        add(distributions[move], 0.0, p)
                continue

            legal_moves = set(board.pseudo_legal_moves)
            scores = {}

            # process null move (root) first
            board.push(chess.Move.null())
            try:
                info = self.engine.analyse(board, chess.engine.Limit(time=time), info=chess.engine.INFO_SCORE)
                score = info["score"].pov(self.color)
                if score.is_mate():
                    if score.mate() > 0:
                        scores[chess.Move.null()] = 1.0
                    else:
                        scores[chess.Move.null()] = 0.0
                else:
                    scores[chess.Move.null()] = sigmoid(score.score())
            except chess.engine.EngineTerminatedError:
                scores[chess.Move.null()] = 0.5
                print("Stockfish crashed")
                print("Time: " + str(time) + "s")
                print("Move: None")
                print("Board: ")
                print(board)
                print(str(board.fen(shredder=True)))
                self.start_engine()
            add(distributions[chess.Move.null()], scores[chess.Move.null()], p)
            board.pop()

            # process rest of moves in topological order
            for move in move_actions:
                # legal move
                if move in legal_moves:
                    try:
                        info = self.engine.analyse(board, chess.engine.Limit(time=time), info=chess.engine.INFO_SCORE, root_moves=[move])
                        score = info["score"].pov(self.color)
                        if score.is_mate():
                            if score.mate() > 0:
                                scores[move] = 1.0
                            else:
                                scores[move] = 0.0
                        else:
                            scores[move] = sigmoid(score.score())
                    except chess.engine.EngineTerminatedError:
                        scores[move] = 0.5
                        print("Stockfish crashed")
                        print("Time: " + str(time) + "s")
                        print("Move: " + move.uci())
                        print("Board: ")
                        print(board)
                        print(str(board.fen(shredder=True)))
                        self.start_engine()
                # blocked move
                else:
                    scores[move] = scores[graph[move]]
                add(distributions[move], scores[move], p)

        # choose move by maximizing some function f
        f_max = -math.inf
        self.move = None
        for move, dist in distributions.items():
            # f is min score
            # f = min(dist)

            # f is expected value of score
            f = 0
            for s, p in dist.items():
                f += s * p
            print(move.uci() + " " + str(f))
            # take max
            if f > f_max:
                f_max = f
                self.move = move

        print("Choose move " + self.move.uci())

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
        print("Handling move result")
        print("Hypotheses count (before): " + str(len(self.hypotheses)))

        # update friendly_board
        if taken_move is None:
            self.friendly_board.push(chess.Move.null())
        else:
            self.friendly_board.push(taken_move)

        # update hypotheses
        # taken_move is equal to requested_move, is a blocked sliding capture move, or is a blocked pawn push, pawn capture, or castle.
        new_hypotheses = {}
        for h, p in self.hypotheses.items():
            board = chess.Board(h)
            # flag is boolean representing if current hypothesis matches given info
            if requested_move == taken_move:
                # make sure requested_move = taken_move is legal in board and matches capture info
                flag = self.check_move(board, requested_move, self.color, captured_opponent_piece, capture_square)
            else:
                # make sure requested_move is not legal, taken_move is legal, and taken_move matches capture info
                flag = not self.check_move(board, requested_move, self.color)
                flag &= self.check_move(board, taken_move, self.color, captured_opponent_piece, capture_square)
            if flag:
                if taken_move is None:
                    board.push(chess.Move.null())
                else:
                    board.push(taken_move)
                new_hypotheses[board.fen(shredder=True)] = p
        self.hypotheses = new_hypotheses

        # normalize probabilities
        tot = sum(self.hypotheses.values())
        for h, p in self.hypotheses.items():
            self.hypotheses[h] = p / tot

        print("Hypotheses count (after): " + str(len(self.hypotheses)))

    def handle_game_end(self, winner_color: Optional[Color], win_reason: Optional[WinReason], game_history: GameHistory):
        print("Game ended")
        if winner_color == self.color:
            print("We won")
        else:
            print("We lost")

        self.color = None
        self.hypotheses = None
        self.sense = None
        self.move = None
        try:
            self.engine.quit()
            self.engine = None
            print("Shutting engine down")
        except chess.engine.EngineTerminatedError:
            print("Engine already terminated")
            pass
