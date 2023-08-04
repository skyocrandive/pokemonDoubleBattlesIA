"""This module defines a random players baseline
"""
import random
from pprint import pprint

import numpy as np

from poke_env.player.player import Player
from poke_env.player.battle_order import BattleOrder, DoubleBattleOrder, DefaultBattleOrder


class DoubleRandomPlayer(Player):

    def choose_move(self, battle) -> BattleOrder:
        active_orders = [[], []]

        for (
                idx,
                (orders, mon, switches, moves),
        ) in enumerate(
            zip(
                active_orders,
                battle.active_pokemon,
                battle.available_switches,
                battle.available_moves
            )
        ):
            if mon:
                # print("indice e ", idx)
                targets = {}
                for move in moves:
                    targetList = battle.get_possible_showdown_targets(move, mon)

                    noSelfTarg = [x for x in targetList if x>0]
                    if len(noSelfTarg):  #if the move can target an opponent don't target ally
                        targetList=noSelfTarg
                    targets[move] = targetList

                orders.extend(
                    [
                        BattleOrder(move, move_target=target)
                        for move in moves
                        for target in targets[move]
                    ]
                )
                orders.extend([BattleOrder(switch) for switch in switches])

                if sum(battle.force_switch) == 1:
                    if orders:

                        return orders[int(random.random() * len(orders))]
                    return self.choose_default_move()

        orders = DoubleBattleOrder.join_orders(*active_orders)
        if orders:
            return orders[int(random.random() * len(orders))]
        else:
            return DefaultBattleOrder()
        #return self.choose_random_doubles_move(battle)



def teampreview(self, battle):
    # We sort our mons by performance
    ordered_mons = battle.team.values()
    np.random.shuffle(ordered_mons)
    ordered_mons = ordered_mons[:4]


    # We start with the one we consider best overall
    # We use i + 1 as python indexes start from 0
    #  but showdown's indexes start from 1
    return "/team " + ''.join([str(i + 1) for i in ordered_mons])