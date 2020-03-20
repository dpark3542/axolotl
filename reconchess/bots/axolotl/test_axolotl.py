import unittest

import chess
from reconchess import GameHistory
from reconchess.bots.axolotl.axolotl import AxolotlBot


class GameStartTestCase(unittest.TestCase):
    def test_standard_board(self):
        bot = AxolotlBot()
        bot.handle_game_start(chess.WHITE, chess.Board(), "")
        self.assertEqual(1, len(bot.hypotheses))
        bot.handle_game_end(None, None, GameHistory())


class OpponentMoveResultTestCase(unittest.TestCase):
    def test_basic(self):
        bot = AxolotlBot()
        bot.handle_game_start(chess.BLACK, chess.Board(), "")
        bot.handle_opponent_move_result(False, None)
        self.assertEqual(21, len(bot.hypotheses))
        bot.handle_game_end(None, None, GameHistory())

    def test_false(self):
        bot = AxolotlBot()
        bot.handle_game_start(chess.BLACK, chess.Board(), "")
        bot.handle_opponent_move_result(True, chess.A7)
        self.assertEqual(0, len(bot.hypotheses))
        bot.handle_game_end(None, None, GameHistory())

    def test_nonstandard(self):
        bot = AxolotlBot()
        bot.handle_game_start(chess.WHITE, chess.Board("r1bqkb1r/ppp1pp1p/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"), "")
        bot.handle_opponent_move_result(False, None)
        self.assertEqual(28, len(bot.hypotheses))
        bot.handle_game_end(None, None, GameHistory())

        bot.handle_game_start(chess.WHITE, chess.Board("r1bqkb1r/ppp1pp1p/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"), "")
        bot.handle_opponent_move_result(True, chess.D2)
        self.assertEqual(1, len(bot.hypotheses))
        bot.handle_game_end(None, None, GameHistory())

        bot.handle_game_start(chess.BLACK, chess.Board("rnbqkbnr/pppppppp/8/8/8/8/P1P1PPPP/R1BQKB1R w KQkq - 0 1"), "")
        bot.handle_opponent_move_result(False, None)
        self.assertEqual(28, len(bot.hypotheses))
        bot.handle_game_end(None, None, GameHistory())

        bot.handle_game_start(chess.BLACK, chess.Board("rnbqkbnr/pppppppp/8/8/8/8/P1P1PPPP/R1BQKB1R w KQkq - 0 1"), "")
        bot.handle_opponent_move_result(True, chess.D7)
        self.assertEqual(1, len(bot.hypotheses))
        bot.handle_game_end(None, None, GameHistory())

    def test_castle(self):
        bot = AxolotlBot()
        bot.handle_game_start(chess.WHITE, chess.Board("8/8/8/b7/3Pp3/8/8/4K2R b K d3 0 1"), "")
        bot.handle_opponent_move_result(False, None)
        self.assertEqual(8, len(bot.hypotheses))
        bot.handle_game_end(None, None, GameHistory())

        bot.handle_game_start(chess.WHITE, chess.Board("8/8/8/b7/3Pp3/8/8/4K2R b K d3 0 1"), "")
        bot.handle_opponent_move_result(True, chess.D3)
        self.assertEqual(1, len(bot.hypotheses))
        bot.handle_game_end(None, None, GameHistory())

        bot.handle_game_start(chess.WHITE, chess.Board("8/8/8/b7/3Pp3/8/8/4K2R b K d3 0 1"), "")
        bot.handle_opponent_move_result(True, chess.E1)
        self.assertEqual(1, len(bot.hypotheses))
        bot.handle_game_end(None, None, GameHistory())

        bot.handle_game_start(chess.BLACK, chess.Board("8/8/8/b7/3Pp3/8/8/4K2R w K - 0 1"), "")
        bot.handle_opponent_move_result(False, None)
        self.assertEqual(17, len(bot.hypotheses))
        bot.handle_game_end(None, None, GameHistory())

    def test_promotion(self):
        bot = AxolotlBot()
        bot.handle_game_start(chess.BLACK, chess.Board("8/3P4/8/8/8/8/1p4p1/8 w - - 0 1"), "")
        bot.handle_opponent_move_result(False, None)
        self.assertEqual(5, len(bot.hypotheses))
        bot.handle_game_end(None, None, GameHistory())

        bot.handle_game_start(chess.WHITE, chess.Board("8/3P4/8/8/8/8/1p4p1/8 b - - 0 1"), "")
        bot.handle_opponent_move_result(False, None)
        self.assertEqual(9, len(bot.hypotheses))
        bot.handle_game_end(None, None, GameHistory())


