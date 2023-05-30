import enum

from poke_env.environment import Move, Pokemon, DoubleBattle, Effect, Status, Weather, SideCondition
from poke_env.environment.move_category import MoveCategory
from poke_env.environment.pokemon_type import PokemonType

_multiTargets = {
    "all",
    "allAdjacent",
    "allAdjacentFoes",
}

_abilityWaterImmune = {
    "dry skin",
    "storm drain",
    "water absorb"
}

_abilityElectricImmune = {
    "lightning rod",
    "motor drive",
    "volt absorb"
}


class Stat(enum.Enum):
    HP = "hp"
    ATTACK = "atk"
    DEFENSE = "def"
    SPECIAL_ATTACK = "spa"
    SPECIAL_DEFENSE = "spd"
    SPEED = "spe"


# =============================================================================
# if Move its multiple targets
# =============================================================================
def multiple_targets(move: Move, battle: DoubleBattle):
    target_data = move.target
    if target_data not in _multiTargets:
        return False
    match target_data:
        case "allAdjacent":
            return len(battle.all_active_pokemons) > 2
        case "all":
            return len(battle.all_active_pokemons) > 2
        case "allAdjacentFoes":
            return len(battle.opponent_active_pokemon) > 1
    return False


# =============================================================================
# Move's type effectiveness
# =============================================================================


# For switching. Determines the effectiveness of a potential switch-in against
# an opposing battler.
def pokemon_type_advantage(user: Pokemon, target: Pokemon):
    mod1 = target.damage_multiplier(user.type_1)
    mod2 = 1
    type2 = user.type_2
    if type2:
        mod2 = target.damage_multiplier(type2)
    return mod1 * mod2


# =============================================================================
# Immunity to a move because of the target's ability, item or other effects
# =============================================================================
def is_move_immune(score, move: Move, user: Pokemon, target: Pokemon):
    move_type = move.type
    type_mod = target.damage_multiplier(move_type)
    if (move.base_power > 0 and type_mod == 0) or score <= 0:
        return True
    match move_type:
        case move_type.GROUND:
            if target.ability and target.ability.lower() == "levitate":
                return True
        case move_type.FIRE:
            if target.ability and target.ability.lower() == "flash fire":
                return True
        case move_type.WATER:
            if target.ability and target.ability.lower() in _abilityWaterImmune:
                return True
        case move_type.GRASS:
            if target.ability and target.ability.lower() == "sap sipper":
                return True
        case move_type.ELECTRIC:
            if target.ability and target.ability.lower() in _abilityElectricImmune:
                return True

    if move.base_power > 0 and type_mod <= 1 and target.ability == "wonder guard":
        return True

    if move.id.lower() == Move.retrieve_id("spore"):
        if PokemonType.GRASS in target.types:
            return True
        if target.ability and target.ability.lower() == "overcoat":
            return True
        if target.item and target.item.lower() == "safety goggles":
            return True

    if move.category.value == MoveCategory.STATUS and move.status and Effect.SUBSTITUTE in target.effects.values():
        return True

    if move.category.value == MoveCategory.STATUS and user.ability.lower() == "prankster" \
            and PokemonType.DARK in target.types:
        return True

    if move.priority and Effect.PSYCHIC_TERRAIN in target.effects.values():
        return True
    if move.category.value == MoveCategory.STATUS and move.status and Effect.MISTY_TERRAIN in target.effects.values():
        return True
    if move.category.value == MoveCategory.STATUS and move.status.value == Status.SLP \
            and Effect.ELECTRIC_TERRAIN in target.effects.values():
        return True
    return False


# =============================================================================
# Get approximate properties for a battler
# =============================================================================

def speed_calc(battler: Pokemon):
    stage_mul = [2, 2, 2, 2, 2, 2, 2, 3, 4, 5, 6, 7, 8]
    stage_div = [8, 7, 6, 5, 4, 3, 2, 2, 2, 2, 2, 2, 2]
    stage = battler.boosts["spe"] + 6

    speed = battler.stats["spe"]
    multiplier = 1
    if speed is None:
        speed = battler.base_stats["spe"]

    if battler.status.value == Status.PAR:
        multiplier = 0.5
        if battler.ability and battler.ability.lower() == "quick feet":
            multiplier = 1

    if battler.item and battler.item.lower() == "choice scarf":
        multiplier *= 1.5

    return speed * multiplier * stage_mul[stage] / stage_div[stage]


def pb_rough_stat(battler: Pokemon, stat: Stat):
    if stat == Stat.SPEED:
        return speed_calc(battler)

    stage_mul = [2, 2, 2, 2, 2, 2, 2, 3, 4, 5, 6, 7, 8]
    stage_div = [8, 7, 6, 5, 4, 3, 2, 2, 2, 2, 2, 2, 2]
    stage = battler.boosts[stat.value] + 6
    value = battler.stats[stat.value]
    if value is None:
        value = battler.base_stats[stat.value]
    return (value * stage_mul[stage] / stage_div[stage]).floor


