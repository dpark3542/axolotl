import chess
import unittest

from reconchess import GameHistory

from reconchess.bots.axolotl.axolotl import AxolotlBot


class MoveResultTestCase(unittest.TestCase):
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

if __name__ == '__main__':
    unittest.main()
