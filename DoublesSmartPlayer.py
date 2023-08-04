import numpy as np
from poke_env.environment import DoubleBattle
from poke_env.environment.pokemon import Pokemon
from poke_env.player.battle_order import BattleOrder, DoubleBattleOrder, DefaultBattleOrder
from poke_env.player.player import Player

import MoveHelper
from SwitchHelper import choose_possible_best_switch


class DoublesSmartPlayer(Player):
    def choose_move(self, battle) -> BattleOrder:
        if not isinstance(battle, DoubleBattle):
            return DefaultBattleOrder()
        # return self.choose_random_doubles_move(battle)
        active_orders = [[], []]
        # if forced to switch choose best switch
        forceSwitch = battle.force_switch
        if sum(forceSwitch) == 1:
            # print("only one to switch")
            best_switch = choose_possible_best_switch(battle, 0)
            # print(best_switch.__repr__)
            return self.create_order(best_switch)
        opponents = battle.opponent_active_pokemon
        for (
                idx,
                (mon, force_switch),
        ) in enumerate(
            zip(
                battle.active_pokemon,
                battle.force_switch
            )
        ):
            if mon:
                if force_switch:
                    best_switch = choose_possible_best_switch(battle, idx)
                    active_orders[idx] = BattleOrder(best_switch)
                    # print(mon.__str__())
                else:
                    order = MoveHelper.default_choose_command(battle, idx)
                    active_orders[idx] = order

        # end for action
        orders = DoubleBattleOrder(*active_orders)
        if orders:
            return orders
        else:
            return DefaultBattleOrder()

    # --------------------------------------------------------------------------------------------------

    ###########################################################
    # teampreview functions ###################################
    def teampreview_performance(self, mon_a: Pokemon, mon_b: Pokemon):
        # We evaluate the performance on mon_a against mon_b as its type advantage
        a_on_b = b_on_a = -np.inf
        for type_ in mon_a.types:
            if type_:
                a_on_b = max(a_on_b, mon_b.damage_multiplier(type_))

        # We do the same for mon_b over mon_a
        for type_ in mon_b.types:
            if type_:
                b_on_a = max(b_on_a, mon_a.damage_multiplier(type_))
        # Our performance metric is the different between the two
        return a_on_b - b_on_a

    def teampreview(self, battle):
        mon_performance = {}
        # For each of our pokémon
        for i, mon in enumerate(battle.team.values()):
            # We store their average performance against the opponent team
            mon_performance[i] = np.mean([
                self.teampreview_performance(mon, opp)
                for opp in battle.opponent_team.values()
            ])

        # We sort our mons by performance
        ordered_mons = sorted(mon_performance, key=lambda k: -mon_performance[k])

        # We start with the one we consider best overall
        # We use i + 1 as python indexes start from 0
        #  but showdown's indexes start from 1
        return "/team " + ''.join([str(i + 1) for i in ordered_mons])
