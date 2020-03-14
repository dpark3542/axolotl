import chess
import unittest

from reconchess.bots.axolotl.axolotl import AxolotlBot


class InitializationTestCase(unittest.TestCase):
    def test_standard_board(self):
        bot = AxolotlBot()
        bot.handle_game_start(chess.WHITE, chess.Board(), "")
        self.assertEqual(1, len(bot.hypotheses))

        bot = AxolotlBot()
        bot.handle_game_start(chess.BLACK, chess.Board(), "")
        self.assertEqual(21, len(bot.hypotheses))

    def test_nonstandard_board(self):
        bot = AxolotlBot()
        bot.handle_game_start(chess.WHITE, chess.Board("r1bqkb1r/ppp1pp1p/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"), "")
        self.assertEqual(29, len(bot.hypotheses))

        bot = AxolotlBot()
        bot.handle_game_start(chess.BLACK, chess.Board("rnbqkbnr/pppppppp/8/8/8/8/P1P1PPPP/R1BQKB1R w KQkq - 0 1"), "")
        self.assertEqual(29, len(bot.hypotheses))

    def test_edge_board(self):
        bot = AxolotlBot()
        bot.handle_game_start(chess.WHITE, chess.Board("8/8/8/b7/3Pp3/8/8/4K2R b K d3 0 1"), "")
        self.assertEqual(10, len(bot.hypotheses))

        bot = AxolotlBot()
        bot.handle_game_start(chess.BLACK, chess.Board("8/8/8/b7/3Pp3/8/8/4K2R w K - 0 1"), "")
        self.assertEqual(16, len(bot.hypotheses))

if __name__ == '__main__':
    unittest.main()