# =============================================================================
# Get a better move's base damage value
# =============================================================================
def pb_move_base_damage(move: Move, user: Pokemon, target: Pokemon):
    base_dmg = move.base_power
    if move.target == "scripted":
        base_dmg = 60
    if move.id == Move.retrieve_id("acrobatics"):
        if user.item is None:
            base_dmg *= 2
    if move.id == Move.retrieve_id("gyro ball"):
        target_speed = pb_rough_stat(target, Stat.SPEED)
        user_speed = pb_rough_stat(user, Stat.SPEED)
        base_dmg = max([min([(25 * target_speed / user_speed).floor, 150]), 1])

    # multi-hit move
    min_hits, max_hits = move.n_hit
    if user.ability.lower() == "skill link":
        base_dmg *= max_hits
    else:
        base_dmg *= move.expected_hits

    return base_dmg


# =============================================================================
# Damage calculation
# =============================================================================

def rough_damage(move: Move, user: Pokemon, target: Pokemon, base_dmg, battle: DoubleBattle):
    # Fixed damage moves

    # Get the move's type
    move_type = move.type
    type_advantage = target.damage_multiplier(move_type)
    if type_advantage == 0:
        return 0

    # ------- Calculate user's attack stat -------------
    atk = pb_rough_stat(user, Stat.ATTACK)
    if move.id == Move.retrieve_id("foul play"):  # Foul Play
        atk = pb_rough_stat(target, Stat.ATTACK)
    elif move.id == Move.retrieve_id("body press"):  # Body Press
        atk = pb_rough_stat(user, Stat.DEFENSE)
    # if special move:
    elif move.category == MoveCategory.SPECIAL:
        atk = pb_rough_stat(user, Stat.SPECIAL_ATTACK)

    # ----- Calculate target's defense stat ---------
    defense = pb_rough_stat(target, Stat.DEFENSE)
    if move.category == MoveCategory.SPECIAL and not move.id == Move.retrieve_id("psyshock"):
        defense = pb_rough_stat(target, Stat.SPECIAL_DEFENSE)

    # ----- Calculate all multiplier effects -------
    multipliers = {
        "base_damage_multiplier": type_advantage,
        "attack_multiplier": 1.0,
        "defense_multiplier": 1.0,
        "final_damage_multiplier": 1.0
    }
    # Ability effects that alter damage
    mold_breaker = False
    if user.ability.lower() == "mold breaker":
        mold_breaker = True

    # Item effects that alter damage
    if user.item.lower() == "life orb":
        multipliers["attack_multiplier"] *= 1.3
    elif user.item.lower() == "expert belt" and type_advantage >= 2:
        multipliers["base_damage_multiplier"] *= 1.2

    if move.category == MoveCategory.SPECIAL:
        if user.item.lower() == "choice specs":
            multipliers["attack_multiplier"] *= 1.5
        if target.item.lower() == "assault vest":
            multipliers["defense_multiplier"] *= 1.5

    elif move.category == MoveCategory.PHYSICAL:
        if user.item.lower() == "choice band":
            multipliers["attack_multiplier"] *= 1.5
        if user.status is not None:
            if user.ability.lower() == "guts":
                multipliers["attack_multiplier"] *= 1.5
            if move.id == move.retrieve_id("facade"):
                multipliers["base_damage_multiplier"] *= 2
        if target.ability.lower() == "multiscale" and target.current_hp_fraction == 1 and not mold_breaker:
            multipliers["defense_multiplier"] *= 2

    # Me First
    # TODO
    # Helping Hand - n/a

    # Terrain moves
    match user.effects.values():
        case Effect.ELECTRIC_TERRAIN:
            if move_type == move_type.ELECTRIC:
                multipliers["base_damage_multiplier"] *= 1.5
        case Effect.PSYCHIC_TERRAIN:
            if move_type == move_type.PSYCHIC:
                multipliers["base_damage_multiplier"] *= 1.5
        case Effect.MISTY_TERRAIN:
            if move_type == move_type.DRAGON:
                multipliers["base_damage_multiplier"] /= 2

    # Multi-targeting attacks
    if multiple_targets(move, battle):
        multipliers["final_damage_multiplier"] *= 0.75

    # Weather
    match battle.weather.values():
        case Weather.SUNNYDAY:
            if move_type == move_type.FIRE:
                multipliers["final_damage_multiplier"] *= 1.5
            elif move_type == move_type.WATER:
                multipliers["final_damage_multiplier"] /= 2
        case Weather.RAINDANCE:
            if move_type == move_type.FIRE:
                multipliers["final_damage_multiplier"] /= 2
            elif move_type == move_type.WATER:
                multipliers["final_damage_multiplier"] *= 1.5
        case Weather.SANDSTORM:
            if PokemonType.ROCK in target.types and move.category == MoveCategory.SPECIAL \
                    and not move.id == Move.retrieve_id("psyshock"):
                multipliers["defense_multiplier"] *= 1.5

    # Critical hits - n/a
    # Random variance - n/a
    # STAB
    if move_type in user.types:
        if user.ability.upper() == "ADAPTABILITY":
            multipliers["final_damage_multiplier"] *= 2
        else:
            multipliers["final_damage_multiplier"] *= 1.5

    # Type effectiveness
    typemod = target.damage_multiplier(move_type)
    multipliers["final_damage_multiplier"] *= typemod

    # Burn, Facade
    if move.category == MoveCategory.PHYSICAL and user.status == Status.BRN \
            and not user.ability.lower() == "guts" and not move.id == move.retrieve_id("facade"):
        multipliers["final_damage_multiplier"] /= 2

    # Aurora Veil, Reflect, Light Screen
    if not move.id == move.retrieve_id("brick break") and not move.id == move.retrieve_id(
            "psychic fangs") and not user.ability.upper() == "INFILTRATOR":
        if SideCondition.AURORA_VEIL in battle.opponent_side_conditions.values():
            multipliers[
                "final_damage_multiplier"] *= 2 / 3.0  # in double battles screens reduce damage by nearly 2/3
            # if len(battle.opponent_active_pokemon) > 1:
            #  multipliers["final_damage_multiplier"] *= 2 / 3.0
            # else:
            #  multipliers["final_damage_multiplier"] /= 2

        elif SideCondition.REFLECT in battle.opponent_side_conditions.values() \
                and move.category == MoveCategory.PHYSICAL:
            multipliers[
                "final_damage_multiplier"] *= 2 / 3.0  # in double battles screens reduce damage by nearly 2/3
            # if len(battle.opponent_active_pokemon) > 1:
            #  multipliers["final_damage_multiplier"] *= 2 / 3.0
            # else:
            #  multipliers["final_damage_multiplier"] /= 2

        elif SideCondition.LIGHT_SCREEN in battle.opponent_side_conditions.values() \
                and move.category == MoveCategory.SPECIAL:
            multipliers[
                "final_damage_multiplier"] *= 2 / 3.0  # in double battles screens reduce damage by nearly 2/3
            # if len(battle.opponent_active_pokemon) > 1:
            #  multipliers["final_damage_multiplier"] *= 2 / 3.0
            # else:
            #  multipliers["final_damage_multiplier"] /= 2

    # ---- Main damage calculation --------
    base_dmg = max([(base_dmg * multipliers["base_damage_multiplier"]).round, 1])
    atk = max([(atk * multipliers["attack_multiplier"]).round, 1])
    defense = max([(defense * multipliers["defense_multiplier"]).round, 1])
    damage = ((((2.0 * user.level / 5) + 2) * base_dmg * atk / defense).floor / 50).floor + 2
    damage = max([(damage * multipliers["final_damage_multiplier"]).round, 1])
    # "AI-specific calculations below"
    # Increased critical hit rates

    return damage.floor


