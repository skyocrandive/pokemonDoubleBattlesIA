import enum

from poke_env.environment import Move, Pokemon, DoubleBattle, Effect, Status, Weather, SideCondition
from poke_env.environment.move_category import MoveCategory
from poke_env.environment.pokemon_type import PokemonType

_fixedDamageLevel = {
    Move.retrieve_id("night shade"),
    Move.retrieve_id("seismic toss"),
}
_moveHalveHP = {
    Move.retrieve_id("nature's madness"),
    Move.retrieve_id("super fang"),
}

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
            if target.item and target.item.lower() == "air balloon":
                return True
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

    if move.base_power > 0 and type_mod <= 1 and target.ability and target.ability == "wonder guard":
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
    """
    estimates battler's current speed value
    :param battler: ,
    :return:
    """
    stage_mul = [2, 2, 2, 2, 2, 2, 2, 3, 4, 5, 6, 7, 8]
    stage_div = [8, 7, 6, 5, 4, 3, 2, 2, 2, 2, 2, 2, 2]
    stage = battler.boosts["spe"] + 6

    speed = battler.stats["spe"]
    multiplier = 1
    if speed is None:
        iv = 31
        ev = 0
        level = battler.level
        base_speed = battler.base_stats["spe"]
        nature = 1
        # speed = math.floor(math.floor(2*base_speed+iv+math.floor(ev/4)*level)*nature)
        speed = calc_non_hp_stat_value(base_speed, iv, ev, level, nature)
    if battler.status.value == Status.PAR:
        multiplier = 0.5
        if battler.ability and battler.ability.lower() == "quick feet":
            multiplier = 1

    if battler.item and battler.item.lower() == "choice scarf":
        multiplier *= 1.5

    return speed * multiplier * stage_mul[stage] / stage_div[stage]


def rough_stat(battler: Pokemon, stat: Stat):
    """
    estimates battler current value of a given stat
    :param battler: Pokémon,
    :param stat: Stat,
    :return:
    """
    if stat == Stat.SPEED:
        return speed_calc(battler)

    stage_mul = [2, 2, 2, 2, 2, 2, 2, 3, 4, 5, 6, 7, 8]
    stage_div = [8, 7, 6, 5, 4, 3, 2, 2, 2, 2, 2, 2, 2]
    stage = battler.boosts[stat.value] + 6
    value = battler.stats[stat.value]
    if value is None:
        base_value = battler.base_stats[stat.value]
        iv = 31
        ev = 0
        level = battler.level
        nature = 1
        # value = math.floor(math.floor(2*base_value+iv+math.floor(ev/4)*level)*nature)
        value = calc_non_hp_stat_value(base_value, iv, ev, level, nature)
    return value * stage_mul[stage] / stage_div[stage]


def calc_hp_stat_value(base_hp, iv, ev, level):
    """
    calculate the hp stat of a Pokémon given base stat, iv, ev and level
    :param base_hp:
    :param iv:,
    :param ev:,
    :param level:,
    :return:
    """
    return math.floor(((2 * base_hp + iv + math.floor(ev / 4)) * level) / 100) + level + 10


def calc_non_hp_stat_value(base_stat, iv, ev, level, nature_bonus):
    """
    calculate the stat value of a Pokémon using the given base stat, iv, ev, level, and the bonus given to the nature.
    this function does not calculate the HP stat.
    To calculate the HP stat use calc_hp_stat_value(base_stat, iv, ev, level)
    :param base_stat:
    :param iv:,
    :param ev:,
    :param level:,
    :param nature_bonus:,
    :return:
    """
    return math.floor(math.floor(2 * base_stat + iv + math.floor(ev / 4) * level) * nature_bonus)


