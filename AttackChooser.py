import MoveUtilities

from poke_env.environment import Move, Pokemon, DoubleBattle, Effect, Status, Weather, SideCondition
from poke_env.environment.move_category import MoveCategory
from poke_env.environment.pokemon_type import PokemonType

import SwitchHelper


class ScoreOrder:
    move: Move
    score: int
    target: int

    def __init__(self, move, score, target):
        self.move = move
        self.score = score
        self.target = target


def pbChooseMoves(battle: DoubleBattle, idxBattler):
    user = battle.active_pokemon[idxBattler]

    # Get scores and targets for each move
    # NOTE: A move is only added to the choices array if it has a non-zero
    #       score.
    choices     = []
    user.eachMoveWithIndex do |_m, i|
      if not @battle.pbCanChooseMove(idxBattler, i, False):
        continue
      pbRegisterMoveTrainer(user, i, choices, skill)
      end
    end
    # Figure out useful information about the choices
    totalScore = 0
    maxScore   = 0
    choices.each do |c|
      totalScore += c[1]
      maxScore = c[1] if maxScore < c[1]
    end
    # Log the available choices
    if $INTERNAL
      logMsg = "[AI] Move choices for #{user.pbThis(True)} (#{user.index}): "
      choices.each_with_index do |c, i|
        logMsg += "#{user.moves[c[0]].name}=#{c[1]}"
        logMsg += " (target #{c[2]})" if c[2] >= 0
        logMsg += ", " if i < choices.length - 1
      end
      PBDebug.log(logMsg)
    end
    # Find any preferred moves and just choose from them
    if !wildBattler && skill >= PBTrainerAI.highSkill && maxScore > 100
      stDev = pbStdDev(choices)
      if stDev >= 40 && pbAIRandom(100) < 90
        preferredMoves = []
        choices.each do |c|
          next if c[1] < 200 && c[1] < maxScore * 0.8
          preferredMoves.push(c)
          preferredMoves.push(c) if c[1] == maxScore   # Doubly prefer the best move
        end
        if preferredMoves.length > 0
          m = preferredMoves[pbAIRandom(preferredMoves.length)]
          PBDebug.log("[AI] #{user.pbThis} (#{user.index}) prefers #{user.moves[m[0]].name}")
          @battle.pbRegisterMove(idxBattler, m[0], False)
          @battle.pbRegisterTarget(idxBattler, m[2]) if m[2] >= 0
          return
        end
      end
    end
    # Decide whether all choices are bad, and if so, try switching instead
    if !wildBattler && skill >= PBTrainerAI.highSkill
      badMoves = False
      if ((maxScore <= 20 && user.turnCount > 2) ||
         (maxScore <= 40 && user.turnCount > 5)) && pbAIRandom(100) < 80
        badMoves = True
      end
      if !badMoves && totalScore < 100 && user.turnCount > 1
        badMoves = True
        choices.each do |c|
          next if !user.moves[c[0]].damagingMove?
          badMoves = False
          break
        end
        badMoves = False if badMoves && pbAIRandom(100) < 10
      end
      if badMoves && pbEnemyShouldWithdrawEx?(idxBattler, True)
        if $INTERNAL
          PBDebug.log("[AI] #{user.pbThis} (#{user.index}) will switch due to terrible moves")
        end
        return
      end
    end
    # If there are no calculated choices, pick one at random
    if choices.length == 0
      PBDebug.log("[AI] #{user.pbThis} (#{user.index}) doesn't want to use any moves; picking one at random")
      user.eachMoveWithIndex do |_m, i|
        next if !@battle.pbCanChooseMove?(idxBattler, i, False)
        choices.push([i, 100, -1])   # Move index, score, target
      end
      if choices.length == 0   # No moves are physically possible to use; use Struggle
        @battle.pbAutoChooseMove(user.index)
      end
    end
    # Randomly choose a move from the choices and register it
    randNum = pbAIRandom(totalScore)
    choices.each do |c|
      randNum -= c[1]
      next if randNum >= 0
      @battle.pbRegisterMove(idxBattler, c[0], False)
      @battle.pbRegisterTarget(idxBattler, c[2]) if c[2] >= 0
      break
    end
    # Log the result
    if @battle.choices[idxBattler][2]
      PBDebug.log("[AI] #{user.pbThis} (#{user.index}) will use #{@battle.choices[idxBattler][2].name}")
    end
  end

    # =============================================================================
    # Get scores for the given move against each possible target
    # =============================================================================
    # Trainer Pokémon calculate how much they want to use each of their moves.


def pbRegisterMoveTrainer(battle: DoubleBattle, user: Pokemon, move: Move, idxMove, choices):
    target_data = battle.get_possible_showdown_targets(move, user)
    if len(target_data) == 1:
        # If move has no targets, affects the user, a side or the whole field, or
        # specially affects multiple Pokémon and the AI calculates an overall
        # score at once instead of per target
        score = pbGetMoveScoreArea(battle, move, user)

        if score > 0:
            value = ScoreOrder(move, score, target=target_data[0])
            choices.append(value)
            # choices.push([idxMove, score, -1])
    else:
        # If move affects one battler and you have to choose which one
        scoresAndTargets = []
        for idx, oppo in enumerate(battle.opponent_active_pokemon):
            score = pbGetMoveScore(move, user, oppo)
            if score > 0:
                value = ScoreOrder(move, score, target=target_data[idx + 1])
                scoresAndTargets.append(value)
                # scoresAndTargets.push([score, idx+1])
        if scoresAndTargets.length > 0:
            # Get the one best target for the move
            scoresAndTargets.sort(key=lambda scoreOrder: scoreOrder.score, reverse=True)
            # scoresAndTargets.sort! { | a, b | b[0] <= > a[0]}
            choices.append(scoresAndTargets.index(0))
            # choices.push([idxMove, scoresAndTargets[0][0], scoresAndTargets[0][1]])

    # =============================================================================
    # Get a score for the given move being used against the given target
    # =============================================================================


