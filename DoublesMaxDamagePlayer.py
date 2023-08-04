"""This module defines a random players baseline
"""
import random
from pprint import pprint

import numpy as np
from poke_env.environment.pokemon import Pokemon
from poke_env.environment.move import Move
from poke_env.player.player import Player
from poke_env.player.battle_order import BattleOrder, DoubleBattleOrder, DefaultBattleOrder

import BattleUtilities


class DoublesMaxDamagePlayer(Player):
    def choose_move(self, battle) -> BattleOrder:
        # return self.choose_random_doubles_move(battle)
        active_orders = [[], []]

        # if forced to switch choose best switch
        forceSwitch = battle.force_switch
        if sum(forceSwitch) == 1:
            # print("only one to switch")
            best_switch = self.choose_best_switch(battle, 0)
            # print(best_switch.__repr__)
            return self.create_order(best_switch)
        opponents = battle.opponent_active_pokemon
        for (
                idx,
                (mon, switches, moves, force_switch),
        ) in enumerate(
            zip(
                battle.active_pokemon,
                battle.available_switches,
                battle.available_moves,
                battle.force_switch
            )
        ):
            if mon:
                if force_switch:
                    best_switch = self.choose_best_switch(battle, idx)
                    active_orders[idx] = BattleOrder(best_switch)
                    # print(mon.__str__())
                else:
                    (move, target, damage) = BattleUtilities.get_max_damage_move(battle, mon, opponents, moves)
                    # print("move ", move, " target ", target, "predicted damage", damage)
                    active_orders[idx] = BattleOrder(move, move_target=target)

        # end for action
        orders = DoubleBattleOrder(*active_orders)
        if orders:
            return orders
        else:
            return DefaultBattleOrder()


#------------------------------------------------------
    def choose_best_switch(self, battle, index: int):
        if not battle.available_switches:
            return None
        # Go through each Pokémon that can be switched to, and choose one with the best type matchup against both opponents
        # (smaller multipliers are better)
        best_score = float('inf')
        best_switch = battle.available_switches[index][0]
        for switch in battle.available_switches[index]:
            score1 = self.get_matchup_score(switch, battle.opponent_active_pokemon[0])
            score2 = self.get_matchup_score(switch, battle.opponent_active_pokemon[1])
            score = score1+score2
            if score < best_score:
                best_score = score
                best_switch = switch
        return best_switch

    def get_matchup_score(self, my_pokemon, opponent_pokemon):
        score = 0
        if opponent_pokemon is None:
            return score
        defensive_multiplier = BattleUtilities.get_defensive_type_multiplier(my_pokemon, opponent_pokemon)
        # A multiplier greater than 1 means we are at a type disadvantage. If there is a better type match, switch
        if defensive_multiplier == 4:
            score += 1
        elif defensive_multiplier == 2:
            score += 0.5
        elif defensive_multiplier == 0.5:
            score -= 0.5
        elif defensive_multiplier == 0.25:
            score -= 1
        if BattleUtilities.opponent_can_outspeed(my_pokemon, opponent_pokemon):
            score += 0.5
        return score

###########################################################
# teampreview functions ###################################
    def teampreview_performance(self, mon_a : Pokemon, mon_b : Pokemon):
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