# =============================================================================
# Get a better move's base damage value
# =============================================================================
def move_base_damage(move: Move, user: Pokemon, target: Pokemon):
    """
    calculate a move's base damage even considering special cases such as acrobatics, gyro ball
    and sets the base damage for counter-like moves to 60
    :param move:,
    :param user:,
    :param target:,
    :return:
    """
    base_dmg = move.base_power
    if move.target == "scripted":
        base_dmg = 60
    if move.id == Move.retrieve_id("acrobatics"):
        if user.item is None:
            base_dmg *= 2
    if move.id == Move.retrieve_id("gyro ball"):
        target_speed = rough_stat(target, Stat.SPEED)
        user_speed = rough_stat(user, Stat.SPEED)
        base_dmg = max([min([(25 * target_speed / user_speed), 150]), 1])

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
    """
    calculate a rough estimation of the damage dealt by a move to the target given the move's base damage
    :param move:,
    :param user:,
    :param target:,
    :param base_dmg:,
    :param battle:,
    :return:
    """

    # Fixed damage moves
    if move.id in _fixedDamageLevel:  # move deals damage depending on user level
        return user.level

    if move.id in _moveHalveHP:  # move deals half of target's current HP
        max_hp = target.max_hp
        if max_hp <= 100:
            max_hp = rough_max_hp(target)
        return math.floor(max_hp * target.current_hp_fraction / 2)

    if base_dmg == 0:
        return 0

    # Get the move's type
    move_type = move.type
    type_advantage = target.damage_multiplier(move_type)
    if type_advantage == 0:
        return 0

    # ------- Calculate user's attack stat -------------
    atk = rough_stat(user, Stat.ATTACK)
    if move.id == Move.retrieve_id("foul play"):  # Foul Play
        atk = rough_stat(target, Stat.ATTACK)
    elif move.id == Move.retrieve_id("body press"):  # Body Press
        atk = rough_stat(user, Stat.DEFENSE)
    # if special move:
    elif move.category == MoveCategory.SPECIAL:
        atk = rough_stat(user, Stat.SPECIAL_ATTACK)

    # ----- Calculate target's defense stat ---------
    defense = rough_stat(target, Stat.DEFENSE)
    if move.category == MoveCategory.SPECIAL and not move.id == Move.retrieve_id("psyshock"):
        defense = rough_stat(target, Stat.SPECIAL_DEFENSE)

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
    if user.item and user.item.lower() == "life orb":
        multipliers["attack_multiplier"] *= 1.3
    elif user.item and user.item.lower() == "expert belt" and type_advantage >= 2:
        multipliers["base_damage_multiplier"] *= 1.2

    if move.category == MoveCategory.SPECIAL:
        if user.item and user.item.lower() == "choice specs":
            multipliers["attack_multiplier"] *= 1.5
        if target.item and target.item.lower() == "assault vest":
            multipliers["defense_multiplier"] *= 1.5

    elif move.category == MoveCategory.PHYSICAL:
        if user.item and user.item.lower() == "choice band":
            multipliers["attack_multiplier"] *= 1.5
        if user.status is not None:
            if user.ability.lower() == "guts":
                multipliers["attack_multiplier"] *= 1.5
            if move.id == move.retrieve_id("facade"):
                multipliers["base_damage_multiplier"] *= 2
        if target.ability and target.ability.lower() == "multiscale" and target.current_hp_fraction == 1 \
                and not mold_breaker:
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
    base_dmg = max([(base_dmg * multipliers["base_damage_multiplier"]), 1])
    atk = max([(atk * multipliers["attack_multiplier"]), 1])
    defense = max([(defense * multipliers["defense_multiplier"]), 1])
    damage = ((((2.0 * user.level / 5) + 2) * base_dmg * atk / defense) / 50) + 2
    damage = max([(damage * multipliers["final_damage_multiplier"]), 1])
    # "AI-specific calculations below"
    # Increased critical hit rates

    return damage


# ----- fine rough_damage -------------------

# =============================================================================
# Accuracy calculation
# =============================================================================
def rough_accuracy(move: Move, user: Pokemon, target: Pokemon):
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
    accuracy = (accuracy * modifiers["accuracy_multiplier"])
    evasion = (evasion * modifiers["evasion_multiplier"])
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


def get_max_damage_move(battle: DoubleBattle, my_pokemon: Pokemon, opponents: List[Pokemon], moves: List[Move]) -> \
        (Move, int, int):
    """
    returns the move that deals the most damage across the opponent's active Pokémon
    the value returned is a tuple (move, target, damage) with
    move : the most damaging move
    target : integer specifying the target of the move (useful to create BattleOrder)
    damage : the sum of the predicted damage dealt with one single move

    """
    maxmove = None
    maxtarget = 0
    maxdamage = 0
    for move in moves:
        # print(move.__str__())

        move_targets = battle.get_possible_showdown_targets(move, my_pokemon)
        '''
        base_damage1 = move_base_damage(move, my_pokemon, opponents[0])
        damage1 = rough_damage(move, my_pokemon, opponents[0], base_damage1, battle)
        base_damage2 = move_base_damage(move, my_pokemon, opponents[1])
        damage2 = rough_damage(move, my_pokemon, opponents[1], base_damage2, battle)
        '''
        damage1 = calculate_percentage_damage(move, my_pokemon, opponents[0], battle)
        damage2 = calculate_percentage_damage(move, my_pokemon, opponents[1], battle)
        if len(move_targets) == 1:  # status / spread move (moveTargets = [0])
            damage = damage1 + damage2
            target = move_targets[0]
        else:  # can select target
            if damage1 > damage2:
                damage = damage1
                target = 1
            else:
                damage = damage2
                target = 2
        if damage > maxdamage:
            maxdamage = damage
            maxmove = move
            maxtarget = target
    return maxmove, maxtarget, maxdamage

def rough_max_hp(battler : Pokemon):
    base = battler.base_stats[Stat.HP.value]
    level = battler.level
    iv = 31
    ev = 0
    hp = math.floor(((2*base+iv+math.floor(ev/4))*level)/100) + level + 10
    return hp
def rough_percentage_damage(move: Move, user: Pokemon, target: Pokemon, base_dmg, battle: DoubleBattle):
    damage = rough_damage(move, user, target, base_dmg, battle)
    hp = rough_max_hp(target)
    # print("move", move, "target", target, "damage", damage, "target hp", hp)
    if damage <= 0:
        return 0
    return (damage / hp) * 100


def calculate_percentage_damage(move: Move, user: Pokemon, target: Pokemon, battle: DoubleBattle):
    base_damage = move_base_damage(move, user, target)
    return rough_percentage_damage(move, user, target, base_damage, battle)


def calculate_damage(move: Move, user: Pokemon, target: Pokemon, battle: DoubleBattle):
    base_damage = move_base_damage(move, user, target)
    return rough_damage(move, user, target, base_damage, battle)
