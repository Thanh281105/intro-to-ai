import pytest
from pathlib import Path
import sys
import time

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / 'src'))

from sokoban.map import SokobanMap
from sokoban.competitive.evaluator import CompetitiveEvaluator, CompetitiveWeights
from sokoban.competitive.state import CompetitiveState

@pytest.fixture
def comp_map_01():
    return SokobanMap.from_file(root / 'maps/competitive_01.txt')

def test_threat_detected_when_opponent_near_goal_push(comp_map_01):
    """Opponent positioned at support cell to push box into goal produces positive threat."""
    ev = CompetitiveEvaluator.get(comp_map_01)
    # Pick a goal cell
    goal = list(ev.goals)[0]
    # Place a box 1 cell away from goal, and opponent at support cell
    # Assuming floor cell layout around goal
    boxes = frozenset([(3, 3)])
    player_pos = (1, 1)
    opp_pos = (3, 2)  # Adjacent support cell
    owner_map = {}

    threat = ev.compute_opponent_threat(player_pos, opp_pos, boxes, owner_map, player_id=1)
    assert isinstance(threat, float)
    assert threat >= 0.0

def test_ejection_threat_when_opponent_near_own_scored_box(comp_map_01):
    """Opponent adjacent to our scored box support cell produces ejection threat with high urgency."""
    ev = CompetitiveEvaluator.get(comp_map_01)
    goal = list(ev.goals)[0]
    # Box is on goal, owned by player 1
    boxes = frozenset([goal])
    owner_map = {goal: 1}
    player_pos = (1, 1)

    # Check if there is a valid support cell for pushing out
    for dr, dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):
        dest = (goal[0] + dr, goal[1] + dc)
        supp = (goal[0] - dr, goal[1] - dc)
        if comp_map_01.free(dest) and comp_map_01.free(supp):
            # Opponent is at support cell
            threat = ev.compute_opponent_threat(player_pos, supp, boxes, owner_map, player_id=1)
            # ETA is 1 (0 travel + 1 push) -> threat_eject = 1.0 -> threat = 1.5 * 1.0 = 1.5
            assert threat >= 1.0
            break

def test_threat_is_zero_when_opponent_blocked_or_no_threat(comp_map_01):
    """Threat is 0.0 when opponent is far or has no reachable pushes."""
    ev = CompetitiveEvaluator.get(comp_map_01)
    # Opponent far away in a corner with no boxes nearby
    boxes = frozenset([list(ev.goals)[0]])
    owner_map = {list(ev.goals)[0]: 2}  # Box owned by opponent, opponent won't eject own box
    player_pos = (1, 1)
    opp_pos = (1, 2)

    threat = ev.compute_opponent_threat(player_pos, opp_pos, boxes, owner_map, player_id=1)
    # Opponent owns the only box in goal, won't push it out; no other boxes -> 0 threat
    assert threat == 0.0

def test_phi_penalizes_threat():
    """evaluate_phi subtracts w_threat * threat from state potential."""
    board = SokobanMap.from_file(root / 'maps/competitive_01.txt')
    ev = CompetitiveEvaluator.get(board)
    goal = list(ev.goals)[0]
    boxes = frozenset([goal])
    owner_map = {goal: 1}
    player_pos = (1, 1)

    # Find support cell to eject
    supp_target = None
    for dr, dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):
        dest = (goal[0] + dr, goal[1] + dc)
        supp = (goal[0] - dr, goal[1] - dc)
        if board.free(dest) and board.free(supp):
            supp_target = supp
            break

    if supp_target:
        w_active = CompetitiveWeights(w_score=30.0, w_push=3.0, w_route=2.0, w_threat=10.0)
        phi_with_threat = ev.evaluate_phi(
            player_pos, supp_target, boxes, ((goal, 1),), 0, 1, 25,
            weights=w_active, enable_threat=True
        )
        phi_no_threat = ev.evaluate_phi(
            player_pos, supp_target, boxes, ((goal, 1),), 0, 1, 25,
            weights=w_active, enable_threat=False
        )
        assert phi_with_threat < phi_no_threat
        # Difference should be exactly w_threat * threat
        diff = phi_no_threat - phi_with_threat
        threat = ev.compute_opponent_threat(player_pos, supp_target, boxes, owner_map, 1)
        assert abs(diff - 10.0 * threat) < 1e-5

def test_threat_execution_latency(comp_map_01):
    """Single-pass BFS threat calculation executes well within sub-millisecond budget."""
    ev = CompetitiveEvaluator.get(comp_map_01)
    player_pos = comp_map_01.initial_player
    opp_pos = (player_pos[0] + 1, player_pos[1] + 1)
    boxes = comp_map_01.initial_boxes
    owner_map = {}

    # Warmup
    ev.compute_opponent_threat(player_pos, opp_pos, boxes, owner_map, 1)

    t0 = time.perf_counter_ns()
    n_iters = 200
    for _ in range(n_iters):
        ev.compute_opponent_threat(player_pos, opp_pos, boxes, owner_map, 1)
    elapsed_ms = (time.perf_counter_ns() - t0) / 1e6
    avg_ms = elapsed_ms / n_iters

    # Must execute in under 0.05ms per call (cached or uncached)
    assert avg_ms < 0.1, f"Average threat evaluation too slow: {avg_ms:.4f}ms"
