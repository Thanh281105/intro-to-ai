import pytest
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / 'src'))

from sokoban.map import SokobanMap
from sokoban.competitive.evaluator import CompetitiveEvaluator, CompetitiveWeights

@pytest.fixture
def comp_map_01():
    return SokobanMap.from_file(root / 'maps/competitive_01.txt')

def test_dynamic_horizon_leading_late_boosts_defense(comp_map_01):
    ev = CompetitiveEvaluator.get(comp_map_01)
    goal = list(ev.goals)[0]
    boxes = frozenset([goal])
    w = CompetitiveWeights(w_defense=10.0, w_disrupt=10.0)

    # Lead = +1 (we own goal)
    # At early game (step 1 / 25) vs late game (step 24 / 25)
    # Find support cell for ejection so vulnerability > 0
    supp_eject = None
    for dr, dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):
        dest = (goal[0] + dr, goal[1] + dc)
        supp = (goal[0] - dr, goal[1] - dc)
        if comp_map_01.free(dest) and comp_map_01.free(supp):
            supp_eject = supp
            break

    if supp_eject:
        # Opponent near ejection cell
        bd_early = ev.breakdown((0, 0), supp_eject, boxes, ((goal, 1),), step=1, player_id=1, step_limit=25, weights=w)
        bd_late = ev.breakdown((0, 0), supp_eject, boxes, ((goal, 1),), step=24, player_id=1, step_limit=25, weights=w)
        # Defense penalty is scaled more strictly late game
        assert bd_late['defense_contrib'] <= bd_early['defense_contrib']

def test_dynamic_horizon_losing_late_boosts_score_weight(comp_map_01):
    ev = CompetitiveEvaluator.get(comp_map_01)
    goal = list(ev.goals)[0]
    boxes = frozenset([goal])
    w = CompetitiveWeights(w_score=30.0)

    # Losing: opponent owns goal, our score = 0, opp = 1
    bd_early = ev.breakdown((1, 1), (10, 10), boxes, ((goal, 2),), step=1, player_id=1, step_limit=25, weights=w)
    bd_late = ev.breakdown((1, 1), (10, 10), boxes, ((goal, 2),), step=24, player_id=1, step_limit=25, weights=w)
    # The penalty for trailing becomes more severe late in the game
    assert bd_late['score_contrib'] < bd_early['score_contrib']


def test_breakdown_matches_evaluate_phi(comp_map_01):
    ev = CompetitiveEvaluator.get(comp_map_01)
    boxes = frozenset(comp_map_01.initial_boxes)
    pos1 = comp_map_01.initial_player
    pos2 = comp_map_01.initial_player2
    owners = tuple((b, 1) for b in boxes)
    weights = CompetitiveWeights()

    for step in [0, 5, 12, 24]:
        bd = ev.breakdown(pos1, pos2, boxes, owners, step=step, player_id=1, step_limit=25, weights=weights)
        phi = ev.evaluate_phi(pos1, pos2, boxes, owners, step=step, player_id=1, step_limit=25, weights=weights)
        expected_sum = (
            bd['score_contrib']
            + bd['push_contrib']
            + bd['route_contrib']
            + bd['threat_contrib']
            + bd['defense_contrib']
            + bd['disrupt_contrib']
            + bd['blocking_contrib']
        )
        assert abs(bd['phi'] - phi) < 1e-4
        assert abs(expected_sum - phi) < 0.1

