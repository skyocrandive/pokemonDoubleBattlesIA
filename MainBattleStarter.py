import asyncio
import time
import sys

from poke_env import PlayerConfiguration, LocalhostServerConfiguration

from DoublesRandomPlayer import DoubleRandomPlayer
from DoublesMaxDamagePlayer import DoublesMaxDamagePlayer
from DoublesSmartPlayer import DoublesSmartPlayer
from DoublesTrueMaxDamagePlayer import DoublesTrueMaxDamagePlayer
from Teams import RandomTeamFromPool

sys.path.append("..")

import BattleUtilities
from poke_env.player.random_player import RandomPlayer
#from MaxDamagePlayer import MaxDamagePlayer
from poke_env.player.player import Player
from poke_env.player.baselines import SimpleHeuristicsPlayer
from poke_env.environment.move_category import MoveCategory

async def main():
    start = time.time()

    random_player = DoubleRandomPlayer(
        player_configuration=PlayerConfiguration("rando", None),
        server_configuration=LocalhostServerConfiguration,
        team=RandomTeamFromPool(),
        battle_format="gen8vgc2020"

    )

    maxdamage_player = DoublesMaxDamagePlayer(
        player_configuration=PlayerConfiguration("elMaxoDamagio", None),
        server_configuration=LocalhostServerConfiguration,
        team=RandomTeamFromPool(),
        battle_format="gen8vgc2020"
    )

    true_maxdamage_player = DoublesTrueMaxDamagePlayer(
        player_configuration=PlayerConfiguration("elMaxoDamagioMax", None),
        server_configuration=LocalhostServerConfiguration,
        team=RandomTeamFromPool(),
        battle_format="gen8vgc2020"
    )

    smart_player = DoublesSmartPlayer(
        player_configuration=PlayerConfiguration("SmartBoyVGC", None),
        server_configuration=LocalhostServerConfiguration,
        team=RandomTeamFromPool(),
        battle_format="gen8vgc2020"
    )

    start = time.time()
    #await random_player.send_challenges("skyocrandive", n_challenges=1)
    #await maxdamage_player.send_challenges("skyocrandive", n_challenges=1)
    #await true_maxdamage_player.send_challenges("skyocrandive", n_challenges=1)
    await smart_player.send_challenges("skyocrandive", n_challenges=1)
    #await smart_damage_player.battle_against(heuristic_player, n_battles=500)

    print(
        "Smart damage player won %d / 500 battles against heuristic_player (this took %f seconds)"
        % (
            random_player.n_won_battles, time.time() - start
        )
    )

if __name__ == "__main__":
        asyncio.get_event_loop().run_until_complete(main())

