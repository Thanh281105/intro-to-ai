import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from sokoban.map import SokobanMap
from sokoban.problem import SokobanProblem
from sokoban.search.ucs import solve as ucs_solve
from sokoban.search.astar import solve as astar_solve
from sokoban.state import DIRECTIONS

root = Path(__file__).resolve().parents[1]
maps = ('easy_01.txt', 'medium_01.txt', 'hard_01.txt', 'example_map.txt')

print("Running final end-to-end search verification across all benchmark maps...")

for name in maps:
    b = SokobanMap.from_file(root / 'maps' / name)
    p = SokobanProblem(b)
    r_ucs = ucs_solve(p)
    r_astar = astar_solve(p)

    assert r_ucs.solved and r_astar.solved, f"{name}: both algorithms must solve the map"
    assert r_ucs.total_cost == r_astar.total_cost, f"{name}: optimal cost mismatch UCS={r_ucs.total_cost} vs A*={r_astar.total_cost}"

    for alg_name, r in (('UCS', r_ucs), ('A*', r_astar)):
        state = p.initial_state
        for act in r.actions:
            choices = dict(p.get_successors(state))
            assert act in choices, f"{name} ({alg_name}): invalid action {act}"
            state = choices[act]
        assert p.is_goal(state), f"{name} ({alg_name}): final state must be goal"
        assert r.total_cost == len(r.actions), f"{name} ({alg_name}): cost must match action count"

    print(f"PASS: {name:16s} | Cost: {r_astar.total_cost:2d} | UCS nodes: {r_ucs.expanded_nodes:5d} | A* nodes: {r_astar.expanded_nodes:5d} (Replay Legal)")

print("\nALL FINAL SEARCH VERIFICATIONS PASSED SUCCESSFULLY.")
