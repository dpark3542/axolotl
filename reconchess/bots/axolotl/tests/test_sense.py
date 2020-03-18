import chess
import unittest

from reconchess.bots.axolotl.axolotl import AxolotlBot


class ChooseSenseTestCase(unittest.TestCase):
    def test_basic(self):
        bot = AxolotlBot()
        bot.hypotheses = {chess.STARTING_BOARD_FEN: 0.5, "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/1NBQKBNR w Kkq - 0 1": 0.5}
        self.assertEqual(chess.B2, bot.choose_sense([], [], 10))


class SenseResultTestCase(unittest.TestCase):
    def test_basic(self):
        bot = AxolotlBot()
        bot.hypotheses = {chess.STARTING_BOARD_FEN: 0.5, "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/1NBQKBNR w Kkq - 0 1": 0.5}
        bot.sense = chess.B2
        # don't know what order sense results come in
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

    def test_false(self):
        bot = AxolotlBot()
        bot.hypotheses = {chess.STARTING_BOARD_FEN: 0.5, "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/1NBQKBNR w Kkq - 0 1": 0.5}
        bot.sense = chess.B2
        # don't know what order sense results come in
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


if __name__ == '__main__':
    unittest.main()
