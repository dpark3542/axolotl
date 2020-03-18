import chess
import unittest

from reconchess import GameHistory

from reconchess.bots.axolotl.axolotl import AxolotlBot


class GameStartTestCase(unittest.TestCase):
    def test_standard_board(self):
        bot = AxolotlBot()
        bot.handle_game_start(chess.WHITE, chess.Board(), "")
        self.assertEqual(1, len(bot.hypotheses))
        bot.handle_game_end(None, None, GameHistory())


if __name__ == '__main__':
    unittest.main()
