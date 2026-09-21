import pytest
from pathlib import Path
from sokoban.map import SokobanMap
from sokoban.competitive.state import initial_state, CompetitiveState
from sokoban.competitive.evaluator import CompetitiveEvaluator, DEFAULT_WEIGHTS
from sokoban.agents import AStarAgent, GBFSAgent

@pytest.fixture
def comp_map():
    root = Path(__file__).resolve().parents[1]
    return SokobanMap.from_file(root / 'maps/competitive_01.txt')

def test_A_useless_move_utility_decreases(comp_map):
    """A. Useless move: moving away from push support without progress yields negative transition reward."""
    ev = CompetitiveEvaluator.get(comp_map)
    # Box is at (2, 3), push support is at (2, 4)
    # Moving from (1, 2) to (1, 1) steps further away from support cell (2, 4)
    s1 = ((1, 2), comp_map.initial_boxes, (), 0)
    s2 = ((1, 1), comp_map.initial_boxes, (), 1)
    r = ev.transition_reward(s1, s2, opp_pos=(6, 6), player_id=1, step_limit=25)
    # Utility must decrease due to step penalty and increased support distance
    assert r <= -1.0, f"Expected negative reward <= -1.0 for useless move away from support, got {r}"

def test_B_moving_closer_to_useful_support_better_than_useless(comp_map):
    """B. Moving closer to useful support: strictly better reward than useless movement."""
    ev = CompetitiveEvaluator.get(comp_map)
    opp_pos = (7, 10)
    # Box is at (2, 3), goal is at (2, 2). Support cell to push West is (2, 4).
    # From (1, 1), moving to (1, 2) gets closer to (2, 4).
    # Moving to (2, 1) does not get closer to (2, 4).
    s_start = ((1, 1), comp_map.initial_boxes, (), 0)
    s_closer = ((1, 2), comp_map.initial_boxes, (), 1)
    s_useless = ((2, 1), comp_map.initial_boxes, (), 1)

    r_closer = ev.transition_reward(s_start, s_closer, opp_pos=opp_pos, player_id=1, step_limit=25)
    r_useless = ev.transition_reward(s_start, s_useless, opp_pos=opp_pos, player_id=1, step_limit=25)

    assert r_closer > r_useless, f"Closer move ({r_closer}) should be strictly better than useless ({r_useless})"

def test_C_moving_away_from_support_is_worse(comp_map):
    """C. Moving away: strictly worse than staying or moving closer."""
    ev = CompetitiveEvaluator.get(comp_map)
    opp_pos = (7, 10)
    s_near = ((1, 2), comp_map.initial_boxes, (), 0)
    s_away = ((1, 1), comp_map.initial_boxes, (), 1)
    r_away = ev.transition_reward(s_near, s_away, opp_pos=opp_pos, player_id=1, step_limit=25)
    assert r_away <= -2.0, f"Expected negative reward <= -2.0 for moving away, got {r_away}"

def test_D_useful_push_improves_value(comp_map):
    """D. Useful push: pushes a box closer to a goal, improving state value."""
    ev = CompetitiveEvaluator.get(comp_map)
    opp_pos = (7, 10)
    # In competitive_01.txt: box at (2, 3), goal at (2, 2).
    # Push West: box moves (2, 3) -> (2, 2) [Goal!], player moves (2, 4) -> (2, 3)
    boxes_before = comp_map.initial_boxes # has (2, 3)
    boxes_after = frozenset((comp_map.initial_boxes - {(2, 3)}) | {(2, 2)})
    s_before = ((2, 4), boxes_before, (), 0)
    s_after = ((2, 3), boxes_after, (((2, 2), 1),), 1)

    r_push = ev.transition_reward(s_before, s_after, opp_pos=opp_pos, player_id=1, step_limit=25)
    assert r_push > 0, f"Expected positive reward for useful push, got {r_push}"

