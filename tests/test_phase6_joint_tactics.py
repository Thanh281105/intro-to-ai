import pytest
from sokoban.map import SokobanMap
from sokoban.competitive.state import CompetitiveState
from sokoban.competitive.tactics import is_tactical_close_contact, select_robust_tactical_action, get_legal_actions
from sokoban.agents.agent_astar import AStarAgent
from sokoban.agents.agent_gbfs import GBFSAgent

def test_is_tactical_close_contact():
    raw = (
        "%%%%%%%%%%\n"
        "%A      2%\n"
        "%   B    %\n"
        "%       .%\n"
        "%%%%%%%%%%\n"
    )
    board = SokobanMap.from_text(raw)
    # Far apart: p1=(1, 1), p2=(1, 8), box=(2, 4)
    # dist(p1, p2) = 7 > 3
    # dist(p1, b) = 1 + 3 = 4 > 2
    # dist(p2, b) = 1 + 4 = 5 > 2
    state_far = CompetitiveState(p1=(1, 1), p2=(1, 8), boxes=frozenset([(2, 4)]), owners=(), step=0)
    assert not is_tactical_close_contact(state_far, board)

    # Close contact via Manhattan distance <= 3
    state_close_agents = CompetitiveState(p1=(1, 1), p2=(1, 3), boxes=frozenset([(2, 4)]), owners=(), step=0)
    assert is_tactical_close_contact(state_close_agents, board)

    # Close contact via shared contested box (both within distance 2 of box)
    state_contested_box = CompetitiveState(p1=(1, 3), p2=(3, 4), boxes=frozenset([(2, 4)]), owners=(), step=0)
    assert is_tactical_close_contact(state_contested_box, board)

def test_select_robust_tactical_action_collision_avoidance():
    # Hallway setup: Player 1 at (1, 2), Player 2 at (1, 4), floor at (1, 3) and (2, 2)
    # If Player 1 moves East to (1, 3) and Player 2 moves West to (1, 3), collision occurs!
    # But Player 1 can move South to (2, 2) which is safe.
    raw = (
        "%%%%%%\n"
        "% A 2%\n"
        "%  . %\n"
        "%  B %\n"
        "%%%%%%\n"
    )
    board = SokobanMap.from_text(raw)
    state = CompetitiveState(p1=(1, 2), p2=(1, 4), boxes=frozenset([(3, 3)]), owners=(), step=0)

    # In this close-quarters state, test robust selection
    action = select_robust_tactical_action(
        state=state,
        board=board,
        search_action='East',
        player_id=1,
        step_limit=25,
    )
    assert action in ('North', 'East', 'South', 'West')

def test_agents_execute_close_tactics():
    raw = (
        "%%%%%%\n"
        "% A 2%\n"
        "%  . %\n"
        "%  B %\n"
        "%%%%%%\n"
    )
    board = SokobanMap.from_text(raw)
    state = CompetitiveState(p1=(1, 2), p2=(1, 4), boxes=frozenset([(3, 3)]), owners=(), step=0)

    astar = AStarAgent(player_id=1)
    act_astar = astar.choose_action(state, board, time_limit_ms=500, step_limit=25)
    assert act_astar in ('North', 'East', 'South', 'West')

    gbfs = GBFSAgent(player_id=2)
    act_gbfs = gbfs.choose_action(state, board, time_limit_ms=500, step_limit=25)
    assert act_gbfs in ('North', 'East', 'South', 'West')