def pbGetMoveScore(battle: DoubleBattle, move: Move, user: Pokemon, target: Pokemon):
    score = 100

    # Prefer damaging moves if AI has no more Pokémon
    if len(battle.available_switches[0]) == 0:
        if move.category.value == MoveCategory.STATUS:
            score /= 1.5
        elif target.current_hp_fraction <= 0.5:
            score *= 1.5

    base_dmg = MoveUtilities.move_base_damage(move, battler, target)
    # Pick a good move for the Choice items
    if (battler.item and battler.item.lower().startswith("choice")) or (
            battler.ability and battler.ability.lower() == "gorilla tactics"):

        if base_dmg >= 60:
            score += 60
        elif base_dmg > 0:
            score += 30
        elif move.id.lower() == Move.retrieve_id("trick"):
            score += 70  # Trick
        else:
            score -= 60

    # Don't prefer moves that are ineffective because of abilities or effects
    if MoveUtilities.is_move_immune(score, move, user, target):
        return 0
    # Adjust score based on how much damage it can deal
    if base_dmg > 0:
        score = pbGetMoveScoreDamage(score, move, user, target)
    else:  # Status moves
        # Don't prefer attacks which don't deal damage
        score -= 10
        score = evalStatusMove(move, user, target, score)
        # Account for accuracy of move
        accuracy = pbRoughAccuracy(move, user, target, skill)
        score *= accuracy / 100.0
        if score <= 10:  # and skill >= PBTrainerAI.highSkill:
            score = 0

    score = score.to_i
    if score < 0:
        score = 0
    return score


def pbGetMoveScoreArea(battle: DoubleBattle, move: Move, user: Pokemon):
    total_score = 200

    # Prefer damaging moves if AI has no more Pokémon
    if len(battle.available_switches[0]) == 0:
        if move.category.value == MoveCategory.STATUS:
            total_score /= 1.5
        elif target.current_hp_fraction <= 0.5:
            total_score *= 1.5
    if move.category.value == MoveCategory.STATUS:  # self buff
        return total_score

    for target in battle.opponent_active_pokemon:
        score = 0
        # Don't prefer moves that are ineffective because of abilities or effects
        if MoveUtilities.is_move_immune(score, move, user, target):
            continue
        # Adjust score based on how much damage it can deal
        if base_dmg > 0:
            score = pbGetMoveScoreDamage(score, move, user, target)
        else:  # Status moves
            # Don't prefer attacks which don't deal damage
            score -= 10
            score = evalStatusMove(move, user, target)
            # Account for accuracy of move
            accuracy = pbRoughAccuracy(move, user, target, skill)
            score *= accuracy / 100.0
            if score <= 10:  # and skill >= PBTrainerAI.highSkill:
                score = 0
            total_score += score

    total_score = total_score / 2
    if total_score < 0:
        total_score = 0

    return total_score


def evalStatusMove(move, user, target, score):
    if move.status == Status.BRN and target.base_stats[MoveUtilities.Stat.ATTACK] > 100:
        score *= 2
    if move.status == Status.PAR and target.base_stats[MoveUtilities.Stat.SPEED] > 70:
        score += 50
        if target.base_stats[MoveUtilities.Stat.SPEED] > 100:
            score += 20
    return score
    # =============================================================================
    # Add to a move's score based on how much damage it will deal (as a percentage
    # of the target's current HP)
    # =============================================================================


def pbGetMoveScoreDamage(score, move, user, target, skill):
    if score <= 0:
        return 0
    # Calculate how much damage the move will do (roughly)
    baseDmg = pbMoveBaseDamage(move, user, target, skill)
    realDamage = pbRoughDamage(move, user, target, skill, baseDmg)
    # Account for accuracy of move
    accuracy = pbRoughAccuracy(move, user, target, skill)
    realDamage *= accuracy / 100.0

    # Prefer flinching external effects (note that move effects which cause
    # flinching are dealt with in the function code part of score calculation)
    # skill >= PBTrainerAI.mediumSkill and
    if not move.flinchingMove and \
            not target.ability.upper() == "INNERFOCUS" and \
            not target.ability.upper() == "SHIELDDUST" and \
            target.effects[Effects.SUBSTITUTE] == 0:
        canFlinch = False

        if canFlinch:
            realDamage *= 1.3
    # Convert damage to percentage of target's remaining HP
    damagePercentage = realDamage * 100.0 / target.current_hp
    # Don't prefer weak attacks
    #    damagePercentage /= 2 if damagePercentage<20

    # Adjust score
    if damagePercentage > 120:  # Treat all lethal moves the same
        damagePercentage = 120
    if damagePercentage > 100:  # Prefer moves likely to be lethal
        damagePercentage += 40
    score += damagePercentage.to_i
    return score


def useProtect(battle: DoubleBattle, idxBattler):
    user = battle.active_pokemon[idxBattler]
    has_protect = False
    protect = None
    for move in battle.available_moves[idxBattler]:
        if move.id == Move.retrieve_id("protect") or move.id == Move.retrieve_id("detect"):
            has_protect = True
            protect = move
            break
    if not has_protect or user.protect_counter > 0:
        return None # can't protect for sure
    do_protect = False
    damagers = 0
    for oppo in battle.opponent_active_pokemon:
        if MoveUtilities.can_damage(oppo, user):
            damagers+=1
##60% se 1 damagers 100% se due damagers, 0 else