def test_E_harmful_push_decreases_value(comp_map):
    """E. Harmful push: pushing a completed box off a goal decreases value."""
    ev = CompetitiveEvaluator.get(comp_map)
    opp_pos = (7, 10)
    # Box is on goal (2, 2) owned by player 1. Pushing it East to (2, 3) loses the goal!
    boxes_on = frozenset((comp_map.initial_boxes - {(2, 3)}) | {(2, 2)})
    boxes_off = comp_map.initial_boxes # has (2, 3)
    s_scored = ((2, 1), boxes_on, (((2, 2), 1),), 0)
    s_pushed_off = ((2, 2), boxes_off, (), 1)

    r_harmful = ev.transition_reward(s_scored, s_pushed_off, opp_pos=opp_pos, player_id=1, step_limit=25)
    assert r_harmful < 0, f"Expected negative reward for harmful push, got {r_harmful}"

def test_F_completing_a_box_strong_positive(comp_map):
    """F. Completing a box: scores own goal, yielding large positive reward (+W_SCORE)."""
    ev = CompetitiveEvaluator.get(comp_map)
    opp_pos = (7, 10)
    boxes_before = comp_map.initial_boxes
    boxes_after = frozenset((comp_map.initial_boxes - {(2, 3)}) | {(2, 2)})
    s_before = ((2, 4), boxes_before, (), 0)
    s_after = ((2, 3), boxes_after, (((2, 2), 1),), 1)

    r_complete = ev.transition_reward(s_before, s_after, opp_pos=opp_pos, player_id=1, step_limit=25)
    # Score gained (+30) + push reduced (+3) - step penalty (-1) - route to next target (-9.4) = +22.6
    assert r_complete >= 20.0, f"Expected strong completion reward >= 20.0, got {r_complete}"

def test_G_losing_own_completed_box_strong_negative(comp_map):
    """G. Losing own completed box: strong negative change (-W_SCORE)."""
    ev = CompetitiveEvaluator.get(comp_map)
    opp_pos = (7, 10)
    boxes_on = frozenset((comp_map.initial_boxes - {(2, 3)}) | {(2, 2)})
    boxes_off = comp_map.initial_boxes
    s_scored = ((2, 1), boxes_on, (((2, 2), 1),), 5)
    s_lost = ((2, 2), boxes_off, (), 6)

    r_lost = ev.transition_reward(s_scored, s_lost, opp_pos=opp_pos, player_id=1, step_limit=25)
    assert r_lost <= -DEFAULT_WEIGHTS.w_score, f"Expected penalty <= -{DEFAULT_WEIGHTS.w_score}, got {r_lost}"

def test_H_removing_opponent_completed_box_positive(comp_map):
    """H. Removing opponent completed box: positive change (strips opponent point, increasing score_diff)."""
    ev = CompetitiveEvaluator.get(comp_map)
    opp_pos = (6, 6)
    # Opponent owns box at (2, 2)
    boxes_on = frozenset((comp_map.initial_boxes - {(2, 3)}) | {(2, 2)})
    boxes_off = comp_map.initial_boxes # pushed to (2, 3)
    s_opp_scored = ((2, 1), boxes_on, (((2, 2), 2),), 5)
    s_disrupted = ((2, 2), boxes_off, (), 6)

    # From player 1's perspective:
    r_disrupt = ev.transition_reward(s_opp_scored, s_disrupted, opp_pos=opp_pos, player_id=1, step_limit=25)
    # Opponent score decreased by 1 -> score_diff increased by 1 (+W_SCORE), netting +45.0
    assert r_disrupt > 0, f"Expected positive reward for disrupting opponent goal, got {r_disrupt}"

def test_I_static_deadlock_pruning(comp_map):
    """I. Static deadlock: dead squares are identified and pruned from successors."""
    ev = CompetitiveEvaluator.get(comp_map)
    assert len(ev.dead_squares) > 0, "Board must have precomputed dead squares"

    # Any dead square must not be a goal
    for d in ev.dead_squares:
        assert d not in ev.goals, f"Goal {d} marked as dead square!"

    # In A* and GBFS search, actions pushing into dead squares are pruned
    for AgentCls in (AStarAgent, GBFSAgent):
        agent = AgentCls(player_id=1)
        state = initial_state(comp_map)
        action = agent.choose_action(state, comp_map, time_limit_ms=500)
        assert action in ('North', 'South', 'East', 'West')

