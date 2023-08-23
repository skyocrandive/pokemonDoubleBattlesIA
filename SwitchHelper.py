# =============================================================================
# Decide whether the IA should switch Pokémon
# =============================================================================
import random

from poke_env.player import BattleOrder

import AttackChooser
import MoveUtilities

from poke_env.environment import Move, Pokemon, DoubleBattle, Effect

def should_withdraw(battle: DoubleBattle, idx_battler, last_switch=None) -> BattleOrder | None:
    """
    return the best switch if pokémon identified by idxBattler should switch, else return None
    :param battle:
    :param idx_battler:
    :return:
    """

    ai_random = random
    ai_random.randint(0, 100)
    should_switch = False

    battler = battle.active_pokemon[idx_battler]
    predictions = []

    # If foe's move can  be super-effective and powerful
    for target in battle.opponent_active_pokemon:
        # predicted_move = Move
        if target is None:
            continue
        (predicted_move, predicted_damage) = MoveUtilities.get_opponent_max_damage_move(battle, battler, target)
        if predicted_damage > 0:
            predictions.append((target, predicted_move, predicted_damage))
        if MoveUtilities.can_outspeed(battle, target,
                                      battler) and predicted_move is not None and battler.damage_multiplier(
                predicted_move.type) > 1:
            switch_chance = 0
            if predicted_damage >= 98:  # most certain ohko
                switch_chance = 80
            elif predicted_damage > 70:  # does a lot of damage
                switch_chance = 30
            should_switch = ai_random.randint(0, 100) < switch_chance

    # Pokémon can't do anything
    if battle.available_moves[idx_battler][0] == Move.retrieve_id("struggle"):
        should_switch = True

    # Pokémon is Encored into an unfavourable move
    if battler.effects.get(Effect.ENCORE) is not None:
        move = battle.available_moves[idx_battler][0]
        score_sum = 0
        score_count = 0
        for target in battle.opponent_active_pokemon:
            score_sum += AttackChooser.get_move_score(battle, move, battler, target)
            score_count += 1
        if score_count > 0 and score_sum / score_count <= 20 and ai_random.randint(0, 100) < 80:
            should_switch = True

    # If there is a single foe which is resting after Hyper Beam or is
    # Truanting (i.e. free turn)
    if len(battle.opponent_active_pokemon) == 1:
        opp = battle.opponent_active_pokemon[0]
        if opp.must_recharge and ai_random.randint(0, 100) < 80:
            should_switch = False

    # Pokémon is about to faint because of Perish Song
    if battler.effects.get(Effect.PERISH1) is not None:
        should_switch = True

    if should_switch:
        switch_order = []
        for pkmn in battle.available_switches[idx_battler]:
            weight = 0
            for (target, move, damage) in predictions:
                move_type = move.type
                # moveType is the type of the predicted move that will hit battler
                type_mod = pkmn.damage_multiplier(move_type)
                temp_weight = 0
                if type_mod == 0:  # if switch immune
                    temp_weight = 65
                    if MoveUtilities.can_damage(pkmn, target):
                        # Greater weight if new Pokémon's can hit effectively the target
                        temp_weight = 85
                elif type_mod < 1:  # if switch resist
                    temp_weight = 40
                    if MoveUtilities.can_damage(pkmn, target):
                        # Greater weight if new Pokémon's can hit effectively the target
                        temp_weight = 60
                if temp_weight > weight:
                    weight = temp_weight
            if weight < 40:
                continue
            if ai_random.randint(0, 100) < weight:
                switch_order.insert(0, pkmn)  # Put this Pokémon first

            else:
                switch_order.append(pkmn)  # put this Pokémon last

        if len(switch_order) > 0:
            switch = switch_order[0]
            if last_switch is not None and switch == last_switch:
                if len(switch_order) > 1:
                    # last_switch = switch_order[1]
                    return BattleOrder(last_switch)
                else:
                    return None
            return BattleOrder(switch_order[0])
    return None


# =============================================================================
# Choose a replacement Pokémon
# =============================================================================

def choose_possible_best_switch(battle, index: int) -> Pokemon | None:
    if not battle.available_switches:
        return None
    # Go through each Pokémon that can be switched to, and choose one with the best type matchup against both opponents
    # (smaller multipliers are better)
    best_score = float('inf')
    best_switch = battle.available_switches[index][0]
    for switch in battle.available_switches[index]:
        score1 = get_matchup_score_default(battle, switch, battle.opponent_active_pokemon[0])
        score2 = get_matchup_score_default(battle, switch, battle.opponent_active_pokemon[1])
        score = score1 + score2
        if score < best_score:
            best_score = score
            best_switch = switch
    return best_switch


def get_matchup_score_default(battle: DoubleBattle, my_pokemon: Pokemon, opponent_pokemon: Pokemon):
    score = 0
    if opponent_pokemon is None:
        return score
    defensive_multiplier = MoveUtilities.pokemon_type_advantage(my_pokemon, opponent_pokemon)
    # A multiplier greater than 1 means we are at a type disadvantage. If there is a better type match, switch
    if defensive_multiplier == 4:
        score += 1
    elif defensive_multiplier == 2:
        score += 0.5
    elif defensive_multiplier == 0.5:
        score -= 0.5
    elif defensive_multiplier == 0.25:
        score -= 1
    if MoveUtilities.can_outspeed(battle, my_pokemon, opponent_pokemon):
        score += 0.5
    if MoveUtilities.can_damage(my_pokemon, opponent_pokemon):
        score += 0.5
    return score
