import pytest
from pathlib import Path
import sys
import time

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / 'src'))

from sokoban.map import SokobanMap
from sokoban.competitive.evaluator import CompetitiveEvaluator, CompetitiveWeights

@pytest.fixture
def comp_map_01():
    return SokobanMap.from_file(root / 'maps/competitive_01.txt')

def test_defense_zero_when_no_scored_boxes(comp_map_01):
    ev = CompetitiveEvaluator.get(comp_map_01)
    boxes = comp_map_01.initial_boxes
    owner_map = {}
    player_pos = (1, 1)
    opp_pos = (2, 2)
    def_score = ev.compute_defense(player_pos, opp_pos, boxes, owner_map, player_id=1)
    assert def_score == 0.0

def test_defense_rewards_player_blocking_ejection(comp_map_01):
    ev = CompetitiveEvaluator.get(comp_map_01)
    goal = list(ev.goals)[0]
    boxes = frozenset([goal])
    owner_map = {goal: 1}  # Player 1 scored this goal

    # Find support cell for ejection
    supp_eject = None
    for dr, dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):
        dest = (goal[0] + dr, goal[1] + dc)
        supp = (goal[0] - dr, goal[1] - dc)
        if comp_map_01.free(dest) and comp_map_01.free(supp):
            supp_eject = supp
            break

    if supp_eject:
        # Opponent nearby
        opp_pos = (supp_eject[0] + 1, supp_eject[1]) if comp_map_01.free((supp_eject[0] + 1, supp_eject[1])) else supp_eject
        # If player blocks supp_eject vs player far away
        def_blocked = ev.compute_defense(supp_eject, opp_pos, boxes, owner_map, player_id=1)
        def_unblocked = ev.compute_defense((0, 0), opp_pos, boxes, owner_map, player_id=1)
        assert def_blocked >= def_unblocked

def test_disruption_rewards_player_near_opp_scored_box(comp_map_01):
    ev = CompetitiveEvaluator.get(comp_map_01)
    goal = list(ev.goals)[0]
    boxes = frozenset([goal])
    owner_map = {goal: 2}  # Opponent scored this goal

    # Find support cell for ejection
    supp_eject = None
    for dr, dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):
        dest = (goal[0] + dr, goal[1] + dc)
        supp = (goal[0] - dr, goal[1] - dc)
        if comp_map_01.free(dest) and comp_map_01.free(supp):
            supp_eject = supp
            break

    if supp_eject:
        disrupt_close = ev.compute_disruption(supp_eject, (10, 10), boxes, owner_map, player_id=1)
        assert disrupt_close >= 1.0

def test_phi_integrates_defense_and_disruption(comp_map_01):
    ev = CompetitiveEvaluator.get(comp_map_01)
    goal = list(ev.goals)[0]
    boxes = frozenset([goal])
    w = CompetitiveWeights(w_defense=5.0, w_disrupt=5.0)

    # Find support cell for ejection
    supp_eject = None
    for dr, dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):
        dest = (goal[0] + dr, goal[1] + dc)
        supp = (goal[0] - dr, goal[1] - dc)
        if comp_map_01.free(dest) and comp_map_01.free(supp):
            supp_eject = supp
            break

    if supp_eject:
        # 1. Defense: When opponent is adjacent to ejection cell, active defense penalty applies
        opp_near = supp_eject
        phi_threatened = ev.evaluate_phi((0, 0), opp_near, boxes, ((goal, 1),), 0, 1, 25, weights=w, enable_defense=True)
        phi_unthreatened = ev.evaluate_phi((0, 0), opp_near, boxes, ((goal, 1),), 0, 1, 25, weights=w, enable_defense=False)
        assert phi_threatened < phi_unthreatened

        # 2. Disruption: When player is adjacent to opponent's scored box, disruption bonus applies
        phi_disrupt = ev.evaluate_phi(supp_eject, (10, 10), boxes, ((goal, 2),), 0, 1, 25, weights=w, enable_disrupt=True)
        phi_no_disrupt = ev.evaluate_phi(supp_eject, (10, 10), boxes, ((goal, 2),), 0, 1, 25, weights=w, enable_disrupt=False)
        assert phi_disrupt > phi_no_disrupt