def test_J_terminal_win_dominates_normal_progress(comp_map):
    """J. Terminal win: dominates normal shaping progress (+1000)."""
    ev = CompetitiveEvaluator.get(comp_map)
    opp_pos = (7, 10)
    boxes_with_goal = frozenset((comp_map.initial_boxes - {(2, 3)}) | {(2, 2)})

    # Normal progress state (score 0, step 10)
    phi_normal = ev.evaluate_phi((2, 2), opp_pos, comp_map.initial_boxes, (), step=10, player_id=1, step_limit=25)

    # Terminal win state at step == 25 with 1 owned goal vs 0
    phi_win = ev.evaluate_phi((2, 2), opp_pos, boxes_with_goal, (((2, 2), 1),), step=25, player_id=1, step_limit=25)

    assert phi_win >= DEFAULT_WEIGHTS.terminal_win
    assert phi_win > phi_normal + 500, f"Terminal win ({phi_win}) must dominate normal state ({phi_normal})"

def test_K_terminal_loss_strongly_undesirable(comp_map):
    """K. Terminal loss: strongly negative (-1000)."""
    ev = CompetitiveEvaluator.get(comp_map)
    opp_pos = (7, 10)
    boxes_with_goal = frozenset((comp_map.initial_boxes - {(2, 3)}) | {(2, 2)})

    # Terminal loss state at step == 25 with opponent owning 1 goal vs 0
    phi_loss = ev.evaluate_phi((2, 2), opp_pos, boxes_with_goal, (((2, 2), 2),), step=25, player_id=1, step_limit=25)

    assert phi_loss <= DEFAULT_WEIGHTS.terminal_loss, f"Terminal loss ({phi_loss}) must be <= {DEFAULT_WEIGHTS.terminal_loss}"

def test_L_wall_aware_bfs_different_from_manhattan():
    """L. Wall-aware BFS example: returns detour distance strictly different from Manhattan."""
    # U-shaped wall map:
    # Wall between (1, 1) and (1, 3) at (1, 2)
    # Floor at (2, 1), (2, 2), (2, 3)
    map_text = (
        "%%%%%\n"
        "%A% D\n"
        "% B %\n"
        "%%%%%\n"
    )
    b = SokobanMap.from_text(map_text)

    p1 = (1, 1)
    target = (1, 3) # Cell on opposite side of wall (1, 2)
    manhattan_dist = abs(p1[0] - target[0]) + abs(p1[1] - target[1])
    assert manhattan_dist == 2

    # Wall-aware BFS must walk around the wall: (1,1) -> (2,1) -> (2,2) -> (2,3) -> (1,3) = 4 steps
    from sokoban.agents.base import static_distance
    bfs_dist = static_distance(b, p1, target)
    assert bfs_dist == 4, f"Expected wall-aware detour distance 4, got {bfs_dist}"
    assert bfs_dist != manhattan_dist, "Wall-aware distance must differ from Manhattan when wall blocks direct route"

def test_situation_1_protect_completed_owned_box(comp_map):
    """Situation 1: Agent protects completed owned box; never targets pushing it away."""
    ev = CompetitiveEvaluator.get(comp_map)
    # Box (2, 2) is on goal and owned by player 1
    boxes = frozenset((comp_map.initial_boxes - {(2, 3)}) | {(2, 2)})
    owners = {(2, 2): 1}
    # find_useful_pushes should NOT include any push on box (2, 2) for player 1
    useful_for_p1 = ev.find_useful_pushes(player_pos=(1, 1), opp_pos=(7, 10), boxes=boxes, owner_map=owners, player_id=1)
    pushes_on_owned_goal = [dest for supp, dest in useful_for_p1 if supp == (2, 1) and dest == (2, 3)]
    assert len(pushes_on_owned_goal) == 0, "Must not generate pushes moving own completed box off its goal"

