"""
gives a score to each move (switch or move+target)
"""

from poke_env.environment import DoubleBattle
from poke_env.player import BattleOrder

from AttackChooser import use_prio, use_protect, choose_moves
from SwitchHelper import should_withdraw


def default_choose_command(battle: DoubleBattle, idx_active, last_switch = None) -> BattleOrder:
    order: BattleOrder
    order = use_prio(battle, idx_active)

    if order is not None:
        # print("use prio")
        return order

    order = use_protect(battle, idx_active)

    if order is not None:
        # print("use protect")
        return order

    order = should_withdraw(battle, idx_active, last_switch)
    if order is not None:
        # print("use do switch")
        return order

    order = choose_moves(battle, idx_active)
    return order
