from concurrent.futures import ProcessPoolExecutor, as_completed
import random
from tqdm.autonotebook import tqdm


def _play_one(game_cls, game_args, game_kwargs, game_index, save_round_data, seed):  # noqa: PLR0917
    random.seed(seed)

    game = game_cls(*game_args, **game_kwargs)
    game.play_game()

    out = [
        {
            'name': str(key),
            'score': val['score'],
            'game': game_index,
            'busted': val['busted'],
            'rounds': val['rounds'],
        }
        for key, val in game.player_scores.items()
    ]

    round_data = []

    if save_round_data:
        round_data = [r.copy() for r in game.round_data]
        for r in round_data:
            r['game'] = game_index

    return out, round_data


def simulate_parallel(
    game_cls,
    n=100,
    workers=8,
    save_round_data=False,
    *game_args,
    **game_kwargs,
):
    """future/parallel part I outsourced to ChatGPT, faster than my Game.simulate approach"""
    out = []
    all_round_data = []

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(
                _play_one,
                game_cls,
                game_args,
                game_kwargs,
                i,
                save_round_data,
                random.randrange(2**63),
            )
            for i in range(n)
        ]

        with tqdm(total=n) as pbar:
            for future in as_completed(futures):
                game_out, round_data = future.result()

                out.extend(game_out)
                all_round_data.extend(round_data)

                pbar.update(1)

    return out, all_round_data