class ChooseSenseTestCase(unittest.TestCase):
    def test_basic(self):
        bot = AxolotlBot()
        bot.handle_game_start(chess.WHITE, chess.Board(), "")
        bot.hypotheses = {chess.STARTING_BOARD_FEN: 0.5, "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/1NBQKBNR w Kkq - 0 1": 0.5}
        self.assertEqual(chess.B2, bot.choose_sense([], [], 10))
        bot.handle_game_end(None, None, GameHistory())


class SenseResultTestCase(unittest.TestCase):
    def test_basic(self):
        bot = AxolotlBot()
        bot.handle_game_start(chess.WHITE, chess.Board(), "")
        bot.hypotheses = {chess.STARTING_BOARD_FEN: 0.5, "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/1NBQKBNR w Kkq - 0 1": 0.5}
        bot.sense = chess.B2
        bot.handle_sense_result([
            (chess.A1, chess.Piece(chess.ROOK, chess.WHITE)),
            (chess.B1, chess.Piece(chess.KNIGHT, chess.WHITE)),
            (chess.C1, chess.Piece(chess.BISHOP, chess.WHITE)),
            (chess.A2, chess.Piece(chess.PAWN, chess.WHITE)),
            (chess.B2, chess.Piece(chess.PAWN, chess.WHITE)),
            (chess.C2, chess.Piece(chess.PAWN, chess.WHITE)),
            (chess.A3, None),
            (chess.B3, None),
            (chess.C3, None)
        ])
        self.assertIn(chess.STARTING_BOARD_FEN, bot.hypotheses)
        self.assertEqual(1.0, bot.hypotheses[chess.STARTING_BOARD_FEN])
        bot.handle_game_end(None, None, GameHistory())

    def test_false(self):
        bot = AxolotlBot()
        bot.handle_game_start(chess.WHITE, chess.Board(), "")
        bot.hypotheses = {chess.STARTING_BOARD_FEN: 0.5, "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/1NBQKBNR w Kkq - 0 1": 0.5}
        bot.sense = chess.B2
        bot.handle_sense_result([
            (chess.A1, chess.Piece(chess.ROOK, chess.WHITE)),
            (chess.B1, chess.Piece(chess.KNIGHT, chess.WHITE)),
            (chess.C1, chess.Piece(chess.BISHOP, chess.WHITE)),
            (chess.A2, chess.Piece(chess.PAWN, chess.WHITE)),
            (chess.B2, chess.Piece(chess.PAWN, chess.WHITE)),
            (chess.C2, chess.Piece(chess.PAWN, chess.WHITE)),
            (chess.A3, None),
            (chess.B3, None),
            (chess.C3, chess.Piece(chess.PAWN, chess.WHITE))
        ])
        self.assertEqual(0, len(bot.hypotheses))
        bot.handle_game_end(None, None, GameHistory())


class ChooseMoveTestCase(unittest.TestCase):
    def test_basic(self):
        bot = AxolotlBot()
        bot.handle_game_start(chess.WHITE, chess.Board(), "")
        moves = list(chess.Board().pseudo_legal_moves)
        for i in range(7):
            moves.append(chess.Move.from_uci("abcdefgh"[i] + "2" + "abcdefgh"[i + 1] + "3"))
        for i in range(1, 8):
            moves.append(chess.Move.from_uci("abcdefgh"[i] + "2" + "abcdefgh"[i - 1] + "3"))
        self.assertNotEqual(chess.Move.null(), bot.choose_move(moves, 1.0))
        bot.handle_game_end(None, None, GameHistory())

    def test_basic_2(self):
        bot = AxolotlBot()
        bot.handle_game_start(chess.WHITE, chess.Board("7k/b7/8/8/3P4/8/5K2/R7 w - - 0 1"), "")
        moves = list(chess.Board("7k/b7/8/8/3P4/8/5K2/R7 w - - 0 1").pseudo_legal_moves)
        moves.append(chess.Move.from_uci("d4c5"))
        moves.append(chess.Move.from_uci("d4e5"))
        self.assertIn(bot.choose_move(moves, 1.0), [chess.Move.from_uci("a1a7"), chess.Move.from_uci("a1h1")])
        bot.handle_game_end(None, None, GameHistory())


