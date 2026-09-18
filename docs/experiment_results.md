# Experiment Results

The benchmark evaluates duplicate-aware Uniform Cost Search (UCS) and A* Search with Reverse-Push Matching Heuristic across four benchmark maps, including the fully restored assignment map (`example_map.txt`). Timing experiments were conducted with `tracemalloc` completely disabled across 5 measured runs (after 1 warm-up run), reporting both mean and median runtimes. Memory consumption was measured in isolated runs with `tracemalloc` enabled.

## Single-Agent Search Benchmark Summary

| Map | Algorithm | Solved | Cost | Mean Expanded | Generated | Max Frontier | Mean Runtime (ms) | Median Runtime (ms) | Peak Memory (KB) |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| easy_01.txt | UCS | Yes | 3 | 12 | 26 | 9 | 0.140 | 0.130 | 5.56 |
| easy_01.txt | A* | Yes | 3 | 10 | 22 | 9 | 0.180 | 0.160 | 8.60 |
| medium_01.txt | UCS | Yes | 7 | 101 | 240 | 48 | 1.410 | 1.310 | 26.96 |
| medium_01.txt | A* | Yes | 7 | 55 | 134 | 34 | 1.100 | 1.000 | 30.84 |
| hard_01.txt | UCS | Yes | 10 | 811 | 2,059 | 397 | 11.670 | 12.000 | 238.81 |
| hard_01.txt | A* | Yes | 10 | 204 | 525 | 130 | 3.970 | 3.860 | 96.71 |
| **example_map.txt** | **UCS** | **Yes** | **34** | **38,405** | **106,750** | **17,543** | **1019.060** | **1006.710** | **19,546.01** |
| **example_map.txt** | **A\*** | **Yes** | **34** | **6,616** | **18,740** | **3,388** | **565.680** | **556.890** | **3,350.12** |

### Key Findings
1. **Assignment Map Solvability**: When restored character-by-character from the assignment PDF (8 `%` in final row, 8 columns wide, enclosed perimeter) and parsed with proper void isolation, `example_map.txt` is **100% solvable**. Both UCS and A* find the optimal path of 34 steps.
2. **Search Efficiency**: On `example_map.txt`, A* achieves an **82.8% reduction in expanded nodes** (6,616 vs 38,405) and reduces peak memory from 19.5 MB down to 3.35 MB (82.9% reduction).
3. **Optimality Verification**: On all four maps, UCS and A* return identical optimal costs ($3, 7, 10, 34$). Every returned action sequence was verified by step-by-step state simulation.

## Heuristic Validation

Empirical validation checked admissibility ($h(s) \le h^*(s)$ using optimal UCS cost) and monotonicity/consistency ($h(s) \le 1 + h(s')$) across 90 reachable states and 304 successor edges.
- Admissibility violations: **0 / 90 (0.0%)**
- Consistency violations: **0 / 304 (0.0%)**
- Maximum violation: **0.0**

## Competitive Multi-Agent Benchmark

Two autonomous planners were benchmarked:
- **Agent 1 (A*)**: Time-bounded A* graph search minimizing $f(n) = g(n) + h(n)$ with OPEN priority queue and `best_g` pruning.
- **Agent 2 (GBFS)**: Greedy Best-First Search prioritizing minimal $h(n)$ with OPEN priority queue.

Both agents enforce an internal deadline $\le 950$ ms using `time.perf_counter_ns()`. Across all maps and horizons ($n = 10, 25, 50$):
- **Maximum observed decision latency**: 124.26 ms (average 0.45 ms – 66.5 ms).
- **Deadline violations**: **0 / 15 matches (0.0%)**.
- On `competitive_01.txt`, Agent 1 (A*) won 2–1 at $n=25$ and $n=50$.
- On `example_map.txt`, both agents actively navigated corridors and scored boxes onto designated targets.
