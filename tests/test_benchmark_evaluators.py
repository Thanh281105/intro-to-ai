import pytest
from pathlib import Path
import sys

# Ensure src is in path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'src'))

from sokoban.map import SokobanMap
from sokoban.competitive.evaluator import CompetitiveEvaluator, DEFAULT_WEIGHTS
from sokoban.agents import AStarAgent, GBFSAgent
from sokoban.competitive.game import CompetitiveGame
from scripts.benchmark_evaluators import run_single_match, build_summary

@pytest.fixture
def mini_comp_map():
    return SokobanMap.from_file(root / 'maps/competitive_01.txt')

def test_astar_new_vs_old_execution(mini_comp_map):
    """1. A* NEW vs A* OLD can step and complete cleanly without errors."""
    a1 = AStarAgent(player_id=1, evaluator_type='new')
    a2 = AStarAgent(player_id=2, evaluator_type='old')
    game = CompetitiveGame(mini_comp_map, a1, a2, step_limit=3)
    game.run()
    assert game.state.step == 3
    assert len(game.turn_history) == 3

def test_astar_old_vs_new_execution(mini_comp_map):
    """2. A* OLD vs A* NEW can step and complete cleanly without errors (role swap)."""
    a1 = AStarAgent(player_id=1, evaluator_type='old')
    a2 = AStarAgent(player_id=2, evaluator_type='new')
    game = CompetitiveGame(mini_comp_map, a1, a2, step_limit=3)
    game.run()
    assert game.state.step == 3
    assert len(game.turn_history) == 3

def test_gbfs_new_vs_old_execution(mini_comp_map):
    """3. GBFS NEW vs GBFS OLD can step and complete cleanly without errors."""
    a1 = GBFSAgent(player_id=1, evaluator_type='new')
    a2 = GBFSAgent(player_id=2, evaluator_type='old')
    game = CompetitiveGame(mini_comp_map, a1, a2, step_limit=3)
    game.run()
    assert game.state.step == 3
    assert len(game.turn_history) == 3

def test_gbfs_old_vs_new_execution(mini_comp_map):
    """4. GBFS OLD vs GBFS NEW can step and complete cleanly without errors (role swap)."""
    a1 = GBFSAgent(player_id=1, evaluator_type='old')
    a2 = GBFSAgent(player_id=2, evaluator_type='new')
    game = CompetitiveGame(mini_comp_map, a1, a2, step_limit=3)
    game.run()
    assert game.state.step == 3
    assert len(game.turn_history) == 3

def test_evaluator_identity_and_role_swap_recording(mini_comp_map):
    """5. Evaluator identity and role-assignment metadata are accurately recorded."""
    res_A = run_single_match(mini_comp_map, "comp_01", "astar", "new", "old", limit=2)
    assert res_A['p1_evaluator'] == 'new'
    assert res_A['p2_evaluator'] == 'old'
    assert res_A['role_assignment'] == 'new_as_p1'
    assert res_A['new_score'] == res_A['p1_score']
    assert res_A['old_score'] == res_A['p2_score']

    res_B = run_single_match(mini_comp_map, "comp_01", "astar", "old", "new", limit=2)
    assert res_B['p1_evaluator'] == 'old'
    assert res_B['p2_evaluator'] == 'new'
    assert res_B['role_assignment'] == 'new_as_p2'
    assert res_B['new_score'] == res_B['p2_score']
    assert res_B['old_score'] == res_B['p1_score']

def test_role_swap_aggregation():
    """6. Role-swap aggregation mathematically combines paired matches without loss."""
    dummy_matches = [
        {
            'algorithm': 'astar', 'map': 'test_map', 'step_limit': 10,
            'p1_evaluator': 'new', 'p2_evaluator': 'old', 'role_assignment': 'new_as_p1',
            'winner': 'new', 'new_score': 2, 'old_score': 1, 'score_diff_new_minus_old': 1,
            'new_useful_pushes': 2, 'old_useful_pushes': 1,
            'new_ineffective_actions': 0, 'old_ineffective_actions': 1,
            'new_avg_latency_ms': 5.0, 'old_avg_latency_ms': 6.0,
            'new_max_latency_ms': 10.0, 'old_max_latency_ms': 12.0,
            'new_deadline_fallbacks': 0, 'old_deadline_fallbacks': 0
        },
        {
            'algorithm': 'astar', 'map': 'test_map', 'step_limit': 10,
            'p1_evaluator': 'old', 'p2_evaluator': 'new', 'role_assignment': 'new_as_p2',
            'winner': 'tie', 'new_score': 1, 'old_score': 1, 'score_diff_new_minus_old': 0,
            'new_useful_pushes': 1, 'old_useful_pushes': 1,
            'new_ineffective_actions': 1, 'old_ineffective_actions': 1,
            'new_avg_latency_ms': 4.0, 'old_avg_latency_ms': 5.0,
            'new_max_latency_ms': 8.0, 'old_max_latency_ms': 10.0,
            'new_deadline_fallbacks': 0, 'old_deadline_fallbacks': 0
        }
    ]
    summary = build_summary(dummy_matches)
    # The first row is the paired group
    group_row = summary[0]
    assert group_row['algorithm'] == 'astar'
    assert group_row['new_score'] == 3
    assert group_row['old_score'] == 2
    assert group_row['score_diff'] == 1
    assert group_row['new_wins'] == 1
    assert group_row['old_wins'] == 0
    assert group_row['ties'] == 1

def test_breakdown_mathematical_consistency(mini_comp_map):
    """27. For non-terminal finite states: score_contrib + push_contrib + route_contrib == round(phi, 2)."""
    ev = CompetitiveEvaluator.get(mini_comp_map)
    boxes = mini_comp_map.initial_boxes
    owners = ()
    step = 5
    step_limit = 25

    for p_id in (1, 2):
        p_pos = mini_comp_map.initial_player if p_id == 1 else mini_comp_map.initial_player2
        opp_pos = mini_comp_map.initial_player2 if p_id == 1 else mini_comp_map.initial_player

        b = ev.breakdown(
            player_pos=p_pos, opp_pos=opp_pos, boxes=boxes, owners=owners,
            step=step, player_id=p_id, step_limit=step_limit
        )

        sum_components = round(b['score_contrib'] + b['push_contrib'] + b['route_contrib'], 2)
        assert sum_components == b['phi'], f"Breakdown components ({sum_components}) must exactly sum to phi ({b['phi']})"

def test_no_deadline_violations_in_fixtures(mini_comp_map):
    """7. Latency remains well under the 950ms internal safety threshold."""
    res = run_single_match(mini_comp_map, "comp_01", "astar", "new", "old", limit=2)
    assert res['new_max_latency_ms'] < 950.0
    assert res['old_max_latency_ms'] < 950.0
    assert res['new_deadline_fallbacks'] == 0
    assert res['old_deadline_fallbacks'] == 0

def test_single_agent_code_path_unmodified():
    """8. Single-agent A* solver and heuristic remain strictly isolated and intact."""
    from sokoban.problem import SokobanProblem
    from sokoban.search.astar import solve as solve_astar
    from sokoban.search.ucs import solve as solve_ucs

    board = SokobanMap.from_file(root / 'maps/easy_01.txt')
    prob = SokobanProblem(board)
    res_astar = solve_astar(prob)
    res_ucs = solve_ucs(prob)

    assert res_astar.solved is True
    assert res_ucs.solved is True
    assert res_astar.total_cost == res_ucs.total_cost == 3
