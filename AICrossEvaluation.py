import asyncio
import sys
import time

import poke_env.player
from poke_env import PlayerConfiguration, LocalhostServerConfiguration
from poke_env.player import background_cross_evaluate
from tabulate import tabulate

from DoublesRandomPlayer import DoubleRandomPlayer
from DoublesMaxDamagePlayer import DoublesMaxDamagePlayer
from DoublesSmartPlayer import DoublesSmartPlayer
from DoublesTrueMaxDamagePlayer import DoublesTrueMaxDamagePlayer
from Teams import RandomTeamFromPool

sys.path.append("..")


async def main():
    battle_format = "gen8vgc2021"

    random_player = DoubleRandomPlayer(
        player_configuration=PlayerConfiguration("rando", None),
        server_configuration=LocalhostServerConfiguration,
        team=RandomTeamFromPool(),
        battle_format=battle_format

    )

    maxdamage_player = DoublesMaxDamagePlayer(
        player_configuration=PlayerConfiguration("elMaxoDamagio", None),
        server_configuration=LocalhostServerConfiguration,
        team=RandomTeamFromPool(),
        battle_format=battle_format
    )

    true_maxdamage_player = DoublesTrueMaxDamagePlayer(
        player_configuration=PlayerConfiguration("elMaxoDamagioMax", None),
        server_configuration=LocalhostServerConfiguration,
        team=RandomTeamFromPool(),
        battle_format=battle_format
    )

    smart_player = DoublesSmartPlayer(
        player_configuration=PlayerConfiguration("SmartBoyVGC", None),
        server_configuration=LocalhostServerConfiguration,
        team=RandomTeamFromPool(),
        battle_format=battle_format
    )

    n_challenges = 50
    players = [
        random_player,
        maxdamage_player,
        true_maxdamage_player,
        smart_player,
    ]
    cross_eval_task = background_cross_evaluate(players, n_challenges)
    cross_evaluation = cross_eval_task.result()
    table = [["-"] + [p.username for p in players]]
    for p_1, results in cross_evaluation.items():
        table.append([p_1] + [cross_evaluation[p_1][p_2] for p_2 in results])
    print("Cross evaluation of DQN with baselines:")
    print(tabulate(table))

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
