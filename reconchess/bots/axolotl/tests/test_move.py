import chess
import unittest

from reconchess import GameHistory
from reconchess.bots.axolotl.axolotl import AxolotlBot


class ChooseMoveTestCase(unittest.TestCase):
    def test_basic(self):
        bot = AxolotlBot()
        bot.handle_game_start(chess.WHITE, chess.Board(), "")
        moves = list(chess.Board().pseudo_legal_moves)
        for i in range(7):
            moves.append(chess.Move.from_uci("abcdefgh"[i] + "2" + "abcdefgh"[i + 1] + "3"))
        for i in range(1, 8):
            moves.append(chess.Move.from_uci("abcdefgh"[i] + "2" + "abcdefgh"[i - 1] + "3"))
        moves.append(chess.Move.null())
        self.assertNotEqual(chess.Move.null(), bot.choose_move(moves, 1.0))
        bot.handle_game_end(None, None, GameHistory())


if __name__ == '__main__':
    unittest.main()
