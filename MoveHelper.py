"""
gives a score to each move (switch or move+target)
"""

from poke_env.environment import Move, Pokemon, DoubleBattle
def default_choose_command(battle : DoubleBattle, idxActive):
    if should_withdraw(battle, idxActive):
        return
    pbChooseMoves(battle, idxActive)

