import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from sokoban.map import SokobanMap
from sokoban.state import State
from sokoban.problem import SokobanProblem
from sokoban.search.ucs import solve as ucs_solve
from sokoban.search.astar import solve as astar_solve

def sample_board() -> SokobanMap:
    return SokobanMap.from_text('%%%%%%\n% .B %\n%  A %\n%%%%%%')

def test_parser_and_hash():
    b = sample_board()
    assert b.goals == frozenset({(1, 2)})
    s1 = State(b.initial_player, b.initial_boxes)
    s2 = State(b.initial_player, b.initial_boxes)
    assert s1 == s2
    assert hash(s1) == hash(s2)

def test_ragged_map_parsing_and_void_isolation():
    # Row 0: length 7
    # Row 1: length 5 (missing cols 5, 6)
    # Row 2: length 7
    raw = (
        "%%%%%%%\n"
        "% A %  \n"
        "%%%%%%%\n"
    )
    b = SokobanMap.from_text(raw)
    assert b.width == 7
    assert b.height == 3
    # Explicit space inside source row is traversable floor
    assert b.free((1, 1)) is True   # ' '
    assert b.free((1, 2)) is True   # 'A'
    assert b.free((1, 3)) is True   # ' '
    assert b.free((1, 0)) is False  # '%'
    assert b.free((1, 4)) is False  # '%'
    # Explicit space in row 1 at col 5, 6
    assert b.free((1, 5)) is True
    assert b.free((1, 6)) is True

    # Truly ragged map where row 1 ends early (no trailing spaces)
    ragged_raw = (
        "%%%%%%%\n"
        "% A %\n"
        "%%%%%%%\n"
    )
    b_ragged = SokobanMap.from_text(ragged_raw)
    assert b_ragged.free((1, 1)) is True   # Explicit space
    assert b_ragged.free((1, 2)) is True   # Agent
    assert b_ragged.free((1, 3)) is True   # Explicit space
    assert b_ragged.free((1, 4)) is False  # Wall
    # Coordinates beyond the end of row 1 (len=5) are VOID and MUST NOT be traversable
    assert b_ragged.free((1, 5)) is False
    assert b_ragged.free((1, 6)) is False
    assert b_ragged.inside((1, 5)) is False
    assert b_ragged.inside((1, 6)) is False


def test_successors_and_goal():
    p = SokobanProblem(sample_board())
    r = ucs_solve(p)
    assert r.solved is True
    assert r.total_cost == 3
    assert p.is_goal(r.solution_states[-1])

def test_astar_optimal_equals_ucs():
    p = SokobanProblem(sample_board())
    r_astar = astar_solve(p)
    r_ucs = ucs_solve(p)
    assert r_astar.solved is True
    assert r_ucs.solved is True
    assert r_astar.total_cost == r_ucs.total_cost == 3
    assert r_astar.actions == r_ucs.actions

def test_example_map_restored_solvability():
    root = Path(__file__).resolve().parents[1]
    b = SokobanMap.from_file(root / 'maps/example_map.txt')
    assert len(b.walls) == 35
    assert len(b.goals) == 7
    assert len(b.initial_boxes) == 7
    p = SokobanProblem(b)
    r = astar_solve(p)
    assert r.solved is True
    assert r.total_cost == 34
    assert len(r.actions) == 34
    assert p.is_goal(r.solution_states[-1])

def test_heuristic_goal_zero_on_real_solved_state():
    p = SokobanProblem(sample_board())
    r = astar_solve(p)
    assert r.solved is True
    goal_state = r.solution_states[-1]
    assert p.is_goal(goal_state)
    # Heuristic on real goal state must be exactly 0
    assert p.heuristic(goal_state) == 0

def test_heuristic_nonnegative_finite():
    p = SokobanProblem(sample_board())
    h_val = p.heuristic(p.initial_state)
    assert h_val >= 0
    assert h_val < float('inf')

def test_heuristic_multiple_box_matching():
    root = Path(__file__).resolve().parents[1]
    b = SokobanMap.from_file(root / 'maps/medium_01.txt')
    p = SokobanProblem(b)
    assert len(b.goals) == 2
    assert len(b.initial_boxes) == 2
    h_val = p.heuristic(p.initial_state)
    assert h_val > 0
    assert h_val < float('inf')

def test_heuristic_impossible_assignment_returns_infinity():
    # Map with an isolated trapped box cell where no push can ever reach any goal
    text = (
        "%%%%%%%%\n"
        "%  . %B%\n"
        "% A  %%%\n"
        "%%%%%%%%\n"
    )
    b = SokobanMap.from_text(text)
    p = SokobanProblem(b)
    # The box at (1, 6) cannot be moved anywhere, distance to goal is inf
    assert p.heuristic(p.initial_state) == float('inf')

def test_heuristic_cache_reuse_and_invalidation():
    p = SokobanProblem(sample_board())
    s1 = State((2, 3), p.board.initial_boxes)
    s2 = State((1, 1), p.board.initial_boxes)
    # Same box positions with different player positions must hit cache
    h1 = p.heuristic(s1)
    misses_before = p.heuristic_model.cache_misses
    hits_before = p.heuristic_model.cache_hits
    h2 = p.heuristic(s2)
    assert h1 == h2
    assert p.heuristic_model.cache_hits == hits_before + 1
    assert p.heuristic_model.cache_misses == misses_before

    # Different box configuration must compute new value and not reuse old
    different_boxes = frozenset({(1, 1)})
    s3 = State((2, 3), different_boxes)
    h3 = p.heuristic(s3)
    assert p.heuristic_model.cache_misses == misses_before + 1
