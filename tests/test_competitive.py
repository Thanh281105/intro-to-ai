import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from sokoban.map import SokobanMap
from sokoban.competitive.state import CompetitiveState, initial_state, resolve, get_deterministic_p2
from sokoban.competitive.game import CompetitiveGame
from sokoban.agents import AStarAgent, GBFSAgent

def board_arena() -> SokobanMap:
    # 7x7 arena with 2 goals and 2 boxes
    text = (
        "%%%%%%%\n"
        "% .   %\n"
        "%  BB %\n"
        "% A   %\n"
        "%   . %\n"
        "%     %\n"
        "%%%%%%%\n"
    )
    return SokobanMap.from_text(text)


def test_legal_push_semantics():
    # Agent at (3, 2), Box at (2, 2), Empty at (1, 2)
    b = board_arena()
    s = CompetitiveState(p1=(3, 2), p2=(5, 5), boxes=frozenset({(2, 2)}))
    n = resolve(s, 'North', 'North', b)
    # Box moves to (1, 2), Player 1 moves to (2, 2) (the box's OLD position)
    assert (1, 2) in n.boxes
    assert (2, 2) not in n.boxes
    assert n.p1 == (2, 2)
    # INVARIANT: Player must NEVER be inside a box
    assert n.p1 not in n.boxes
    assert n.p2 not in n.boxes

def test_no_player_box_overlap_invariant():
    b = board_arena()
    # Test multiple sequential moves ensuring invariant holds
    s = CompetitiveState(p1=(3, 2), p2=(5, 5), boxes=frozenset({(2, 2)}))
    n1 = resolve(s, 'North', 'West', b)
    assert n1.p1 not in n1.boxes
    assert n1.p2 not in n1.boxes
    # Push into wall should be blocked
    n2 = resolve(n1, 'North', 'West', b)
    assert n2.p1 not in n2.boxes
    assert n2.p2 not in n2.boxes

def test_independent_movements():
    b = board_arena()
    s = CompetitiveState(p1=(3, 1), p2=(5, 5), boxes=frozenset({(2, 2)}))
    n = resolve(s, 'East', 'North', b)
    assert n.p1 == (3, 2)
    assert n.p2 == (4, 5)
    assert n.boxes == s.boxes

def test_independent_pushes():
    text = (
        "%%%%%%%%\n"
        "% .  . %\n"
        "% B  B %\n"
        "% A  2 %\n"
        "%%%%%%%%\n"
    )
    b = SokobanMap.from_text(text)
    s = CompetitiveState(p1=(3, 2), p2=(3, 5), boxes=frozenset({(2, 2), (2, 5)}))
    n = resolve(s, 'North', 'North', b)
    assert n.p1 == (2, 2)
    assert n.p2 == (2, 5)
    assert n.boxes == frozenset({(1, 2), (1, 5)})
    assert n.scores(b.goals) == (1, 1)

def test_same_player_destination_conflict():
    b = board_arena()
    # P1 at (3, 2), P2 at (3, 4). Both try to move into (3, 3)
    s = CompetitiveState(p1=(3, 2), p2=(3, 4), boxes=frozenset())
    n = resolve(s, 'East', 'West', b)
    # Both blocked, remain at starting positions
    assert n.p1 == (3, 2)
    assert n.p2 == (3, 4)

def test_direct_swap_conflict():
    b = board_arena()
    # P1 at (3, 2), P2 at (3, 3). P1 tries East, P2 tries West (direct swap)
    s = CompetitiveState(p1=(3, 2), p2=(3, 3), boxes=frozenset())
    n = resolve(s, 'East', 'West', b)
    assert n.p1 == (3, 2)
    assert n.p2 == (3, 3)

def test_entering_opponent_current_cell_conflict():
    b = board_arena()
    # P1 at (3, 2), P2 at (3, 3). P1 tries East, P2 tries North
    s = CompetitiveState(p1=(3, 2), p2=(3, 3), boxes=frozenset())
    n = resolve(s, 'East', 'North', b)
    # P1 cannot enter P2's starting cell (conservative resolution)
    assert n.p1 == (3, 2)
    # P2 moved North safely
    assert n.p2 == (2, 3)

def test_same_box_push_conflict():
    b = board_arena()
    # Box at (3, 3). P1 at (3, 2) tries East, P2 at (3, 4) tries West
    s = CompetitiveState(p1=(3, 2), p2=(3, 4), boxes=frozenset({(3, 3)}))
    n = resolve(s, 'East', 'West', b)
    # Both pushes conflict on the same box; both cancelled
    assert n.p1 == (3, 2)
    assert n.p2 == (3, 4)
    assert (3, 3) in n.boxes

