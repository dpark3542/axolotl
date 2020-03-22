import argparse
import datetime
import traceback
import chess
import os
from reconchess import load_player, LocalGame
from scripts.play_debug import play_local_game


# modification of reconchess.scripts.rc_bot_match for running multiples bot games


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('bot1_path', help='path to first bot source file')
    parser.add_argument('bot2_path', help='path to second bot source file')
    parser.add_argument('number_of_games', type=int, help='number of games bots have to play for each color')
    parser.add_argument('--seconds_per_player', default=900, type=float, help='number of seconds each player has to play the entire game.')
    args = parser.parse_args()
    n = int(args.number_of_games)
    bot1_wins = 0
    bot2_wins = 0
    draws = 0
    errors = 0

    for i in range(n):
        winner = play(args.bot1_path, args.bot2_path, args.seconds_per_player)

        if winner == "white":
            bot1_wins += 1
        elif winner == "black":
            bot2_wins += 1
        elif winner == "Draw":
            draws += 1
        else:
            errors += 1

        winner = play(args.bot2_path, args.bot1_path, args.seconds_per_player)

        if winner == "white":
            bot2_wins += 1
        elif winner == "black":
            bot1_wins += 1
        elif winner == "Draw":
            draws += 1
        else:
            errors += 1

    print("\n\nResults:")
    print(os.path.split(args.bot1_path)[1] +  " wins: " + str(bot1_wins))
    print(os.path.split(args.bot2_path)[1] + " wins: " + str(bot2_wins))
    print("Draws: " + str(draws))
    print("Errors: " + str(errors))


def play(bot1_path, bot2_path, seconds_per_player):
    white_bot_name, white_player_cls = load_player(bot1_path)
    black_bot_name, black_player_cls = load_player(bot2_path)

    game = LocalGame(seconds_per_player)

    try:
        winner_color, win_reason, history = play_local_game(white_player_cls(), black_player_cls(), game=game)

        winner = 'Draw' if winner_color is None else chess.COLOR_NAMES[winner_color]
    except:
        traceback.print_exc()
        game.end()

        winner = 'ERROR'
        history = game.get_game_history()

    print('Game Over!')
    print('Winner: {}!'.format(winner))

    timestamp = datetime.datetime.now().strftime('%Y_%m_%d-%H_%M_%S')

    replay_path = '{}-{}-{}-{}.json'.format(white_bot_name, black_bot_name, winner, timestamp)
    print('Saving replay to {}...'.format(replay_path))
    history.save(replay_path)

    return winner


if __name__ == '__main__':
    main()
