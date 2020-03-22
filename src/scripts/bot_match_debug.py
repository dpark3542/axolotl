import argparse
import datetime
import random
import chess
from reconchess import load_player, LocalGame
from scripts.play_debug import play_local_game

# modification of reconchess.scripts.rc_bot_match for debugging


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('bot1_path', help='path to first bot source file')
    parser.add_argument('bot2_path', help='path to second bot source file')
    parser.add_argument('--seconds_per_player', default=900, type=float, help='number of seconds each player has to play the entire game.')
    args = parser.parse_args()

    if random.randint(0, 1) == 0:
        white_bot_name, white_player_cls = load_player(args.bot1_path)
        black_bot_name, black_player_cls = load_player(args.bot2_path)
    else:
        white_bot_name, white_player_cls = load_player(args.bot2_path)
        black_bot_name, black_player_cls = load_player(args.bot1_path)

    game = LocalGame(args.seconds_per_player)

    winner_color, win_reason, history = play_local_game(white_player_cls(), black_player_cls(), game=game)

    winner = 'Draw' if winner_color is None else chess.COLOR_NAMES[winner_color]

    print('Game Over!')
    print('Winner: {}!'.format(winner))

    timestamp = datetime.datetime.now().strftime('%Y_%m_%d-%H_%M_%S')

    replay_path = '{}-{}-{}-{}.json'.format(white_bot_name, black_bot_name, winner, timestamp)
    print('Saving replay to {}...'.format(replay_path))
    history.save(replay_path)


if __name__ == '__main__':
    main()