def test_two_pushed_boxes_same_destination_conflict():
    text = (
        "%%%%%%%%\n"
        "% .  . %\n"
        "% B  B %\n"
        "% A  2 %\n"
        "%%%%%%%%\n"
    )
    b = SokobanMap.from_text(text)
    # Boxes at (2, 2) and (2, 4). P1 at (2, 1) tries East, P2 at (2, 5) tries West
    s = CompetitiveState(p1=(2, 1), p2=(2, 5), boxes=frozenset({(2, 2), (2, 4)}))
    n = resolve(s, 'East', 'West', b)
    # Both boxes would end up at (2, 3) -> conflict!
    assert n.p1 == (2, 1)
    assert n.p2 == (2, 5)
    assert n.boxes == frozenset({(2, 2), (2, 4)})

def test_player_destination_conflicts_with_pushed_box_destination():
    text = (
        "%%%%%%%%\n"
        "%  .   %\n"
        "%  B   %\n"
        "%  A 2 %\n"
        "%%%%%%%%\n"
    )
    b = SokobanMap.from_text(text)
    # Box at (2, 3). P1 at (3, 3) pushes North into (1, 3).
    # P2 is at (1, 4) and tries to move West into (1, 3).
    s = CompetitiveState(p1=(3, 3), p2=(1, 4), boxes=frozenset({(2, 3)}))
    n = resolve(s, 'North', 'West', b)
    # Pushed box and player conflict on destination (1, 3) -> conflict resolved, no overlap
    assert n.p1 not in n.boxes
    assert n.p2 not in n.boxes
    assert n.p1 != n.p2
    assert (1, 3) not in (n.p1, n.p2) or (1, 3) not in n.boxes


def test_push_into_opponent_location():
    b = board_arena()
    # Box at (3, 3), P1 at (3, 2). P2 is at (3, 4).
    # P1 tries to push box East into (3, 4) where P2 is located.
    s = CompetitiveState(p1=(3, 2), p2=(3, 4), boxes=frozenset({(3, 3)}))
    n = resolve(s, 'East', 'South', b)
    # P1's push into opponent's position is cancelled
    assert n.p1 == (3, 2)
    assert (3, 3) in n.boxes

def test_one_action_invalid_and_both_actions_invalid():
    b = board_arena()
    # P1 tries to walk into wall North from (1, 2) (wall is at (0, 2))
    # P2 at (5, 5) walks North legally
    s = CompetitiveState(p1=(1, 2), p2=(5, 5), boxes=frozenset({(3, 3)}))
    n1 = resolve(s, 'North', 'North', b)
    assert n1.p1 == (1, 2)  # Blocked by wall
    assert n1.p2 == (4, 5)  # Legal move

    # Both walk into walls
    n2 = resolve(s, 'North', 'South', b)  # Row 6 is wall for P2
    assert n2.p1 == (1, 2)
    assert n2.p2 == (5, 5)

def test_ownership_lifecycle_and_recompletion():
    text = (
        "%%%%%%%%\n"
        "% .    %\n"
        "% B    %\n"
        "% A  2 %\n"
        "%%%%%%%%\n"
    )
    b = SokobanMap.from_text(text)
    goal = (1, 2)
    s = CompetitiveState(p1=(3, 2), p2=(3, 5), boxes=frozenset({(2, 2)}))
    
    # 1. Agent 1 pushes box onto goal -> Agent 1 gains ownership
    s1 = resolve(s, 'North', 'West', b)
    assert (1, 2) in s1.boxes
    assert s1.scores(b.goals) == (1, 0)
    assert s1.owner_map().get(goal) == 1

    # 2. Agent 2 moves closer and pushes box out of goal -> ownership removed
    s_adj = CompetitiveState(p1=(3, 2), p2=(1, 3), boxes=frozenset({(1, 2)}), owners=((goal, 1),))
    s2 = resolve(s_adj, 'South', 'West', b)
    assert (1, 1) in s2.boxes
    assert (1, 2) not in s2.boxes
    assert s2.scores(b.goals) == (0, 0)
    assert s2.owner_map().get((1, 1)) is None

    # 3. Another push puts box back on goal by Agent 2 -> Agent 2 gains ownership
    s_before_recomplete = CompetitiveState(p1=(3, 2), p2=(1, 0), boxes=frozenset({(1, 1)}))
    # Wait, col 0 is wall. Let's put P2 at (1, 0) -> no, P2 at (2, 1) pushing North into (1, 1)...
    # Let's push box from (1, 1) to (1, 2) with East push from (1, 0)? (1, 0) is wall.
    # From (2, 2), push North to (1, 2):
    s_recomp = CompetitiveState(p1=(3, 5), p2=(2, 2), boxes=frozenset({(1, 2)}), owners=())
    # If box is already at (1, 2), push from (2, 2) is blocked if beyond is wall.
    # Instead, let box be at (2, 2) and goal at (1, 2), pushed by Agent 2:
    s_recomp_prep = CompetitiveState(p1=(3, 5), p2=(3, 2), boxes=frozenset({(2, 2)}), owners=())
    s3 = resolve(s_recomp_prep, 'North', 'North', b)
    assert s3.scores(b.goals) == (0, 1)
    assert s3.owner_map().get(goal) == 2

