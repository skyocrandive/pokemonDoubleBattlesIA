import asyncio
import sys

from poke_env import PlayerConfiguration, LocalhostServerConfiguration

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

    match player_choice:
        case 1:
            print("battle request sent by " + random_player.username)
            await random_player.send_challenges(human_player_name, n_challenges=1)
        case 2:
            print("battle request sent by " + maxdamage_player.username)
            await maxdamage_player.send_challenges(human_player_name, n_challenges=1)
        case 3:
            print("battle request sent by " + true_maxdamage_player.username)
            await true_maxdamage_player.send_challenges(human_player_name, n_challenges=1)
        case 4:
            print("battle request sent by " + smart_player.username)
            await smart_player.send_challenges(human_player_name, n_challenges=1)
        case _:
            print("Invalid IA. Closing...")


if __name__ == "__main__":
    # skyocrandive
    human_player_name = input("Please enter a Pokemon Showdown username:\n")

    player_choice = int(input("1: DoublesRandomPlayer\n"
                              "2: DoublesMaxDamagePlayer\n"
                              "3: DoublesTrueMaxDamagePlayer\n"
                              "4: DoublesSmartPlayer\n"))

    asyncio.get_event_loop().run_until_complete(main())