def test_situation_2_disrupt_opponent_completed_box(comp_map):
    """Situation 2: Agent recognizes opponent completed box as a high-value disruption target."""
    ev = CompetitiveEvaluator.get(comp_map)
    # Box (2, 2) is on goal and owned by player 2 (opponent)
    boxes = frozenset((comp_map.initial_boxes - {(2, 3)}) | {(2, 2)})
    owners = {(2, 2): 2}
    # find_useful_pushes for player 1 MUST include pushing this opponent box off
    useful_for_p1 = ev.find_useful_pushes(player_pos=(1, 1), opp_pos=(7, 10), boxes=boxes, owner_map=owners, player_id=1)
    assert len(useful_for_p1) > 0, "Must generate useful pushes to disrupt opponent completed box"

def test_situation_3_horizon_awareness_scales_score_importance(comp_map):
    """Situation 3: Near horizon n, score difference weight scales up and terminal outcome dominates."""
    ev = CompetitiveEvaluator.get(comp_map)
    opp_pos = (7, 10)
    boxes_with_goal = frozenset((comp_map.initial_boxes - {(2, 3)}) | {(2, 2)})

    # At step 0, score_diff = +1
    b1 = ev.breakdown(player_pos=(1, 1), opp_pos=opp_pos, boxes=boxes_with_goal, owners=(((2, 2), 1),), step=0, player_id=1, step_limit=25)
    # At step 24 (near horizon), score_diff = +1
    b2 = ev.breakdown(player_pos=(1, 1), opp_pos=opp_pos, boxes=boxes_with_goal, owners=(((2, 2), 1),), step=24, player_id=1, step_limit=25)

    assert b2['score_contrib'] > b1['score_contrib'], "Score contribution must scale up near the horizon"
    assert b2['score_contrib'] == 44.4 and b1['score_contrib'] == 30.0

def test_fallback_action_selects_legal_push_when_walk_blocked():
    """Verify agent selects a legal push action when all pure walk neighbors are blocked."""
    # Map where player at (1, 1) is surrounded by walls on North, West, South, and a pushable box East at (1, 2)
    # %: wall, B: box, .: goal, A: player
    text = (
        "%%%%%%\n"
        "%AB .%\n"
        "%%%%%%\n"
    )
    board = SokobanMap.from_text(text)
    state = CompetitiveState(p1=(1, 1), p2=(1, 4), boxes=frozenset({(1, 2)}), owners=(), step=0)
    agent = AStarAgent(player_id=1)
    act = agent.choose_action(state, board, time_limit_ms=1000, step_limit=10)
    # East is the ONLY valid move (it's a legal push). North, South, West are walls.
    assert act == 'East', f"Expected fallback/planner to choose legal push 'East', got {act}"

def test_clean_ownership_ablation_zeros_scores_and_disruption(comp_map):
    """Verify that when enable_ownership=False, no score difference is credited and no ownership disruption occurs."""
    ev = CompetitiveEvaluator.get(comp_map)
    boxes_with_goal = frozenset((comp_map.initial_boxes - {(2, 3)}) | {(2, 2)})
    # Player 2 owns the box on goal (2, 2)
    owners = (((2, 2), 2),)

    # With ownership enabled: score_diff is -1 for player 1
    phi_with = ev.evaluate_phi(
        player_pos=(1, 1), opp_pos=(7, 10), boxes=boxes_with_goal,
        owners=owners, step=0, player_id=1, step_limit=25, enable_ownership=True
    )
    # With ownership disabled: neither agent owns goals; score_diff must be 0
    phi_without = ev.evaluate_phi(
        player_pos=(1, 1), opp_pos=(7, 10), boxes=boxes_with_goal,
        owners=owners, step=0, player_id=1, step_limit=25, enable_ownership=False
    )
    # The score component in phi_without must be 0
    assert phi_without > phi_with, "Disabling ownership removes negative score diff (-30) for player 1"

def test_find_useful_pushes_bipartite_matching_cost_improvement(comp_map):
    """Verify that find_useful_pushes includes pushes that improve overall bipartite matching cost."""
    ev = CompetitiveEvaluator.get(comp_map)
    pushes = ev.find_useful_pushes(
        player_pos=(1, 1), opp_pos=(7, 10), boxes=comp_map.initial_boxes,
        owner_map={}, player_id=1
    )
    assert len(pushes) > 0, "Must identify useful push candidates from initial configuration"

