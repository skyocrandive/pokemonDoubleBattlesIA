import random

from poke_env.environment import Move, Pokemon, DoubleBattle, Status
from poke_env.environment.move_category import MoveCategory
from poke_env.player import BattleOrder

import MoveUtilities
import SwitchHelper


class ScoreOrder:
    move: Move
    score: int
    target: int

    def __init__(self, move, score, target):
        self.move = move
        self.score = score
        self.target = target


def choose_moves(battle: DoubleBattle, idxBattler) -> BattleOrder:

    user = battle.active_pokemon[idxBattler]

    # Get scores and targets for each move
    # NOTE: A move is only added to the choices array if it has a non-zero
    #       score.
    # lista di (move, score, target) aka list of ScoreOrder
    choices = []
    for i, move in enumerate(battle.available_moves[idxBattler]):
        register_move_trainer(battle, user, move, choices)

    # Figure out useful information about the choices
    totalScore = 0
    maxScore = 0
    for c in choices:
        score = c.score
        totalScore += score
        if maxScore < score:
            maxScore = score

    preferredMoves = []
    for c in choices:
        score = c.score
        if score < 200 and score < maxScore * 0.8:
            continue
        preferredMoves.append(c)
        if score == maxScore:  # Doubly prefer the best move
            preferredMoves.append(c)

    if len(preferredMoves) > 0:
        m = preferredMoves[random.randint(0, len(preferredMoves) - 1)]
        # m = preferredMoves[pbAIRandom(preferredMoves.length)]
        order = BattleOrder(m.move, move_target=m.target)
        # PBDebug.log("[AI] #{user.pbThis} (#{user.index}) prefers #{user.moves[m[0]].name}")
        # @battle.pbRegisterMove(idxBattler, m[0], False)
        # @battle.pbRegisterTarget(idxBattler, m[2]) if m[2] >= 0
        return order

    # Decide whether all choices are bad, and if so, try switching instead
    badMoves = False
    if maxScore <= 20:
        badMoves = True

    if not badMoves and totalScore < 100 and user.first_turn:
        badMoves = True
        for c in choices:
            if c.move.base_power > 0:
                badMoves = False
                break

    if badMoves:
        # switch due to terrible moves
        switch = SwitchHelper.choose_possible_best_switch(battle, idxBattler)
        if switch is not None:
            return BattleOrder(switch)

    # If there are no calculated choices, pick one at random
    moves = battle.available_moves[idxBattler]
    if len(choices) == 0:
        targets = {}
        for move in moves:
            targetList = battle.get_possible_showdown_targets(move, user)

            noSelfTarg = [x for x in targetList if x > 0]
            if len(noSelfTarg):  # if the move can target an opponent don't target ally
                targetList = noSelfTarg
            targets[move] = targetList

        choices.append(
            [
                ScoreOrder(move, 0, target)
                for move in moves
                for target in targets[move]
            ]
        )
        # choices.push([i, 100, -1])   # Move index, score, target

    # Randomly choose a move from the choices and register it
    random.shuffle(choices)
    res = choices[0]
    order = BattleOrder(res.move, move_target=res.target)

    return order

    # =============================================================================
    # Get scores for the given move against each possible target
    # =============================================================================
    # Trainer Pokémon calculate how much they want to use each of their moves.


def register_move_trainer(battle: DoubleBattle, user: Pokemon, move: Move, output):
    target_data = battle.get_possible_showdown_targets(move, user)
    if len(target_data) == 1:
        # If move has no targets, affects the user, a side or the whole field, or
        # specially affects multiple Pokémon and the AI calculates an overall
        # score at once instead of per target
        score = get_move_score_area(battle, move, user)

        if score > 0:
            value = ScoreOrder(move, score, target=target_data[0])
            output.append(value)
            # choices.push([idxMove, score, -1])
    else:
        # If move affects one battler && you have to choose which one
        scoresAndTargets = []
        for idx, oppo in enumerate(battle.opponent_active_pokemon):
            score = get_move_score(battle, move, user, oppo)
            if score > 0:
                value = ScoreOrder(move, score, target=target_data[idx + 1])
                scoresAndTargets.append(value)
                # scoresAndTargets.push([score, idx+1])
        if len(scoresAndTargets) > 0:
            # Get the one best target for the move
            scoresAndTargets.sort(key=lambda scoreOrder: scoreOrder.score, reverse=True)
            # scoresAndTargets.sort! { | a, b | b[0] <= > a[0]}
            output.append(scoresAndTargets[0])
            # choices.push([idxMove, scoresAndTargets[0][0], scoresAndTargets[0][1]])

    # =============================================================================
    # Get a score for the given move being used against the given target
    # =============================================================================


def get_move_score(battle: DoubleBattle, move: Move, user: Pokemon, target: Pokemon) -> int:
    score = 100

    # Prefer damaging moves if AI has no more Pokémon
    if len(battle.available_switches[0]) == 0:
        if move.category.value == MoveCategory.STATUS:
            score /= 1.5
        elif target.current_hp_fraction <= 0.5:
            score *= 1.5

    base_dmg = MoveUtilities.move_base_damage(move, user, target)
    # Pick a good move for the Choice items
    if (user.item and user.item.lower().startswith("choice")) or (
            user.ability and user.ability.lower() == "gorilla tactics"):

        if base_dmg >= 60:
            score += 60
        elif base_dmg > 0:
            score += 30
        elif move.id.lower() == Move.retrieve_id("Trick"):
            score += 70  # Trick
        else:
            score -= 60

    # Don't prefer moves that are ineffective because of abilities or effects
    if MoveUtilities.is_move_immune(move, user, target):
        return 0
    # Adjust score based on how much damage it can deal
    if base_dmg > 0:
        score = get_move_score_damage(score, move, user, target, battle)
    else:  # Status moves
        # Don't prefer attacks which don't deal damage
        score -= 10
        score = eval_status_move(move, user, target, score)
        # Account for accuracy of move
        accuracy = MoveUtilities.rough_accuracy(move, user, target)
        score *= accuracy / 100.0
        if score <= 10:
            score = 0

    score = score
    if score < 0:
        score = 0
    return int(score)