# ----- fine rough_damage -------------------

# =============================================================================
# Accuracy calculation
# =============================================================================
def rough_accuracy(move: Move, user: Pokemon, target: Pokemon = 100):
    # "Always hit" effects and "always hit" accuracy
    if target.effects[Effect.MINIMIZE] and move.id == move.retrieve_id("heavy slam"):
        return 125
    if target.effects[Effect.TELEKINESIS] > 0:
        return 125

    base_acc = move.accuracy

    # if at least medium skill
    if base_acc == 0:
        return 125
    # Get the move's type.
    # type = move.type  # returns a PokemonType object

    # Calculate all modifier effects
    modifiers = {
        "base_accuracy": base_acc,
        "accuracy_stage": user.boosts["accuracy"],
        "evasion_stage": target.boosts["evasion"],
        "accuracy_multiplier": 1.0,
        "evasion_multiplier": 1.0
    }
    # pbCalcAccuracyModifiers(user, target, modifiers, move, type )
    # Check if move can't miss
    if modifiers["base_accuracy"] == 0:
        return 125
    # Calculation
    acc_stage = min([max([modifiers["accuracy_stage"], -6]), 6]) + 6
    eva_stage = min([max([modifiers["evasion_stage"], -6]), 6]) + 6
    stage_mul = [3, 3, 3, 3, 3, 3, 3, 4, 5, 6, 7, 8, 9]
    stage_div = [9, 8, 7, 6, 5, 4, 3, 3, 3, 3, 3, 3, 3]
    accuracy = 100.0 * stage_mul[acc_stage] / stage_div[acc_stage]
    evasion = 100.0 * stage_mul[eva_stage] / stage_div[eva_stage]
    accuracy = (accuracy * modifiers["accuracy_multiplier"]).round
    evasion = (evasion * modifiers["evasion_multiplier"]).round
    if evasion < 1:
        evasion = 1
    return modifiers["base_accuracy"] * accuracy / evasion


'''

  def pbCalcAccuracyModifiers(user: Pokemon, target: Pokemon, modifiers, move: Move, type : PokemonType):
    #moldBreaker = False
    #if user.ability.lower() == "mold breaker":
    #  moldBreaker = True

    modifiers["base_accuracy"] = move.accuracy

    # if weather=hail,blizzard always hits
    if Weather.HAIL in DoubleBattle.weather and move.id.lower() == "blizzard":
      modifiers["accuracy_multiplier"] = 1

    # if weather=raining, hurricane always hits
    if Weather.RAINDANCE in DoubleBattle.weather and move.id.lower() == "hurricane":
      modifiers["accuracy_multiplier"] = 1

'''
