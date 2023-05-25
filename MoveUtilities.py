from enum import Enum

from poke_env.environment import Move, Pokemon, DoubleBattle, Field, Effect, Status, Weather, SideCondition
from poke_env.environment.move_category import MoveCategory
from poke_env.environment.pokemon_type import PokemonType

_multiTargets = {
  "all",
  "allAdjacent",
  "allAdjacentFoes",
}

_abilityWaterImune = {
  "dryskin",
  "stormdrain",
  "waterabsirb"
}

_abilityElectricImune = {
  "lightningrod",
  "motordrive",
  "voltabsorb"
}

class Stat(Enum):
  HP = "hp"
  ATTACK = "atk"
  DEFENSE = "def"
  SPECIAL_ATTACK = "spa"
  SPECIAL_DEFENSE = "spd"
  SPEED = "spe"

# =============================================================================
# if Move its multiple targets
# =============================================================================
def pbTargetsMultiple(move : Move, user : Pokemon, battle: DoubleBattle):
  target_data = move.target
  if not target_data in _multiTargets:
    return False
  match target_data:
    case "allAdjacent":
      return len(battle.all_active_pokemons) > 2
    case "all":
      return len(battle.all_active_pokemons) > 2
    case "allAdjacentFoes":
      return len(battle.opponent_active_pokemon) > 1
  return False




  #=============================================================================
  # Move's type effectiveness
  #=============================================================================
  def pbCalcTypeModSingle(moveType : PokemonType, defType : PokemonType, user : Pokemon, target : Pokemon):
    return moveType.damage_multiplier(defType)


  def pbCalcTypeMod(moveType : PokemonType, user : Pokemon, target : Pokemon):
    return target.damage_multiplier(moveType)


  # For switching. Determines the effectiveness of a potential switch-in against
  # an opposing battler.
  def pbCalcTypeModPokemon(user : Pokemon, target : Pokemon):
    mod1 = target.damage_multiplier(user.types_1)
    mod2 = 1
    type2 = user.type_2
    if (type2):
      mod2 = target.damage_multiplier(type2)
    return mod1*mod2


  #=============================================================================
  # Immunity to a move because of the target's ability, item or other effects
  #=============================================================================
  def pbCheckMoveImmunity(score, move : Move, user : Pokemon, target : Pokemon, skill):
    type = move.type
    typeMod = pbCalcTypeMod(type, user, target)
    if (move.base_power>0 and typeMod==0) or score <=0:
      return True
    match type:
      case type.GROUND:
        if target.ability and target.ability.lower() == "levitate":
          return True
      case type.FIRE:
        if target.ability and target.ability.lower() == "flashfire":
          return True
      case type.WATER:
        if target.ability and  target.ability.lower() in _abilityWaterImune:
          return True
      case type.GRASS:
        if target.ability and target.ability.lower() == "sapsipper":
          return True
      case type.ELECTRIC:
        if target.ability and  target.ability.lower() in _abilityElectricImune:
          return True

    if move.base_power>0 and typeMod <=1 and target.ability == "wonderguard":
      return True

    if move.id.lower() == Move.retrieve_id("spore"):
      if PokemonType.GRASS in target.types:
        return  True
      if target.ability and target.ability.lower() == "overcoat":
        return True
      if target.item and target.item.lower() == "safety goggles":
        return True

    if move.category.value == MoveCategory.STATUS and move.status and Effect.SUBSTITUTE in target.effects.values():
      return True

    if move.category.value == MoveCategory.STATUS and user.ability.lower() == "prankster" and PokemonType.DARK in target.types:
      return True

    if move.priority and Effect.PSYCHIC_TERRAIN in target.effects.values():
      return True
    if move.category.value == MoveCategory.STATUS and move.status and Effect.MISTY_TERRAIN in target.effects.values():
      return True
    if move.category.value == MoveCategory.STATUS and move.status.value == Status.SLP and Effect.ELECTRIC_TERRAIN in target.effects.values():
      return True
    return False

  #=============================================================================
  # Get approximate properties for a battler
  #=============================================================================
  def pbRoughType(move : Move, user, skill):
    ret = move.type
    return ret


  def speedCalc(battler : Pokemon):
    stageMul = [2, 2, 2, 2, 2, 2, 2, 3, 4, 5, 6, 7, 8]
    stageDiv = [8, 7, 6, 5, 4, 3, 2, 2, 2, 2, 2, 2, 2]
    stage = battler.boosts["spe"] + 6

    speed = battler.stats["spe"]
    multiplier = 1
    if speed is None:
      speed = battler.base_stats["spe"]

    if battler.status.value==Status.PAR:
      multiplier = 0.5
      if battler.ability and battler.ability.lower() == "quickfeet":
        multiplier = 1


    if battler.item and battler.item.lower() == "choice scarf":
      multiplier *= 1.5

    return speed * multiplier * stageMul[stage] / stageDiv[stage]


  def pbRoughStat(battler : Pokemon, stat : Stat, skill):
    if stat == Stat.SPEED:
      return speedCalc(battler)

    stageMul = [2, 2, 2, 2, 2, 2, 2, 3, 4, 5, 6, 7, 8]
    stageDiv = [8, 7, 6, 5, 4, 3, 2, 2, 2, 2, 2, 2, 2]
    stage = battler.boosts[stat.value] + 6
    value = battler.stats[stat.value]
    if value is None:
      value = battler.base_stats[stat.value]
    return (value * stageMul[stage] / stageDiv[stage]).floor


  #=============================================================================
  # Get a better move's base damage value
  #=============================================================================
  def pbMoveBaseDamage(move : Move, user : Pokemon, target : Pokemon, skill):
    baseDmg = move.base_power
    if move.target == "scripted":
      baseDmg = 60
    if move.id == Move.retrieve_id("acrobatics"):
      if (user.item is None):
        baseDmg *= 2
    if move.id == Move.retrieve_id("gyro ball"):
      targetSpeed = pbRoughStat(target, Stat.SPEED, skill)
      userSpeed = pbRoughStat(user, Stat.SPEED, skill)
      baseDmg = [[(25 * targetSpeed / userSpeed).floor, 150].min, 1].max

  # multihit move
    min_hits, max_hits = move.n_hit
    if user.ability.lower()=="skill link":
        baseDmg *=max_hits
    else:
      baseDmg *= move.expected_hits

    return baseDmg

  #=============================================================================
  # Damage calculation
  #=============================================================================


  def pbRoughDamage(move: Move, user: Pokemon, target: Pokemon, skill, baseDmg, battle:DoubleBattle):
    skill = 100
    # Fixed damage moves

    # Get the move's type
    type = move.type
    typeAdvantage = type.damage_multiplier(target.types)
    if typeAdvantage == 0:
      return 0

    ##### Calculate user's attack stat ####
    atk = pbRoughStat(user, Stat.ATTACK, skill)
    if move.id == Move.retrieve_id("foul play"):   # Foul Play
      atk = pbRoughStat(target, Stat.ATTACK, skill)
    elif move.id == Move.retrieve_id("body press"):   # Body Press
      atk = pbRoughStat(user, Stat.DEFENSE, skill)
    #if special move:
    elif move.category == MoveCategory.SPECIAL:
        atk = pbRoughStat(user, Stat.SPECIAL_ATTACK, skill)


    ##### Calculate target's defense stat #####
    defense = pbRoughStat(target, Stat.DEFENSE, skill)
    if move.category == MoveCategory.SPECIAL and not move.id == Move.retrieve_id("psyshock"):
      defense = pbRoughStat(target, Stat.SPECIAL_DEFENSE, skill)

    ##### Calculate all multiplier effects #####
    multipliers = {
      "base_damage_multiplier" : typeAdvantage,
      "attack_multiplier" : 1.0,
      "defense_multiplier"  :  1.0,
      "final_damage_multiplier" : 1.0
    }
    # Ability effects that alter damage
    moldBreaker = False
    if user.ability.lower() == "mold breaker":
      moldBreaker = True


  #TODO set multiplier given by guts or items
    # Item effects that alter damage
    if user.item.lower() == "life orb":
      multipliers["attack_multiplier"] *=1.3
    elif user.item.lower()=="expert belt" and typeAdvantage >=2:
      multipliers["base_damage_multiplier"] *= 1.2

    if move.category==MoveCategory.SPECIAL:
      if user.item.lower() == "choice specs":
        multipliers["attack_multiplier"] *= 1.5
      if target.item.lower() == "assault vest":
        multipliers["defense_multiplier"] *= 1.5

    elif move.category==MoveCategory.PHYSICAL:
      if user.item.lower() == "choice band":
        multipliers["attack_multiplier"] *= 1.5
      if user.status is not None:
        if user.ability.lower() == "guts":
          multipliers["attack_multiplier"] *= 1.5
        if move.id == move.retrieve_id("facade"):
          multipliers["base_damage_multiplier"] *=2




    # Me First
    # TODO
    # Helping Hand - n/a

    # Terrain moves
    match user.effects.values():
      case Effect.ELECTRIC_TERRAIN:
        if type==type.ELECTRIC:
          multipliers["base_damage_multiplier"] *= 1.5
      case Effect.PSYCHIC_TERRAIN:
        if type==type.PSYCHIC : multipliers["base_damage_multiplier"] *= 1.5
      case Effect.MISTY_TERRAIN:
        if type==type.DRAGON : multipliers["base_damage_multiplier"] /= 2


    # Multi-targeting attacks
    if pbTargetsMultiple(move, user):
      multipliers["final_damage_multiplier"] *= 0.75

    # Weather
    match battle.weather.values():
      case Weather.SUNNYDAY:
        if type == type.FIRE:
          multipliers["final_damage_multiplier"] *= 1.5
        elif type == type.WATER:
          multipliers["final_damage_multiplier"] /= 2
      case Weather.RAINDANCE:
        if type == type.FIRE:
          multipliers["final_damage_multiplier"] /= 2
        elif type == type.WATER:
          multipliers["final_damage_multiplier"] *= 1.5
      case Weather.SANDSTORM:
        if PokemonType.ROCK in target.types and move.category==MoveCategory.SPECIAL and not move.id == Move.retrieve_id("psyshock"):
          multipliers["defense_multiplier"] *= 1.5

    # Critical hits - n/a
    # Random variance - n/a
    # STAB
    if type in user.types:
      if user.ability.upper()=="ADAPTABILITY":
        multipliers["final_damage_multiplier"] *= 2
      else:
        multipliers["final_damage_multiplier"] *= 1.5

    # Type effectiveness
    typemod = pbCalcTypeMod(type, user, target)
    multipliers["final_damage_multiplier"] *= typemod

    # Burn, Facade
    if move.category==MoveCategory.PHYSICAL and user.status == Status.BRN and not user.ability.lower()=="guts" and not move.id == move.retrieve_id("facade"):
      multipliers["final_damage_multiplier"] /= 2

    # Aurora Veil, Reflect, Light Screen
    if not move.id==move.retrieve_id("brick break") and not move.id==move.retrieve_id("psychic fangs") and not user.ability.upper()=="INFILTRATOR":
      if SideCondition.AURORA_VEIL in battle.opponent_side_conditions.values():
        multipliers["final_damage_multiplier"] *= 2 / 3.0 #in double battles screens reduce damage by nearly 2/3
        #if len(battle.opponent_active_pokemon) > 1:
        #  multipliers["final_damage_multiplier"] *= 2 / 3.0
        #else:
        #  multipliers["final_damage_multiplier"] /= 2

      elif SideCondition.REFLECT in battle.opponent_side_conditions.values() and move.category==MoveCategory.PHYSICAL:
        multipliers["final_damage_multiplier"] *= 2 / 3.0  # in double battles screens reduce damage by nearly 2/3
        # if len(battle.opponent_active_pokemon) > 1:
        #  multipliers["final_damage_multiplier"] *= 2 / 3.0
        # else:
        #  multipliers["final_damage_multiplier"] /= 2

      elif SideCondition.LIGHT_SCREEN in battle.opponent_side_conditions.values() and move.category==MoveCategory.SPECIAL:
        multipliers["final_damage_multiplier"] *= 2 / 3.0  # in double battles screens reduce damage by nearly 2/3
        # if len(battle.opponent_active_pokemon) > 1:
        #  multipliers["final_damage_multiplier"] *= 2 / 3.0
        # else:
        #  multipliers["final_damage_multiplier"] /= 2


    # Move-specific base damage modifiers
    # TODO
    # Move-specific final damage modifiers
    # TODO
    ##### Main damage calculation #####
    baseDmg = [(baseDmg * multipliers["base_damage_multiplier"]).round, 1].max
    atk     = [(atk     * multipliers["attack_multiplier"]).round, 1].max
    defense = [(defense * multipliers["defense_multiplier"]).round, 1].max
    damage  = ((((2.0 * user.level / 5) + 2).floor * baseDmg * atk / defense).floor / 50).floor + 2
    damage  = [(damage * multipliers["final_damage_multiplier"]).round, 1].max
    # "AI-specific calculations below"
    # Increased critical hit rates

    return damage.floor