def test_game_stops_exactly_at_step_limit():
    b = board_arena()
    game = CompetitiveGame(b, AStarAgent(), GBFSAgent(), step_limit=10)
    final_state = game.run()
    assert final_state.step == 10
    assert len(game.history) == 11  # Initial state + 10 steps

def test_deterministic_p2_start_validation():
    root = Path(__file__).resolve().parents[1]
    for map_path in (root / 'maps').glob('*.txt'):
        b = SokobanMap.from_file(map_path)
        p2 = get_deterministic_p2(b, b.initial_player)
        assert b.free(p2) is True
        assert p2 not in b.walls
        assert p2 not in b.initial_boxes
        assert p2 != b.initial_player

def test_agents_priority_queue_search_and_valid_action():
    root = Path(__file__).resolve().parents[1]
    b = SokobanMap.from_file(root / 'maps/competitive_01.txt')
    s = initial_state(b)

    agent1 = AStarAgent(player_id=1)
    agent2 = GBFSAgent(player_id=2)

    act1 = agent1.choose_action(s, b, time_limit_ms=1000)
    act2 = agent2.choose_action(s, b, time_limit_ms=1000)

    assert act1 in {'North', 'East', 'South', 'West'}
    assert act2 in {'North', 'East', 'South', 'West'}

def test_agent_deadline_behavior_under_950ms():
    root = Path(__file__).resolve().parents[1]
    b = SokobanMap.from_file(root / 'maps/example_map.txt')
    s = initial_state(b)

    agent = AStarAgent(player_id=1)
    t0 = time.perf_counter_ns()
    # Call with 500ms time limit
    act = agent.choose_action(s, b, time_limit_ms=500)
    elapsed_ms = (time.perf_counter_ns() - t0) / 1e6

    assert act in {'North', 'East', 'South', 'West'}
    # Must comfortably return before 1000ms and within internal limit
    assert elapsed_ms < 950.0


def test_winner_loser_emotes_active_vs_final_invariants():
    from sokoban.gui.renderer import get_match_emotes_and_standing
    
    # 1. While round is active (is_finished=False): STRICTLY NO CROWN, NO CRYING ICON
    # Regardless of whether A1 leads, A2 leads, or tied
    e1, e2, lead_str, _ = get_match_emotes_and_standing(s1=2, s2=0, is_finished=False)
    assert e1 is None and e2 is None
    assert "Leads" in lead_str and "WINS" not in lead_str

    e1, e2, lead_str, _ = get_match_emotes_and_standing(s1=0, s2=2, is_finished=False)
    assert e1 is None and e2 is None
    assert "Leads" in lead_str and "WINS" not in lead_str

    e1, e2, lead_str, _ = get_match_emotes_and_standing(s1=1, s2=1, is_finished=False)
    assert e1 is None and e2 is None
    assert "Tied" in lead_str and "WINS" not in lead_str

    # 2. When match is complete (is_finished=True): Crown to winner, crying to loser, derived from final score
    # A1 wins
    e1, e2, lead_str, _ = get_match_emotes_and_standing(s1=2, s2=1, is_finished=True)
    assert e1 == "celebrate"  # Crown
    assert e2 == "cry"        # Crying icon
    assert "AGENT 1 WINS!" in lead_str

    # A2 wins
    e1, e2, lead_str, _ = get_match_emotes_and_standing(s1=1, s2=3, is_finished=True)
    assert e1 == "cry"        # Crying icon
    assert e2 == "celebrate"  # Crown
    assert "AGENT 2 WINS!" in lead_str

    # Tie
    e1, e2, lead_str, _ = get_match_emotes_and_standing(s1=2, s2=2, is_finished=True)
    assert e1 == "tie" and e2 == "tie"
    assert "MATCH DRAWN" in lead_str


def test_turn_history_telemetry():
    b = board_arena()
    game = CompetitiveGame(b, AStarAgent(1), GBFSAgent(2), step_limit=5)
    final_state = game.run()

    assert final_state.step == 5
    assert len(game.turn_history) == 5

    for turn in game.turn_history:
        assert turn.a1_action in {'North', 'East', 'South', 'West'}
        assert turn.a2_action in {'North', 'East', 'South', 'West'}
        assert turn.a1_outcome in {'MOVE', 'PUSH', 'BLOCKED', 'CONFLICT'}
        assert turn.a2_outcome in {'MOVE', 'PUSH', 'BLOCKED', 'CONFLICT'}
        assert turn.a1_latency_ms >= 0.0
        assert turn.a2_latency_ms >= 0.0
        assert isinstance(turn.resolution_summary, str)