class MoveResultTestCase(unittest.TestCase):
    def test_basic(self):
        bot = AxolotlBot()
        bot.handle_game_start(chess.WHITE, chess.Board("8/b7/8/8/3P4/8/5K2/R7 w - - 0 1"), "")
        bot.move = chess.Move.from_uci("a1a7")
        bot.handle_move_result(chess.Move.from_uci("a1a7"), chess.Move.from_uci("a1a7"), True, chess.A7)
        self.assertEqual(1, len(bot.hypotheses))
        bot.handle_game_end(None, None, GameHistory())

    def test_false(self):
        bot = AxolotlBot()
        bot.handle_game_start(chess.WHITE, chess.Board("8/b7/8/8/3P4/8/5K2/R7 w - - 0 1"), "")
        bot.move = chess.Move.from_uci("a1a7")
        bot.handle_move_result(chess.Move.from_uci("a1a7"), chess.Move.from_uci("a1a7"), False, None)
        self.assertEqual(0, len(bot.hypotheses))
        bot.handle_game_end(None, None, GameHistory())

        bot.handle_game_start(chess.WHITE, chess.Board("8/b7/8/8/3P4/8/5K2/R7 w - - 0 1"), "")
        bot.move = chess.Move.from_uci("a1a7")
        bot.handle_move_result(chess.Move.from_uci("a1a7"), chess.Move.from_uci("a1a6"), False, None)
        self.assertEqual(0, len(bot.hypotheses))
        bot.handle_game_end(None, None, GameHistory())

    def test_blocked(self):
        bot = AxolotlBot()
        bot.handle_game_start(chess.WHITE, chess.Board("8/b7/8/8/3P4/8/5K2/R7 w - - 0 1"), "")
        bot.move = chess.Move.from_uci("a1a8")
        bot.handle_move_result(chess.Move.from_uci("a1a8"), chess.Move.from_uci("a1a7"), True, chess.A7)
        self.assertEqual(1, len(bot.hypotheses))
        bot.handle_game_end(None, None, GameHistory())

        bot.handle_game_start(chess.BLACK, chess.Board(), "")
        bot.hypotheses = {"8/b7/8/8/3P4/8/5K2/R7 b - - 0 1": 0.5, "8/b7/8/8/8/8/5K2/R7 b - - 0 1": 0.5}
        bot.move = chess.Move.from_uci("a7f2")
        bot.handle_move_result(chess.Move.from_uci("a7f2"), chess.Move.from_uci("a7f2"), True, chess.F2)
        self.assertEqual(1, len(bot.hypotheses))
        bot.handle_game_end(None, None, GameHistory())

        bot.handle_game_start(chess.BLACK, chess.Board(), "")
        bot.hypotheses = {"8/b7/8/8/3P4/8/5K2/R7 b - - 0 1": 0.5, "8/b7/8/8/8/8/5K2/R7 b - - 0 1": 0.5}
        bot.move = chess.Move.from_uci("a7f2")
        bot.handle_move_result(chess.Move.from_uci("a7f2"), chess.Move.from_uci("a7d4"), True, chess.D4)
        self.assertEqual(1, len(bot.hypotheses))
        bot.handle_game_end(None, None, GameHistory())


class BasicTestCases(unittest.TestCase):
    def test_one_turn(self):
        board = chess.Board()

        bot = AxolotlBot()
        bot.handle_game_start(chess.BLACK, chess.Board(), "")

        board.push(chess.Move.from_uci("e2e4"))

        self.assertEqual(1, len(bot.hypotheses))

        bot.handle_opponent_move_result(False, None)

        self.assertEqual(21, len(bot.hypotheses))

        moves = list(board.pseudo_legal_moves)
        for i in range(7):
            moves.append(chess.Move.from_uci("abcdefgh"[i] + "7" + "abcdefgh"[i + 1] + "6"))
        for i in range(1, 8):
            moves.append(chess.Move.from_uci("abcdefgh"[i] + "7" + "abcdefgh"[i - 1] + "6"))

        sense = bot.choose_sense(chess.BB_SQUARES, moves, 10)

        # code for sense from reconchess.LocalGame
        rank, file = chess.square_rank(sense), chess.square_file(sense)
        sense_result = []
        for delta_rank in [1, 0, -1]:
            for delta_file in [-1, 0, 1]:
                if 0 <= rank + delta_rank <= 7 and 0 <= file + delta_file <= 7:
                    sense_square = chess.square(file + delta_file, rank + delta_rank)
                    sense_result.append((sense_square, board.piece_at(sense_square)))

        bot.handle_sense_result(sense_result)

        self.assertLess(1, len(bot.hypotheses))

        move = bot.choose_move(moves, 10)

        if move in board.pseudo_legal_moves:
            bot.handle_move_result(move, move, False, None)
        else:
            bot.handle_move_result(move, None, False, None)

        self.assertLess(1, len(bot.hypotheses))

        bot.handle_game_end(None, None, GameHistory())

if __name__ == '__main__':
    unittest.main()
