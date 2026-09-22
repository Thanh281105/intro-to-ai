from sokoban.map import SokobanMap
from sokoban.competitive.state import CompetitiveState
from sokoban.agents.agent_astar import AStarAgent
from sokoban.agents.agent_gbfs import GBFSAgent

def test_astar_tactical_ordering():
    # Setup where player A is at (1, 1), box B is at (1, 2), goal is at (1, 3).
    # Moving East pushes box into goal (rank 0).
    # Moving South is a walk move (rank 3).
    raw = (
        "%%%%%%\n"
        "%AB. %\n"
        "%    %\n"
        "%  2 %\n"
        "%%%%%%\n"
    )
    board = SokobanMap.from_text(raw)
    state = CompetitiveState(
        p1=(1, 1),
        p2=(3, 3),
        boxes=frozenset([(1, 2)]),
        owners=(),
        step=0,
    )
    agent = AStarAgent(player_id=1)
    act = agent.choose_action(state, board, time_limit_ms=500, step_limit=25)
    # Must choose 'East' to push into goal immediately!
    assert act == 'East'

def test_gbfs_tactical_ordering():
    raw = (
        "%%%%%%\n"
        "%AB. %\n"
        "%    %\n"
        "%  2 %\n"
        "%%%%%%\n"
    )
    board = SokobanMap.from_text(raw)
    state = CompetitiveState(
        p1=(1, 1),
        p2=(3, 3),
        boxes=frozenset([(1, 2)]),
        owners=(),
        step=0,
    )
    agent = GBFSAgent(player_id=1)
    act = agent.choose_action(state, board, time_limit_ms=500, step_limit=25)
    # Must choose 'East' to push into goal immediately!
    assert act == 'East'

def test_ejection_tactical_ordering():
    # Setup where opponent scored box at (1, 3) with owner 2.
    # Player 1 is at (1, 2), box is at (1, 3), floor at (1, 4).
    # Moving East ejects opponent's scored box (rank 1).
    raw = (
        "%%%%%%%\n"
        "% AB. 2%\n"
        "%     %\n"
        "%%%%%%%\n"
    )
    board = SokobanMap.from_text(raw)
    state = CompetitiveState(
        p1=(1, 2),
        p2=(1, 6),
        boxes=frozenset([(1, 3)]),
        owners=(( (1, 3), 2 ),),
        step=5,
    )
    agent_astar = AStarAgent(player_id=1)
    act_astar = agent_astar.choose_action(state, board, time_limit_ms=500, step_limit=25)
    assert act_astar == 'East'

    agent_gbfs = GBFSAgent(player_id=1)
    act_gbfs = agent_gbfs.choose_action(state, board, time_limit_ms=500, step_limit=25)
    assert act_gbfs == 'East'
