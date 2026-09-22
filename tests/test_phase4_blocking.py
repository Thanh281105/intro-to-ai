import pytest
from sokoban.map import SokobanMap
from sokoban.competitive.evaluator_potential import CompetitiveEvaluator
from sokoban.competitive.weights import CompetitiveWeights

@pytest.fixture
def corridor_board():
    """A map with a narrow 1-wide corridor connecting two rooms."""
    raw = (
        "%%%%%%%%%%\n"
        "%A      2%\n"
        "%%%%..%%%%\n"
        "%  %..%  %\n"
        "%  %B %  %\n"
        "%  %  %  %\n"
        "%%%%%%%%%%\n"
    )
    return SokobanMap.from_text(raw)

def test_chokepoints_detection():
    # Tunnel map: (2, 2) is flanked by walls above and below
    raw = (
        "%%%%%\n"
        "% % %\n"
        "%   %\n"
        "% % %\n"
        "%%%%%\n"
    )
    # Actually:
    # row 0: %%%%%
    # row 1: % % % -> (1, 1) is wall? No: ' ' is floor, '%' is wall
    raw_tunnel = (
        "%%%%%\n"
        "%A  %\n"
        "%% %%\n"
        "% B.%\n"
        "%%%%%\n"
    )
    # In row 2: (2, 2) is ' ', (2, 1) is '%', (2, 3) is '%' -> opposing walls left & right!
    board = SokobanMap.from_text(raw_tunnel)
    evaluator = CompetitiveEvaluator(board)
    assert (2, 2) in evaluator.chokepoints
    # (1, 2) is open (walls not opposing)
    assert (1, 2) not in evaluator.chokepoints

def test_compute_blocking_interception():
    # Opponent at (1, 3), Goal at (3, 2), Box at (3, 2)?
    # Let's create a clear setup where opp wants to push box B at (3, 2)
    # Chokepoint is at (2, 2) between top room and bottom room
    raw = (
        "%%%%%%%\n"
        "%A   2%\n"
        "%%% %%%\n"
        "%  B. %\n"
        "%%%%%%%\n"
    )
    board = SokobanMap.from_text(raw)
    evaluator = CompetitiveEvaluator(board)
    # Chokepoint is at (2, 3)
    assert (2, 3) in evaluator.chokepoints

    boxes = frozenset([(3, 3)])  # Box at (3, 3), Goal is at (3, 4) '.'
    # Player 1 is at (2, 3) (the chokepoint)
    # Opponent is at (1, 4) or (1, 5)
    block_val = evaluator.compute_blocking(
        player_pos=(2, 3),
        opp_pos=(1, 5),
        boxes=boxes,
        owner_map={},
        player_id=1,
    )
    assert block_val > 0.0

    # If player is not at chokepoint (e.g. at (1, 1))
    block_val_none = evaluator.compute_blocking(
        player_pos=(1, 1),
        opp_pos=(1, 5),
        boxes=boxes,
        owner_map={},
        player_id=1,
    )
    assert block_val_none == 0.0

def test_evaluate_phi_blocking_inclusion():
    raw = (
        "%%%%%%%\n"
        "%A   2%\n"
        "%%% %%%\n"
        "%  B. %\n"
        "%%%%%%%\n"
    )
    board = SokobanMap.from_text(raw)
    evaluator = CompetitiveEvaluator(board)
    boxes = frozenset([(3, 3)])
    phi_with_block = evaluator.evaluate_phi(
        player_pos=(2, 3),
        opp_pos=(1, 5),
        boxes=boxes,
        owners=(),
        step=10,
        player_id=1,
        step_limit=50,
        enable_blocking=True,
    )
    phi_without_block = evaluator.evaluate_phi(
        player_pos=(2, 3),
        opp_pos=(1, 5),
        boxes=boxes,
        owners=(),
        step=10,
        player_id=1,
        step_limit=50,
        enable_blocking=False,
    )
    assert phi_with_block > phi_without_block

def test_breakdown_contains_blocking():
    raw = (
        "%%%%%%%\n"
        "%A   2%\n"
        "%%% %%%\n"
        "%  B. %\n"
        "%%%%%%%\n"
    )
    board = SokobanMap.from_text(raw)
    evaluator = CompetitiveEvaluator(board)
    boxes = frozenset([(3, 3)])
    bd = evaluator.breakdown(
        player_pos=(2, 3),
        opp_pos=(1, 5),
        boxes=boxes,
        owners=(),
        step=10,
        player_id=1,
        step_limit=50,
    )
    assert 'blocking' in bd
    assert 'blocking_contrib' in bd
    assert bd['blocking'] > 0.0