#### fine roughDamageCalc #############################################

  #=============================================================================
  # Accuracy calculation
  #=============================================================================
  def pbRoughAccuracy(move: Move, user: Pokemon, target: Pokemon, skill = 100):
    # "Always hit" effects and "always hit" accuracy
    # if at least medium skilll:
    if target.effects[Effect.MINIMIZE] and move.tramplesMinimize: return 125
    if target.effects[Effect.TELEKINESIS] > 0: return 125

    baseAcc = move.accuracy()

    #if at least medium skill
    if baseAcc == 0 : return 125
    # Get the move's type
    type = pbRoughType(move, user, skill) #returns a PokemonType object


    # Calculate all modifier effects
    modifiers = {}
    modifiers["base_accuracy"]  = baseAcc
    modifiers["accuracy_stage"] = user.boosts["accuracy"]
    modifiers["evasion_stage"]  = target.boosts["evasion"]
    modifiers["accuracy_multiplier"] = 1.0
    modifiers["evasion_multiplier"]  = 1.0
    pbCalcAccuracyModifiers(user, target, modifiers, move, type, skill)
    # Check if move can't miss
    if modifiers["base_accuracy"] == 0: return 125
    # Calculation
    accStage = [[modifiers["accuracy_stage"], -6].max, 6].min + 6
    evaStage = [[modifiers["evasion_stage"], -6].max, 6].min + 6
    stageMul = [3, 3, 3, 3, 3, 3, 3, 4, 5, 6, 7, 8, 9]
    stageDiv = [9, 8, 7, 6, 5, 4, 3, 3, 3, 3, 3, 3, 3]
    accuracy = 100.0 * stageMul[accStage] / stageDiv[accStage]
    evasion  = 100.0 * stageMul[evaStage] / stageDiv[evaStage]
    accuracy = (accuracy * modifiers["accuracy_multiplier"]).round
    evasion  = (evasion  * modifiers["evasion_multiplier"]).round
    if evasion < 1: evasion = 1
    return modifiers["base_accuracy"] * accuracy / evasion


  def pbCalcAccuracyModifiers(user: Pokemon, target: Pokemon, modifiers, move: Move, type : PokemonType, skill = 100):
    #moldBreaker = False
    #if user.ability.lower() == "moldbreaker":
    #  moldBreaker = True

    modifiers["base_accuracy"] = move.accuracy

    # if weather=hail,blizzard always hits
    if Weather.HAIL in DoubleBattle.weather and move.id.lower() == "blizzard":
      modifiers["accuracy_multiplier"] = 1

    # if weather=raining, hurricane always hits
    if Weather.RAINDANCE in DoubleBattle.weather and move.id.lower() == "hurricane":
      modifiers["accuracy_multiplier"] = 1