def get_move_score_area(battle: DoubleBattle, move: Move, user: Pokemon) -> int:
    base_score = 100

    if move.id == Move.retrieve_id("Protect") or move.id == Move.retrieve_id("Detect"):
        base_score = 20

    # Prefer damaging moves if AI has no more Pokémon
    if len(battle.available_switches[0]) == 0:
        if move.category.value == MoveCategory.STATUS:
            base_score /= 1.5

    if move.category.value == MoveCategory.STATUS:  # self buff
        return int(base_score)

    total_score = 0
    for target in battle.opponent_active_pokemon:
        score = 0
        # Don't prefer moves that are ineffective because of abilities or effects
        if MoveUtilities.is_move_immune(move, user, target):
            continue
        # Adjust score based on how much damage it can deal
        if move.base_power > 0:
            score = get_move_score_damage(score, move, user, target, battle)
        else:  # Status moves
            # Don't prefer attacks which don't deal damage
            score -= 10
            score = eval_status_move(move, user, target, score)
            # Account for accuracy of move
            accuracy = MoveUtilities.rough_accuracy(move, user, target)
            score *= accuracy / 100.0
            if score <= 10:
                score = 0
            total_score += score

    total_score = total_score / 2
    if total_score < 0:
        total_score = 0

    return int(total_score + base_score)


def eval_status_move(move, user, target, score) -> int:
    if MoveUtilities.is_move_immune(move, user, target):
        return 0
    if move.status == Status.BRN and target.base_stats[MoveUtilities.Stat.ATTACK] > 100:
        score *= 2
    if move.status == Status.PAR and target.base_stats[MoveUtilities.Stat.SPEED] > 70:
        score += 50
        if target.base_stats[MoveUtilities.Stat.SPEED] > 100:
            score += 20
    return int(score)
    # =============================================================================
    # Add to a move's score based on how much damage it will deal (as a percentage
    # of the target's current HP)
    # =============================================================================


def get_move_score_damage(score, move: Move, user, target, battle) -> int:
    if score <= 0:
        return 0
    # Calculate how much damage the move will do (roughly)
    baseDmg = MoveUtilities.move_base_damage(move, user, target)
    realDamage = MoveUtilities.rough_damage(move, user, target, baseDmg, battle)
    # Account for accuracy of move
    accuracy = MoveUtilities.rough_accuracy(move, user, target)
    realDamage *= accuracy / 100.0

    # Convert damage to percentage of target's remaining HP
    damagePercentage = realDamage * 100.0 / target.current_hp
    # Don't prefer weak attacks
    #    damagePercentage /= 2 if damagePercentage<20

    # Adjust score
    if damagePercentage > 120:  # Treat all lethal moves the same
        damagePercentage = 120
    if damagePercentage > 100:  # Prefer moves likely to be lethal
        damagePercentage += 40
    score += damagePercentage
    return int(score)


def use_protect(battle: DoubleBattle, idxBattler) -> BattleOrder | None:
    user = battle.active_pokemon[idxBattler]
    has_protect = False
    protect = None
    for move in battle.available_moves[idxBattler]:
        if move.id == Move.retrieve_id("Protect") or move.id == Move.retrieve_id("Detect"):
            print("has protect")
            has_protect = True
            protect = move
            break
    if not has_protect or user.protect_counter > 0:
        return None  # can't protect for sure
    damagers = 0
    for oppo in battle.opponent_active_pokemon:
        if MoveUtilities.can_damage(oppo, user):
            damagers += 1
    base_probability = damagers * 30
    if len(battle.available_switches) == 0:
        base_probability -= 20
    if random.randint(0, 100) < base_probability:
        return BattleOrder(protect, move_target=battle.get_possible_showdown_targets(protect, user)[0])


"""
def usePrio(battle: DoubleBattle, idxBattler) -> BattleOrder | None:
    user = battle.active_pokemon[idxBattler]
    prio_moves = []
    for move in battle.available_moves[idxBattler]:
        if move.priority > 0:
            if move.id == move.retrieve_id("fake out") and user.first_turn:
                prio_moves.append(move)
            elif move.base_power > 0:
                prio_moves.append(move)
    if len(prio_moves) == 0:
        return None
    for move in prio_moves:
        targets = battle.get_possible_showdown_targets(move, user)
        noSelfTarg = [x for x in targets if x > 0]
        for target in noSelfTarg:
            if MoveUtilities.move_can_ko(move, user, target):
                return BattleOrder(move, move_target=target)
    return None
"""


def use_prio(battle: DoubleBattle, idxBattler) -> BattleOrder | None:
    user = battle.active_pokemon[idxBattler]
    for move in battle.available_moves[idxBattler]:
        if move.priority > 0:
            if move.base_power == 0 or (move.id == move.retrieve_id("Fake Out") and move.max_pp > move.current_pp): #Pokemon.first_turn doesn't work
                continue
            targets = battle.get_possible_showdown_targets(move, user)
            noSelfTarg = [x for x in targets if x > 0]
            for idxtarget in noSelfTarg:
                target = battle.opponent_active_pokemon[idxtarget-1]
                if MoveUtilities.move_can_ko(move, user, target, battle):
                    return BattleOrder(move, move_target=idxtarget)
    return None
