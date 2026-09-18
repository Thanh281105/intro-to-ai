import csv
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from sokoban.map import SokobanMap
from sokoban.problem import SokobanProblem
from sokoban.search.ucs import solve as ucs_solve
from sokoban.search.astar import solve as astar_solve

root = Path(__file__).resolve().parents[1]
out = root / 'experiments/results'
out.mkdir(parents=True, exist_ok=True)

benchmark_maps = [
    root / 'maps' / name for name in ('easy_01.txt', 'medium_01.txt', 'hard_01.txt', 'example_map.txt')
]

def verify_plan(board: SokobanMap, actions: list[str]) -> bool:
    """Replay returned actions step by step to verify solution legality."""
    from sokoban.state import DIRECTIONS, State
    cur = State(board.initial_player, board.initial_boxes)
    for act in actions:
        dr, dc = DIRECTIONS[act]
        nxt = (cur.player[0] + dr, cur.player[1] + dc)
        if not board.free(nxt):
            return False
        boxes = set(cur.boxes)
        if nxt in boxes:
            beyond = (nxt[0] + dr, nxt[1] + dc)
            if not board.free(beyond) or beyond in boxes:
                return False
            boxes.remove(nxt)
            boxes.add(beyond)
            cur = State(nxt, frozenset(boxes))
        else:
            cur = State(nxt, cur.boxes)
    return cur.boxes == board.goals

detailed_rows = []
summary_rows = []

print("Starting rigorous benchmark (tracemalloc separated, >=5 measured runs)...")

for mp in benchmark_maps:
    board = SokobanMap.from_file(mp)
    costs = {}

    for name, fn in [('ucs', ucs_solve), ('astar', astar_solve)]:
        problem = SokobanProblem(board)

        # 1. Warm-up run (tracemalloc OFF)
        _ = fn(problem)

        # 2. Timing benchmark: 5 measured runs with tracemalloc OFF
        runtimes = []
        det_result = None
        for run_idx in range(5):
            prob = SokobanProblem(board)
            t0 = time.perf_counter_ns()
            res = fn(prob)
            elapsed_ms = (time.perf_counter_ns() - t0) / 1e6
            runtimes.append(elapsed_ms)
            det_result = res
            detailed_rows.append({
                'map': mp.name,
                'algorithm': name,
                'run': run_idx + 1,
                'phase': 'timing',
                'solved': res.solved,
                'solution_cost': res.total_cost,
                'action_count': len(res.actions),
                'runtime_ms': round(elapsed_ms, 4),
                'expanded_nodes': res.expanded_nodes,
                'generated_nodes': res.generated_nodes,
                'max_frontier': res.max_frontier_size,
                'peak_memory_kb': None,
                'heuristic_calls': res.heuristic_calls,
                'heuristic_cache_hits': res.heuristic_cache_hits,
                'heuristic_cache_misses': res.heuristic_cache_misses,
            })

        # 3. Memory benchmark: isolated run with tracemalloc ON
        prob_mem = SokobanProblem(board)
        tracemalloc.start()
        res_mem = fn(prob_mem)
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_kb = round(peak_bytes / 1024, 2)

        detailed_rows.append({
            'map': mp.name,
            'algorithm': name,
            'run': 'memory_run',
            'phase': 'memory',
            'solved': res_mem.solved,
            'solution_cost': res_mem.total_cost,
            'action_count': len(res_mem.actions),
            'runtime_ms': round(res_mem.elapsed_ms, 4),
            'expanded_nodes': res_mem.expanded_nodes,
            'generated_nodes': res_mem.generated_nodes,
            'max_frontier': res_mem.max_frontier_size,
            'peak_memory_kb': peak_kb,
            'heuristic_calls': res_mem.heuristic_calls,
            'heuristic_cache_hits': res_mem.heuristic_cache_hits,
            'heuristic_cache_misses': res_mem.heuristic_cache_misses,
        })

        costs[name] = det_result.total_cost
        is_legal = verify_plan(board, det_result.actions)
        assert is_legal, f"Solution plan for {name} on {mp.name} failed legality replay!"

        mean_time = statistics.mean(runtimes)
        median_time = statistics.median(runtimes)

        summary_rows.append({
            'map': mp.name,
            'algorithm': name,
            'runs': len(runtimes),
            'solved': det_result.solved,
            'solution_cost': det_result.total_cost,
            'actions': len(det_result.actions),
            'runtime_ms_mean': round(mean_time, 3),
            'runtime_ms_median': round(median_time, 3),
            'expanded_nodes_mean': det_result.expanded_nodes,
            'generated_nodes_mean': det_result.generated_nodes,
            'max_frontier_mean': det_result.max_frontier_size,
            'peak_memory_kb_mean': peak_kb,
            'heuristic_cache_hits': det_result.heuristic_cache_hits,
            'heuristic_cache_misses': det_result.heuristic_cache_misses,
            'plan_verified_legal': is_legal,
        })
        print(f"[{mp.name}] {name.upper()}: solved={det_result.solved}, cost={det_result.total_cost}, "
              f"mean={mean_time:.2f}ms, med={median_time:.2f}ms, exp={det_result.expanded_nodes}, mem={peak_kb}KB")

    # Verify UCS and A* equal optimal costs
    assert costs['ucs'] == costs['astar'], f"Cost mismatch on {mp.name}: UCS={costs['ucs']} vs A*={costs['astar']}"

with (out / 'benchmark.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(detailed_rows[0].keys()))
    w.writeheader()
    w.writerows(detailed_rows)

with (out / 'benchmark_summary.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
    w.writeheader()
    w.writerows(summary_rows)

print(f"Successfully wrote {len(detailed_rows)} detailed benchmark rows and {len(summary_rows)} summary rows.")
